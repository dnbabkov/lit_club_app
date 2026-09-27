import asyncio
from contextlib import suppress
from datetime import datetime, timedelta
import logging
from pathlib import Path

from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException


class DailyErrorHandler(logging.FileHandler):
    """Keep only today's records, including across application restarts."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.day = datetime.fromtimestamp(path.stat().st_mtime).date() if path.exists() else datetime.now().date()
        super().__init__(path, encoding="utf-8")
        self.setLevel(logging.WARNING)
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        self.clear_if_new_day()

    def clear_if_new_day(self):
        self.acquire()
        try:
            today = datetime.now().date()
            if today != self.day:
                self.stream.seek(0)
                self.stream.truncate()
                self.stream.flush()
                self.day = today
        finally:
            self.release()

    def emit(self, record):
        self.clear_if_new_day()
        super().emit(record)


def configure_error_logging(path: Path) -> DailyErrorHandler:
    root = logging.getLogger()
    for handler in root.handlers:
        if isinstance(handler, DailyErrorHandler):
            return handler
    handler = DailyErrorHandler(path)
    root.addHandler(handler)
    # Uvicorn's default logger does not propagate records to the root logger.
    uvicorn = logging.getLogger("uvicorn")
    if not uvicorn.propagate:
        uvicorn.addHandler(handler)
    return handler


async def clear_logs_daily(handler: DailyErrorHandler):
    while True:
        handler.clear_if_new_day()
        now = datetime.now()
        midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
        await asyncio.sleep(max(1, midnight.timestamp() - now.timestamp()))


class ErrorLoggingMiddleware:
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger("lit_club_app.backend.errors")

    async def __call__(self, scope, receive, send):
        if scope["type"] not in {"http", "websocket"}:
            return await self.app(scope, receive, send)

        async def log_response(message):
            if message["type"] == "http.response.start" and message["status"] >= 400:
                self.logger.log(
                    logging.ERROR if message["status"] >= 500 else logging.WARNING,
                    "%s %s -> %s", scope.get("method", "WEBSOCKET"), scope["path"], message["status"],
                )
            await send(message)

        try:
            await self.app(scope, receive, log_response)
        except Exception:
            self.logger.exception("Unhandled exception: %s %s", scope.get("method", "WEBSOCKET"), scope["path"])
            raise


def install_error_handlers(app):
    logger = logging.getLogger("lit_club_app.backend.errors")

    @app.exception_handler(HTTPException)
    async def log_http_exception(request, exc):
        # Includes the original traceback when a router converts an exception to HTTPException.
        logger.log(logging.ERROR if exc.status_code >= 500 else logging.WARNING,
                   "%s %s: HTTP %s — %s", request.method, request.url.path,
                   exc.status_code, exc.detail, exc_info=exc if exc.status_code >= 500 else None)
        return await http_exception_handler(request, exc)

    @app.exception_handler(RequestValidationError)
    async def log_validation_exception(request, exc):
        # Do not write request bodies, passwords or Telegram init_data into logs.
        errors = [{"loc": error["loc"], "type": error["type"]} for error in exc.errors()]
        logger.warning("%s %s: validation failed: %s", request.method, request.url.path, errors)
        return await request_validation_exception_handler(request, exc)


async def stop_log_cleanup(task):
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task

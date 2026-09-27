from datetime import datetime, timedelta
import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from starlette.background import BackgroundTask

from lit_club_app.backend.core.logging import DailyErrorHandler, ErrorLoggingMiddleware, install_error_handlers


def test_http_validation_unhandled_and_background_errors_are_logged(tmp_path):
    app = FastAPI()
    app.add_middleware(ErrorLoggingMiddleware)
    install_error_handlers(app)

    @app.get("/handled")
    def handled():
        try:
            raise ValueError("original failure")
        except ValueError as exc:
            raise HTTPException(500, "converted failure") from exc

    @app.get("/unhandled")
    def unhandled():
        raise RuntimeError("unexpected failure")

    @app.get("/validation")
    def validation(count: int):
        return count

    @app.get("/explicit")
    def explicit():
        return JSONResponse({"detail": "unavailable"}, status_code=503)

    @app.get("/background")
    def background():
        def fail():
            raise RuntimeError("background failure")
        return JSONResponse({}, background=BackgroundTask(fail))

    path = tmp_path / "errors.log"
    handler = DailyErrorHandler(path)
    logger = logging.getLogger()
    logger.addHandler(handler)
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            assert client.get("/handled").status_code == 500
            assert client.get("/unhandled").status_code == 500
            assert client.get("/validation?count=secret-input").status_code == 422
            assert client.get("/explicit").status_code == 503
            assert client.get("/missing").status_code == 404
            assert client.get("/background").status_code == 200
        content = path.read_text()
        for expected in ["original failure", "converted failure", "unexpected failure", "background failure",
                         "Traceback", "GET /explicit -> 503", "GET /missing", "validation failed"]:
            assert expected in content
        assert "secret-input" not in content
    finally:
        logger.removeHandler(handler)
        handler.close()


def test_old_logs_cleared_on_restart_and_without_new_records(tmp_path):
    path = tmp_path / "errors.log"
    path.write_text("yesterday's errors")
    yesterday = (datetime.now() - timedelta(days=1)).timestamp()
    os.utime(path, (yesterday, yesterday))
    handler = DailyErrorHandler(path)
    try:
        assert path.read_text() == ""
        record = logging.LogRecord("test", logging.ERROR, __file__, 1, "today's error", (), None)
        handler.handle(record)
        assert "today's error" in path.read_text()
        handler.clear_if_new_day()
        assert "today's error" in path.read_text()
        handler.day = datetime.now().date() - timedelta(days=1)
        handler.clear_if_new_day()
        assert path.read_text() == ""
        assert list(tmp_path.iterdir()) == [path]
    finally:
        handler.close()

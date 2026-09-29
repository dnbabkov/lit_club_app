import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from lit_club_app.backend.core.config import BACKEND_DIR, settings
from lit_club_app.backend.core.logging import (
    ErrorLoggingMiddleware, clear_logs_daily, configure_error_logging,
    install_error_handlers, stop_log_cleanup,
)

error_log_handler = configure_error_logging(BACKEND_DIR / "logs" / "errors.log")

from fastapi.middleware.cors import CORSMiddleware

from lit_club_app.backend.users.router import router as users_router
from lit_club_app.backend.selections.router import router as selections_router
from lit_club_app.backend.meetings.router import router as meetings_router
from lit_club_app.backend.books.router import router as books_router
from lit_club_app.backend.reviews.router import router as reviews_router
from lit_club_app.backend.quotes.router import router as quotes_router
from lit_club_app.backend.comics.router import router as comics_router
from lit_club_app.backend.shark.router import router as achievements_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup = asyncio.create_task(clear_logs_daily(error_log_handler))
    try:
        yield
    finally:
        await stop_log_cleanup(cleanup)


app = FastAPI(
    title="Literature Club API",
    version="0.1.0",
    lifespan=lifespan,
)

install_error_handlers(app)
app.add_middleware(ErrorLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
                   "http://127.0.0.1:5173",
                   "https://litclub.nnbabkov.ru:8000",
                   "https://77.110.119.153:8000",
                   ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings.upload_dir.mkdir(parents=True, exist_ok=True)

app.include_router(users_router)
app.include_router(selections_router)
app.include_router(meetings_router)
app.include_router(books_router)
app.include_router(reviews_router)
app.include_router(quotes_router)
app.include_router(comics_router)
app.include_router(achievements_router)

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

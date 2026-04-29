from fastapi import FastAPI

from lit_club_app.users.router import router as users_router
from lit_club_app.selections.router import router as selections_router
from lit_club_app.meetings.router import router as meetings_router
from lit_club_app.books.router import router as books_router
from lit_club_app.reviews.router import router as reviews_router

app = FastAPI(
    title="Literature Club API",
    version="0.1.0",
)

app.include_router(users_router)
app.include_router(selections_router)
app.include_router(meetings_router)
app.include_router(books_router)
app.include_router(reviews_router)
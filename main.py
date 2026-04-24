from fastapi import FastAPI

from lit_club_app.users.router import router as users_router

app = FastAPI(
    title="Literature Club API",
    version="0.1.0",
)

app.include_router(users_router)
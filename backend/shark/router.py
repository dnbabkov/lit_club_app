from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from lit_club_app.backend.api.dependencies import get_current_user, get_db
from lit_club_app.backend.core.config import BASE_DIR
from lit_club_app.backend.common.enums import Roles
from lit_club_app.backend.shark import service
from lit_club_app.backend.shark.models import Achievement
from lit_club_app.backend.shark.schemas import AchievementRead
from lit_club_app.backend.users.models import User

router = APIRouter(prefix="/achievements", tags=["achievements"])


def get_profile_achievements(db: Session, owner: User):
    rows = db.execute(
        select(Achievement, User).join(User, Achievement.giver_id == User.id)
        .where(Achievement.user_id == owner.id).order_by(Achievement.id.desc())
    )
    return [
        {"id": achievement.id, "image_url": f"/achievements/{achievement.id}/image",
         "giver": {"id": giver.id, "username": giver.username}}
        for achievement, giver in rows
    ]


def require_visible_profile(owner: User | None, viewer: User):
    if owner is None or (owner.role == Roles.ADMIN and viewer.role != Roles.ADMIN):
        raise HTTPException(404, "Пользователь не найден")


@router.get("/me", response_model=list[AchievementRead])
def my_achievements(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_profile_achievements(db, user)


@router.get("/{achievement_id}/image")
def achievement_image(achievement_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    achievement = db.scalar(select(Achievement).where(
        Achievement.id == achievement_id,
    ))
    if achievement is None:
        raise HTTPException(404, "Ачивка не найдена")
    require_visible_profile(db.get(User, achievement.user_id), user)

    path = Path(achievement.path)
    if not path.is_absolute():
        path = service.achievements_path / path if len(path.parts) == 1 else BASE_DIR / path
    path = path.resolve()
    if not path.is_relative_to(service.achievements_path.resolve()) or not path.is_file():
        raise HTTPException(404, "Изображение ачивки не найдено")
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "private, no-store"})

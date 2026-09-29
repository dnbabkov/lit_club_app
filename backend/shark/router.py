from pathlib import Path
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from lit_club_app.backend.api.dependencies import get_current_user, get_db
from lit_club_app.backend.core.config import BASE_DIR
from lit_club_app.backend.common.enums import Roles
from lit_club_app.backend.shark import service
from lit_club_app.backend.shark.models import Achievement
from lit_club_app.backend.shark.schemas import AchievementRead
from lit_club_app.backend.shark.repository import AchievementRepository
from lit_club_app.backend.users.models import User

router = APIRouter(prefix="/achievements", tags=["achievements"])
logger = logging.getLogger(__name__)


def get_profile_achievements(db: Session, owner: User):
    rows = db.execute(
        select(Achievement, User).join(User, Achievement.giver_id == User.id)
        .where(Achievement.user_id == owner.id).order_by(Achievement.id.desc())
    )
    return [
        {"id": achievement.id, "image_url": f"/achievements/{achievement.id}/image",
         "giver": {"id": giver.id, "username": giver.username},
         "title": achievement.title, "description": achievement.description}
        for achievement, giver in rows
    ]


def require_visible_profile(owner: User | None, viewer: User):
    if owner is None or (owner.role == Roles.ADMIN and viewer.role != Roles.ADMIN):
        raise HTTPException(404, "Пользователь не найден")


def require_visible_achievement_owner(owner: User | None, viewer: User):
    if owner is None:
        raise HTTPException(404, "Пользователь не найден")


@router.get("/me", response_model=list[AchievementRead], response_model_exclude_none=True)
def my_achievements(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_profile_achievements(db, user)


@router.post("", response_model=AchievementRead, response_model_exclude_none=True, status_code=201)
async def create_achievement(
    recipient_id: int = Form(...), title: str = Form(...), description: str = Form(...),
    image: UploadFile = File(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    title = title.strip()
    description = description.strip()
    if not title or len(title) > 200:
        raise HTTPException(422, "Название должно содержать от 1 до 200 символов")
    if not description or len(description) > 5000:
        raise HTTPException(422, "Описание должно содержать от 1 до 5000 символов")
    recipient = db.get(User, recipient_id)
    if recipient is None:
        raise HTTPException(404, "Пользователь не найден")
    filename = await service.compose_uploaded_image(image, title, description)
    try:
        achievement = AchievementRepository().create(
            db, recipient.id, filename, user.id, title, description,
        )
    except Exception:
        (service.private_achievements_path() / filename).unlink(missing_ok=True)
        raise
    return {"id": achievement.id, "image_url": f"/achievements/{achievement.id}/image",
            "giver": {"id": user.id, "username": user.username},
            "title": achievement.title, "description": achievement.description}


@router.get("/{achievement_id}/image")
def achievement_image(achievement_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    achievement = db.scalar(select(Achievement).where(
        Achievement.id == achievement_id,
    ))
    if achievement is None:
        raise HTTPException(404, "Ачивка не найдена")
    require_visible_achievement_owner(db.get(User, achievement.user_id), user)

    path = _achievement_path(achievement.path)
    if path is None or not path.is_file():
        raise HTTPException(404, "Изображение ачивки не найдено")
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "private, no-store"})


def _achievement_path(value: str) -> Path | None:
    resolved = _canonical_achievement_path(value)
    if resolved is not None and resolved.is_file():
        return resolved
    return None


def _canonical_achievement_path(value: str) -> Path | None:
    candidate = Path(value)
    roots = [service.private_achievements_path(), service.achievements_path]
    if not candidate.is_absolute():
        if len(candidate.parts) == 1:
            candidates = [root / candidate for root in roots]
        else:
            candidates = [BASE_DIR / candidate]
            roots = [service.achievements_path]
    else:
        candidates = [candidate, candidate]
    for item, root in zip(candidates, roots):
        try:
            resolved = item.resolve()
            if resolved.is_relative_to(root.resolve()) and (candidate.is_absolute() or resolved.is_file()):
                return resolved
        except (OSError, RuntimeError):
            continue
    return None


@router.delete("/{achievement_id}", status_code=204)
def delete_achievement(achievement_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    repository = AchievementRepository()
    achievement = repository.get(db, achievement_id)
    if achievement is None:
        raise HTTPException(404, "Ачивка не найдена")
    if achievement.giver_id != user.id and user.role != Roles.ADMIN:
        raise HTTPException(403, "Удалять ачивку может только выдавший её пользователь или администратор")
    stored_path = achievement.path
    path = _achievement_path(stored_path)
    canonical_path = _canonical_achievement_path(stored_path)
    repository.delete_achievement(db, achievement_id)
    private_root = service.private_achievements_path().resolve()
    if canonical_path is not None and canonical_path.is_relative_to(private_root):
        remaining_paths = db.scalars(select(Achievement.path)).all()
        remaining = any(
            _canonical_achievement_path(value) == canonical_path for value in remaining_paths
        )
        if not remaining and path is not None:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                logger.warning("Could not remove achievement image", exc_info=True)

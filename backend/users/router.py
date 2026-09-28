import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from lit_club_app.backend.api.dependencies import get_db, get_current_user
from lit_club_app.backend.common.enums import Roles
from lit_club_app.backend.core.security import create_access_token
from lit_club_app.backend.core.config import settings
from lit_club_app.backend.core.telegram import InvalidTelegramData, validate_init_data
from lit_club_app.backend.users.repository import UserRepository
from lit_club_app.backend.users.models import User
from lit_club_app.backend.users.schemas import TelegramLogin, UserRead, TokenResponse, UserProfileRead, UserPublicRead, UserAdminWrite, UserAdminRead
from lit_club_app.backend.users.service import user_service
from lit_club_app.backend.shark.router import get_profile_achievements, require_visible_profile
from lit_club_app.backend.shark.schemas import AchievementRead
from lit_club_app.backend.core.exceptions import (
    UserNotFoundError,
)

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != Roles.ADMIN:
        raise HTTPException(status_code=403, detail="Only admin can manage users")
    return user


@router.post("/", response_model=UserAdminRead, status_code=201, dependencies=[Depends(require_admin)])
def create_user(payload: UserAdminWrite, db: Session = Depends(get_db)):
    try:
        return user_service.save_admin_user(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.patch("/{user_id}", response_model=UserAdminRead, dependencies=[Depends(require_admin)])
def edit_user(user_id: int, payload: UserAdminWrite, db: Session = Depends(get_db)):
    user = UserRepository().get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        return user_service.save_admin_user(db, payload, user)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

@router.post("/auth/dev", response_model=TokenResponse)
def login_dev(db: Session = Depends(get_db)):
    if not settings.dev_auth_allowed:
        raise HTTPException(status_code=404, detail="Not found")
    if settings.dev_auth_user_id is None:
        raise HTTPException(status_code=503, detail="DEV_AUTH_USER_ID is not configured")
    user = UserRepository().get_by_id(db, settings.dev_auth_user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=403, detail="Access not granted")
    access_token = create_access_token({"sub": str(user.id), "auth_method": "dev"})
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post("/auth/telegram", response_model=TokenResponse)
def login_telegram(payload: TelegramLogin, db: Session = Depends(get_db)):
    token = settings.telegram_bot_token
    if token is None or not token.get_secret_value().strip():
        raise HTTPException(status_code=503, detail="Telegram authentication is not configured")
    try:
        tg_id = validate_init_data(payload.init_data, token.get_secret_value(),
                                   settings.telegram_init_data_max_age_seconds)
    except InvalidTelegramData as exc:
        logger.warning(
            "Telegram login rejected: reason=%s age_seconds=%s max_age_seconds=%s",
            exc.reason, exc.age_seconds, settings.telegram_init_data_max_age_seconds,
        )
        raise HTTPException(status_code=401, detail="Invalid or expired Telegram data")
    user = UserRepository().get_by_tg_id(db, tg_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=403, detail="Access not granted")
    access_token = create_access_token({
        "sub": str(user.id), "auth_method": "telegram", "tg_id": str(tg_id),
    })
    return TokenResponse(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserRead, status_code=200)
def get_user_me(current_user: User = Depends(get_current_user)):
    try:
        return current_user
    except:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/me/profile/achievements", response_model=list[AchievementRead])
def my_profile_achievements(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_profile_achievements(db, current_user)


@router.get("/{username}/profile/achievements", response_model=list[AchievementRead])
def user_profile_achievements(username: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    owner = UserRepository().get_by_username(db, username)
    require_visible_profile(owner, current_user)
    return get_profile_achievements(db, owner)


@router.get("/me/profile", response_model=UserProfileRead, status_code=200)
def get_user_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        return user_service.get_user_profile(db=db, user_id=current_user.id)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.get("/", response_model=list[UserAdminRead], status_code=200, dependencies=[Depends(require_admin)])
def get_all_users(db: Session = Depends(get_db)):
    try:
        return user_service.get_all_users(db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.get("/public", response_model=list[UserPublicRead], status_code=200, dependencies=[Depends(get_current_user)])
def get_all_users_public(db: Session = Depends(get_db)):
    try:
        return user_service.get_all_non_admin_users(db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.get("/{username}/profile", response_model=UserProfileRead, status_code=200)
def get_other_user_profile(username: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        user = user_service.get_user_by_username(db=db, username=username)
        if user.role == Roles.ADMIN and current_user.role != Roles.ADMIN:
            raise UserNotFoundError()
        return user_service.get_user_profile(db=db, user_id=user.id)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

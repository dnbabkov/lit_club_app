from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from lit_club_app.backend.api.dependencies import get_db, get_current_user
from lit_club_app.backend.common.enums import Roles
from lit_club_app.backend.core.security import create_access_token
from lit_club_app.backend.users.models import User
from lit_club_app.backend.users.schemas import UserRegister, UserLogin, UserRead, TokenResponse, UserProfileRead, \
    UpdatePassword, UpdatePasswordAdmin, UserPublicRead
from lit_club_app.backend.users.service import user_service
from lit_club_app.backend.core.exceptions import (
    UsernameAlreadyExistsError,
    TelegramLoginAlreadyExistsError,
    UserNotFoundError,
    InvalidPasswordError, EmptyTelegramLoginError, SamePasswordError, NotEnoughPermissionsError,
)

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=TokenResponse, status_code=201)
def register_user(payload: UserRegister, db: Session = Depends(get_db)):
    try:
        user = user_service.register_user(db=db, user_data=payload)
        access_token = create_access_token({"sub": str(user.id)})
        return TokenResponse(access_token=access_token, token_type="bearer")
    except (UsernameAlreadyExistsError, TelegramLoginAlreadyExistsError, EmptyTelegramLoginError) as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    try:
        user = user_service.authenticate_user(db=db, login_data=payload)
        access_token = create_access_token({"sub": str(user.id)})
        return TokenResponse(access_token=access_token, token_type="bearer")
    except (UserNotFoundError, InvalidPasswordError):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except EmptyTelegramLoginError:
        raise HTTPException(status_code=409, detail="Empty TG tag")

@router.get("/me", response_model=UserRead, status_code=200)
def get_user_me(current_user: User = Depends(get_current_user)):
    try:
        return current_user
    except:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/me/profile", response_model=UserProfileRead, status_code=200)
def get_user_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        return user_service.get_user_profile(db=db, user_id=current_user.id)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.get("/", response_model=list[UserRead], status_code=200, dependencies=[Depends(get_current_user)])
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

@router.patch("/me/profile/password", response_model=UserRead, status_code=200)
def update_user_password(payload: UpdatePassword, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return user_service.update_user_password(db=db, user=user, current_password=payload.current_password, new_password=payload.new_password)
    except InvalidPasswordError:
        raise HTTPException(status_code=401, detail="Incorrect password")
    except SamePasswordError:
        raise HTTPException(status_code=409, detail="New password can't be the same as the old password")
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

@router.patch("/{user_id}/profile/password", response_model=UserRead, status_code=200)
def update_user_password_admin(payload: UpdatePasswordAdmin, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        return user_service.update_user_password_admin(db=db, user=current_user, target_user_id=user_id, new_password=payload.new_password)
    except NotEnoughPermissionsError:
        raise HTTPException(status_code=403, detail="Only admin can change others' passwords!")
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from lit_club_app.backend.api.dependencies import get_db, get_current_user
from lit_club_app.backend.core.security import create_access_token
from lit_club_app.backend.users.models import User
from lit_club_app.backend.users.schemas import UserRegister, UserLogin, UserRead, TokenResponse, UserProfileRead
from lit_club_app.backend.users.service import user_service
from lit_club_app.backend.core.exceptions import (
    UsernameAlreadyExistsError,
    TelegramLoginAlreadyExistsError,
    UserNotFoundError,
    InvalidPasswordError, EmptyTelegramLoginError,
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
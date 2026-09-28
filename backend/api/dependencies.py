from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from lit_club_app.backend.db.session import SessionLocal
from lit_club_app.backend.core.security import decode_access_token
from lit_club_app.backend.core.config import settings
from lit_club_app.backend.users.models import User
from lit_club_app.backend.users.repository import UserRepository

security = HTTPBearer(auto_error=False)
user_repo = UserRepository()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> User:

    if not credentials:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    auth_method = payload.get("auth_method")
    if auth_method == "dev":
        if not settings.dev_auth_allowed:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    elif auth_method != "telegram":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    subject = payload.get("sub")
    if subject is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        user_id = int(subject)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = user_repo.get_by_id(db=db, user_id=user_id)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if auth_method == "dev" and user.id != settings.dev_auth_user_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if auth_method == "telegram" and (user.tg_id is None or payload.get("tg_id") != str(user.tg_id)):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Access not granted")

    return user

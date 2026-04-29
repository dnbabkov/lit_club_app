from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from lit_club_app.backend.db.session import SessionLocal
from lit_club_app.backend.core.security import decode_access_token
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

    return user
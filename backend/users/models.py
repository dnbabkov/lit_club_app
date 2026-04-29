from sqlalchemy import Column, Integer, String, Enum
from lit_club_app.backend.db.base import Base
from lit_club_app.backend.common.enums import Roles

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    telegram_login = Column(String, unique=True, nullable=False, index=True)
    role = Column(Enum(Roles), nullable=False, default=Roles.MEMBER)
    password_hash = Column(String, nullable=False)
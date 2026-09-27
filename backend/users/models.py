from sqlalchemy import BigInteger, Boolean, Column, Integer, String, Enum, UniqueConstraint, true
from lit_club_app.backend.db.base import Base
from lit_club_app.backend.common.enums import Roles

class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tg_id", name="uq_users_tg_id"),)

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    telegram_login = Column(String, unique=True, nullable=True, index=True)
    tg_id = Column(BigInteger, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default=true())
    role = Column(Enum(Roles), nullable=False, default=Roles.MEMBER)
    # Removed in a later migration when password-based endpoints are retired.
    password_hash = Column(String, nullable=True)

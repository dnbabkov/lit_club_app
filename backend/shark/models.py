from sqlalchemy import Integer, VARCHAR, BigInteger, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from lit_club_app.backend.db.base import Base

class Achievement(Base):
    __tablename__='achievement'

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    path: Mapped[str] = mapped_column(VARCHAR(), nullable=False)
    giver_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    title: Mapped[str | None] = mapped_column(VARCHAR(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

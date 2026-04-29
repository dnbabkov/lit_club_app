from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey
from lit_club_app.backend.db.base import Base

from lit_club_app.backend.common.enums import MeetingStatus

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=True)
    scheduled_for = Column(DateTime, nullable=True)
    status = Column(Enum(MeetingStatus), nullable=False, default=MeetingStatus.BOOK_SELECTION)
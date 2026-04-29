from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from lit_club_app.meetings.models import Meeting
from lit_club_app.common.enums import MeetingStatus

class MeetingRepository:
    def get_by_id(self, db: Session, meeting_id: int) -> Meeting | None:
        statement = (
            select(Meeting)
            .where(Meeting.id == meeting_id)
        )
        result = db.execute(statement)
        return result.scalar_one_or_none()
    def create_meeting(self, db: Session, status: MeetingStatus = MeetingStatus.BOOK_SELECTION, book_id: int | None = None, scheduled_for: datetime | None = None) -> Meeting:
        meeting = Meeting(book_id=book_id, scheduled_for=scheduled_for, status=status)
        try:
            db.add(meeting)
            db.commit()
            db.refresh(meeting)
            return meeting
        except Exception:
            db.rollback()
            raise

    def assign_book(self, db: Session, meeting: Meeting, book_id: int) -> Meeting:
        try:
            meeting.book_id = book_id
            db.commit()
            db.refresh(meeting)
            return meeting
        except Exception:
            db.rollback()
            raise

    def update_status(self, db: Session, meeting: Meeting, target_status: MeetingStatus) -> Meeting:
        try:
            meeting.status = target_status
            db.commit()
            db.refresh(meeting)
            return meeting
        except Exception:
            db.rollback()
            raise

    def assign_book_no_commit(self, db: Session, meeting: Meeting, book_id: int) -> Meeting:
        meeting.book_id = book_id
        return meeting

    def schedule_meeting(self, db: Session, meeting: Meeting, scheduled_for: datetime) -> Meeting:
        try:
            meeting.scheduled_for = scheduled_for
            meeting.status = MeetingStatus.SCHEDULED
            db.commit()
            db.refresh(meeting)
            return meeting
        except Exception:
            db.rollback()
            raise

    def get_all(self, db: Session) -> Sequence[Meeting]:
        statement = select(Meeting).order_by(Meeting.id.desc())
        result = db.execute(statement)
        return result.scalars().all()

    def get_latest(self, db: Session) -> Meeting | None:
        statement = select(Meeting).order_by(Meeting.id.desc()).limit(1)
        result = db.execute(statement)
        return result.scalar_one_or_none()

    def get_meetings_by_year(self, db: Session, year: int) -> Sequence[Meeting]:
        start_date = datetime(year, 1, 1)
        end_date = datetime(year+1, 1, 1)
        statement = (
            select(Meeting)
            .where(
                Meeting.scheduled_for >= start_date,
                Meeting.scheduled_for < end_date,
            )
            .order_by(Meeting.id.desc())
        )
        result = db.execute(statement)
        return result.scalars().all()
from datetime import datetime
from typing import Sequence

from sqlalchemy.orm import Session

from lit_club_app.backend.common.enums import MeetingStatus
from lit_club_app.backend.core.exceptions import (
    MeetingNotFoundError, LatestMeetingNotFinishedError, ScheduleInThePastError,
    CantFinishMeetingError, LatestMeetingNotStartedError,
)
from lit_club_app.backend.meetings.models import Meeting
from lit_club_app.backend.meetings.repository import MeetingRepository
from lit_club_app.backend.meetings.schemas import (
    MeetingCreate,
    MeetingRead,
    MeetingScheduleUpdate,
    MeetingStatusUpdate, MeetingWithSelectionRead,
)
from lit_club_app.backend.selections.repository import BookSelectionRepository
from lit_club_app.backend.selections.models import BookSelection
from lit_club_app.backend.selections.service import selection_service

class MeetingService:
    def __init__(self):
        self.book_selection_repo = BookSelectionRepository()
        self.meeting_repo = MeetingRepository()

    def create_meeting(self, db: Session, status: MeetingStatus | None = None, book_id: int | None = None, scheduled_for: datetime | None = None) -> Meeting:
        latest_meeting = self.get_latest_meeting(db=db)
        if status is None:
            status = MeetingStatus.BOOK_SELECTION
        if latest_meeting is None:
            return self.meeting_repo.create_meeting(db=db, status=status, book_id=book_id, scheduled_for=scheduled_for)
        if latest_meeting.status != MeetingStatus.FINISHED:
            raise LatestMeetingNotFinishedError()
        return self.meeting_repo.create_meeting(db=db, status=status, book_id=book_id, scheduled_for=scheduled_for)

    def get_latest_meeting(self, db: Session) -> Meeting | None:
        return self.meeting_repo.get_latest(db=db)

    def get_meeting_by_id(self, db: Session, meeting_id: int) -> Meeting:
        meeting = self.meeting_repo.get_by_id(db=db, meeting_id=meeting_id)
        if meeting is None:
            raise MeetingNotFoundError()
        return meeting

    def get_all_meetings(self, db: Session) -> Sequence[Meeting]:
        return self.meeting_repo.get_all(db=db)

    def get_meetings_by_year(self, db: Session, year: int) -> Sequence[Meeting]:
        return self.meeting_repo.get_meetings_by_year(db=db, year=year)

    def schedule_meeting(self, db: Session, meeting_id: int, scheduled_for: datetime) -> Meeting:
        meeting = self.get_meeting_by_id(db=db, meeting_id=meeting_id)
        if scheduled_for < datetime.now():
            raise ScheduleInThePastError()
        return self.meeting_repo.schedule_meeting(db=db, meeting=meeting, scheduled_for=scheduled_for)

    def finish_meeting(self, db: Session, meeting_id: int) -> Meeting:
        meeting = self.meeting_repo.get_by_id(db=db,meeting_id=meeting_id)
        if meeting is None:
            raise MeetingNotFoundError()
        if meeting.status != MeetingStatus.SCHEDULED:
            raise CantFinishMeetingError()
        return self.meeting_repo.update_status(db=db, meeting=meeting, target_status=MeetingStatus.FINISHED)

    def start_next(self, db: Session) -> MeetingWithSelectionRead:
        latest_meeting = self.get_latest_meeting(db=db)
        if latest_meeting is None or latest_meeting.status == MeetingStatus.FINISHED:
            new_meeting = self.create_meeting(db=db)
            new_selection = selection_service.create_selection(db=db, meeting_id=new_meeting.id)
            state = {
                "meeting": MeetingRead.model_validate(new_meeting),
                "selection_id": new_selection.id
            }
            return MeetingWithSelectionRead.model_validate(state)
        if latest_meeting.status == MeetingStatus.BOOK_SELECTION:
            raise LatestMeetingNotStartedError()
        self.finish_meeting(db=db, meeting_id=latest_meeting.id)
        new_meeting = self.create_meeting(db=db)
        new_selection = selection_service.create_selection(db=db, meeting_id=new_meeting.id)
        state = {
            "meeting": MeetingRead.model_validate(new_meeting),
            "selection_id": new_selection.id
        }
        return MeetingWithSelectionRead.model_validate(state)

meeting_service = MeetingService()
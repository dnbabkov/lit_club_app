from datetime import datetime

from pydantic import BaseModel, ConfigDict

from lit_club_app.backend.common.enums import MeetingStatus

class MeetingCreate(BaseModel):
    status: MeetingStatus | None = None
    book_id: int | None = None
    scheduled_for: datetime | None = None

class MeetingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: MeetingStatus
    book_id: int | None
    scheduled_for: datetime | None

class MeetingScheduleUpdate(BaseModel):
    scheduled_for: datetime

class MeetingStatusUpdate(BaseModel):
    status: MeetingStatus

class MeetingWithSelectionRead(BaseModel):
    meeting: MeetingRead
    selection_id: int
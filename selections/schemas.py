from pydantic import BaseModel, ConfigDict

from lit_club_app.common.enums import BookSelectionStatus

class BookSelectionCreate(BaseModel):
    meeting_id: int

class BookSelectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    meeting_id: int
    status: BookSelectionStatus
    winning_nomination_id: int | None

class NominationCreate(BaseModel):
    selection_id: int
    title: str
    author: str
    comment: str | None

class NominationUpdate(BaseModel):
    title: str
    author: str
    comment: str | None

class NominationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    selection_id: int
    book_id: int
    title: str
    author: str
    comment: str | None

class VoteCreate(BaseModel):
    selection_id: int
    nomination_ids: list[int]

class VoteCountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    nomination_id: int
    vote_count: int

class WinnerSelectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    selection_id: int
    winning_nomination_id: int
    book_id: int
    title: str
    author: str
    vote_count: int
from pydantic import BaseModel, ConfigDict

from lit_club_app.common.enums import BookSelectionStatus, WinnerSelectionStatus


class BookSelectionCreate(BaseModel):
    meeting_id: int

class BookSelectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    meeting_id: int
    status: BookSelectionStatus
    winning_nomination_id: int | None

class NominationCreate(BaseModel):
    title: str
    author: str
    comment: str | None

class NominationUpdate(BaseModel):
    title: str
    author: str
    comment: str | None

class NominationCommentUpdate(BaseModel):
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
    description: str | None
    vote_count: int

class WinnerSelectionStepCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nomination_id: int
    vote_count: int
    elimination_weight: float
    elimination_probability: float
    was_eliminated: bool

class WinnerSelectionStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    step_id: int
    round_number: int
    eliminated_nomination_id: int
    candidates: list[WinnerSelectionStepCandidateRead]

class WinnerSelectionStateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: int
    selection_id: int
    status: WinnerSelectionStatus
    current_round: int
    winner_nomination_id: int | None
    steps: list[WinnerSelectionStepRead]
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from lit_club_app.backend.common.enums import MeetingStatus
from lit_club_app.backend.files.schemas import BookFileRead
from lit_club_app.backend.reviews.schemas import ReviewRead

class BookCreate(BaseModel):
    title: str
    author: str
    description: str | None
    epoch: str | None = Field(default=None, max_length=10)
    meeting_date: date | None = None

    @field_validator("meeting_date", mode="before")
    @classmethod
    def empty_date_is_none(cls, value):
        return None if value == "" else value

class BookChangeDescription(BaseModel):
    description: str

class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    epoch: str | None
    meeting_date: date | None
    description: str | None
    user_id: int | None

    cover_url : str | None = None
    book_file: BookFileRead | None = None

class CanDeleteBookRead(BaseModel):
    book: BookRead
    can_delete: bool

class BookWithReviewsRead(BaseModel):
    book: BookRead
    reviews: list[ReviewRead]

class BooksRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    books: list[CanDeleteBookRead]

class BookAssignUser(BaseModel):
    user_id: int

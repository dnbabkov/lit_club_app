from pydantic import BaseModel, ConfigDict

from lit_club_app.backend.common.enums import MeetingStatus
from lit_club_app.backend.reviews.schemas import ReviewRead

class BookCreate(BaseModel):
    title: str
    author: str
    description: str | None

class BookChangeDescription(BaseModel):
    description: str

class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    description: str | None

class BookWithReviewsRead(BaseModel):
    book: BookRead
    reviews: list[ReviewRead]

class BooksRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    books: list[BookRead]
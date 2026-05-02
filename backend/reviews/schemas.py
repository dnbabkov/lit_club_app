from pydantic import BaseModel, ConfigDict

class ReviewCreate(BaseModel):
    book_id: int
    rating: int
    anonymous: bool
    review_text: str | None

class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str | None
    book_id: int
    rating: int
    anonymous: bool
    review_text: str | None
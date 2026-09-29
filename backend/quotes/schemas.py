from pydantic import BaseModel, ConfigDict, Field, field_validator


class QuoteCreate(BaseModel):
    book_id: int
    text: str = Field(min_length=1, max_length=10000)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Quote text cannot be blank")
        return value


class QuoteUpdate(BaseModel):
    text: str = Field(min_length=1, max_length=10000)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Quote text cannot be blank")
        return value


class QuoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    user_id: int
    username: str
    text: str


class RandomQuoteRead(BaseModel):
    book_id: int
    book_title: str
    book_author: str
    text: str

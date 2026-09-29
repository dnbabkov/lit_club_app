from pydantic import BaseModel, Field, ConfigDict, field_validator, field_serializer
from lit_club_app.backend.common.enums import Roles

class TelegramLogin(BaseModel):
    init_data: str = Field(min_length=1, max_length=16384)

class UserRegister(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    telegram_login: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=4, max_length=50)

class UserLogin(BaseModel):
    telegram_login: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=4, max_length=50)

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str = Field(min_length=1, max_length=50)
    telegram_login: str | None = Field(min_length=1, max_length=64)
    role: Roles

class UserPublicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str = Field(min_length=1, max_length=50)


class UserSelfUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    username: str = Field(min_length=1, max_length=50)


class UserAdminWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    username: str = Field(min_length=1, max_length=50)
    tg_id: int | None = Field(ge=1, le=2**63 - 1)
    telegram_login: str | None = Field(default=None, max_length=64, pattern=r"^[a-z0-9_]+$")

    @field_validator("tg_id", mode="before")
    @classmethod
    def validate_telegram_id(cls, value):
        if value is None or type(value) is int:
            return value
        if isinstance(value, str) and value.isascii() and value.isdecimal():
            return int(value)
        raise ValueError("Telegram ID must be a positive integer")

    @field_validator("telegram_login", mode="before")
    @classmethod
    def normalize_login(cls, value):
        if isinstance(value, str):
            return value.strip().removeprefix("@").lower() or None
        return value


class UserAdminRead(UserRead):
    tg_id: int | None

    @field_serializer("tg_id")
    def serialize_telegram_id(self, value: int | None) -> str | None:
        # Keep BIGINT exact when consumed by JavaScript.
        return str(value) if value is not None else None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class UserProfileBookRatingRead(BaseModel):
    username: str | None
    rating: int

class UserProfileBookRead(BaseModel):
    book_id: int
    title: str
    author: str
    nomination_count: int
    meeting_dates: list[str]
    has_won: bool
    ratings: list[UserProfileBookRatingRead]

class UserProfileRead(BaseModel):
    id: int
    username: str
    telegram_login: str | None
    role: Roles
    nominated_books: list[UserProfileBookRead]

class UpdatePassword(BaseModel):
    current_password: str = Field(min_length=4, max_length=50)
    new_password: str = Field(min_length=4, max_length=50)

class UpdatePasswordAdmin(BaseModel):
    new_password: str = Field(min_length=4, max_length=50)

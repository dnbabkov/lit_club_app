from pydantic import BaseModel, Field, ConfigDict
from lit_club_app.backend.common.enums import Roles

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
    telegram_login: str = Field(min_length=1, max_length=64)
    role: Roles

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

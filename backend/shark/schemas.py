from pydantic import BaseModel, Field, ConfigDict


class AchievementGiverRead(BaseModel):
    id: int
    username: str


class AchievementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: str
    giver: AchievementGiverRead
    title: str | None = None
    description: str | None = None


class AchievementWrite(BaseModel):
    recipient_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)

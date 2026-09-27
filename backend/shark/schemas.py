from pydantic import BaseModel


class AchievementGiverRead(BaseModel):
    id: int
    username: str


class AchievementRead(BaseModel):
    id: int
    image_url: str
    giver: AchievementGiverRead

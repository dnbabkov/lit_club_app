from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    secret_key: str
    alg: str = "HS256"
    access_token_expire_minutes: int = 240

settings = Settings()
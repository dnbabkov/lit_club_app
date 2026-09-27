from pathlib import Path
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = BASE_DIR / "backend"
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    telegram_bot_token: SecretStr | None = None
    telegram_init_data_max_age_seconds: int = Field(default=300, ge=1)

    upload_dir: Path = BACKEND_DIR / "uploads"
    public_uploads_url: str = "/uploads"

    max_cover_size_bytes: int = 5 * 1024 * 1024
    max_book_file_size_bytes: int = 10 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
    )

    log_file: str
    old_log_file: str


    log_file: str
    old_log_file: str
    max_log_size: str

    mime_file: str
    max_mime_size: str

    test_db_user: str
    test_db_password: str
    test_db_host: str
    test_db_port: str
    test_db_name: str

    api_id: str
    api_hash: str

settings = Settings()

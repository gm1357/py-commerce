from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# apps/api/src/api/core/config.py -> repo root
REPO_ROOT = Path(__file__).resolve().parents[5]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/pycommerce"
    cors_origins: list[str] = ["http://localhost:3000"]
    session_ttl_days: int = 7
    # Send the session cookie over HTTPS only. Keep it off for local http:// development.
    cookie_secure: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()

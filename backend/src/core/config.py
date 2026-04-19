from functools import lru_cache

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    POSTGRES_USER: str | None = Field(default=None)
    POSTGRES_PASSWORD: str | None = Field(default=None)
    POSTGRES_DB: str | None = Field(default=None)
    DATABASE_URL: PostgresDsn = Field(...)

    BACKEND_URL: str = Field(default="http://backend:8000")
    VITE_API_URL: str = Field(default="http://localhost:8000")

    SCRAPER_CRON: str = Field(default="0 3 * * 0")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

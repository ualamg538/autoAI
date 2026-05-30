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

    OPENAI_API_KEY: str | None = Field(default=None)
    OPENAI_MODEL: str = Field(default="gpt-5.4-mini-2026-03-17")

    # Directorio base permitido para /ingest (el volumen scraper_output:/data).
    INGEST_DIR: str = Field(default="/data")

    # Orígenes CORS permitidos, en CSV. En prod, poner la URL real del front.
    CORS_ORIGINS: str = Field(default="http://localhost:5173")

    # Hooks de seguridad de /chat e /ingest, INERTES por defecto.
    RATE_LIMIT_PER_MIN: int = Field(default=0)  # 0 = desactivado
    CHAT_API_KEY: str | None = Field(default=None)  # None = desactivado

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

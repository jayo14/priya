"""Priya application configuration module using Pydantic Settings."""

from typing import List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    APP_NAME: str = "Priya"
    APP_ENV: str = "development"
    DEBUG: bool = True

    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    DATABASE_URL: str = Field(
        default="postgresql+psycopg://priya_user:priya_pass@127.0.0.1:5432/priya",
        description="PostgreSQL connection string with psycopg driver",
    )
    TEST_DATABASE_URL: Optional[str] = Field(
        default="postgresql+psycopg://priya_user:priya_pass@127.0.0.1:5432/priya_test",
        description="Test PostgreSQL database connection string",
    )

    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    LOG_LEVEL: str = "INFO"
    TIMEZONE: str = "Africa/Lagos"

    TELEGRAM_BOT_TOKEN: Optional[str] = Field(
        default=None, description="Telegram Bot API Token for subscriber alerts"
    )
    TELEGRAM_CHAT_ID: Optional[str] = Field(
        default=None, description="Default Telegram Chat ID for subscriber alerts"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()


def get_settings() -> Settings:
    """Dependency helper to retrieve cached application settings."""
    return settings

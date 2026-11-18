"""Configuración leída de variables de entorno (o de un archivo .env en desarrollo)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/valor_ganado"
    cors_origins: list[str] = ["http://localhost:5173"]
    api_prefix: str = "/api/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()

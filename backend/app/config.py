"""
Configuration de l'application via variables d'environnement.

Utilise pydantic-settings pour charger depuis .env et valider les types.
Toutes les variables sont documentées dans .env.example.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings de l'application, chargés depuis l'environnement."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    env: Literal["development", "staging", "production"] = Field(default="development")
    log_level: Literal["debug", "info", "warning", "error"] = Field(default="info")

    # --- Base de données ---
    database_url: PostgresDsn = Field(
        ...,
        description="URL SQLAlchemy, ex. postgresql+psycopg://user:pass@host:5432/db",
    )

    # --- Auth ---
    api_key_read: str = Field(..., min_length=8, description="Clé API pour la lecture")
    jwt_secret: str = Field(..., min_length=16, description="Secret JWT pour l'écriture")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_min: int = Field(default=60, ge=1)

    # --- Export ---
    max_export_rows: int = Field(default=100_000, ge=1)

    # --- Fichiers ---
    upload_dir: str = Field(default="/app/uploads")

    # --- CORS ---
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Origines autorisées (front)",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, v: str | list[str]) -> list[str]:
        """Accepte une chaîne 'a,b' ou une liste."""
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retourne l'instance unique des settings (mise en cache)."""
    return Settings()  # type: ignore[call-arg]
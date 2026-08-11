from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "模块化剧本题材素材库 API"
    app_version: str = "1.0.0"
    app_env: Literal["development", "test", "production"] = "development"
    app_host: str = "127.0.0.1"
    app_port: int = Field(default=8000, ge=1, le=65535)
    api_prefix: str = "/api"
    debug: bool = False

    database_url: str = "sqlite:///./script_materials.db"
    storage_root: Path = Path("storage")
    # Kept for backward compatibility with Sprint 3. When it is not set
    # explicitly it always follows STORAGE_ROOT/materials.
    material_storage_path: Path = Path("storage/materials")
    log_dir: Path = Path("logs")
    backup_root: Path = Path("backups")
    temp_root: Path = Path("temp")

    max_upload_mb: int = Field(default=100, gt=0)
    backup_retention_days: int = Field(default=30, ge=1)
    sqlite_busy_timeout_ms: int = Field(default=5_000, ge=1)
    sqlite_wal_enabled: bool = True

    serve_frontend: bool = False
    frontend_dist: Path = BACKEND_ROOT.parent / "frontend" / "dist"

    # CORS_ALLOWED_ORIGINS is the production key. CORS_ORIGINS remains
    # accepted so existing development .env files keep working.
    cors_allowed_origins: str = ""
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    log_max_bytes: int = Field(default=10 * 1024 * 1024, ge=1024)
    log_backup_count: int = Field(default=10, ge=1)

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        del dotenv_settings
        configured_file = os.getenv("SETTINGS_ENV_FILE")
        if configured_file:
            env_file = Path(configured_file)
        elif os.getenv("APP_ENV", "").strip().lower() == "production":
            env_file = BACKEND_ROOT / ".env.production"
        else:
            env_file = BACKEND_ROOT / ".env"
        return (
            init_settings,
            env_settings,
            DotEnvSettingsSource(settings_cls, env_file=env_file, env_file_encoding="utf-8"),
            file_secret_settings,
        )

    @model_validator(mode="after")
    def derive_compatible_paths(self) -> "Settings":
        if self.is_production:
            # Production attachment files have one fixed containment root.
            # Ignore the deprecated override even if it leaks in from a
            # parent shell or an older environment file.
            self.material_storage_path = self.storage_root / "materials"
        elif "material_storage_path" not in self.model_fields_set:
            self.material_storage_path = self.storage_root / "materials"
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        configured = (
            self.cors_allowed_origins
            if self.is_production or self.cors_allowed_origins.strip()
            else self.cors_origins
        )
        return [item.strip() for item in configured.split(",") if item.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

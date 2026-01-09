"""Application configuration management using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "PlaneBrane"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    secret_key: str = Field(default="dev-secret-key-change-me")

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/planebrane"
    )

    # JWT Settings
    jwt_secret_key: str = Field(default="jwt-secret-key-change-me")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # File Storage
    upload_dir: Path = Path("storage/uploads")
    processed_dir: Path = Path("storage/processed")
    export_dir: Path = Path("storage/exports")
    max_upload_size_mb: int = 50

    # Image Processing
    default_edge_threshold_low: int = 50
    default_edge_threshold_high: int = 150
    default_blur_kernel_size: int = 5

    # 3D Generation
    default_subdivision_level: int = 2
    default_smoothing_iterations: int = 3
    max_vertices: int = 100000

    @field_validator("upload_dir", "processed_dir", "export_dir", mode="before")
    @classmethod
    def ensure_path(cls, v: str | Path) -> Path:
        """Convert string paths to Path objects."""
        return Path(v) if isinstance(v, str) else v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    def ensure_storage_dirs(self) -> None:
        """Create storage directories if they don't exist."""
        for dir_path in [self.upload_dir, self.processed_dir, self.export_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

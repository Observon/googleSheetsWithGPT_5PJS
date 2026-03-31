"""Application configuration using Pydantic Settings."""

import json
import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings

from src.domain.exceptions import ConfigError


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    # Google Drive Configuration
    google_credentials_json: str = ""
    google_drive_folder_id: Optional[str] = None

    # OpenAI Configuration
    openai_api_key: str = ""

    # Application Configuration
    log_level: str = "INFO"
    cache_dir: str = ".cache"
    output_dir: str = "output"
    max_spreadsheet_size_mb: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **kwargs):
        """Initialize settings and validate required fields."""
        super().__init__(**kwargs)
        self._validate()

    def _validate(self):
        """Validate required configuration."""
        if not self.google_credentials_json:
            raise ConfigError("GOOGLE_CREDENTIALS_JSON not found in environment variables")
        if not self.openai_api_key:
            raise ConfigError("OPENAI_API_KEY not found in environment variables")

    def get_credentials_dict(self) -> dict:
        """
        Parse Google credentials from JSON string or file path.

        Returns:
            dict: Credentials dictionary

        Raises:
            ConfigError: If credentials cannot be parsed
        """
        try:
            # Check if it's a JSON string
            if self.google_credentials_json.startswith("{"):
                return json.loads(self.google_credentials_json)
            # Check if it's a file path
            elif os.path.exists(self.google_credentials_json):
                with open(self.google_credentials_json) as f:
                    return json.load(f)
            else:
                raise ConfigError(
                    f"Google credentials: '{self.google_credentials_json}' is neither valid JSON nor a valid file path"
                )
        except json.JSONDecodeError as e:
            raise ConfigError(f"Failed to parse Google credentials JSON: {e}")

    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)


# Global settings instance
try:
    settings = Settings()
    settings.ensure_directories()
except ConfigError as e:
    raise ConfigError(f"Configuration initialization failed: {e}")

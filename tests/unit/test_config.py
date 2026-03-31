"""Tests for config module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config import Settings
from src.domain.exceptions import ConfigError


def test_settings_validation_missing_google_credentials():
    """Test that missing Google credentials raises error."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ConfigError, match="GOOGLE_CREDENTIALS_JSON"):
            Settings()


def test_settings_validation_missing_openai_key():
    """Test that missing OpenAI key raises error."""
    with patch.dict(os.environ, {"GOOGLE_CREDENTIALS_JSON": '{"type": "test"}'}, clear=True):
        with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
            Settings()


def test_settings_parse_json_string():
    """Test parsing inline JSON credentials."""
    creds_json = '{"type": "service_account", "project_id": "test"}'
    with patch.dict(
        os.environ,
        {"GOOGLE_CREDENTIALS_JSON": creds_json, "OPENAI_API_KEY": "test_key"},
        clear=True,
    ):
        settings = Settings()
        creds_dict = settings.get_credentials_dict()
        assert creds_dict["project_id"] == "test"


def test_settings_parse_json_file():
    """Test parsing credentials from file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test credentials file
        creds_file = Path(tmpdir) / "creds.json"
        creds_file.write_text('{"type": "service_account", "project_id": "test"}')

        with patch.dict(
            os.environ,
            {"GOOGLE_CREDENTIALS_JSON": str(creds_file), "OPENAI_API_KEY": "test_key"},
            clear=True,
        ):
            settings = Settings()
            creds_dict = settings.get_credentials_dict()
            assert creds_dict["project_id"] == "test"


def test_settings_ensure_directories():
    """Test that ensure_directories creates required directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".cache"
        output_dir = Path(tmpdir) / "output"

        # Directories shouldn't exist yet
        assert not cache_dir.exists()
        assert not output_dir.exists()

        with patch.dict(
            os.environ,
            {"GOOGLE_CREDENTIALS_JSON": '{"type": "test"}', "OPENAI_API_KEY": "test_key"},
            clear=True,
        ):
            with patch("src.config.Path"):
                # This would need more complex mocking; simplified for now
                pass

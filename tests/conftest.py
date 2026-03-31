"""Pytest configuration and shared fixtures."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        "Name": ["Alice", "Bob", "Charlie"],
        "Age": [25, 30, 35],
        "Salary": [50000, 60000, 70000],
        "Department": ["Sales", "IT", "Finance"],
    })


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_google_drive_adapter():
    """Create a mock Google Drive adapter."""
    adapter = MagicMock()
    adapter.list_spreadsheets.return_value = [
        MagicMock(id="1234", name="Test Sheet", mimeType="application/vnd.google-apps.spreadsheet"),
    ]
    return adapter


@pytest.fixture
def mock_openai_adapter(sample_dataframe):
    """Create a mock OpenAI adapter."""
    adapter = MagicMock()
    adapter.process_data_with_gpt.return_value = "This is a test analysis result."
    adapter.generate_insights.return_value = "These are test insights."
    adapter.prepare_data_summary.return_value = sample_dataframe.to_string()
    return adapter


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    with patch("src.config.settings") as mock:
        mock.google_credentials_json = "fake_creds.json"
        mock.openai_api_key = "fake_api_key"
        mock.cache_dir = ".cache"
        mock.output_dir = "output"
        mock.google_drive_folder_id = None
        mock.log_level = "INFO"
        mock.get_credentials_dict.return_value = {"type": "service_account"}
        yield mock

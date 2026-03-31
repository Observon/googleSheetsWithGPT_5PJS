"""Tests for data loader service."""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.domain.exceptions import ValidationError
from src.services.data_loader import DataLoaderService


def test_list_spreadsheets_returns_adapter_result():
    """Should return spreadsheet list from adapter."""
    drive = MagicMock()
    drive.list_spreadsheets.return_value = [
        MagicMock(id="file-1", name="Sheet A"),
        MagicMock(id="file-2", name="Sheet B"),
    ]

    service = DataLoaderService(drive_adapter=drive)
    result = service.list_spreadsheets(folder_id="folder-123")

    assert len(result) == 2
    drive.list_spreadsheets.assert_called_once_with("folder-123")


def test_load_spreadsheet_success_returns_dataset(sample_dataframe):
    """Should build Dataset from loaded DataFrame."""
    drive = MagicMock()
    drive.read_spreadsheet.return_value = sample_dataframe

    service = DataLoaderService(drive_adapter=drive)
    dataset = service.load_spreadsheet("sheet-1", "Sales Sheet")

    assert dataset.id == "sheet-1"
    assert dataset.name == "Sales Sheet"
    assert dataset.shape == sample_dataframe.shape
    assert dataset.columns == list(sample_dataframe.columns)
    drive.read_spreadsheet.assert_called_once_with("sheet-1", None)


def test_load_spreadsheet_empty_dataframe_raises_validation_error():
    """Should reject empty DataFrame."""
    drive = MagicMock()
    drive.read_spreadsheet.return_value = pd.DataFrame()

    service = DataLoaderService(drive_adapter=drive)

    with pytest.raises(ValidationError, match="DataFrame is empty"):
        service.load_spreadsheet("sheet-1", "Empty Sheet")


def test_validate_dataframe_no_columns_raises_validation_error():
    """Should reject DataFrame with no columns."""
    no_columns_df = pd.DataFrame(index=[0, 1, 2])

    with pytest.raises(ValidationError, match="DataFrame is empty"):
        DataLoaderService._validate_dataframe(no_columns_df)


def test_load_spreadsheet_wraps_unexpected_errors():
    """Should convert adapter errors into ValidationError."""
    drive = MagicMock()
    drive.read_spreadsheet.side_effect = RuntimeError("boom")

    service = DataLoaderService(drive_adapter=drive)

    with pytest.raises(ValidationError, match="Failed to load spreadsheet"):
        service.load_spreadsheet("sheet-1", "Broken Sheet")

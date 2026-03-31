"""Data loading service."""

import logging
import uuid
from typing import List, Optional

import pandas as pd

from src.adapters.google_drive import GoogleDriveAdapter
from src.domain.exceptions import ValidationError
from src.domain.models import Dataset, FileInfo

logger = logging.getLogger(__name__)


class DataLoaderService:
    """Service for loading and managing datasets."""

    def __init__(self, drive_adapter: Optional[GoogleDriveAdapter] = None):
        """
        Initialize data loader service.

        Args:
            drive_adapter: Google Drive adapter (defaults to new instance)
        """
        self.drive_adapter = drive_adapter or GoogleDriveAdapter()

    def list_spreadsheets(self, folder_id: Optional[str] = None) -> List[FileInfo]:
        """
        List available spreadsheets.

        Args:
            folder_id: Optional folder ID to limit results

        Returns:
            List of FileInfo objects
        """
        logger.info("Listing spreadsheets from Google Drive")
        return self.drive_adapter.list_spreadsheets(folder_id)

    def load_spreadsheet(
        self, file_id: str, file_name: str, sheet_name: Optional[str] = None
    ) -> Dataset:
        """
        Load a spreadsheet and return as Dataset object.

        Args:
            file_id: Google Sheet file ID
            file_name: File name for reference
            sheet_name: Optional specific sheet name

        Returns:
            Dataset object

        Raises:
            ValidationError: If data validation fails
        """
        try:
            logger.info(f"Loading spreadsheet: {file_name} (ID: {file_id})")

            # Load data
            df = self.drive_adapter.read_spreadsheet(file_id, sheet_name)

            # Validate
            self._validate_dataframe(df)

            # Create Dataset object
            dataset = Dataset(
                id=file_id,
                name=file_name,
                shape=df.shape,
                columns=list(df.columns),
            )

            logger.info(f"Successfully loaded dataset: {file_name} with shape {df.shape}")
            return dataset

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error loading spreadsheet: {str(e)}")
            raise ValidationError(f"Failed to load spreadsheet: {str(e)}") from e

    @staticmethod
    def _validate_dataframe(df: pd.DataFrame):
        """
        Validate DataFrame for analysis.

        Args:
            df: DataFrame to validate

        Raises:
            ValidationError: If validation fails
        """
        if df.empty:
            raise ValidationError("DataFrame is empty")

        if len(df.columns) == 0:
            raise ValidationError("DataFrame has no columns")

        logger.info(f"DataFrame validation passed: {df.shape}")

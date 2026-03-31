"""Google Drive API adapter."""

import io
import logging
from typing import List, Dict, Optional, Any

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from src.config import settings
from src.domain.exceptions import GoogleDriveError
from src.domain.models import FileInfo

logger = logging.getLogger(__name__)


class GoogleDriveAdapter:
    """Adapter for Google Drive API operations."""

    def __init__(self):
        """Initialize Google Drive API client."""
        self.creds = None
        self.service = None
        self._initialize()

    def _initialize(self):
        """Initialize Google Drive API with service account credentials."""
        try:
            creds_dict = settings.get_credentials_dict()

            self.creds = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=["https://www.googleapis.com/auth/drive.readonly"],
            )
            self.service = build("drive", "v3", credentials=self.creds)
            logger.info("Google Drive API initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing Google Drive: {str(e)}")
            raise GoogleDriveError(f"Failed to initialize Google Drive: {str(e)}") from e

    def list_spreadsheets(self, folder_id: Optional[str] = None) -> List[FileInfo]:
        """
        List all Google Sheets in a folder or root.

        Args:
            folder_id: Optional folder ID to limit results

        Returns:
            List of FileInfo objects

        Raises:
            GoogleDriveError: If the operation fails
        """
        try:
            query = "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
            if folder_id:
                query += f" and '{folder_id}' in parents"

            results = self.service.files().list(
                q=query,
                pageSize=50,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, size)",
                orderBy="modifiedTime desc",
            ).execute()

            files = results.get("files", [])
            logger.info(f"Found {len(files)} spreadsheets")

            return [FileInfo(**file) for file in files]

        except Exception as e:
            logger.error(f"Error listing spreadsheets: {str(e)}")
            raise GoogleDriveError(f"Failed to list spreadsheets: {str(e)}") from e

    def read_spreadsheet(
        self, file_id: str, sheet_name: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Read a Google Sheet and return as pandas DataFrame.

        Args:
            file_id: Google Sheet file ID
            sheet_name: Optional specific sheet name

        Returns:
            pandas DataFrame

        Raises:
            GoogleDriveError: If the operation fails
        """
        try:
            logger.info(f"Reading spreadsheet with ID: {file_id}")

            # Export the Google Sheet as Excel
            request = self.service.files().export_media(
                fileId=file_id,
                mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            # Download the file
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.info(f"Download progress: {int(status.progress() * 100)}%")

            # Read the Excel file into a pandas DataFrame
            fh.seek(0)
            df = pd.read_excel(fh, engine="openpyxl", sheet_name=sheet_name)

            if isinstance(df, dict):
                # Multiple sheets - return the first one or specified sheet
                df = df[list(df.keys())[0]] if not sheet_name else df[sheet_name]

            logger.info(f"Successfully loaded spreadsheet with shape: {df.shape}")
            return df

        except Exception as e:
            logger.error(f"Error reading spreadsheet: {str(e)}")
            raise GoogleDriveError(f"Failed to read spreadsheet: {str(e)}") from e

    def get_file_info(self, file_id: str) -> FileInfo:
        """
        Get detailed information about a file.

        Args:
            file_id: File ID to get info for

        Returns:
            FileInfo object

        Raises:
            GoogleDriveError: If the operation fails
        """
        try:
            file_info = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, modifiedTime, size",
            ).execute()

            return FileInfo(**file_info)

        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            raise GoogleDriveError(f"Failed to get file info: {str(e)}") from e

"""Batch processing service."""

import logging
from typing import Any, Dict, List, Optional

from tqdm import tqdm

from src.adapters.google_drive import GoogleDriveAdapter
from src.domain.exceptions import ApplicationError
from src.services.analyzer import AnalyzerService
from src.services.export import ExportService

logger = logging.getLogger(__name__)


class BatchService:
    """Service for batch processing multiple spreadsheets."""

    def __init__(
        self,
        analyzer_service: Optional[AnalyzerService] = None,
        export_service: Optional[ExportService] = None,
        drive_adapter: Optional[GoogleDriveAdapter] = None,
    ):
        """
        Initialize batch service.

        Args:
            analyzer_service: Analyzer service (defaults to new instance)
            export_service: Export service (defaults to new instance)
            drive_adapter: Google Drive adapter (defaults to new instance)
        """
        self.analyzer_service = analyzer_service or AnalyzerService()
        self.export_service = export_service or ExportService()
        self.drive_adapter = drive_adapter or GoogleDriveAdapter()

    def process_folder(
        self,
        folder_id: str,
        prompt: str,
        export_format: Optional[str] = None,
        output_dir: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process all spreadsheets in a folder.

        Args:
            folder_id: Google Drive folder ID
            prompt: Analysis prompt to use for all sheets
            export_format: Optional format to export (csv, pdf, md)
            output_dir: Optional output directory for exports

        Returns:
            List of result dictionaries

        Raises:
            ApplicationError: If processing fails
        """
        try:
            logger.info(f"Starting batch processing for folder: {folder_id}")

            # List all spreadsheets in the folder
            spreadsheets = self.drive_adapter.list_spreadsheets(folder_id)

            if not spreadsheets:
                logger.warning("No spreadsheets found in folder")
                return []

            logger.info(f"Found {len(spreadsheets)} spreadsheets to process")

            results = []

            # Process each spreadsheet with progress bar
            for sheet in tqdm(spreadsheets, desc="Processing spreadsheets", unit="sheet"):
                try:
                    logger.info(f"Processing: {sheet.name}")

                    # Analyze
                    analysis = self.analyzer_service.analyze_spreadsheet(
                        sheet.id, sheet.name, prompt
                    )

                    result = {
                        "file_id": sheet.id,
                        "file_name": sheet.name,
                        "analysis_id": analysis.id,
                        "status": "success",
                        "cached": analysis.cached,
                    }

                    # Export if requested
                    if export_format:
                        try:
                            export_result = self.export_service.export_analysis(
                                analysis, export_format
                            )
                            result["export_path"] = export_result.filepath
                            result["export_size"] = export_result.size_bytes
                        except Exception as e:
                            logger.error(f"Export failed for {sheet.name}: {str(e)}")
                            result["export_error"] = str(e)

                    results.append(result)

                except Exception as e:
                    logger.error(f"Failed to process {sheet.name}: {str(e)}")
                    results.append(
                        {
                            "file_id": sheet.id,
                            "file_name": sheet.name,
                            "status": "error",
                            "error": str(e),
                        }
                    )

            logger.info(f"Batch processing completed: {len(results)} sheets processed")
            return results

        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}")
            raise ApplicationError(f"Batch processing failed: {str(e)}") from e

    def process_spreadsheets(
        self,
        file_ids: List[str],
        file_names: List[str],
        prompt: str,
        export_format: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process a list of specific spreadsheets.

        Args:
            file_ids: List of file IDs
            file_names: List of file names
            prompt: Analysis prompt
            export_format: Optional format to export

        Returns:
            List of result dictionaries
        """
        if len(file_ids) != len(file_names):
            raise ApplicationError("file_ids and file_names must have the same length")

        results = []

        for file_id, file_name in tqdm(
            zip(file_ids, file_names, strict=False),
            desc="Processing",
            unit="file",
        ):
            try:
                analysis = self.analyzer_service.analyze_spreadsheet(file_id, file_name, prompt)

                result = {
                    "file_id": file_id,
                    "file_name": file_name,
                    "analysis_id": analysis.id,
                    "status": "success",
                }

                if export_format:
                    try:
                        export_result = self.export_service.export_analysis(analysis, export_format)
                        result["export_path"] = export_result.filepath
                    except Exception as e:
                        result["export_error"] = str(e)

                results.append(result)

            except Exception as e:
                results.append(
                    {
                        "file_id": file_id,
                        "file_name": file_name,
                        "status": "error",
                        "error": str(e),
                    }
                )

        return results

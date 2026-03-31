"""Tests for batch service."""

from unittest.mock import MagicMock

import pytest

from src.domain.exceptions import ApplicationError
from src.domain.models import Analysis
from src.services.batch import BatchService


def _analysis(analysis_id: str = "a1") -> Analysis:
    return Analysis(
        id=analysis_id,
        dataset_id="sheet-1",
        dataset_name="Sheet",
        prompt="Prompt",
        result="Result",
        cached=False,
    )


def test_process_folder_returns_empty_when_no_spreadsheets():
    """Should return empty list when no sheets are found."""
    drive = MagicMock()
    drive.list_spreadsheets.return_value = []

    service = BatchService(
        analyzer_service=MagicMock(),
        export_service=MagicMock(),
        drive_adapter=drive,
    )

    result = service.process_folder("folder-1", "Prompt")

    assert result == []


def test_process_folder_success_with_export():
    """Should process all spreadsheets and include export metadata."""
    sheet_a = MagicMock(id="s1", name="Sheet A")
    sheet_b = MagicMock(id="s2", name="Sheet B")

    drive = MagicMock()
    drive.list_spreadsheets.return_value = [sheet_a, sheet_b]

    analyzer = MagicMock()
    analyzer.analyze_spreadsheet.side_effect = [_analysis("a1"), _analysis("a2")]

    export = MagicMock()
    export.export_analysis.side_effect = [
        MagicMock(filepath="output/a1.pdf", size_bytes=120),
        MagicMock(filepath="output/a2.pdf", size_bytes=140),
    ]

    service = BatchService(analyzer_service=analyzer, export_service=export, drive_adapter=drive)

    result = service.process_folder("folder-1", "Prompt", export_format="pdf")

    assert len(result) == 2
    assert result[0]["status"] == "success"
    assert result[0]["analysis_id"] == "a1"
    assert result[0]["export_path"] == "output/a1.pdf"
    assert result[1]["analysis_id"] == "a2"


def test_process_folder_keeps_processing_on_item_failure():
    """Should continue batch when one spreadsheet fails."""
    sheet_a = MagicMock(id="s1", name="Sheet A")
    sheet_b = MagicMock(id="s2", name="Sheet B")

    drive = MagicMock()
    drive.list_spreadsheets.return_value = [sheet_a, sheet_b]

    analyzer = MagicMock()
    analyzer.analyze_spreadsheet.side_effect = [_analysis("a1"), RuntimeError("broken")]

    service = BatchService(
        analyzer_service=analyzer,
        export_service=MagicMock(),
        drive_adapter=drive,
    )

    result = service.process_folder("folder-1", "Prompt")

    assert len(result) == 2
    assert result[0]["status"] == "success"
    assert result[1]["status"] == "error"
    assert "broken" in result[1]["error"]


def test_process_folder_wraps_top_level_failures():
    """Should wrap top-level errors in ApplicationError."""
    drive = MagicMock()
    drive.list_spreadsheets.side_effect = RuntimeError("drive unavailable")

    service = BatchService(
        analyzer_service=MagicMock(),
        export_service=MagicMock(),
        drive_adapter=drive,
    )

    with pytest.raises(ApplicationError, match="Batch processing failed"):
        service.process_folder("folder-1", "Prompt")


def test_process_spreadsheets_rejects_mismatched_lengths():
    """Should reject mismatched file_ids/file_names lengths."""
    service = BatchService(
        analyzer_service=MagicMock(),
        export_service=MagicMock(),
        drive_adapter=MagicMock(),
    )

    with pytest.raises(ApplicationError, match="same length"):
        service.process_spreadsheets(["s1"], ["Sheet A", "Sheet B"], "Prompt")


def test_process_spreadsheets_records_export_error_and_continues():
    """Should include export_error when export fails."""
    analyzer = MagicMock()
    analyzer.analyze_spreadsheet.return_value = _analysis("a1")

    export = MagicMock()
    export.export_analysis.side_effect = RuntimeError("pdf error")

    service = BatchService(
        analyzer_service=analyzer,
        export_service=export,
        drive_adapter=MagicMock(),
    )

    result = service.process_spreadsheets(
        ["s1"],
        ["Sheet A"],
        "Prompt",
        export_format="pdf",
    )

    assert len(result) == 1
    assert result[0]["status"] == "success"
    assert "pdf error" in result[0]["export_error"]

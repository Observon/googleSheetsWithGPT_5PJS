"""Tests for FastAPI routes."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import (
    get_analyzer_service,
    get_batch_service,
    get_data_loader_service,
    get_export_service,
    store_analysis,
)
from src.api.main import app
from src.domain.exceptions import GoogleDriveError, OpenAIError
from src.domain.models import Analysis, FileInfo


@pytest.fixture
def client():
    """Create API client with clean dependency overrides."""
    app.dependency_overrides = {}
    with TestClient(app) as c:
        yield c
    app.dependency_overrides = {}


def _analysis() -> Analysis:
    return Analysis(
        id="analysis-1",
        dataset_id="sheet-1",
        dataset_name="Sheet 1",
        prompt="Prompt",
        result="Result",
        cached=False,
    )


def test_health_check(client):
    """Health endpoint should return service status."""
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "timestamp" in payload


def test_list_sheets_success(client):
    """List spreadsheets should return serialized file data."""
    loader = MagicMock()
    loader.list_spreadsheets.return_value = [
        FileInfo(id="s1", name="Sheet A", mimeType="application/vnd.google-apps.spreadsheet"),
        FileInfo(id="s2", name="Sheet B", mimeType="application/vnd.google-apps.spreadsheet"),
    ]
    app.dependency_overrides[get_data_loader_service] = lambda: loader

    response = client.get("/sheets")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    assert payload["sheets"][0]["id"] == "s1"


def test_list_sheets_google_error_maps_502(client):
    """List spreadsheets should map drive errors to 502."""
    loader = MagicMock()
    loader.list_spreadsheets.side_effect = GoogleDriveError("drive down")
    app.dependency_overrides[get_data_loader_service] = lambda: loader

    response = client.get("/sheets")

    assert response.status_code == 502


def test_analyze_success(client):
    """Analyze endpoint should return Analysis payload."""
    loader = MagicMock()
    loader.drive_adapter.get_file_info.return_value = MagicMock(name="Sheet A")

    analyzer = MagicMock()
    analyzer.analyze_spreadsheet.return_value = _analysis()

    app.dependency_overrides[get_data_loader_service] = lambda: loader
    app.dependency_overrides[get_analyzer_service] = lambda: analyzer

    response = client.post(
        "/sheets/sheet-1/analyze",
        json={"prompt": "What changed?", "use_cache": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "analysis-1"
    assert payload["dataset_id"] == "sheet-1"


def test_analyze_openai_error_maps_503(client):
    """Analyze endpoint should map OpenAI errors to 503."""
    loader = MagicMock()
    loader.drive_adapter.get_file_info.return_value = MagicMock(name="Sheet A")

    analyzer = MagicMock()
    analyzer.analyze_spreadsheet.side_effect = OpenAIError("rate limit")

    app.dependency_overrides[get_data_loader_service] = lambda: loader
    app.dependency_overrides[get_analyzer_service] = lambda: analyzer

    response = client.post(
        "/sheets/sheet-1/analyze",
        json={"prompt": "What changed?", "use_cache": True},
    )

    assert response.status_code == 503


def test_insights_success(client):
    """Insights endpoint should return generated Analysis payload."""
    loader = MagicMock()
    loader.drive_adapter.get_file_info.return_value = MagicMock(name="Sheet A")

    analyzer = MagicMock()
    analyzer.generate_insights.return_value = _analysis()

    app.dependency_overrides[get_data_loader_service] = lambda: loader
    app.dependency_overrides[get_analyzer_service] = lambda: analyzer

    response = client.post(
        "/sheets/sheet-1/insights",
        json={"use_cache": False},
    )

    assert response.status_code == 200
    assert response.json()["id"] == "analysis-1"


def test_export_analysis_file_response(client, tmp_path: Path):
    """Export endpoint should stream generated file."""
    analysis = _analysis()
    store_analysis(analysis)

    out_file = tmp_path / "analysis.csv"
    out_file.write_text("col\nvalue\n", encoding="utf-8")

    export_service = MagicMock()
    export_service.export_analysis.return_value = MagicMock(filepath=str(out_file))
    app.dependency_overrides[get_export_service] = lambda: export_service

    response = client.get("/exports/analysis-1/csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")


def test_batch_process_success(client):
    """Batch endpoint should return processed payload with total."""
    batch = MagicMock()
    batch.process_folder.return_value = [
        {"file_id": "s1", "status": "success"},
        {"file_id": "s2", "status": "error"},
    ]
    app.dependency_overrides[get_batch_service] = lambda: batch

    response = client.post(
        "/batch/process",
        json={"folder_id": "f1", "prompt": "Analyze", "export_format": "pdf"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert len(payload["processed"]) == 2


def test_clear_cache_success(client):
    """Cache endpoint should return number of deleted entries."""
    analyzer = MagicMock()
    analyzer.clear_cache.return_value = 4
    app.dependency_overrides[get_analyzer_service] = lambda: analyzer

    response = client.delete("/cache")

    assert response.status_code == 200
    payload = response.json()
    assert payload["cleared"] == 4

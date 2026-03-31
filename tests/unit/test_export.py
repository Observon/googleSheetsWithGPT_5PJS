"""Tests for data export service."""

import tempfile
from pathlib import Path

import pytest

from src.domain.exceptions import ApplicationError
from src.domain.models import Analysis
from src.services.export import ExportService


@pytest.fixture
def export_service():
    """Create an export service with temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield ExportService(output_dir=tmpdir)


@pytest.fixture
def sample_analysis():
    """Create a sample analysis result."""
    return Analysis(
        id="test-123",
        dataset_id="sheet-456",
        dataset_name="Test Sheet",
        prompt="What are the main insights?",
        result="The main insight is that values increased over time.",
        model="gpt-4o-mini",
        cached=False,
    )


def test_export_csv(export_service, sample_analysis):
    """Test CSV export."""
    result = export_service.export_analysis(sample_analysis, "csv")

    assert result.format == "csv"
    assert result.filepath.endswith(".csv")
    assert result.size_bytes > 0
    assert Path(result.filepath).exists()


def test_export_markdown(export_service, sample_analysis):
    """Test Markdown export."""
    result = export_service.export_analysis(sample_analysis, "md")

    assert result.format == "md"
    assert result.filepath.endswith(".md")
    assert result.size_bytes > 0
    assert Path(result.filepath).exists()

    # Verify content
    with open(result.filepath) as f:
        content = f.read()
        assert "# Analysis Report" in content
        assert sample_analysis.dataset_name in content


def test_export_pdf(export_service, sample_analysis):
    """Test PDF export."""
    try:
        result = export_service.export_analysis(sample_analysis, "pdf")

        assert result.format == "pdf"
        assert result.filepath.endswith(".pdf")
        assert result.size_bytes > 0
        assert Path(result.filepath).exists()
    except ApplicationError as e:
        # reportlab might not be installed in test environment
        if "reportlab not installed" in str(e):
            pytest.skip("reportlab not installed")
        raise


def test_export_unsupported_format(export_service, sample_analysis):
    """Test that unsupported format raises error."""
    with pytest.raises(ApplicationError, match="Unsupported export format"):
        export_service.export_analysis(sample_analysis, "json")


def test_export_case_insensitive(export_service, sample_analysis):
    """Test that format is case insensitive."""
    result = export_service.export_analysis(sample_analysis, "CSV")
    assert result.format == "csv"

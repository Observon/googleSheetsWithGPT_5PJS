"""Tests for analyzer service."""

from unittest.mock import MagicMock, patch

import pytest

from src.domain.exceptions import OpenAIError
from src.services.analyzer import AnalyzerService


def test_analyze_spreadsheet_returns_cached_result_without_api_calls():
    """Should use cache and skip Drive/OpenAI calls when cache hit."""
    openai = MagicMock()
    cache = MagicMock()
    drive = MagicMock()

    cache.get.return_value = "cached answer"

    service = AnalyzerService(openai_adapter=openai, cache_adapter=cache, drive_adapter=drive)
    analysis = service.analyze_spreadsheet("sheet-1", "Sales", "What changed?")

    assert analysis.cached is True
    assert analysis.result == "cached answer"
    cache.get.assert_called_once_with("sheet-1", "What changed?")
    drive.read_spreadsheet.assert_not_called()
    openai.process_data_with_gpt.assert_not_called()


def test_analyze_spreadsheet_cache_miss_calls_openai_and_stores_result(sample_dataframe):
    """Should analyze data and cache result when cache misses."""
    openai = MagicMock()
    cache = MagicMock()
    drive = MagicMock()

    cache.get.return_value = None
    drive.read_spreadsheet.return_value = sample_dataframe
    openai.process_data_with_gpt.return_value = "fresh answer"

    service = AnalyzerService(openai_adapter=openai, cache_adapter=cache, drive_adapter=drive)
    analysis = service.analyze_spreadsheet("sheet-1", "Sales", "Explain trends")

    assert analysis.cached is False
    assert analysis.result == "fresh answer"
    drive.read_spreadsheet.assert_called_once_with("sheet-1")
    openai.process_data_with_gpt.assert_called_once_with(sample_dataframe, "Explain trends")
    cache.set.assert_called_once_with("sheet-1", "Explain trends", "fresh answer")


def test_analyze_spreadsheet_without_cache_does_not_read_cache(sample_dataframe):
    """Should skip cache lookup when use_cache=False."""
    openai = MagicMock()
    cache = MagicMock()
    drive = MagicMock()

    drive.read_spreadsheet.return_value = sample_dataframe
    openai.process_data_with_gpt.return_value = "no-cache answer"

    service = AnalyzerService(openai_adapter=openai, cache_adapter=cache, drive_adapter=drive)
    analysis = service.analyze_spreadsheet(
        "sheet-1",
        "Sales",
        "Explain trends",
        use_cache=False,
    )

    assert analysis.cached is False
    cache.get.assert_not_called()


def test_analyze_spreadsheet_wraps_errors_as_openai_error(sample_dataframe):
    """Should wrap unexpected errors in OpenAIError."""
    openai = MagicMock()
    cache = MagicMock()
    drive = MagicMock()

    cache.get.return_value = None
    drive.read_spreadsheet.return_value = sample_dataframe
    openai.process_data_with_gpt.side_effect = RuntimeError("model down")

    service = AnalyzerService(openai_adapter=openai, cache_adapter=cache, drive_adapter=drive)

    with pytest.raises(OpenAIError, match="Failed to analyze spreadsheet"):
        service.analyze_spreadsheet("sheet-1", "Sales", "Explain trends")


def test_generate_insights_delegates_to_analyze_spreadsheet():
    """Should delegate to analyze_spreadsheet with built-in prompt."""
    service = AnalyzerService(
        openai_adapter=MagicMock(),
        cache_adapter=MagicMock(),
        drive_adapter=MagicMock(),
    )

    with patch.object(service, "analyze_spreadsheet") as analyze_mock:
        analyze_mock.return_value = MagicMock(result="ok")

        service.generate_insights("sheet-1", "Sales", use_cache=False)

        called_prompt = analyze_mock.call_args[0][2]
        assert "Principais insights" in called_prompt
        assert analyze_mock.call_args[0][3] is False


def test_clear_cache_returns_deleted_count():
    """Should delegate cache cleanup and return deleted count."""
    cache = MagicMock()
    cache.clear.return_value = 7

    service = AnalyzerService(
        openai_adapter=MagicMock(),
        cache_adapter=cache,
        drive_adapter=MagicMock(),
    )

    deleted = service.clear_cache()

    assert deleted == 7
    cache.clear.assert_called_once_with()

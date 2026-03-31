"""API dependencies and shared runtime state."""

from __future__ import annotations

from functools import lru_cache
from threading import Lock
from typing import Dict, Optional

from src.domain.models import Analysis
from src.services.analyzer import AnalyzerService
from src.services.batch import BatchService
from src.services.data_loader import DataLoaderService
from src.services.export import ExportService


_analysis_store: Dict[str, Analysis] = {}
_analysis_lock = Lock()


@lru_cache(maxsize=1)
def get_data_loader_service() -> DataLoaderService:
    """Return singleton data loader service for API handlers."""
    return DataLoaderService()


@lru_cache(maxsize=1)
def get_analyzer_service() -> AnalyzerService:
    """Return singleton analyzer service for API handlers."""
    return AnalyzerService()


@lru_cache(maxsize=1)
def get_export_service() -> ExportService:
    """Return singleton export service for API handlers."""
    return ExportService()


@lru_cache(maxsize=1)
def get_batch_service() -> BatchService:
    """Return singleton batch service for API handlers."""
    return BatchService()


def store_analysis(analysis: Analysis) -> None:
    """Store analysis in memory for later export retrieval by analysis id."""
    with _analysis_lock:
        _analysis_store[analysis.id] = analysis


def get_stored_analysis(analysis_id: str) -> Optional[Analysis]:
    """Return analysis by id from in-memory store, if available."""
    with _analysis_lock:
        return _analysis_store.get(analysis_id)

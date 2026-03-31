"""Spreadsheet-related API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.dependencies import (
    get_analyzer_service,
    get_data_loader_service,
    store_analysis,
)
from src.domain.exceptions import (
    ApplicationError,
    GoogleDriveError,
    OpenAIError,
    ValidationError,
)
from src.domain.models import Analysis
from src.services.analyzer import AnalyzerService
from src.services.data_loader import DataLoaderService

router = APIRouter(prefix="/sheets", tags=["sheets"])


class AnalyzeRequest(BaseModel):
    """Request payload for custom spreadsheet analysis."""

    prompt: str = Field(min_length=1)
    use_cache: bool = True


class InsightsRequest(BaseModel):
    """Request payload for automatic insights generation."""

    use_cache: bool = True


def _resolve_file_name(data_loader: DataLoaderService, sheet_id: str) -> str:
    """Resolve a spreadsheet name from Google Drive by id."""
    file_info = data_loader.drive_adapter.get_file_info(sheet_id)
    return file_info.name


@router.get("")
def list_spreadsheets(
    folder_id: str | None = None,
    data_loader: DataLoaderService = Depends(get_data_loader_service),
):
    """List available spreadsheets from Google Drive."""
    try:
        sheets = data_loader.list_spreadsheets(folder_id)
        return {
            "count": len(sheets),
            "sheets": [sheet.model_dump(by_alias=True) for sheet in sheets],
        }
    except GoogleDriveError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except ApplicationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/{sheet_id}/analyze", response_model=Analysis)
def analyze_spreadsheet(
    sheet_id: str,
    payload: AnalyzeRequest,
    data_loader: DataLoaderService = Depends(get_data_loader_service),
    analyzer: AnalyzerService = Depends(get_analyzer_service),
):
    """Analyze spreadsheet with a custom prompt."""
    try:
        file_name = _resolve_file_name(data_loader, sheet_id)
        analysis = analyzer.analyze_spreadsheet(
            sheet_id,
            file_name,
            payload.prompt,
            use_cache=payload.use_cache,
        )
        store_analysis(analysis)
        return analysis
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except OpenAIError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except GoogleDriveError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ApplicationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/{sheet_id}/insights", response_model=Analysis)
def generate_insights(
    sheet_id: str,
    payload: InsightsRequest,
    data_loader: DataLoaderService = Depends(get_data_loader_service),
    analyzer: AnalyzerService = Depends(get_analyzer_service),
):
    """Generate automatic insights for a spreadsheet."""
    try:
        file_name = _resolve_file_name(data_loader, sheet_id)
        analysis = analyzer.generate_insights(
            sheet_id,
            file_name,
            use_cache=payload.use_cache,
        )
        store_analysis(analysis)
        return analysis
    except OpenAIError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except GoogleDriveError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ApplicationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

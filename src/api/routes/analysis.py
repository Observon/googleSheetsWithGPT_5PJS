"""Analysis utility routes (cache and batch)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.dependencies import get_analyzer_service, get_batch_service
from src.domain.exceptions import ApplicationError
from src.services.analyzer import AnalyzerService
from src.services.batch import BatchService

router = APIRouter(tags=["analysis"])


class BatchProcessRequest(BaseModel):
    """Request payload for folder batch processing."""

    folder_id: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    export_format: str | None = None


@router.post("/batch/process")
def batch_process_folder(
    payload: BatchProcessRequest,
    batch_service: BatchService = Depends(get_batch_service),
):
    """Run analysis for all spreadsheets inside a Google Drive folder."""
    try:
        processed = batch_service.process_folder(
            folder_id=payload.folder_id,
            prompt=payload.prompt,
            export_format=payload.export_format,
        )
        return {
            "job_id": str(uuid.uuid4()),
            "total": len(processed),
            "processed": processed,
        }
    except ApplicationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete("/cache")
def clear_cache(analyzer: AnalyzerService = Depends(get_analyzer_service)):
    """Clear all cached analysis entries."""
    try:
        deleted = analyzer.clear_cache()
        return {
            "cleared": deleted,
            "message": "Cache cleared successfully",
        }
    except ApplicationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

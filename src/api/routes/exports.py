"""Export API routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from src.api.dependencies import get_export_service, get_stored_analysis
from src.domain.exceptions import ApplicationError
from src.services.export import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])

_MEDIA_TYPES = {
    "csv": "text/csv",
    "pdf": "application/pdf",
    "md": "text/markdown",
}


@router.get("/{analysis_id}/{format}")
def export_analysis(
    analysis_id: str,
    format: str,
    export_service: ExportService = Depends(get_export_service),
):
    """Export a stored analysis by id and format."""
    analysis = get_stored_analysis(analysis_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Analysis not found in runtime store. Run "
                "/sheets/{sheet_id}/analyze "
                "or /sheets/{sheet_id}/insights first."
            ),
        )

    try:
        result = export_service.export_analysis(analysis, format)
    except ApplicationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    filepath = Path(result.filepath)
    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export generated but output file was not found on disk.",
        )

    media_type = _MEDIA_TYPES.get(format.lower(), "application/octet-stream")
    return FileResponse(
        path=filepath,
        media_type=media_type,
        filename=filepath.name,
    )

"""FastAPI application entrypoint."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI

from src.api.routes.analysis import router as analysis_router
from src.api.routes.exports import router as exports_router
from src.api.routes.spreadsheets import router as spreadsheets_router

app = FastAPI(
    title="Google Sheets GPT Analyzer API",
    description=(
        "REST API for spreadsheet analysis using Google Drive and OpenAI"
    ),
    version="1.0.0",
)


@app.get("/health")
def health_check():
    """Return API health and server timestamp."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


app.include_router(spreadsheets_router)
app.include_router(exports_router)
app.include_router(analysis_router)

"""Domain models using Pydantic for validation."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """Google Drive file information."""

    id: str
    name: str
    mime_type: str = Field(alias="mimeType")
    modified_time: Optional[str] = Field(alias="modifiedTime", default=None)
    size: Optional[int] = None

    class Config:
        populate_by_name = True


class Dataset(BaseModel):
    """Represents a loaded dataset/spreadsheet."""

    id: str
    name: str
    shape: tuple[int, int]  # (rows, columns)
    columns: List[str]
    data: Optional[Dict[str, Any]] = None  # For sample data
    loaded_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True


class Analysis(BaseModel):
    """Represents an analysis result."""

    id: str
    dataset_id: str
    dataset_name: str
    prompt: str
    result: str
    model: str = "gpt-4o-mini"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    cached: bool = False

    class Config:
        arbitrary_types_allowed = True


class ExportResult(BaseModel):
    """Represents an export operation result."""

    analysis_id: str
    format: str  # csv, pdf, md
    filepath: str
    size_bytes: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True

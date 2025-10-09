from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field


class Stage(str, Enum):
    APPROVAL_WAITING = 'APPROVAL_WAITING'
    UPLOADED = 'UPLOADED'
    PROCESSED = 'PROCESSED'
    ARCHIVED = 'ARCHIVED'

    def next(self) -> "Stage":
        """Return the next Stage in declaration order; stays at last (ARCHIVED)."""
        members: list[Stage] = [e for e in Stage]
        idx = members.index(self)
        return members[idx] if idx == len(members) - 1 else members[idx + 1]

class ImageEntry(BaseModel):
    id: str = Field(..., description="Unique ID")
    original_name: Annotated[str, Field(..., min_length=1, description="Original file name")]
    stored_name: Annotated[str, Field(..., min_length=1, description="Stored file name")]
    url: str = Field(..., description="URL to the file")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    uploaded_at: str = Field(..., description="Timestamp of upload")
    medicine_name: Annotated[str, Field(..., description="Medicine name")]
    version: int = Field(..., description="Version number")
    stage: Stage = Field(..., description="Current state")

    # Allow ORM-like access if needed; serialize enums by value
    model_config = {
        'use_enum_values': True
    }

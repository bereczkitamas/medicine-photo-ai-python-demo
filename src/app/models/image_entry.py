from enum import Enum
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
    original_name: str
    stored_name: str
    url: str
    size: int
    content_type: str
    uploaded_at: str
    medicine_name: str
    version: int
    stage: Stage

    # Allow ORM-like access if needed; serialize enums by value
    model_config = {
        'use_enum_values': True
    }

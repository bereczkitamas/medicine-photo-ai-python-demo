from dataclasses import dataclass
from enum import Enum


class Stage(str, Enum):
    UPLOADED = 'UPLOADED'
    PROCESSED = 'PROCESSED'
    ARCHIVED = 'ARCHIVED'

    def next(self) -> "Stage":
        """Return the next Stage in declaration order; stays at last (ARCHIVED)."""
        members = list(type(self))
        idx = members.index(self)
        return members[idx] if idx == len(members) - 1 else members[idx + 1]


@dataclass
class ImageEntry:
    id: str
    original_name: str
    stored_name: str
    url: str
    size: int
    content_type: str
    uploaded_at: str
    medicine_name: str
    version: int
    stage: Stage

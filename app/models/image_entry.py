from dataclasses import dataclass


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

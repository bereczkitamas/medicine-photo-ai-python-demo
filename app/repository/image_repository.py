import json
from typing import List, Dict, Any, Iterable

from app.config import AppConfig
from app.storage.filesystem import FileSystem


class ImageRepository:
    """Handles metadata persistence (SRP, DIP)."""
    def __init__(self, metadata_file: str, fs: FileSystem):
        self._metadata_file = metadata_file
        self._fs = fs

    def load_all(self) -> List[Dict[str, Any]]:
        self._fs.ensure_storage(AppConfig.UPLOAD_DIR, self._metadata_file)
        with open(self._metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_all(self, entries: Iterable[Dict[str, Any]]) -> None:
        with open(self._metadata_file, 'w', encoding='utf-8') as f:
            json.dump(list(entries), f, indent=2)

    def append(self, entry: Dict[str, Any]) -> None:
        entries = self.load_all()
        entries.append(entry)
        self.save_all(entries)

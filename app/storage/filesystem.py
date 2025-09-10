import json
import os
from werkzeug.datastructures import FileStorage


class FileSystem:
    """Abstraction over file system operations (SRP)."""
    def ensure_storage(self, upload_dir: str, metadata_file: str) -> None:
        os.makedirs(upload_dir, exist_ok=True)
        if not os.path.exists(metadata_file):
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def save_file(self, file: FileStorage, path: str) -> None:
        file.save(path)

    def file_size(self, path: str) -> int:
        return os.path.getsize(path)

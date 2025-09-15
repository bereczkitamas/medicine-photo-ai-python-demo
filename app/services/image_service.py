import os
import typing
import uuid
from dataclasses import asdict
from datetime import datetime, UTC
from typing import List, Dict, Any

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.config import AppConfig
from app.models.image_entry import ImageEntry
from app.repository.image_repository import ImageRepository
from app.storage.filesystem import FileSystem
from app.validation.image_validator import ImageValidator


class ImageService:
    """Coordinates upload and listing (SRP, orchestrates collaborators)."""
    def __init__(self, upload_dir: str, repo: ImageRepository, fs: FileSystem, validator: ImageValidator):
        self._upload_dir = upload_dir
        self._repo = repo
        self._fs = fs
        self._validator = validator

    def list_images(self) -> List[Dict[str, Any]]:
        return self._repo.load_all()

    def is_allowed(self, filename: str) -> bool:
        return self._validator.allowed_file(filename)

    def save_upload(self, file: FileStorage, url_builder: typing.Callable[[str], str], medicine_name: str) -> Dict[str, Any]:
        if file.filename == '':
            raise ValueError('No selected file')
        if not self._validator.allowed_file(file.filename):
            raise ValueError('Unsupported file type')

        # Validate medicine name
        med = (medicine_name or '').strip()
        if not med:
            raise ValueError('Medicine name is required')

        original_name = secure_filename(file.filename)
        ext = os.path.splitext(original_name)[1].lower()
        stored_name = f"{uuid.uuid4().hex}{ext}"
        self._fs.ensure_storage(self._upload_dir, AppConfig.METADATA_FILE)
        path = os.path.join(self._upload_dir, stored_name)
        self._fs.save_file(file, path)

        version = self.determine_version(med)

        size = self._fs.file_size(path)
        entry = ImageEntry(
            id=uuid.uuid4().hex,
            original_name=original_name,
            stored_name=stored_name,
            url=url_builder(stored_name),
            size=size,
            content_type=file.mimetype,
            uploaded_at=datetime.now(UTC).isoformat() + 'Z',
            medicine_name=med,
            version=version
        )
        self._repo.append(asdict(entry))
        return asdict(entry)

    def determine_version(self, med: str) -> int:
        # Determine version: max an existing version for this medicine_name + 1
        try:
            existing = self._repo.load_all()
        except Exception:
            existing = []
        med_lower = med.lower()
        max_ver = 0
        for e in existing:
            if str(e.get('medicine_name', '')).lower() == med_lower:
                try:
                    v = int(e.get('version', 0))
                except Exception:
                    v = 0
                if v > max_ver:
                    max_ver = v
        version = max_ver + 1 if max_ver >= 0 else 1
        return version

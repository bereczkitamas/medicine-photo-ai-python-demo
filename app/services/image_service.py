import os
import typing
import uuid
from dataclasses import asdict
from datetime import datetime, UTC
from typing import List, Dict, Any

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.config import AppConfig
from app.models.image_entry import ImageEntry, Stage
from app.repository.image_repository import ImageMetadataRepository
from app.storage.filesystem import FileSystem
from app.validation.image_validator import ImageValidator


class ImageService:
    """Coordinates upload and listing (SRP, orchestrates collaborators)."""
    def __init__(self, upload_dir: str, repo: ImageMetadataRepository, fs: FileSystem, validator: ImageValidator):
        self._upload_dir = upload_dir
        self._repo = repo
        self._fs = fs
        self._validator = validator

    def list_images(self) -> List[Dict[str, Any]]:
        # Ensure backward compatibility: default missing stage to UPLOADED
        images = self._repo.load_all()
        for img in images:
            if 'stage' not in img or not img.get('stage'):
                img['stage'] = Stage.UPLOADED.value
        return images

    def filter_images(self, medicine_query: typing.Optional[str] = None, stage: typing.Optional[str] = None) -> List[Dict[str, Any]]:
        """Return images filtered by optional medicine name contains (case-insensitive)
        and/or stage equals (UPLOADED/PROCESSED/ARCHIVED). Stage comparison uses string values.
        """
        images = self.list_images()
        med_q = (medicine_query or '').strip().lower()
        stage_q = (stage or '').strip().upper()
        if med_q:
            images = [img for img in images if str(img.get('medicine_name', '')).lower().find(med_q) != -1]
        if stage_q and stage_q in {Stage.UPLOADED.value, Stage.PROCESSED.value, Stage.ARCHIVED.value}:
            images = [img for img in images if (img.get('stage') or Stage.UPLOADED.value).upper() == stage_q]
        return images

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
            version=version,
            stage=Stage.UPLOADED.value
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

    def promote_stage(self, image_id: str) -> List[Dict[str, Any]]:
        """Promote the stage of the image with the given ID to the next stage.
        UPLOADED -> PROCESSED -> ARCHIVED (stays at ARCHIVED).
        Returns the updated list of images.
        """
        try:
            entries = self._repo.load_all()
        except Exception:
            entries = []
        changed = False
        for e in entries:
            if e.get('id') == image_id:
                current_stage: Stage = e.get('stage') or Stage.UPLOADED.value
                e['stage'] = current_stage.next().value
                changed = True
                break
        if changed:
            self._repo.save_all(entries)
        # Ensure defaulting on return as well
        for img in entries:
            if 'stage' not in img or not img.get('stage'):
                img['stage'] = Stage.UPLOADED.value
        return entries

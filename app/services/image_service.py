import os
import typing
import uuid
import logging
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
from app.services.photo_analyzer import PackagePhotoAnalyzer

from typing import Optional

logger = logging.getLogger(__name__)

class ImageService:
    """Coordinates upload and listing (SRP, orchestrates collaborators)."""
    def __init__(self, upload_dir: str, repo: ImageMetadataRepository, fs: FileSystem, validator: ImageValidator,
                 analyzer: Optional[PackagePhotoAnalyzer] = None):
        self._upload_dir = upload_dir
        self._repo = repo
        self._fs = fs
        self._validator = validator
        self._analyzer = analyzer or PackagePhotoAnalyzer()

    def list_images(self) -> List[Dict[str, Any]]:
        # Ensure backward compatibility: default missing stage to UPLOADED
        images = self._repo.load_all()
        for img in images:
            if 'stage' not in img or not img.get('stage'):
                img['stage'] = Stage.UPLOADED.value
        logger.debug("list_images -> %d items", len(images))
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
        logger.debug("filter_images q='%s' stage='%s' -> %d items", medicine_query, stage, len(images))
        return images

    def is_allowed(self, filename: str) -> bool:
        return self._validator.allowed_file(filename)

    def save_upload(self, file: FileStorage, url_builder: typing.Callable[[str], str], medicine_name: str) -> Dict[str, Any]:
        if file.filename == '':
            raise ValueError('No selected file')
        if not self._validator.allowed_file(file.filename):
            raise ValueError('Unsupported file type')

        # Validate medicine name (keep for backward-compat with UI/tests)
        med_input = (medicine_name or '').strip()
        if not med_input:
            raise ValueError('Medicine name is required')

        original_name = secure_filename(file.filename)
        ext = os.path.splitext(original_name)[1].lower()
        stored_name = f"{uuid.uuid4().hex}{ext}"
        self._fs.ensure_storage(self._upload_dir, AppConfig.METADATA_FILE)
        path = os.path.join(self._upload_dir, stored_name)
        self._fs.save_file(file, path)
        logger.info("Saved file to %s (size=%s, content_type=%s)", path, getattr(file, 'content_length', None), file.mimetype)

        # Default metadata based on input
        med = med_input
        stage_value = Stage.UPLOADED

        form, med, stage_value, substance = self.__image_analysis(med, path, stage_value, file.mimetype)

        version = self.__determine_version(med)

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
            stage=stage_value
        )
        entry_dict = asdict(entry)
        # Attach optional AI fields for downstream consumers
        if form:
            entry_dict['form'] = form
        if substance:
            entry_dict['substance'] = substance
        self._repo.append(entry_dict)
        return entry_dict

    def __image_analysis(self, med: str, path: str, stage_value: Stage, file_mimetype: str = 'image/*',
                         ) -> tuple[str, str | None, Stage, str | None]:
        # Invoke Gemini analysis if available; failures fall back silently
        analysis_result: tuple[bool, str, str, str] | None = None
        try:
            with open(path, 'rb') as fbytes:
                content = fbytes.read()
            analysis_result = self._analyzer.analyze_image(content, file_mimetype)
        except Exception as e:
            # On any analyzer error, proceed without AI influence
            logger.exception("Analyzer error: %s", e)
        if analysis_result and analysis_result[0] is False:
            # Remove invalid file and reject upload
            # try:
            #     os.remove(path)
            # except Exception:
            #     pass
            raise ValueError('Uploaded image is not recognized as a medicine package')
        # Use detected medicine name if available; otherwise keep user input
        if analysis_result and analysis_result[1]:
            med = analysis_result[1]
        form = analysis_result[2] if analysis_result else None
        substance = analysis_result[3] if analysis_result else None
        # If critical info missing on image, mark for approval
        if not analysis_result or not analysis_result[1] or not analysis_result[2] or not analysis_result[3]:
            stage_value = Stage.APPROVAL_WAITING

        return form, med, stage_value, substance

    def __determine_version(self, med: str) -> int:
        # Determine version: max an existing version for this medicine_name + 1
        try:
            existing = self._repo.load_all()
        except Exception as e:
            logger.exception("Failed to load existing metadata: %s", e)
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
                current_stage: Stage = e.get('stage') or Stage.UPLOADED
                e['stage'] = current_stage.next()
                changed = True
                break
        if changed:
            self._repo.save_all(entries)
        # Ensure defaulting on return as well
        for img in entries:
            if 'stage' not in img or not img.get('stage'):
                img['stage'] = Stage.UPLOADED.value
        return entries

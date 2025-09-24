from typing import Any, Dict, List
import logging
from fastapi import APIRouter, Request, UploadFile, HTTPException, status, Depends, File, Form
from fastapi.responses import JSONResponse
from werkzeug.datastructures import FileStorage

from app.repository.image_repository import ImageMetadataRepository
from app.storage.filesystem import FileSystem
from app.validation.image_validator import ImageValidator
from app.services.image_service import ImageService
from app.config import AppConfig

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Images API"])

# Dependency providers
_fs_singleton = FileSystem()

def get_fs() -> FileSystem:
    return _fs_singleton

def get_repo(fs: FileSystem = Depends(get_fs)) -> ImageMetadataRepository:
    return ImageMetadataRepository(metadata_file=AppConfig.METADATA_FILE, fs=fs)

def get_validator() -> ImageValidator:
    return ImageValidator(allowed_extensions=AppConfig.ALLOWED_EXTENSIONS)

from app.services.photo_analyzer import PackagePhotoAnalyzer

def get_analyzer() -> PackagePhotoAnalyzer:
    return PackagePhotoAnalyzer()


def get_image_service(repo: ImageMetadataRepository = Depends(get_repo), fs: FileSystem = Depends(get_fs),
                      validator: ImageValidator = Depends(get_validator),
                      analyzer: PackagePhotoAnalyzer = Depends(get_analyzer)) -> ImageService:
    return ImageService(upload_dir=AppConfig.UPLOAD_DIR, repo=repo, fs=fs, validator=validator, analyzer=analyzer)


@router.get(
    '/images',
    summary="List uploaded images",
    description="Return all uploaded medicine images with metadata.",
    responses={
        200: {
            "description": "Successful retrieval",
            "content": {
                "application/json": {
                    "example": [{
                        "id": "123", "medicine_name": "Ibuprofen", "original_name": "img.jpg",
                         "stored_name": "123.webp", "url": "/uploads/123.webp", "uploaded_at": "2025-09-24T20:54:00Z",
                         "stage": "new"
                    }]
                }
            }
        }
    }
)
async def api_list_images(request: Request, image_service: ImageService = Depends(get_image_service)) -> List[
    Dict[str, Any]]:
    logger.info("GET /api/images from %s", request.client.host if request.client else "unknown")
    images = image_service.list_images()
    logger.debug("Returned %d images", len(images))
    return images


@router.post(
    '/images',
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image",
    description="Upload a medicine package image as multipart/form-data. Requires authentication via session (web login).",
    responses={
        201: {
            "description": "Image uploaded",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123", "medicine_name": "Ibuprofen", "original_name": "img.jpg", "stored_name": "123.webp",
                        "url": "/uploads/123.webp", "uploaded_at": "2025-09-24T20:54:00Z", "stage": "new"
                    }
                }
            }
        },
        400: {"description": "Validation error"},
        401: {"description": "Authentication required"}
    }
)
async def api_upload_image(request: Request,
                           medicine_name: str = Form(...),
                           file: UploadFile = File(...),
                           image_service: ImageService = Depends(get_image_service)):
    """
    Upload an image with fields:
    - medicine_name: string form field
    - file: multipart file (image)
    """

    # Require authentication to upload via API (session-based)
    if not (getattr(request, 'session', None) and request.session.get('user')):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required')

    try:
        logger.info("POST /api/images medicine_name='%s' content_type=%s", medicine_name,
                    getattr(file, 'content_type', None))
        entry = image_service.save_upload(
            FileStorage(file.file, content_type=file.content_type),
            lambda stored: request.url_for('uploads', path=stored).path,
            medicine_name)
        logger.info("Upload succeeded id=%s stored_name=%s", entry.get('id'), entry.get('stored_name'))
        return JSONResponse(content=entry, status_code=status.HTTP_201_CREATED)
    except ValueError as e:
        logger.warning("Upload failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))

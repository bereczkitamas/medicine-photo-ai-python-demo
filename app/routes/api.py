from typing import Any, Dict, List
from fastapi import APIRouter, Request, UploadFile, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from werkzeug.datastructures import FileStorage

from app.repository.image_repository import ImageRepository
from app.storage.filesystem import FileSystem
from app.validation.image_validator import ImageValidator
from app.services.image_service import ImageService
from app.config import AppConfig

router = APIRouter()


# Dependency providers
_fs_singleton = FileSystem()

def get_fs() -> FileSystem:
    return _fs_singleton

def get_repo(fs: FileSystem = Depends(get_fs)) -> ImageRepository:
    return ImageRepository(metadata_file=AppConfig.METADATA_FILE, fs=fs)

def get_validator() -> ImageValidator:
    return ImageValidator(allowed_extensions=AppConfig.ALLOWED_EXTENSIONS)

def get_image_service(repo: ImageRepository = Depends(get_repo), fs: FileSystem = Depends(get_fs), validator: ImageValidator = Depends(get_validator)) -> ImageService:
    return ImageService(upload_dir=AppConfig.UPLOAD_DIR, repo=repo, fs=fs, validator=validator)


@router.get('/images')
async def api_list_images(request: Request, image_service: ImageService = Depends(get_image_service)) -> List[Dict[str, Any]]:
    return image_service.list_images()


@router.post('/images', status_code=status.HTTP_201_CREATED)
async def api_upload_image(request: Request,
                           medicine_name: str,
                           file: UploadFile,
                           image_service: ImageService = Depends(get_image_service)):

    try:
        entry = image_service.save_upload(
            FileStorage(file.file, content_type=file.content_type),
            lambda stored: request.url_for('uploads', path=stored).path,
            medicine_name)
        return JSONResponse(content=entry, status_code=status.HTTP_201_CREATED)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

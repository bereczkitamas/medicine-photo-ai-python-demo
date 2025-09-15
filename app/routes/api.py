from typing import Any, Dict, List
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import JSONResponse
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
async def api_upload_image(request: Request, file: UploadFile = File(...), image_service: ImageService = Depends(get_image_service)):
    # Build URL to uploaded file using FastAPI mounted static path
    def url_builder(stored: str) -> str:
        return request.url_for('uploads', path=stored)

    # Convert UploadFile to a Werkzeug-like FileStorage adapter expected by service
    # The service expects .filename, .mimetype, and a file-like stream for saving
    class _FileWrapper:
        def __init__(self, uf: UploadFile):
            self.filename = uf.filename or ''
            self.mimetype = uf.content_type or 'application/octet-stream'
            self.file = uf.file
        def save(self, path: str):
            # Write the uploaded content to disk
            self.file.seek(0)
            with open(path, 'wb') as out:
                out.write(self.file.read())

    try:
        entry = image_service.save_upload(_FileWrapper(file), url_builder)
        return JSONResponse(content=entry, status_code=status.HTTP_201_CREATED)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

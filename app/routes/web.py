from typing import List, Dict, Any

from fastapi import APIRouter, Request, UploadFile, File, status, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from werkzeug.datastructures import FileStorage

from app.routes.api import get_image_service
from app.services.image_service import ImageService

router = APIRouter()


def _templates(request: Request):
    return request.app.state.templates


@router.get('/', response_class=HTMLResponse)
async def index(request: Request, image_service: ImageService = Depends(get_image_service)) -> Response:
    # Read filters from query params (for initial page render)
    med_q = request.query_params.get('q')
    stage_q = request.query_params.get('stage')
    images: List[Dict[str, Any]] = image_service.filter_images(med_q, stage_q)
    images_sorted = sorted(images, key=lambda image: image.get('uploaded_at', ''), reverse=True)
    return _templates(request).TemplateResponse('index.html', {"request": request, "images": images_sorted, "q": med_q or '', "stage": (stage_q or '')})


@router.get('/partials/gallery', response_class=HTMLResponse)
async def partial_gallery(request: Request, image_service: ImageService = Depends(get_image_service)) -> Response:
    # Accept HTMX or query params for filtering
    med_q = request.query_params.get('q')
    stage_q = request.query_params.get('stage')
    images: List[Dict[str, Any]] = image_service.filter_images(med_q, stage_q)
    images_sorted = sorted(images, key=lambda image: image.get('uploaded_at', ''), reverse=True)
    return _templates(request).TemplateResponse('_gallery.html', {"request": request, "images": images_sorted})


@router.post('/images/{image_id}/promote', response_class=HTMLResponse)
async def promote_image_stage(request: Request, image_id: str, image_service: ImageService = Depends(get_image_service)) -> Response:
    is_htmx = request.headers.get('HX-Request') == 'true'
    image_service.promote_stage(image_id)
    # Preserve filters after promote
    med_q = request.query_params.get('q')
    stage_q = request.query_params.get('stage')
    images_sorted = sorted(image_service.filter_images(med_q, stage_q), key=lambda image: image.get('uploaded_at', ''), reverse=True)
    if is_htmx:
        return _templates(request).TemplateResponse('_gallery.html', {"request": request, "images": images_sorted})
    return _templates(request).TemplateResponse('index.html', {"request": request, "images": images_sorted, "q": med_q or '', "stage": (stage_q or '')})


@router.get('/upload', response_class=HTMLResponse)
async def upload_form(request: Request) -> Response:
    return _templates(request).TemplateResponse('upload.html', {"request": request})


@router.post('/upload')
async def ui_upload(request: Request, medicine_name: str = Form(None), file: UploadFile = File(None), image_service: ImageService = Depends(get_image_service)) -> Response:
    is_htmx = request.headers.get('HX-Request') == 'true'

    if file is None:
        # HTMX: return gallery and an HX-Trigger header for flash-like behavior
        if is_htmx:
            body = _templates(request).get_template('_gallery.html').render({
                "request": request,
                "images": sorted(image_service.list_images(), key=lambda x: x.get('uploaded_at', ''), reverse=True)
            })
            return Response(content=body, status_code=200, headers={'HX-Trigger': 'flash'})
        # Non-HTMX: redirect to home
        return RedirectResponse(url='/', status_code=status.HTTP_302_FOUND)

    # Build URL using mounted static
    def url_builder(stored: str) -> str:
        return request.url_for('uploads', path=stored).path

    try:
        image_service.save_upload(
            FileStorage(file.file, filename=file.filename, content_type=file.content_type), url_builder, medicine_name or '')
        if is_htmx:
            med_q = request.query_params.get('q')
            stage_q = request.query_params.get('stage')
            images_sorted = sorted(image_service.filter_images(med_q, stage_q), key=lambda image: image.get('uploaded_at', ''), reverse=True)
            return _templates(request).TemplateResponse('_gallery.html', {"request": request, "images": images_sorted})
        return RedirectResponse(url=f"/?q={request.query_params.get('q','')}&stage={request.query_params.get('stage','')}", status_code=status.HTTP_302_FOUND)
    except ValueError:
        if is_htmx:
            med_q = request.query_params.get('q')
            stage_q = request.query_params.get('stage')
            images_sorted = sorted(image_service.filter_images(med_q, stage_q), key=lambda image: image.get('uploaded_at', ''), reverse=True)
            return Response(content=_templates(request).get_template('_gallery.html').render({"request": request, "images": images_sorted}), status_code=400, headers={'HX-Trigger': 'upload-error'})
        return RedirectResponse(url=f"/?q={request.query_params.get('q','')}&stage={request.query_params.get('stage','')}", status_code=status.HTTP_302_FOUND)

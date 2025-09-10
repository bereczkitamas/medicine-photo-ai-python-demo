from typing import List, Dict, Any

from flask import Blueprint, render_template, current_app, send_from_directory, request, redirect, url_for, flash

web = Blueprint('web', __name__)


@web.route('/')
def index():
    image_service = current_app.extensions['image_service']
    images: List[Dict[str, Any]] = image_service.list_images()

    def function(x):
        return x.get('uploaded_at', '')

    images_sorted = sorted(images, key=function, reverse=True)
    return render_template('index.html', images=images_sorted)


@web.route('/partials/gallery')
def partial_gallery():
    image_service = current_app.extensions['image_service']
    images: List[Dict[str, Any]] = image_service.list_images()
    images_sorted = sorted(images, key=lambda x: x.get('uploaded_at', ''), reverse=True)
    return render_template('_gallery.html', images=images_sorted)


@web.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@web.route('/upload', methods=['GET'])
def upload_form():
    return render_template('upload.html')


@web.route('/upload', methods=['POST'])
def ui_upload():
    image_service = current_app.extensions['image_service']
    is_htmx = request.headers.get('HX-Request') == 'true'
    if 'file' not in request.files:
        flash('No file part in request', 'error')
        if is_htmx:
            # Return updated gallery even on error (no change), plus out-of-band flash
            response = render_template('_gallery.html', images=sorted(image_service.list_images(), key=lambda x: x.get('uploaded_at', ''), reverse=True))
            return response, 200, {'HX-Trigger': 'flash'}
        return redirect(url_for('web.index'))
    file = request.files['file']
    try:
        image_service.save_upload(file, lambda stored: url_for('web.uploaded_file', filename=stored, _external=False))
        if is_htmx:
            # Re-render gallery partial after successful upload
            images_sorted = sorted(image_service.list_images(), key=lambda x: x.get('uploaded_at', ''), reverse=True)
            return render_template('_gallery.html', images=images_sorted)
        flash('Image uploaded successfully', 'success')
        return redirect(url_for('web.index'))
    except ValueError as e:
        if is_htmx:
            # On validation error return gallery unchanged; client can show flash if implemented
            images_sorted = sorted(image_service.list_images(), key=lambda x: x.get('uploaded_at', ''), reverse=True)
            # Put message in a response header for potential client handling
            return render_template('_gallery.html', images=images_sorted), 400, {'HX-Trigger': 'upload-error'}
        flash(str(e), 'error')
        return redirect(url_for('web.index'))

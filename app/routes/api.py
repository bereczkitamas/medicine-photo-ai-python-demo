from flask import Blueprint, jsonify, request, url_for, current_app

api = Blueprint('api', __name__)


@api.route('/images', methods=['GET'])
def api_list_images():
    image_service = current_app.extensions['image_service']
    return jsonify(image_service.list_images())


@api.route('/images', methods=['POST'])
def api_upload_image():
    image_service = current_app.extensions['image_service']
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400
    file = request.files['file']
    try:
        entry = image_service.save_upload(file, lambda stored: url_for('web.uploaded_file', filename=stored, _external=False))
        return jsonify(entry), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

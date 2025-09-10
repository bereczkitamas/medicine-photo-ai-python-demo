import os
from flask import Flask
from app.config import AppConfig
from app.storage.filesystem import FileSystem
from app.repository.image_repository import ImageRepository
from app.validation.image_validator import ImageValidator
from app.services.image_service import ImageService


def create_app() -> Flask:
    # Ensure templates path points to project-level templates directory
    templates_path = os.path.join(os.path.dirname(__file__), '..', 'templates')
    app = Flask(__name__, template_folder=templates_path)
    app.config['UPLOAD_FOLDER'] = AppConfig.UPLOAD_DIR
    app.config['MAX_CONTENT_LENGTH'] = AppConfig.MAX_CONTENT_LENGTH

    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

    # Wiring
    fs = FileSystem()
    # Ensure storage folder and metadata file exist on startup
    fs.ensure_storage(AppConfig.UPLOAD_DIR, AppConfig.METADATA_FILE)

    repo = ImageRepository(AppConfig.METADATA_FILE, fs)
    validator = ImageValidator(AppConfig.ALLOWED_EXTENSIONS)
    image_service = ImageService(AppConfig.UPLOAD_DIR, repo, fs, validator)

    # Store services on app for access in blueprints
    app.extensions = getattr(app, 'extensions', {})
    app.extensions['image_service'] = image_service

    # Register routes
    from app.routes.web import web
    from app.routes.api import api
    app.register_blueprint(web)
    app.register_blueprint(api, url_prefix='/api')

    return app

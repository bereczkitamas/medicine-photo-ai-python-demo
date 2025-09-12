import os
from flask import Flask
from app.config import AppConfig
from app.di import build_container

# Factory function to create a Flask app instance
def create_app() -> Flask:
    # Ensure templates path points to project-level templates directory
    templates_path = os.path.join(os.path.dirname(__file__), '..', 'templates')
    app = Flask(__name__, template_folder=templates_path)
    app.config['UPLOAD_FOLDER'] = AppConfig.UPLOAD_DIR
    app.config['MAX_CONTENT_LENGTH'] = AppConfig.MAX_CONTENT_LENGTH # set max file size, otherwise it is unlimited

    # see: https://flask.palletsprojects.com/en/stable/config/#SECRET_KEY
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

    # Build DI container and wire dependencies (dependency-injector)
    container = build_container(AppConfig)

    # Expose commonly used services
    app.extensions['image_service'] = container.image_service()

    # Register routes
    from app.routes.web import web
    from app.routes.api import api
    app.register_blueprint(web)
    app.register_blueprint(api, url_prefix='/api')

    return app

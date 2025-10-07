import os


class AppConfig:
    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')
    METADATA_FILE = os.path.join(UPLOAD_DIR, 'metadata.json')
    ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

Medicine Package Photo Management

A minimal FastAPI web app to upload and list medicine package photos.

Features
- REST API
  - POST /api/images — upload an image (multipart form-data, field name: file)
  - GET /api/images — list uploaded images (JSON)
- UI
  - GET / — page to upload and view uploaded images

Dependency Injection
- The app now uses the `dependency-injector` library via `app/di.py` to wire components.
- `create_app()` builds the container and exposes it:
  - `current_app.extensions['image_service']` — resolved service instance
- Benefits: centralized wiring, easier overrides in tests, clearer composition root.

Run locally
1. Using Poetry (recommended):
   - Install Poetry: https://python-poetry.org/docs/#installation
   - Install deps: poetry install
   - Run the server: poetry run python app.py
   - Run tests: poetry run pytest -q
     - On Windows PowerShell or CMD, the same command applies.
   - Open http://localhost:8000 in your browser.
2. Using pip (legacy):
   - Create and activate a virtual environment (recommended).
   - Install dependencies: pip install -r requirements.txt
   - Run tests: pytest -q
   - Run the server: python app.py
   - Open http://localhost:8000 in your browser.

Notes
- Uploaded files are saved under uploads/ and metadata is tracked in uploads/metadata.json.
- Max upload size is 16 MB. Supported extensions: .png .jpg .jpeg .gif .bmp .webp.
- This is a simple demo; no authentication is included.

Used technologies:
- Python
- Fastapi
- Jinja2
- Tailwind CSS
- uvicorn
- htmx
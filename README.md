Medicine Package Photo Management

A minimal FastAPI web app to upload and list medicine package photos.

[![Build and Deploy to Cloud Run](https://github.com/bereczkitamas/medicine-photo-ai-python-demo/actions/workflows/google-cloudrun-docker.yml/badge.svg)](https://github.com/bereczkitamas/medicine-photo-ai-python-demo/actions/workflows/google-cloudrun-docker.yml)

Features
- REST API
  - POST /api/images — upload an image (multipart form-data, field name: file)
  - GET /api/images — list uploaded images (JSON)
- UI
  - GET / — page to upload and view uploaded images

Run locally
1. Using Poetry (recommended):
   - Install Poetry: https://python-poetry.org/docs/#installation
   - Install deps: poetry install
   - Run the server: poetry run python app.py
   - Run tests: poetry run pytest -q
     - On Windows PowerShell or CMD, the same command applies.
   - Open http://localhost:8000 in your browser.
   - Optional: Configure Google OAuth by setting environment variables before running:
     - GOOGLE_CLIENT_ID
     - GOOGLE_CLIENT_SECRET
     - SESSION_SECRET (optional, for signing session cookies; a default is used if omitted)
     - Authorized redirect URI in Google Cloud Console should be: http://localhost:8000/auth/callback
2. Using pip (legacy):
   - Create and activate a virtual environment (recommended).
   - Install dependencies: pip install -r requirements.txt
   - Run tests: pytest -q
   - Run the server: python app.py
   - Open http://localhost:8000 in your browser.

Notes
- Uploaded files are saved under uploads/ and metadata is tracked in uploads/metadata.json.
- Max upload size is 16 MB. Supported extensions: .png .jpg .jpeg .gif .bmp .webp.
- Optional Google login is included for the web UI. Uploading new images requires being logged in. If Google OAuth is not configured, you won't be able to upload via the UI or API.

Docker
- Build and run with Docker:
  - docker build -t medicine-photo-ai-python-demo .
  - docker run --rm -p 8000:8000 -e PORT=8000 -v %cd%\uploads:/app/uploads medicine-photo-ai-python-demo
- Or using docker-compose:
  - docker compose up --build
  - Then open http://localhost:8000

Used technologies:
- Python
- Fastapi
- Jinja2
- Tailwind CSS
- uvicorn
- htmx

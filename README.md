Medicine Package Photo Management

A minimal Flask web app to upload and list medicine package photos.

Features
- REST API
  - POST /api/images — upload an image (multipart form-data, field name: file)
  - GET /api/images — list uploaded images (JSON)
- UI
  - GET / — page to upload and view uploaded images

Run locally
1. Create and activate a virtual environment (recommended).
2. Install dependencies:
   pip install -r requirements.txt
3. Run the server:
   python app.py
4. Open http://localhost:5000 in your browser.

Notes
- Uploaded files are saved under uploads/ and metadata is tracked in uploads/metadata.json.
- Max upload size is 16 MB. Supported extensions: .png .jpg .jpeg .gif .bmp .webp.
- This is a simple demo; no authentication is included.

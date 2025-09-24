import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from app.config import AppConfig
from app.services.auth import ensure_session_middleware
from app.routes.web import router as web_router
from app.routes.api import router as api_router
from app.routes.auth_api import router as auth_router
from app.logging_config import configure_logging

# Factory function to create a FastAPI app instance
def create_app() -> FastAPI:
    # Lifespan handler to replace deprecated @app.on_event("startup")
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from app.storage.filesystem import FileSystem
        fs = FileSystem()
        fs.ensure_storage(AppConfig.UPLOAD_DIR, AppConfig.METADATA_FILE)
        yield
        # No shutdown actions needed currently

    configure_logging()
    app = FastAPI(lifespan=lifespan)

    # Mount static-like uploads serving
    app.mount("/uploads", StaticFiles(directory=AppConfig.UPLOAD_DIR), name="uploads")

    # Templates setup
    templates_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
    app.state.templates = Jinja2Templates(directory=templates_dir)

    # CORS (optional, open by default for demo)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    ensure_session_middleware(app)
    app.include_router(web_router)
    app.include_router(api_router, prefix="/api")
    app.include_router(auth_router)

    return app

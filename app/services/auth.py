import os

from flask.cli import load_dotenv
from starlette.applications import AppType
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth

# Configure OAuth
oauth = OAuth()

load_dotenv()
oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID', ''),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET', ''),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

def ensure_session_middleware(app: AppType):
    # Starlette/FastAPI requires SessionMiddleware to store user session
    # Add only once; secret from env with fallback for dev
    if not any(isinstance(m.cls, SessionMiddleware) or m.cls is SessionMiddleware for m in app.user_middleware):
        secret = os.environ.get('SESSION_SECRET', 'dev-secret-change-me')
        app.add_middleware(SessionMiddleware, secret_key=secret, same_site='lax')




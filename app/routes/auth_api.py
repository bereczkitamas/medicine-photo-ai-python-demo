from typing import Optional

from authlib.integrations.base_client import OAuthError
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.services.auth import oauth

router = APIRouter()

@router.get('/login')
async def login(request: Request):
    # ensure_session_middleware(request.app)
    # Basic guard if env vars are missing
    # if not os.environ.get('GOOGLE_CLIENT_ID') or not os.environ.get('GOOGLE_CLIENT_SECRET'):
    #     return RedirectResponse(url='/?login=not-configured')
    redirect_uri = request.url_for('auth_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get('/auth/callback')
async def auth_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        return RedirectResponse(url='/?login=failed')

    user: Optional[dict] = token.get('userinfo')
    if not user:
        # If userinfo isn't provided, try to fetch it
        resp = await oauth.google.get('userinfo', token=token)
        user = resp.json() if resp is not None else None
    if not user:
        return RedirectResponse(url='/?login=failed')
    # Persist minimal user info in session
    request.session['user'] = {
        'email': user.get('email'),
        'name': user.get('name') or user.get('given_name') or '',
        'picture': user.get('picture')
    }
    return RedirectResponse(url='/?login=success')


@router.get('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/?logout=1')
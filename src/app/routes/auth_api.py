from typing import Optional
import logging

from authlib.integrations.base_client import OAuthError
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.services.auth import oauth

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Auth"]) 

@router.get('/login', summary="Login with Google",
            description="Initiate OAuth 2.0 login with Google. Redirects user to Google's consent screen.")
async def login(request: Request):
    logger.info("GET /login - starting OAuth flow")
    redirect_uri = request.url_for('auth_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get('/auth/callback', summary="OAuth callback",
            description="Handle the OAuth 2.0 callback from Google. On success, stores a minimal user object in the session and redirects to home.")
async def auth_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        logger.warning("OAuth error during callback: %s", e)
        return RedirectResponse(url='/?login=failed')

    user: Optional[dict] = token.get('userinfo')
    if not user:
        # If userinfo isn't provided, try to fetch it
        resp = await oauth.google.get('userinfo', token=token)
        user = resp.json() if resp is not None else None
    if not user:
        logger.warning("OAuth callback user fetch failed")
        return RedirectResponse(url='/?login=failed')
    # Persist minimal user info in session
    request.session['user'] = {
        'email': user.get('email'),
        'name': user.get('name') or user.get('given_name') or '',
        'picture': user.get('picture')
    }
    logger.info("User '%s' logged in", user.get('email'))
    return RedirectResponse(url='/?login=success')


@router.get('/logout', summary="Logout", description="Clear the current session and redirect to home.")
async def logout(request: Request):
    email = (request.session.get('user') or {}).get('email') if getattr(request, 'session', None) else None
    request.session.pop('user', None)
    logger.info("User '%s' logged out", email)
    return RedirectResponse(url='/?logout=1')
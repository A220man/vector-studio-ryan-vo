from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx

from app.core.config import settings
from app.core.database import get_db
from app.core.models import User
from app.core.auth import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


class TokenExchangeRequest(BaseModel):
    code: str
    redirect_uri: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.get("/login")
async def login():
    """Redirect to Keycloak login page."""
    if not settings.oidc_enabled:
        raise HTTPException(status_code=503, detail="OIDC not enabled")
    
    params = {
        "client_id": settings.oidc_client_id,
        "redirect_uri": settings.oidc_redirect_uri,
        "response_type": "code",
        "scope": "openid profile email",
    }
    from urllib.parse import urlencode
    auth_url = f"{settings.oidc_issuer_url}/protocol/openid-connect/auth?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.post("/callback", response_model=TokenResponse)
async def callback(request: TokenExchangeRequest, db: Session = Depends(get_db)):
    """Exchange authorization code for tokens and create session."""
    if not settings.oidc_enabled:
        raise HTTPException(status_code=503, detail="OIDC not enabled")

    # Exchange code for tokens with Keycloak
    token_url = f"{settings.oidc_issuer_url}/protocol/openid-connect/token"
    data = {
        "grant_type": "authorization_code",
        "code": request.code,
        "redirect_uri": request.redirect_uri,
        "client_id": settings.oidc_client_id,
    }
    
    if settings.oidc_client_secret:
        data["client_secret"] = settings.oidc_client_secret

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(token_url, data=data)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
        token_data = response.json()

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token in response")

    # Validate the token and get/create user
    from app.core.auth import TokenData
    import json
    from jose import jwt
    
    # Decode without verification to get user info (already validated by Keycloak)
    try:
        payload = jwt.get_unverified_claims(access_token)
        token_data = TokenData(**payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid token: {e}")

    user = AuthService.get_or_create_user(token_data)
    
    # Create our session token
    session_token = AuthService.create_access_token(user)

    return TokenResponse(
        access_token=session_token,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "roles": user.get_roles(),
        }
    )


@router.post("/logout")
async def logout():
    """Logout endpoint - client should clear token."""
    if not settings.oidc_enabled:
        raise HTTPException(status_code=503, detail="OIDC not enabled")
    
    # Return Keycloak logout URL
    from urllib.parse import urlencode
    params = {
        "post_logout_redirect_uri": settings.oidc_logout_uri,
    }
    logout_url = f"{settings.oidc_issuer_url}/protocol/openid-connect/logout?{urlencode(params)}"
    return {"logout_url": logout_url}


@router.get("/me")
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Get current authenticated user from session token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header[7:]  # Remove "Bearer "
    payload = AuthService.decode_session_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "roles": user.get_roles(),
    }


async def get_current_user_dependency(request: Request, db: Session = Depends(get_db)) -> User:
    """FastAPI dependency for protected routes."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header[7:]
    payload = AuthService.decode_session_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
from typing import Optional
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from pydantic import BaseModel
import httpx
import json

from app.core.config import settings
from app.core.models import User
from app.core.database import SessionLocal


class TokenData(BaseModel):
    sub: str
    preferred_username: str
    email: str
    realm_access: dict = {}
    exp: int


class AuthService:
    _jwks_cache: Optional[dict] = None
    _jwks_fetched_at: Optional[datetime] = None
    _jwks_cache_ttl = timedelta(hours=1)

    @classmethod
    async def get_jwks(cls) -> dict:
        """Fetch and cache JWKS from Keycloak."""
        now = datetime.now(timezone.utc)
        if (
            cls._jwks_cache
            and cls._jwks_fetched_at
            and (now - cls._jwks_fetched_at) < cls._jwks_cache_ttl
        ):
            return cls._jwks_cache

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.oidc_issuer_url}/protocol/openid-connect/certs")
            response.raise_for_status()
            cls._jwks_cache = response.json()
            cls._jwks_fetched_at = now
            return cls._jwks_cache

    @classmethod
    async def validate_token(cls, token: str) -> Optional[TokenData]:
        """Validate an OIDC access token."""
        if not settings.oidc_enabled:
            return None

        try:
            jwks = await cls.get_jwks()
            # Get the key ID from token header
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")

            key = None
            for k in jwks.get("keys", []):
                if k.get("kid") == kid:
                    key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(k))
                    break

            if not key:
                return None

            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=settings.oidc_client_id,
                issuer=settings.oidc_issuer_url,
            )
            return TokenData(**payload)
        except (JWTError, httpx.HTTPError, json.JSONDecodeError):
            return None

    @classmethod
    def get_or_create_user(cls, token_data: TokenData) -> User:
        """Get existing user or create new one from token data."""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.keycloak_id == token_data.sub).first()
            if not user:
                roles = token_data.realm_access.get("roles", [])
                user = User(
                    keycloak_id=token_data.sub,
                    username=token_data.preferred_username,
                    email=token_data.email,
                    roles=json.dumps(roles),
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            else:
                # Update roles if changed
                new_roles = token_data.realm_access.get("roles", [])
                if set(user.get_roles()) != set(new_roles):
                    user.set_roles(new_roles)
                    db.commit()
            return user
        finally:
            db.close()

    @classmethod
    def create_access_token(cls, user: User) -> str:
        """Create a session token for the user."""
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
        to_encode = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "roles": user.get_roles(),
            "exp": expire,
        }
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    @classmethod
    def decode_session_token(cls, token: str) -> Optional[dict]:
        """Decode a session token."""
        try:
            return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        except JWTError:
            return None
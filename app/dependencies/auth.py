import time
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwk, jwt
from jose.utils import base64url_decode
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models import User

JWKS_CACHE_SECONDS = 300
security = HTTPBearer(auto_error=False)
_jwks_cache: dict[str, Any] = {"keys": [], "expires_at": 0.0}


@dataclass
class AuthenticatedUser:
    user: User
    roles: list[str]
    token: dict[str, Any]


def _get_jwks(settings: Settings) -> list[dict[str, Any]]:
    now = time.time()
    if _jwks_cache["keys"] and _jwks_cache["expires_at"] > now:
        return _jwks_cache["keys"]
    try:
        response = httpx.get(settings.jwks_url, timeout=5.0)
        response.raise_for_status()
        body = response.json()
        keys = body.get("keys", body)
    except Exception as exc:  # pragma: no cover - network failure path
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to fetch JWKS",
        ) from exc
    _jwks_cache["keys"] = keys
    _jwks_cache["expires_at"] = now + JWKS_CACHE_SECONDS
    return keys


def _decode_and_verify_jwt(token: str, settings: Settings) -> dict[str, Any]:
    try:
        headers = jwt.get_unverified_header(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token header")

    kid = headers.get("kid")
    keys = _get_jwks(settings)
    key_data = next((key for key in keys if key.get("kid") == kid), None)
    if not key_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown token key")

    try:
        public_key = jwk.construct(key_data)
        message, encoded_signature = token.rsplit(".", 1)
        decoded_signature = base64url_decode(encoded_signature.encode())
        if not public_key.verify(message.encode(), decoded_signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token verification failed")

    claims = jwt.get_unverified_claims(token)
    if "exp" in claims and time.time() > claims["exp"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    if settings.jwt_audience:
        token_audience = claims.get("aud")
        if token_audience != settings.jwt_audience:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid audience")

    if settings.jwt_issuer:
        token_issuer = claims.get("iss")
        if token_issuer != settings.jwt_issuer:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid issuer")

    return claims


def _roles_from_claims(claims: dict[str, Any]) -> list[str]:
    roles = claims.get("roles") or claims.get("role") or claims.get("authorities") or []
    if isinstance(roles, str):
        return [roles]
    try:
        return list(roles)
    except Exception:
        return []


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    claims = _decode_and_verify_jwt(credentials.credentials, settings)
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    username = claims.get("preferred_username") or claims.get("email") or f"user_{user_id}"
    full_name = claims.get("name")
    roles = _roles_from_claims(claims)

    user = db.get(User, user_id)
    roles_str = ",".join(roles)
    if user is None:
        user = User(id=user_id, username=username, full_name=full_name, roles=roles_str)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.username = username
        user.full_name = full_name
        user.roles = roles_str
        db.commit()

    return AuthenticatedUser(user=user, roles=roles, token=claims)


async def require_admin(auth: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    if "admin" not in auth.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return auth


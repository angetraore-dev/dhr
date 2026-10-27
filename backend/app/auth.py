"""
Authentification : API key (lecture) + JWT Bearer (écriture).
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from jose import JWTError, jwt

from app.config import get_settings

logger = logging.getLogger("dhr.auth")

settings = get_settings()


# --- Extraction de l'API key et du JWT ---
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


# --- Payload JWT ---
class JWTUser:
    """Utilisateur authentifié par JWT."""

    def __init__(self, sub: str, role: str = "ingesteur"):
        self.sub = sub
        self.role = role


# --- Fonctions JWT ---
def create_access_token(sub: str, role: str = "ingesteur", expires_min: int | None = None) -> str:
    """Crée un JWT pour un utilisateur (écriture)."""
    if expires_min is None:
        expires_min = settings.jwt_expire_min
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_min)
    payload = {"sub": sub, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> JWTUser:
    """Décode un JWT et retourne l'utilisateur."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        sub = payload.get("sub")
        role = payload.get("role", "ingesteur")
        if sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide : 'sub' manquant",
            )
        return JWTUser(sub=sub, role=role)
    except JWTError as e:
        logger.warning("JWT invalide : %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT invalide ou expiré",
        )


# --- Dépendances FastAPI ---

async def require_api_key(
    request: Request,
    api_key: str | None = Depends(api_key_header),
) -> None:
    """
    Vérifie la présence et la validité de l'API key (lecture).

    Le header X-API-Key doit correspondre à API_KEY_READ.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header X-API-Key manquant",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    if api_key != settings.api_key_read:
        logger.warning("API key invalide reçue de %s", request.client)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key invalide",
            headers={"WWW-Authenticate": "ApiKey"},
        )


async def require_jwt(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> JWTUser:
    """
    Vérifie le JWT Bearer (écriture).

    Retourne l'utilisateur authentifié.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header Authorization Bearer manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)


async def require_role(role: str):
    """
    Dépendance qui exige un rôle JWT spécifique.
    Usage : user: JWTUser = Depends(require_role("admin"))
    """
    async def _checker(user: JWTUser = Depends(require_jwt)) -> JWTUser:
        if user.role != role and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle '{role}' requis (rôle actuel : {user.role})",
            )
        return user

    return _checker
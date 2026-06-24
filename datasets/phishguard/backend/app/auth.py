"""
auth.py
=======
JWT issuance/verification, OTP generation, refresh-token hashing, and the
FastAPI dependency that resolves the current authenticated user.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app import models

bearer_scheme = HTTPBearer(auto_error=True)


# ----- OTP ------------------------------------------------------------------ #
def generate_otp() -> str:
    """Return a cryptographically-random 6-digit OTP as a zero-padded string."""
    return f"{secrets.randbelow(1_000_000):06d}"


# ----- Refresh-token hashing ------------------------------------------------ #
def hash_token(token: str) -> str:
    """SHA-256 hex digest. Refresh tokens are stored hashed, never in clear."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ----- JWT ------------------------------------------------------------------ #
def create_access_token(user_id: int, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: int, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "refresh",
        # jti makes each refresh token unique even if issued in the same second.
        "jti": secrets.token_hex(16),
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def issue_token_pair(db: Session, user: "models.User") -> tuple[str, str]:
    """Create an access+refresh pair and persist the HASHED refresh token."""
    access = create_access_token(user.id, user.email)
    refresh = create_refresh_token(user.id, user.email)

    db_token = models.RefreshToken(
        user_id=user.id,
        token=hash_token(refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False,
    )
    db.add(db_token)
    db.commit()
    return access, refresh


# ----- Current-user dependency ---------------------------------------------- #
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> "models.User":
    token = credentials.credentials
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong token type",
        )

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

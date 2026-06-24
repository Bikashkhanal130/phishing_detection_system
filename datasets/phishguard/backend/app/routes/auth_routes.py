"""
auth_routes.py
==============
OTP-based authentication (no passwords).

Endpoints:
    POST /api/auth/register/send-otp
    POST /api/auth/register/verify-otp
    POST /api/auth/login/send-otp
    POST /api/auth/login/verify-otp
    POST /api/auth/refresh
    POST /api/auth/logout
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import (
    bearer_scheme,
    decode_token,
    generate_otp,
    get_current_user,
    hash_token,
    issue_token_pair,
)
from app.config import settings
from app.database import get_db
from app.email_service import send_otp_email
from app.utils import now_utc, as_aware_utc
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter(prefix="/api/auth", tags=["auth"])


# --------------------------------------------------------------------------- #
# Shared OTP verification helper                                              #
# --------------------------------------------------------------------------- #
def _verify_otp_record(db: Session, email: str, otp: str, purpose: str) -> models.OtpCode:
    """
    Validate an OTP for the given email+purpose. Raises:
        404 if no OTP exists, 410 if expired, 429 if attempts exhausted,
        400 if the code is wrong (after incrementing the attempt counter).
    Returns the matching OtpCode record on success.
    """
    record = (
        db.query(models.OtpCode)
        .filter(models.OtpCode.email == email, models.OtpCode.purpose == purpose)
        .order_by(models.OtpCode.created_at.desc())
        .first()
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No OTP found. Please request a new code.")

    # Block first if attempts already exhausted.
    if record.attempts >= settings.OTP_MAX_ATTEMPTS:
        db.delete(record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many wrong attempts. Please request a new code.",
        )

    # Expiry check.
    if now_utc() > as_aware_utc(record.expires_at):
        db.delete(record)
        db.commit()
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Code expired, please resend.")

    # Wrong code -> increment attempts.
    if record.otp != otp:
        record.attempts += 1
        db.commit()
        remaining = settings.OTP_MAX_ATTEMPTS - record.attempts
        if remaining <= 0:
            db.delete(record)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many wrong attempts. Please request a new code.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid code. {remaining} attempt(s) remaining.",
        )

    return record


# --------------------------------------------------------------------------- #
# Register                                                                    #
# --------------------------------------------------------------------------- #
@router.post("/register/send-otp", response_model=schemas.MessageResponse)
async def register_send_otp(body: schemas.RegisterSendOtpRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # Clear any stale register OTPs for this email.
    db.query(models.OtpCode).filter(
        models.OtpCode.email == body.email, models.OtpCode.purpose == "register"
    ).delete()

    otp = generate_otp()
    record = models.OtpCode(
        email=body.email,
        otp=otp,
        purpose="register",
        name=body.name,
        expires_at=models.OtpCode.default_expiry(),
        attempts=0,
    )
    db.add(record)
    db.commit()

    await send_otp_email(body.email, otp, "register")
    return {"message": "OTP sent to email"}


@router.post("/register/verify-otp", response_model=schemas.TokenResponse)
async def register_verify_otp(body: schemas.VerifyOtpRequest, db: Session = Depends(get_db)):
    record = _verify_otp_record(db, body.email, body.otp, "register")

    # Create the user (idempotent guard in case of race).
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if user is None:
        user = models.User(
            email=body.email,
            name=record.name,
            is_verified=True,
            is_active=True,
        )
        db.add(user)
        db.flush()  # assign id
    else:
        user.is_verified = True
        if record.name and not user.name:
            user.name = record.name

    # Consume the OTP.
    db.delete(record)
    db.commit()
    db.refresh(user)

    access, refresh = issue_token_pair(db, user)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "user": schemas.UserDto.model_validate(user),
    }


# --------------------------------------------------------------------------- #
# Login                                                                       #
# --------------------------------------------------------------------------- #
@router.post("/login/send-otp", response_model=schemas.MessageResponse)
async def login_send_otp(body: schemas.LoginSendOtpRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

    # Delete any existing OTP for this email (any purpose).
    db.query(models.OtpCode).filter(models.OtpCode.email == body.email).delete()

    otp = generate_otp()
    record = models.OtpCode(
        email=body.email,
        otp=otp,
        purpose="login",
        expires_at=models.OtpCode.default_expiry(),
        attempts=0,
    )
    db.add(record)
    db.commit()

    await send_otp_email(body.email, otp, "login")
    return {"message": "OTP sent to email"}


@router.post("/login/verify-otp", response_model=schemas.TokenResponse)
async def login_verify_otp(body: schemas.VerifyOtpRequest, db: Session = Depends(get_db)):
    record = _verify_otp_record(db, body.email, body.otp, "login")

    user = db.query(models.User).filter(models.User.email == body.email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

    user.last_login_at = now_utc()
    db.delete(record)
    db.commit()
    db.refresh(user)

    access, refresh = issue_token_pair(db, user)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "user": schemas.UserDto.model_validate(user),
    }


# --------------------------------------------------------------------------- #
# Refresh                                                                     #
# --------------------------------------------------------------------------- #
@router.post("/refresh", response_model=schemas.AccessTokenResponse)
def refresh_token(body: schemas.RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")

    token_hash = hash_token(body.refresh_token)
    db_token = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.token == token_hash)
        .first()
    )
    if db_token is None or db_token.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")
    if now_utc() > as_aware_utc(db_token.expires_at):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    user = db.query(models.User).filter(models.User.id == db_token.user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    from app.auth import create_access_token

    new_access = create_access_token(user.id, user.email)
    return {"access_token": new_access}


# --------------------------------------------------------------------------- #
# Logout                                                                      #
# --------------------------------------------------------------------------- #
@router.post("/logout", response_model=schemas.MessageResponse)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Revoke all active refresh tokens for this user.
    db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == current_user.id,
        models.RefreshToken.revoked == False,  # noqa: E712
    ).update({"revoked": True})
    db.commit()
    return {"message": "Logged out"}

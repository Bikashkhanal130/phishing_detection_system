"""
models.py
=========
SQLAlchemy ORM models for the 4 tables:
    users, otp_codes, scan_history, refresh_tokens
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base
from app.config import settings


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    scans = relationship("ScanHistory", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class OtpCode(Base):
    __tablename__ = "otp_codes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, index=True)
    otp = Column(String(6), nullable=False)
    purpose = Column(String(20), nullable=False)  # 'register' | 'login'
    # Carries the name supplied at register/send-otp through to verify-otp.
    name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempts = Column(Integer, default=0, nullable=False)

    @staticmethod
    def default_expiry() -> datetime:
        return datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)


class ScanHistory(Base):
    __tablename__ = "scan_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(Text, nullable=False)
    is_phishing = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=False)
    domain = Column(String(255), nullable=True)
    scanned_at = Column(DateTime(timezone=True), server_default=func.now())
    features_json = Column(JSONB, nullable=True)

    user = relationship("User", back_populates="scans")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Stored HASHED (sha256 hex), never the raw token.
    token = Column(String(512), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")

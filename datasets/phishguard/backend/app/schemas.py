"""
schemas.py
==========
Pydantic request/response models.
"""

from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, EmailStr, Field


# ----- Auth requests -------------------------------------------------------- #
class RegisterSendOtpRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr


class LoginSendOtpRequest(BaseModel):
    email: EmailStr


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class RefreshRequest(BaseModel):
    refresh_token: str


# ----- Auth responses ------------------------------------------------------- #
class UserDto(BaseModel):
    id: int
    name: Optional[str] = None
    email: EmailStr

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserDto


class AccessTokenResponse(BaseModel):
    access_token: str


# ----- Scans ---------------------------------------------------------------- #
class ScanCreateRequest(BaseModel):
    url: str
    is_phishing: bool
    confidence: float
    domain: Optional[str] = None
    features_json: Optional[Any] = None


class ScanResponse(BaseModel):
    id: int
    url: str
    is_phishing: bool
    confidence: float
    domain: Optional[str] = None
    scanned_at: datetime

    class Config:
        from_attributes = True


class ScanHistoryPage(BaseModel):
    page: int
    limit: int
    total: int
    items: List[ScanResponse]


# ----- Profile -------------------------------------------------------------- #
class ProfileResponse(BaseModel):
    id: int
    name: Optional[str] = None
    email: EmailStr
    created_at: Optional[datetime] = None
    total_scans: int
    phishing_count: int
    safe_count: int

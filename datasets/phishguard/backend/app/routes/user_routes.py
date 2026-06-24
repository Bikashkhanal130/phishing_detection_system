"""
user_routes.py
==============
    GET /api/users/profile  (Bearer JWT)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/profile", response_model=schemas.ProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    scans = db.query(models.ScanHistory).filter(models.ScanHistory.user_id == user.id)
    total = scans.count()
    phishing = scans.filter(models.ScanHistory.is_phishing == True).count()  # noqa: E712
    safe = total - phishing

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "created_at": user.created_at,
        "total_scans": total,
        "phishing_count": phishing,
        "safe_count": safe,
    }

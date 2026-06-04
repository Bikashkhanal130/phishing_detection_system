"""
database.py
-----------
PostgreSQL tables defined with SQLAlchemy:
  - User           : accounts (email, hashed password, profile, verified flag)
  - OtpCode        : one-time codes sent to email
  - SearchHistory  : every URL a user has checked + the result
"""

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)

    # profile details
    phone = db.Column(db.String(30))
    bio = db.Column(db.Text)
    profile_image = db.Column(db.String(255))   # filename of uploaded picture

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    history = db.relationship("SearchHistory", backref="user", lazy=True,
                              cascade="all, delete-orphan")

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "is_verified": self.is_verified,
            "phone": self.phone,
            "bio": self.bio,
            "profile_image": self.profile_image,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class OtpCode(db.Model):
    __tablename__ = "otp_codes"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    code = db.Column(db.String(10), nullable=False)
    purpose = db.Column(db.String(30), default="verify_email")  # or "reset_password"
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self, code):
        return (
            not self.used
            and self.code == str(code).strip()
            and datetime.utcnow() < self.expires_at
        )


class SearchHistory(db.Model):
    __tablename__ = "search_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    url = db.Column(db.Text, nullable=False)
    result = db.Column(db.String(20), nullable=False)        # "Phishing" or "Safe"
    confidence = db.Column(db.Float, nullable=False)          # 0..100 (%)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "result": self.result,
            "confidence": round(self.confidence, 2),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

"""
config.py
---------
All settings are read from environment variables so you never hard-code secrets.
Copy .env.example to .env and fill in your values, OR export them in your shell.
"""

import os


class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-in-production")

    # ---- Database ----
    # Reads DATABASE_URL from the environment (set automatically by Render).
    # Hosts like Render/Heroku give a URL starting with "postgres://", but
    # SQLAlchemy needs "postgresql://", so we fix the scheme here.
    _db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/phishingdb",
    )
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- Email / OTP (uses your existing mail provider's SMTP, no new server) ----
    # For Gmail: create an "App Password" (Google Account -> Security -> App passwords)
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))          # 465 = SSL
    SMTP_USER = os.environ.get("SMTP_USER", "khanalbk18@gmail.com")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "afda yetk zzpv rcoq")
    SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", "Phishing Detecting System")

    # OTP behaviour
    OTP_LENGTH = 6
    OTP_TTL_MINUTES = 10

    # JWT
    JWT_EXP_HOURS = 24

    # File uploads (profile pictures)
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024   # 5 MB
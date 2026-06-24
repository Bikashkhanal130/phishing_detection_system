"""
config.py
---------
Central settings. Values are read from environment variables when present,
otherwise the defaults below are used (handy for local testing).
"""

import os

from dotenv import load_dotenv
load_dotenv()   # loads backend/.env into os.environ if present


class Config:
    # ---- Flask ----
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-in-production")

    # ---- Database (PostgreSQL via pgAdmin) ----
    # Your settings: user=postgres, password=Srinidhi@3210, host=localhost, db=phishingdb
    #
    # NOTE: the "@" in the password is written as "%40" in the URL, because "@"
    # is the character that separates the password from the host. Other specials:
    #     @ -> %40    : -> %3A    / -> %2F    # -> %23    space -> %20
    # SQLAlchemy turns "%40" back into "@" automatically when it connects.
    _db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:Srinidhi%403210@localhost:5432/phishingdb",
    )
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- Email / OTP ----
    # To SEND REAL EMAILS, replace the two values marked below with your Gmail
    # address and your 16-character Gmail "App Password".
    #   App password: Google Account -> Security -> 2-Step Verification -> App passwords
    # (If you leave the placeholders, the code is printed in the terminal instead.)
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))            # 465 = SSL
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "").replace(" ", "")
    SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", "Phishing Detecting System")

    # ---- OTP behaviour ----
    OTP_LENGTH = 6
    OTP_TTL_MINUTES = 10

    # ---- JWT ----
    JWT_EXP_HOURS = 24

    # ---- File uploads (profile pictures) ----
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024   # 5 MB
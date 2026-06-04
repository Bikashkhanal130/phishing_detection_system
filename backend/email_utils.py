"""
email_utils.py
--------------
Sends the OTP code by email using plain SMTP.

DEV CONVENIENCE:
If DEV_MODE is on, OR if you haven't filled in real SMTP credentials yet,
the code is PRINTED IN THE TERMINAL instead of emailed. That lets you register
and log in immediately without setting up Gmail. When you later put real SMTP
details in your .env (and DEV_MODE is off), it sends a real email automatically.

No separate server is ever created -- when it does send, it just connects to your
mail provider's existing SMTP server, like any email client.
"""

import os
import random
import smtplib
import ssl
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import Config


def generate_otp(length: int = None) -> str:
    length = length or Config.OTP_LENGTH
    return "".join(random.choices("0123456789", k=length))


def otp_expiry() -> datetime:
    return datetime.utcnow() + timedelta(minutes=Config.OTP_TTL_MINUTES)


def _dev_mode() -> bool:
    return os.environ.get("DEV_MODE", "").strip().lower() in ("1", "true", "yes", "on")


def _smtp_is_configured() -> bool:
    """True only if real SMTP values were provided (not the placeholders)."""
    user = (Config.SMTP_USER or "").strip()
    pwd = (Config.SMTP_PASSWORD or "").strip()
    placeholders = {"", "youremail@gmail.com", "your-app-password", "your-16-char-app-password"}
    return user not in placeholders and pwd not in placeholders and "@" in user


def _print_code_to_console(to_email: str, code: str) -> None:
    line = "=" * 52
    print("\n" + line)
    print(f"  DEV MODE -- verification code for {to_email}")
    print(f"  CODE: {code}")
    print(f"  (No email sent. Type this code into the app to verify.)")
    print(line + "\n", flush=True)


def send_otp_email(to_email: str, code: str) -> None:
    """Send the verification code, or print it to the console in dev mode.

    Never raises in dev / unconfigured mode, so registration always succeeds
    while you are testing locally.
    """
    if _dev_mode() or not _smtp_is_configured():
        _print_code_to_console(to_email, code)
        return

    subject = "Your verification code"
    text = (
        f"Your Phishing Detector verification code is: {code}\n\n"
        f"This code expires in {Config.OTP_TTL_MINUTES} minutes.\n"
        f"If you did not request this, please ignore this email."
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:420px;margin:auto;
                border:1px solid #eee;border-radius:12px;padding:24px">
      <h2 style="color:#1f6feb;margin-top:0">Verify your email</h2>
      <p>Use this code to finish setting up your account:</p>
      <p style="font-size:32px;font-weight:bold;letter-spacing:6px;
                color:#111;background:#f4f6fb;padding:14px;border-radius:8px;
                text-align:center">{code}</p>
      <p style="color:#666">This code expires in {Config.OTP_TTL_MINUTES} minutes.</p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{Config.SMTP_FROM_NAME} <{Config.SMTP_USER}>"
    msg["To"] = to_email
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()
    if Config.SMTP_PORT == 465:
        with smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT, context=context) as server:
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            server.sendmail(Config.SMTP_USER, to_email, msg.as_string())
    else:  # e.g. port 587 (STARTTLS)
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            server.sendmail(Config.SMTP_USER, to_email, msg.as_string())
"""
email_utils.py
--------------
Sends the OTP code by email using your mail provider's SMTP server.

Behaviour:
  * If you have filled in a real Gmail + App Password in config.py (or set the
    SMTP_USER / SMTP_PASSWORD env vars), a REAL EMAIL is sent.
  * If the placeholders are still there (or DEV_MODE=1), the code is printed in
    the terminal instead, so testing never gets blocked.

No separate server is created -- it just connects to Gmail's existing SMTP
server (smtp.gmail.com) the same way an email client does.
"""

import os
import random
import smtplib
import ssl
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import Config

# Values that mean "not configured yet" -> fall back to printing in terminal.
_PLACEHOLDERS = {
    "",
    "youremail@gmail.com",
    "your-app-password",
    "your-16-char-app-password",
    "your-gmail@gmail.com",
    "REPLACE_WITH_YOUR_GMAIL@gmail.com",
    "REPLACE_WITH_YOUR_APP_PASSWORD",
}


def generate_otp(length: int = None) -> str:
    length = length or Config.OTP_LENGTH
    return "".join(random.choices("0123456789", k=length))


def otp_expiry() -> datetime:
    return datetime.utcnow() + timedelta(minutes=Config.OTP_TTL_MINUTES)


def _dev_mode() -> bool:
    return os.environ.get("DEV_MODE", "").strip().lower() in ("1", "true", "yes", "on")


def _smtp_is_configured() -> bool:
    user = (Config.SMTP_USER or "").strip()
    pwd = (Config.SMTP_PASSWORD or "").strip()
    return user not in _PLACEHOLDERS and pwd not in _PLACEHOLDERS and "@" in user


def _print_code_to_console(to_email: str, code: str) -> None:
    line = "=" * 52
    print("\n" + line)
    print(f"  OTP for {to_email}: {code}")
    print("  (Email not configured / DEV_MODE on -- type this code into the app.)")
    print(line + "\n", flush=True)


def send_otp_email(to_email: str, code: str, purpose: str = "verify_email") -> None:
    """Send the OTP code, or print it to the console if email isn't set up.
    purpose: "verify_email" (default) or "reset_password" -- only changes wording."""
    if _dev_mode() or not _smtp_is_configured():
        _print_code_to_console(to_email, code)
        return

    is_reset = purpose == "reset_password"
    subject = "Your password reset code" if is_reset else "Your verification code"
    heading = "Reset your password" if is_reset else "Verify your email"
    intro = (
        "Use this code to reset your password:" if is_reset
        else "Use this code to finish setting up your account:"
    )
    text = (
        f"Your {Config.SMTP_FROM_NAME} {'password reset' if is_reset else 'verification'} "
        f"code is: {code}\n\n"
        f"This code expires in {Config.OTP_TTL_MINUTES} minutes.\n"
        f"If you did not request this, please ignore this email."
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:420px;margin:auto;
                border:1px solid #eee;border-radius:12px;padding:24px">
      <h2 style="color:#1f6feb;margin-top:0">{heading}</h2>
      <p>{intro}</p>
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
    if Config.SMTP_PORT == 465:                       # SSL
        with smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT, context=context) as server:
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            server.sendmail(Config.SMTP_USER, to_email, msg.as_string())
    else:                                             # STARTTLS (e.g. port 587)
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            server.sendmail(Config.SMTP_USER, to_email, msg.as_string())
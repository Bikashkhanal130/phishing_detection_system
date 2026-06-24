"""
email_service.py
================
OTP email delivery via fastapi-mail (Gmail SMTP in dev).

If MAIL_SUPPRESS_SEND is True (default in dev), OTPs are printed to the console
instead of being emailed, so the whole flow is testable without SMTP set up.
"""

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.config import settings

_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME or "dev@example.com",
    MAIL_PASSWORD=settings.MAIL_PASSWORD or "unused",
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    SUPPRESS_SEND=1 if settings.MAIL_SUPPRESS_SEND else 0,
)

_fastmail = FastMail(_conf)


def _build_body(otp: str, purpose: str) -> str:
    action = "registration" if purpose == "register" else "login"
    return (
        f"<div style='font-family:Arial,sans-serif'>"
        f"<h2>PhishGuard</h2>"
        f"<p>Your PhishGuard {action} code is:</p>"
        f"<p style='font-size:28px;font-weight:bold;letter-spacing:6px'>{otp}</p>"
        f"<p>This code expires in {settings.OTP_EXPIRE_MINUTES} minutes. "
        f"If you didn't request it, you can ignore this email.</p>"
        f"</div>"
    )


async def send_otp_email(email: str, otp: str, purpose: str) -> None:
    """
    Send the OTP email. In suppressed/dev mode, prints to console so testing
    works without real SMTP credentials.
    """
    action = "registration" if purpose == "register" else "login"
    subject = f"Your PhishGuard {action} code"

    if settings.MAIL_SUPPRESS_SEND:
        print(f"[DEV OTP] purpose={purpose} email={email} otp={otp}")
        return

    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=_build_body(otp, purpose),
        subtype=MessageType.html,
    )
    await _fastmail.send_message(message)

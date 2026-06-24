"""
test_integration.py
====================
End-to-end backend smoke test against the live PostgreSQL DB using FastAPI's
TestClient. Exercises every endpoint and the OTP attempts/expiry rules.

Run:  python test_integration.py
Requires MAIL_SUPPRESS_SEND=True so OTPs are readable from the DB.
"""

import sys
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app import models

client = TestClient(app)

EMAIL = "tester@example.com"
NAME = "Test User"


def get_latest_otp(email: str, purpose: str) -> str:
    db = SessionLocal()
    try:
        rec = (
            db.query(models.OtpCode)
            .filter(models.OtpCode.email == email, models.OtpCode.purpose == purpose)
            .order_by(models.OtpCode.created_at.desc())
            .first()
        )
        return rec.otp if rec else None
    finally:
        db.close()


def cleanup():
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == EMAIL).first()
        if user:
            db.query(models.ScanHistory).filter(models.ScanHistory.user_id == user.id).delete()
            db.query(models.RefreshToken).filter(models.RefreshToken.user_id == user.id).delete()
            db.delete(user)
        db.query(models.OtpCode).filter(models.OtpCode.email == EMAIL).delete()
        db.commit()
    finally:
        db.close()


def check(cond, msg):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {msg}")
    if not cond:
        raise SystemExit(f"Test failed: {msg}")


def main():
    cleanup()
    print("== 1. Health ==")
    r = client.get("/health")
    check(r.status_code == 200 and r.json()["status"] == "healthy", "health endpoint")

    print("== 2. Register: send-otp ==")
    r = client.post("/api/auth/register/send-otp", json={"name": NAME, "email": EMAIL})
    check(r.status_code == 200, f"register send-otp -> 200 (got {r.status_code})")

    print("== 3. Register: wrong OTP increments attempts ==")
    r = client.post("/api/auth/register/verify-otp", json={"email": EMAIL, "otp": "000000"})
    check(r.status_code == 400, f"wrong otp -> 400 (got {r.status_code}, {r.text[:80]})")

    print("== 4. Register: correct OTP ==")
    otp = get_latest_otp(EMAIL, "register")
    r = client.post("/api/auth/register/verify-otp", json={"email": EMAIL, "otp": otp})
    check(r.status_code == 200, f"register verify -> 200 (got {r.status_code}, {r.text[:120]})")
    data = r.json()
    check("access_token" in data and "refresh_token" in data, "tokens issued on register")
    check(data["user"]["email"] == EMAIL and data["user"]["name"] == NAME, "user dto correct")
    access = data["access_token"]
    refresh = data["refresh_token"]

    print("== 5. Duplicate register blocked ==")
    r = client.post("/api/auth/register/send-otp", json={"name": NAME, "email": EMAIL})
    check(r.status_code == 409, f"duplicate register -> 409 (got {r.status_code})")

    print("== 6. Login: send-otp + verify ==")
    r = client.post("/api/auth/login/send-otp", json={"email": EMAIL})
    check(r.status_code == 200, f"login send-otp -> 200 (got {r.status_code})")
    otp = get_latest_otp(EMAIL, "login")
    r = client.post("/api/auth/login/verify-otp", json={"email": EMAIL, "otp": otp})
    check(r.status_code == 200, f"login verify -> 200 (got {r.status_code})")
    access = r.json()["access_token"]
    refresh = r.json()["refresh_token"]

    print("== 7. Login unknown email -> 404 ==")
    r = client.post("/api/auth/login/send-otp", json={"email": "nobody@example.com"})
    check(r.status_code == 404, f"unknown login -> 404 (got {r.status_code})")

    auth = {"Authorization": f"Bearer {access}"}

    print("== 8. Protected route without token -> 403/401 ==")
    r = client.get("/api/users/profile")
    check(r.status_code in (401, 403), f"no token blocked (got {r.status_code})")

    print("== 9. Create scans ==")
    scans = [
        {"url": "https://www.google.com", "is_phishing": False, "confidence": 0.98, "domain": "www.google.com"},
        {"url": "http://paypal-verify-account.xyz/login", "is_phishing": True, "confidence": 0.95, "domain": "paypal-verify-account.xyz"},
        {"url": "http://192.168.1.1/bank-login", "is_phishing": True, "confidence": 0.91, "domain": "192.168.1.1"},
    ]
    scan_ids = []
    for s in scans:
        r = client.post("/api/scans", json=s, headers=auth)
        check(r.status_code == 201, f"create scan -> 201 (got {r.status_code}, {r.text[:80]})")
        scan_ids.append(r.json()["id"])

    print("== 10. History pagination ==")
    r = client.get("/api/scans/history?page=1&limit=20", headers=auth)
    check(r.status_code == 200, "history -> 200")
    body = r.json()
    check(body["total"] == 3 and len(body["items"]) == 3, f"history has 3 items (got {body['total']})")
    # Ordered desc by scanned_at -> most recent (192.168) first.
    check(body["items"][0]["url"] == scans[-1]["url"], "history ordered desc")

    print("== 11. Profile counts ==")
    r = client.get("/api/users/profile", headers=auth)
    check(r.status_code == 200, "profile -> 200")
    p = r.json()
    check(p["total_scans"] == 3 and p["phishing_count"] == 2 and p["safe_count"] == 1,
          f"profile counts (total={p['total_scans']}, phish={p['phishing_count']}, safe={p['safe_count']})")

    print("== 12. PDF export ==")
    r = client.get("/api/scans/export", headers=auth)
    check(r.status_code == 200, "export -> 200")
    check(r.headers["content-type"] == "application/pdf", "export is application/pdf")
    check(r.content[:4] == b"%PDF", "export body is a PDF (magic bytes)")
    check("scan_history_Test_User.pdf" in r.headers.get("content-disposition", ""), "pdf filename")

    print("== 13. Delete scan (owned) ==")
    r = client.delete(f"/api/scans/{scan_ids[0]}", headers=auth)
    check(r.status_code == 200, f"delete -> 200 (got {r.status_code})")
    r = client.delete(f"/api/scans/{scan_ids[0]}", headers=auth)
    check(r.status_code == 404, "deleting again -> 404")

    print("== 14. Refresh token ==")
    r = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    check(r.status_code == 200 and "access_token" in r.json(), f"refresh -> 200 (got {r.status_code})")

    print("== 15. Logout revokes refresh ==")
    r = client.post("/api/auth/logout", headers=auth)
    check(r.status_code == 200, "logout -> 200")
    r = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    check(r.status_code == 401, f"refresh after logout -> 401 (got {r.status_code})")

    print("== 16. OTP lockout after 3 wrong attempts ==")
    client.post("/api/auth/login/send-otp", json={"email": EMAIL})
    codes = []
    for i in range(3):
        rr = client.post("/api/auth/login/verify-otp", json={"email": EMAIL, "otp": "111111"})
        codes.append(rr.status_code)
    check(codes[-1] == 429, f"3rd wrong attempt -> 429 (got {codes})")

    cleanup()
    print("\nALL BACKEND INTEGRATION TESTS PASSED")


if __name__ == "__main__":
    main()

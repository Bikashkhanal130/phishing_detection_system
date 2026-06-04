"""
app.py
------
The Flask REST API the Android app talks to.

Endpoints (all JSON unless noted):
  POST /api/register          -> create account (unverified) + email an OTP
  POST /api/verify-otp        -> verify email with the code
  POST /api/resend-otp        -> send a fresh code
  POST /api/login             -> returns a JWT token
  GET  /api/profile           -> current user's profile          (auth)
  PUT  /api/profile           -> update name/phone/bio            (auth)
  POST /api/profile/image     -> upload profile picture (multipart)(auth)
  GET  /uploads/<file>        -> serve a profile picture
  POST /api/predict           -> check a URL, save to history     (auth)
  GET  /api/history           -> list this user's checks          (auth)
  GET  /api/history/pdf       -> download history as PDF          (auth)

Run:
  python app.py            (dev)
  gunicorn -w 4 app:app    (production)
"""

import os
import uuid
from datetime import datetime, timedelta
from functools import wraps

import jwt
import joblib
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import Config
from database import OtpCode, SearchHistory, User, db
from email_utils import generate_otp, otp_expiry, send_otp_email
from feature_extraction import vectorize
from pdf_utils import build_history_pdf

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
db.init_app(app)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Create tables on startup. This runs both under `python app.py` AND under
# gunicorn (production), because gunicorn imports this module but never runs
# the __main__ block below.
with app.app_context():
    db.create_all()

# ---- Load the trained model once at startup ----
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "phishing_model.joblib")
_bundle = None
if os.path.exists(MODEL_PATH):
    _bundle = joblib.load(MODEL_PATH)
    print(f"Loaded model (test accuracy {_bundle.get('accuracy', 0)*100:.2f}%)")
else:
    print("WARNING: model not found. Run `python train_model.py` first.")


# ----------------------------- auth helpers -----------------------------
def make_token(user):
    payload = {
        "uid": user.id,
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(hours=app.config["JWT_EXP_HOURS"]),
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")


def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth.split(" ", 1)[1]
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired, please log in again"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        user = User.query.get(data["uid"])
        if not user:
            return jsonify({"error": "User not found"}), 401
        return f(user, *args, **kwargs)
    return wrapper


# ----------------------------- auth endpoints -----------------------------
@app.post("/api/register")
def register():
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or len(password) < 6:
        return jsonify({"error": "Name, email and a 6+ char password are required"}), 400

    existing = User.query.filter_by(email=email).first()
    if existing and existing.is_verified:
        return jsonify({"error": "An account with this email already exists"}), 409

    if existing:                      # unverified -> overwrite details
        user = existing
        user.full_name = name
        user.set_password(password)
    else:
        user = User(full_name=name, email=email)
        user.set_password(password)
        db.session.add(user)

    code = generate_otp()
    db.session.add(OtpCode(email=email, code=code, expires_at=otp_expiry()))
    db.session.commit()

    try:
        send_otp_email(email, code)
    except Exception as e:
        return jsonify({"error": f"Account saved but email failed: {e}"}), 502

    return jsonify({"message": "Registered. Check your email for the code.",
                    "email": email}), 201


@app.post("/api/verify-otp")
def verify_otp():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    code = (data.get("code") or "").strip()

    otp = (OtpCode.query.filter_by(email=email, purpose="verify_email", used=False)
           .order_by(OtpCode.created_at.desc()).first())
    if not otp or not otp.is_valid(code):
        return jsonify({"error": "Invalid or expired code"}), 400

    otp.used = True
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    user.is_verified = True
    db.session.commit()

    return jsonify({"message": "Email verified", "token": make_token(user),
                    "user": user.to_dict()})


@app.post("/api/resend-otp")
def resend_otp():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not User.query.filter_by(email=email).first():
        return jsonify({"error": "No account for this email"}), 404
    code = generate_otp()
    db.session.add(OtpCode(email=email, code=code, expires_at=otp_expiry()))
    db.session.commit()
    try:
        send_otp_email(email, code)
    except Exception as e:
        return jsonify({"error": f"Email failed: {e}"}), 502
    return jsonify({"message": "A new code was sent"})


@app.post("/api/login")
def login():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Wrong email or password"}), 401
    if not user.is_verified:
        # Re-issue a code so they can finish verifying
        code = generate_otp()
        db.session.add(OtpCode(email=email, code=code, expires_at=otp_expiry()))
        db.session.commit()
        try:
            send_otp_email(email, code)
        except Exception:
            pass
        return jsonify({"error": "Email not verified", "need_verification": True,
                        "email": email}), 403

    return jsonify({"message": "Logged in", "token": make_token(user),
                    "user": user.to_dict()})


# ----------------------------- profile -----------------------------
@app.get("/api/profile")
@token_required
def get_profile(user):
    return jsonify({"user": user.to_dict()})


@app.put("/api/profile")
@token_required
def update_profile(user):
    data = request.get_json(force=True, silent=True) or {}
    if "full_name" in data:
        user.full_name = data["full_name"].strip()
    if "phone" in data:
        user.phone = data["phone"].strip()
    if "bio" in data:
        user.bio = data["bio"].strip()
    db.session.commit()
    return jsonify({"message": "Profile updated", "user": user.to_dict()})


@app.post("/api/profile/image")
@token_required
def upload_image(user):
    if "image" not in request.files:
        return jsonify({"error": "No image file"}), 400
    file = request.files["image"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400
    ext = os.path.splitext(secure_filename(file.filename))[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp"):
        return jsonify({"error": "Only png/jpg/jpeg/webp allowed"}), 400
    fname = f"{user.id}_{uuid.uuid4().hex}{ext}"
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], fname))
    user.profile_image = fname
    db.session.commit()
    return jsonify({"message": "Image uploaded", "profile_image": fname})


@app.get("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ----------------------------- prediction -----------------------------
@app.post("/api/predict")
@token_required
def predict(user):
    if _bundle is None:
        return jsonify({"error": "Model not loaded. Train it first."}), 503
    data = request.get_json(force=True, silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "Provide a 'url'"}), 400

    model = _bundle["model"]
    features = [vectorize(url)]
    pred = int(model.predict(features)[0])             # 1 = phishing, 0 = safe
    proba = model.predict_proba(features)[0]
    confidence = float(proba[pred]) * 100.0
    result = "Phishing" if pred == 1 else "Safe"

    record = SearchHistory(user_id=user.id, url=url, result=result, confidence=confidence)
    db.session.add(record)
    db.session.commit()

    return jsonify({
        "url": url,
        "result": result,
        "is_phishing": bool(pred),
        "confidence": round(confidence, 2),
        "checked_at": record.created_at.isoformat(),
    })


# ----------------------------- history -----------------------------
@app.get("/api/history")
@token_required
def history(user):
    items = (SearchHistory.query.filter_by(user_id=user.id)
             .order_by(SearchHistory.created_at.desc()).all())
    return jsonify({"history": [h.to_dict() for h in items], "count": len(items)})


@app.get("/api/history/pdf")
@token_required
def history_pdf(user):
    items = (SearchHistory.query.filter_by(user_id=user.id)
             .order_by(SearchHistory.created_at.desc()).all())
    pdf_bytes = build_history_pdf(user, items)
    import io
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"search_history_{user.id}.pdf",
    )


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "model_loaded": _bundle is not None})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()       # creates the PostgreSQL tables on first run
    # host=0.0.0.0 so your phone on the same Wi-Fi can reach it
    app.run(host="0.0.0.0", port=5000, debug=True)
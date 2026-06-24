"""
run.py  --  PRODUCTION-READY DEVELOPMENT SERVER
================================================

Start the backend with a single command:

    python run.py

What this does:
  * Loads your .env file first (SMTP credentials, database URL, secret key).
  * Trains the ML model on first run if not already trained.
  * Creates / migrates all database tables automatically.
  * Starts Flask on 0.0.0.0:5000 (reachable via ngrok or local network).

OTP delivery:
  * If SMTP_USER and SMTP_PASSWORD are set in .env  -> OTP is EMAILED.
  * If SMTP is not configured                        -> OTP is printed here.

------------------------------------------------------------------------------
HOW TO REGISTER + LOG IN (full flow):
  1. Run:  python run.py          (keep this terminal open)
  2. In the Android app, tap "Create a new account" and submit the form.
  3. Check your email inbox for the 6-digit code.
  4. Type that code into the app's verify screen. You're now logged in.
  5. Next login: just use email + password -- no code needed.
------------------------------------------------------------------------------
"""

import atexit
import os
import shutil
import sys
import subprocess
import time
import urllib.request
import json

# Determine absolute path of this file's directory
HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ #
# ngrok auto-start                                                     #
# ------------------------------------------------------------------ #
NGROK_DOMAIN = os.environ.get("NGROK_DOMAIN", "unrepulsed-diedre-nonfrenetic.ngrok-free.dev")

def _start_ngrok():
    """Start ngrok in the background if not already running. Returns public URL."""
    # Check if ngrok is available
    if not shutil.which("ngrok"):
        print("(ngrok not found in PATH -- skipping tunnel)")
        return None

    # Check if a tunnel is already up
    try:
        with urllib.request.urlopen("http://localhost:4040/api/tunnels", timeout=2) as r:
            data = json.loads(r.read())
            tunnels = data.get("tunnels", [])
            if tunnels:
                url = tunnels[0]["public_url"]
                print(f"(ngrok already running: {url})")
                return url
    except Exception:
        pass  # not running yet -- start it

    proc = subprocess.Popen(
        ["ngrok", "http", f"--domain={NGROK_DOMAIN}", "5000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    atexit.register(proc.terminate)

    # Wait up to 5 s for the tunnel to come up
    for _ in range(10):
        time.sleep(0.5)
        try:
            with urllib.request.urlopen("http://localhost:4040/api/tunnels", timeout=1) as r:
                data = json.loads(r.read())
                tunnels = data.get("tunnels", [])
                if tunnels:
                    return tunnels[0]["public_url"]
        except Exception:
            continue

    print("(ngrok started but tunnel URL not confirmed yet)")
    return f"https://{NGROK_DOMAIN}"

# ------------------------------------------------------------------ #
# 1. Load .env FIRST so its values (SMTP, DATABASE_URL, etc.) are    #
#    picked up before we set any fallback defaults.                   #
# ------------------------------------------------------------------ #
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(HERE, ".env"), override=False)
except ImportError:
    pass  # python-dotenv not installed; rely on OS environment variables

# ------------------------------------------------------------------ #
# 2. Set fallback defaults ONLY when the .env did not supply a value. #
#    NOTE: DEV_MODE is intentionally NOT forced here.  If your .env   #
#    has valid SMTP credentials, real emails will be sent.            #
# ------------------------------------------------------------------ #
# Absolute SQLite path as fallback (avoids CWD-dependent data loss)
_sqlite_path = os.path.join(HERE, "instance", "dev.db")
os.makedirs(os.path.join(HERE, "instance"), exist_ok=True)
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_sqlite_path}")
os.environ.setdefault("SECRET_KEY", "dev-secret-change-me")

# ------------------------------------------------------------------ #
# 3. Train ML model on first run if needed.                           #
# ------------------------------------------------------------------ #
MODEL_PATH = os.path.join(HERE, "model", "phishing_model.joblib")
if not os.path.exists(MODEL_PATH):
    print("No trained model found -- training on sample_dataset.csv ...")
    result = subprocess.run([sys.executable, os.path.join(HERE, "train_model.py")])
    if result.returncode != 0:
        print("(Training failed -- login/register still work; URL checking disabled.)")

# ------------------------------------------------------------------ #
# 4. Import app, ensure tables exist (including new columns), run.    #
# ------------------------------------------------------------------ #
from app import app, db  # noqa: E402  (must come after env setup)

with app.app_context():
    db.create_all()
    # Safety migration: add 'purpose' column to otp_codes if it was
    # created by an older schema that lacked it.
    try:
        from sqlalchemy import text
        db_url = os.environ.get("DATABASE_URL", "")
        if db_url.startswith("sqlite"):
            # SQLite: add column only if missing
            cols = [r[1] for r in db.session.execute(
                text("PRAGMA table_info(otp_codes)"))]
            if "purpose" not in cols:
                db.session.execute(
                    text("ALTER TABLE otp_codes ADD COLUMN purpose VARCHAR(30) DEFAULT 'verify_email'"))
                db.session.execute(
                    text("UPDATE otp_codes SET purpose='verify_email' WHERE purpose IS NULL"))
                db.session.commit()
                print("Migrated: added 'purpose' column to otp_codes.")
        else:
            # PostgreSQL: add column only if missing
            db.session.execute(text(
                "ALTER TABLE otp_codes ADD COLUMN IF NOT EXISTS purpose VARCHAR(30) DEFAULT 'verify_email'"))
            db.session.execute(text(
                "UPDATE otp_codes SET purpose='verify_email' WHERE purpose IS NULL"))
            db.session.commit()
    except Exception as _mig_err:
        db.session.rollback()
        print(f"(Migration note: {_mig_err})")

    print(f"Database ready  ->  {os.environ.get('DATABASE_URL', '')[:40]}...")

# ------------------------------------------------------------------ #
# 5. Start ngrok tunnel, then show startup banner.                    #
# ------------------------------------------------------------------ #
from email_utils import _smtp_is_configured, _dev_mode  # noqa: E402

ngrok_url = _start_ngrok()

print("\n" + "-" * 62)
print(" Server running on http://0.0.0.0:5000")
print("   Android emulator  -> BASE_URL = http://10.0.2.2:5000/")
if ngrok_url:
    print(f"   Real phone (ngrok)-> BASE_URL = {ngrok_url.rstrip('/')}/")
else:
    print("   Real phone        -> ngrok not available; use local IP")

if _smtp_is_configured() and not _dev_mode():
    from config import Config
    print(f" OTP will be EMAILED to users via {Config.SMTP_USER}")
else:
    print(" OTP will be printed IN THIS TERMINAL (SMTP not configured).")
print("-" * 62 + "\n")

# ------------------------------------------------------------------ #
# 6. Start Flask.                                                     #
# ------------------------------------------------------------------ #
# use_reloader=False avoids the double-startup that confuses logging.
app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

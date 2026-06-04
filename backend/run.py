"""
run.py  --  ONE-COMMAND DEVELOPMENT SERVER
==========================================

Start the whole backend with a single command:

    python run.py

This dev launcher removes the two setup hurdles so register + login work
immediately:

  * Database: uses a local SQLite file (dev.db) instead of PostgreSQL.
              Nothing to install. The file is created automatically.
  * Email OTP: the verification code is PRINTED IN THIS TERMINAL instead of
              emailed, so you don't need Gmail set up to test.

It also:
  * trains the model on sample_dataset.csv the first time (if none exists), and
  * creates all database tables automatically.

There is still only ONE server and ONE API. Register and login are just two
endpoints on it (/api/register and /api/login) -- you never run a second program.

------------------------------------------------------------------------------
HOW TO REGISTER + LOG IN (the full flow):
  1. Run:  python run.py        (leave this terminal open)
  2. In the Android app, tap "Create a new account" and submit.
  3. Look at THIS terminal -- the 6-digit code is printed here.
  4. Type that code into the app's verify screen. You're now logged in.
  5. Next time, just use Login with the same email + password.
------------------------------------------------------------------------------

When you are ready for the "real" setup (PostgreSQL + Gmail email), run
`python app.py` instead and use your .env file.
"""

import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))

# 1) Configure the environment BEFORE importing the app, so config.py picks it up.
os.environ.setdefault("DATABASE_URL", "sqlite:///dev.db")   # no PostgreSQL needed
os.environ.setdefault("DEV_MODE", "1")                       # print OTP to terminal
os.environ.setdefault("SECRET_KEY", "dev-secret-change-me")

MODEL_PATH = os.path.join(HERE, "model", "phishing_model.joblib")

# 2) Train a model the first time so /api/predict works too (not needed for login).
if not os.path.exists(MODEL_PATH):
    print("No trained model found -- training one on sample_dataset.csv ...")
    result = subprocess.run([sys.executable, os.path.join(HERE, "train_model.py")])
    if result.returncode != 0:
        print("(Training step failed -- login/register will still work; "
              "URL checking will be disabled until a model is trained.)")

# 3) Import the app, create the tables, and run.
from app import app, db   # noqa: E402  (import must come after env setup above)

with app.app_context():
    db.create_all()
    print("Database ready  ->  sqlite file: dev.db")

print("\n" + "-" * 60)
print(" Server running on http://0.0.0.0:5000")
print("   Android emulator  ->  BASE_URL = http://10.0.2.2:5000/")
print("   Real phone (Wi-Fi)->  BASE_URL = http://<your-PC-IP>:5000/")
print(" OTP codes will appear IN THIS TERMINAL.")
print("-" * 60 + "\n")

# use_reloader=False keeps the OTP prints in one place and avoids double startup
app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
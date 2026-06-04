# Phishing Detection System (Mobile App)

A complete phishing-link detector: a **Python/Flask + Random Forest** backend with
**PostgreSQL**, and a native **Android (Java)** app.

What it does:
- Register / login with a password
- Email **OTP** confirmation (sent over your existing mail provider's SMTP — no extra server)
- Profile with photo, phone, and bio
- Paste any link → model says **Phishing** or **Safe** with a confidence score
- Every check is saved to the user's history
- Download the full history as a **PDF**

```
phishing-detection-system/
├── backend/      Python: Flask API + Random Forest + PostgreSQL + PDF + email OTP
└── android/      Java: Android Studio project (the mobile UI)
```

---

## How the machine learning works

1. `feature_extraction.py` turns each URL into 22 numeric features (length, number of
   dots/hyphens, whether the host is an IP, https or not, suspicious words like
   "login/verify", whether it's a shortened link, digit-to-letter ratio, etc.).
   These are computed from the URL text only — no network calls — so prediction is
   instant on the phone.
2. `train_model.py` loads your dataset, extracts those features, splits the data
   **80% train / 20% test**, trains a `RandomForestClassifier`, prints the accuracy
   and confusion matrix on the held-out 20%, and saves the model.
3. `app.py` loads the saved model and exposes `POST /api/predict`.

The same feature function is used for training and prediction, which is what keeps
the model accurate.

---

## Backend setup

### 1. Install PostgreSQL and create the database
```bash
# after installing postgres
psql -U postgres -c "CREATE DATABASE phishingdb;"
```

### 2. Install Python dependencies
```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# edit .env: set DATABASE_URL, SMTP_USER, SMTP_PASSWORD, SECRET_KEY
```
For Gmail, turn on 2-Step Verification, then create an **App Password**
(Google Account → Security → App passwords) and put that 16-character password
in `SMTP_PASSWORD`. This is what lets Flask send the OTP email directly — no third
party and no separate OTP server.

Load the variables before running:
```bash
set -a; source .env; set +a        # Linux / Mac
```

### 4. Train the model
Use your own dataset (CSV with columns `url,label`):
```bash
python train_model.py --data path/to/your_dataset.csv
```
Or just try the bundled sample first:
```bash
python train_model.py
```
Good public datasets: search Kaggle for "phishing URL dataset" or use the UCI
"Phishing Websites" data. As long as it has a URL column and a label column
(phishing/legitimate, 1/0, bad/good, etc.) the loader will handle it.

### 5. Run the API
```bash
python app.py
# serves on http://0.0.0.0:5000  (tables are auto-created on first run)
```
Check it's alive: open `http://localhost:5000/api/health`.

---

## Android setup

1. Open the `android/` folder in **Android Studio** (File → Open).
2. Let Gradle sync (it downloads Retrofit, Glide, Material, etc.).
3. **Point the app at your backend** in
   `app/src/main/java/com/example/phishingdetector/api/ApiClient.java`:
   - Emulator: `http://10.0.2.2:5000/`  (already the default — `10.0.2.2` is the
     emulator's alias for your computer's `localhost`)
   - Real phone on the same Wi-Fi: `http://YOUR_COMPUTER_IP:5000/`
     (find it with `ipconfig` / `ifconfig`, e.g. `http://192.168.1.20:5000/`)
   - Keep the trailing slash.
4. Run the app on an emulator or device.

### App flow
LoginActivity → RegisterActivity → OtpActivity (email code) → HomeActivity
(check URL) → ProfileActivity / HistoryActivity (with PDF download).

---

## API reference (quick)

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | /api/register | – | create account + email OTP |
| POST | /api/verify-otp | – | confirm email, returns JWT |
| POST | /api/resend-otp | – | send a new code |
| POST | /api/login | – | returns JWT |
| GET/PUT | /api/profile | ✓ | read / update profile |
| POST | /api/profile/image | ✓ | upload profile photo |
| POST | /api/predict | ✓ | check a URL |
| GET | /api/history | ✓ | list checks |
| GET | /api/history/pdf | ✓ | download history PDF |

Auth = send header `Authorization: Bearer <token>`.

---

## Notes & next steps
- The sample dataset is synthetic, so it scores ~100%. Real data lands around 90–97%.
- For production: serve the API over HTTPS (then remove `usesCleartextTraffic`),
  run with `gunicorn -w 4 app:app` behind nginx, and store uploads on disk or S3.
- To improve accuracy, add more/better-labelled URLs and consider extra features
  (domain age, WHOIS, page content) — but those need network calls at predict time.
```

# PhishGuard

End-to-end phishing-URL detection system: ML model (scikit-learn -> ONNX), FastAPI backend, and a native Android (Java) app that runs inference on-device.

```
phishguard/
  ml/         # training pipeline, ONNX export, Jupyter notebook
  backend/    # FastAPI + PostgreSQL + Alembic + OTP email auth + PDF export
  android/    # Java MVVM app, ViewBinding, ONNX Runtime, Retrofit, Room
```

Highlights:
- 15-feature URL classifier, **F1 = 0.9953** on the held-out test set (XGBoost).
- ONNX model embedded in the app (`assets/phishing_model.onnx`, ~130 KB).
- Java `FeatureExtractor` is byte-for-byte identical to the Python version (verified across 10 sample URLs).
- OTP-only auth (no passwords), JWT access (15 min) + refresh (30 days), refresh tokens stored hashed.
- PDF report export via ReportLab.

## 1. ML model

```powershell
cd ml
pip install -r requirements.txt
python train_model.py
```

Auto-detects the PhiUSIIL dataset under `phiusiil+phishing+url+dataset/` (or falls back to `archive/` or the synthetic `data/phishing_urls.csv`). Outputs go to `ml/models/`:
- `optimized_model.pkl` (raw-feature deploy model)
- `scaler.pkl`
- `feature_names.json`
- `phishing_model.onnx`

The notebook `phishing_model_training.ipynb` runs the same pipeline cell-by-cell.

## 2. Backend (FastAPI + PostgreSQL)

```powershell
cd backend
pip install -r requirements.txt
copy .env.example .env   # then edit DATABASE_URL, JWT_SECRET, MAIL_*
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

By default `MAIL_SUPPRESS_SEND=True` prints OTPs to the console instead of emailing, so the full flow is testable without SMTP set up.

Endpoints:
- `POST /api/auth/register/send-otp`, `/register/verify-otp`
- `POST /api/auth/login/send-otp`, `/login/verify-otp`
- `POST /api/auth/refresh`, `/api/auth/logout`
- `POST /api/scans`, `GET /api/scans/history`, `DELETE /api/scans/{id}`, `GET /api/scans/export`
- `GET /api/users/profile`

Smoke test:

```powershell
python test_integration.py
```

(Hits every endpoint against a live PostgreSQL: 30 assertions, all pass.)

## 3. Android app (Java)

### Open and run in Android Studio

1. **Open Android Studio -> Open** and pick `phishguard/android/`.
2. Studio will auto-detect this is a Gradle project. It uses **Gradle 8.10.2** (already pinned in `gradle/wrapper/gradle-wrapper.properties`) and **JDK 17** (the bundled `jbr` is fine).
3. The first sync may install Android SDK Platform 34 and a few build-tools updates. Accept any license prompts.
4. **Run > Run 'app'** with the green Play button. Pick an emulator (API 24+) or a connected device.
   - Emulator base URL is already set to `http://10.0.2.2:8000/api/` in `RetrofitClient.java`.
   - For a real device, change `BASE_URL` to your host's LAN IP, e.g. `http://192.168.1.20:8000/api/`.

### Or build from the command line

```powershell
cd android
powershell -ExecutionPolicy Bypass -File .\build.ps1 :app:assembleDebug
# APK -> app\build\outputs\apk\debug\app-debug.apk
```

### Install the APK on a connected device

```powershell
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
& $adb install -r "app\build\outputs\apk\debug\app-debug.apk"
```

### Screens

- **Splash** -> routes to Login or Main based on stored token.
- **Login / Register** -> email-only, no password fields.
- **OtpVerify** -> 6-box auto-advancing input with a 60s resend countdown.
- **Scanner** (tab 1) -> URL field, on-device ONNX inference, coloured result card, scan auto-saved to backend.
- **Profile** (tab 2) -> avatar, stats (total / phishing / safe), scan history with swipe-to-delete, "Download PDF" -> public Downloads folder + open in viewer.

### Architecture

- **MVVM** with `ViewModel` + `LiveData`; background work via `ExecutorService`.
- **ViewBinding** on every screen.
- **Retrofit + OkHttp** with an `AuthInterceptor` that adds `Authorization: Bearer ...`, refreshes synchronously on 401, and broadcasts a session-expired signal if the refresh fails.
- **EncryptedSharedPreferences** for token storage.
- **ONNX Runtime Android** for inference (`PhishingDetector` -> `predict(String url)`).

## 4. Cross-language feature parity

`ml/feature_extractor.py` and `android/.../ml/FeatureExtractor.java` are kept in lock-step. A tiny parity test (10 URLs covering IPs, multiple subdomains, `@` userinfo, query strings) confirms identical CSV output. Re-run it any time you change one side:

```powershell
# Python:
cd ml
python -c "from feature_extractor import extract_features; \
  print(extract_features('http://192.168.1.1/bank-login'))"
```

The Java equivalent lives in `FeatureExtractor.extractFeatures(String)`.

## License

MIT.

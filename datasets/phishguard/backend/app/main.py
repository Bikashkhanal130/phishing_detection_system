"""
main.py
=======
PhishGuard FastAPI application entrypoint.

Run (dev):
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import auth_routes, scan_routes, user_routes

app = FastAPI(
    title="PhishGuard API",
    version="1.0.0",
    description="OTP-auth backend for the PhishGuard phishing-detection app.",
)

# CORS — configured for the Android client (use specific origins in prod).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(scan_routes.router)
app.include_router(user_routes.router)


@app.get("/", tags=["health"])
def root():
    return {"service": "PhishGuard API", "status": "ok"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy"}

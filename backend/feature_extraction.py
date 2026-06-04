"""
feature_extraction.py
----------------------
Turns a raw URL string into a numeric feature vector.

IMPORTANT: The SAME function is used during training (train_model.py) and during
prediction (app.py /api/predict). The order of FEATURE_NAMES must never change,
otherwise the trained model will read the wrong columns.

These are "lexical" features (computed from the URL text only). They need no
network access, so prediction on the phone is fast and works even if the site
is down. This is the standard approach for URL phishing classifiers.
"""

import re
from urllib.parse import urlparse

# Words that frequently appear in phishing URLs
SUSPICIOUS_WORDS = [
    "login", "signin", "verify", "account", "update", "secure", "bank",
    "confirm", "password", "credential", "ebayisapi", "webscr", "paypal",
    "free", "lucky", "bonus", "gift", "wallet", "billing", "invoice",
    "support", "security", "unlock", "suspended", "limited",
]

# Common URL shortening services (often used to hide the real destination)
SHORTENERS = [
    "bit.ly", "goo.gl", "tinyurl.com", "ow.ly", "t.co", "is.gd", "buff.ly",
    "adf.ly", "tiny.cc", "cutt.ly", "shorte.st", "rb.gy", "rebrand.ly",
]

# The fixed, ordered list of features. DO NOT reorder.
FEATURE_NAMES = [
    "url_length",
    "hostname_length",
    "path_length",
    "num_dots",
    "num_hyphens",
    "num_at",
    "num_question_marks",
    "num_ampersands",
    "num_equals",
    "num_underscores",
    "num_percent",
    "num_slashes",
    "num_digits",
    "num_subdomains",
    "has_ip_address",
    "has_https",
    "has_at_symbol",
    "has_double_slash_in_path",
    "has_suspicious_word",
    "is_shortened",
    "digit_to_letter_ratio",
    "num_special_chars",
]

IP_REGEX = re.compile(
    r"^(?:\d{1,3}\.){3}\d{1,3}$|"            # IPv4
    r"^(?:0x[0-9a-fA-F]+\.){3}0x[0-9a-fA-F]+$"  # hex IPv4
)


def _safe_parse(url: str):
    """Parse a URL even if the scheme is missing."""
    url = (url or "").strip()
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://", url):
        url = "http://" + url
    return urlparse(url)


def extract_features(url: str) -> dict:
    """Return a dict of feature_name -> value for one URL."""
    url = (url or "").strip()
    parsed = _safe_parse(url)
    hostname = parsed.hostname or ""
    path = parsed.path or ""

    letters = sum(c.isalpha() for c in url)
    digits = sum(c.isdigit() for c in url)
    special = sum(not c.isalnum() for c in url)

    lower_url = url.lower()

    features = {
        "url_length": len(url),
        "hostname_length": len(hostname),
        "path_length": len(path),
        "num_dots": url.count("."),
        "num_hyphens": url.count("-"),
        "num_at": url.count("@"),
        "num_question_marks": url.count("?"),
        "num_ampersands": url.count("&"),
        "num_equals": url.count("="),
        "num_underscores": url.count("_"),
        "num_percent": url.count("%"),
        "num_slashes": url.count("/"),
        "num_digits": digits,
        "num_subdomains": max(hostname.count(".") - 1, 0) if hostname else 0,
        "has_ip_address": 1 if IP_REGEX.match(hostname) else 0,
        "has_https": 1 if parsed.scheme == "https" else 0,
        "has_at_symbol": 1 if "@" in url else 0,
        "has_double_slash_in_path": 1 if "//" in path else 0,
        "has_suspicious_word": 1 if any(w in lower_url for w in SUSPICIOUS_WORDS) else 0,
        "is_shortened": 1 if any(s in lower_url for s in SHORTENERS) else 0,
        "digit_to_letter_ratio": round(digits / letters, 4) if letters else 0.0,
        "num_special_chars": special,
    }
    return features


def vectorize(url: str) -> list:
    """Return the feature values as an ordered list (for the model)."""
    f = extract_features(url)
    return [f[name] for name in FEATURE_NAMES]


if __name__ == "__main__":
    test = "http://secure-login.paypal.account-verify.com/webscr?cmd=update"
    print(f"URL: {test}")
    for k, v in extract_features(test).items():
        print(f"  {k:28s} = {v}")

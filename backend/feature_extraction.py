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

import math
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

# TLDs that appear predominantly in phishing/abuse campaigns
SUSPICIOUS_TLDS = {
    "xyz", "tk", "ml", "ga", "cf", "gq", "top", "click", "info", "online",
    "buzz", "work", "date", "loan", "download", "racing", "trade", "review",
    "stream", "accountant", "science", "faith", "cricket", "party", "win",
}

# Common trusted TLDs
COMMON_TLDS = {
    "com", "org", "net", "edu", "gov", "io", "co", "uk", "ca", "de",
    "fr", "jp", "au", "in", "us", "eu", "nz", "sg", "ch", "nl",
}

# Second-level labels used under country-code TLDs (.com.np, .co.uk, .org.au …)
# When parts[-2] is one of these, the registered domain is parts[-3], not parts[-2].
SECOND_LEVEL_LABELS = {"com", "co", "org", "net", "edu", "gov", "int", "ac", "ne"}

# Major brands that phishers frequently impersonate via typosquatting
KNOWN_BRANDS = {
    "facebook", "instagram", "twitter", "youtube", "tiktok", "snapchat",
    "linkedin", "pinterest", "reddit", "telegram", "whatsapp", "discord",
    "google", "apple", "microsoft", "amazon", "netflix", "spotify",
    "dropbox", "adobe", "github", "gitlab", "paypal", "stripe",
    "yahoo", "outlook", "icloud", "gmail", "office",
    "chase", "citibank", "barclays", "wellsfargo",
    # Nepal-specific fintech / banks
    "esewa", "khalti", "fonepay", "imepay", "nabilbank", "kumaribank",
}

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
    "has_https",          # weak safety signal; brand_* features override it for imposters
    "has_at_symbol",
    "has_double_slash_in_path",
    "has_suspicious_word",
    "is_shortened",
    "digit_to_letter_ratio",
    "num_special_chars",
    # --- new features (added round 2) ---
    "tld_length",
    "is_common_tld",
    "is_suspicious_tld",
    "domain_digit_ratio",
    "has_port",
    "domain_entropy",
    "path_depth",
    # --- brand-safety features (added round 3) ---
    "brand_typosquat",      # domain is 1-2 edits from a known brand (but not exact)
    "brand_in_subdomain",   # a brand name appears in hostname but the reg. domain differs
    "domain_is_exact_brand", # registered domain exactly matches a known-legitimate brand
]

IP_REGEX = re.compile(
    r"^(?:\d{1,3}\.){3}\d{1,3}$|"              # IPv4
    r"^(?:0x[0-9a-fA-F]+\.){3}0x[0-9a-fA-F]+$"  # hex IPv4
)


def _safe_parse(url: str):
    """Parse a URL even if the scheme is missing."""
    url = (url or "").strip()
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://", url):
        url = "http://" + url
    return urlparse(url)


def _entropy(s: str) -> float:
    """Shannon entropy of a string."""
    if not s:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    n = len(s)
    return -sum((count / n) * math.log2(count / n) for count in freq.values())


def _levenshtein(a: str, b: str) -> int:
    """Edit distance between two strings (insertions, deletions, substitutions)."""
    if len(a) < len(b):
        return _levenshtein(b, a)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (ca != cb)))
        prev = curr
    return prev[-1]


def _registered_domain(parts: list[str]) -> str:
    """
    Return the registered domain label (the part just before the public suffix).
    Handles multi-level ccTLDs such as .com.np, .co.uk, .org.au by checking
    whether parts[-2] is a known second-level label.
    """
    if len(parts) >= 3 and parts[-2].lower() in SECOND_LEVEL_LABELS:
        return parts[-3].lower()
    if len(parts) >= 2:
        return parts[-2].lower()
    return parts[0].lower() if parts else ""


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
    lower_host = hostname.lower()

    # Split hostname into labels
    parts = hostname.split(".")
    tld = parts[-1].lower() if len(parts) >= 2 else ""

    # Correctly extract the registered domain even for .com.np / .co.uk style hosts
    domain_label = _registered_domain(parts)
    domain_digits = sum(c.isdigit() for c in domain_label)
    domain_len = len(domain_label) if domain_label else 1

    # --- Brand typosquatting ---
    # Compare the registered domain against every known brand.
    # Skip comparisons where the length difference alone rules out a close match.
    min_brand_dist = min(
        (
            _levenshtein(domain_label, brand)
            for brand in KNOWN_BRANDS
            if abs(len(domain_label) - len(brand)) <= 2 and len(domain_label) >= 5
        ),
        default=999,
    )
    # 1-2 edits away from a real brand (but NOT an exact match) = typosquat
    brand_typosquat = 1 if 1 <= min_brand_dist <= 2 else 0

    # A brand name appears somewhere in the hostname but the registered domain
    # is not that brand (e.g. facebook-login.evil.com or secure.paypal.phish.net)
    brand_in_subdomain = 1 if (
        any(b in lower_host for b in KNOWN_BRANDS)
        and domain_label not in KNOWN_BRANDS
    ) else 0

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
        # HTTPS is a weak signal only. brand_typosquat/brand_in_subdomain
        # explicitly override it when the domain is an impersonation.
        "has_https": 1 if parsed.scheme == "https" else 0,
        "has_at_symbol": 1 if "@" in url else 0,
        "has_double_slash_in_path": 1 if "//" in path else 0,
        "has_suspicious_word": 1 if any(w in lower_url for w in SUSPICIOUS_WORDS) else 0,
        "is_shortened": 1 if any(s in lower_url for s in SHORTENERS) else 0,
        "digit_to_letter_ratio": round(digits / letters, 4) if letters else 0.0,
        "num_special_chars": special,
        # round-2 features
        "tld_length": len(tld),
        "is_common_tld": 1 if tld in COMMON_TLDS else 0,
        "is_suspicious_tld": 1 if tld in SUSPICIOUS_TLDS else 0,
        "domain_digit_ratio": round(domain_digits / domain_len, 4),
        "has_port": 1 if parsed.port is not None else 0,
        "domain_entropy": round(_entropy(domain_label), 4),
        "path_depth": len([p for p in path.split("/") if p]),
        # round-3 features
        "brand_typosquat": brand_typosquat,
        "brand_in_subdomain": brand_in_subdomain,
        "domain_is_exact_brand": 1 if domain_label in KNOWN_BRANDS else 0,
    }
    return features


def vectorize(url: str) -> list:
    """Return the feature values as an ordered list (for the model)."""
    f = extract_features(url)
    return [f[name] for name in FEATURE_NAMES]


if __name__ == "__main__":
    tests = [
        "https://facebokk.com.np",
        "http://secure-login.paypal.account-verify.com/webscr?cmd=update",
        "https://facebook.com",
        "https://g00gle.com",
        "https://www.google.com",
    ]
    for t in tests:
        f = extract_features(t)
        print(f"\nURL: {t}")
        print(f"  domain_label     = {f.get('_domain_label_debug', '(see code)')}")
        for key in ("brand_typosquat", "brand_in_subdomain", "has_https",
                    "domain_entropy", "is_suspicious_tld", "has_suspicious_word"):
            print(f"  {key:28s} = {f[key]}")

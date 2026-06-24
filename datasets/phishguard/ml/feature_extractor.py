"""
feature_extractor.py
=====================
Canonical 15-feature extractor for PhishGuard.

This is the SINGLE SOURCE OF TRUTH for feature extraction in Python.
The Java FeatureExtractor.java MUST produce byte-for-byte identical values
in the same order, otherwise the ONNX model will receive different inputs
on Android than it was trained on.

Feature order (index : name):
    [0]  url_length              total length of the URL string
    [1]  num_dots                count of '.' characters
    [2]  num_hyphens             count of '-' characters
    [3]  num_underscores         count of '_' characters
    [4]  num_slashes             count of '/' characters
    [5]  num_questionmarks       count of '?' characters
    [6]  num_equals              count of '=' characters
    [7]  num_at                  count of '@' characters
    [8]  num_ampersand           count of '&' characters
    [9]  has_ip_address          1 if an IPv4 address appears in the URL, else 0
    [10] is_https                1 if URL starts with 'https://', else 0
    [11] domain_length           length of the host/domain part only
    [12] num_subdomains          number of dot-separated host parts minus 2
    [13] has_suspicious_keywords 1 if URL contains any suspicious keyword
    [14] has_numbers_in_domain   1 if the domain contains any digit, else 0
"""

import re
from urllib.parse import urlparse

# Ordered list of feature names. Exported to feature_names.json so every
# layer of the stack agrees on the exact ordering.
FEATURE_NAMES = [
    "url_length",
    "num_dots",
    "num_hyphens",
    "num_underscores",
    "num_slashes",
    "num_questionmarks",
    "num_equals",
    "num_at",
    "num_ampersand",
    "has_ip_address",
    "is_https",
    "domain_length",
    "num_subdomains",
    "has_suspicious_keywords",
    "has_numbers_in_domain",
]

# Keywords that frequently appear in phishing URLs. Kept lowercase; matching
# is done against the lowercased full URL. Must match the Java array exactly.
SUSPICIOUS_KEYWORDS = [
    "login",
    "verify",
    "account",
    "secure",
    "update",
    "confirm",
    "banking",
    "paypal",
]

# Matches a dotted-quad IPv4 address anywhere in the string (e.g. 192.168.1.1).
_IP_REGEX = re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")


def _extract_host(url: str) -> str:
    """
    Return the host/domain portion of a URL.

    We deliberately avoid depending solely on urlparse because many raw
    dataset rows omit the scheme (e.g. "paypal-verify.xyz/login"). The Java
    side replicates this same fallback logic.
    """
    if url is None:
        return ""
    work = url.strip()

    # Strip scheme if present.
    if "://" in work:
        work = work.split("://", 1)[1]

    # Host ends at the first '/', '?' or '#'.
    for sep in ("/", "?", "#"):
        idx = work.find(sep)
        if idx != -1:
            work = work[:idx]

    # Strip userinfo (anything before '@').
    if "@" in work:
        work = work.split("@", 1)[1]

    # Strip port.
    if ":" in work:
        work = work.split(":", 1)[0]

    return work


def extract_features(url: str) -> list:
    """
    Extract the 15 features from a single URL string.

    Returns a list[float] of length 15 in the canonical order. On any error
    a list of 15 zeros is returned (matching the Java try/catch contract).
    """
    try:
        if url is None:
            url = ""
        url = str(url).strip()
        lower = url.lower()

        host = _extract_host(url)

        url_length = float(len(url))
        num_dots = float(url.count("."))
        num_hyphens = float(url.count("-"))
        num_underscores = float(url.count("_"))
        num_slashes = float(url.count("/"))
        num_questionmarks = float(url.count("?"))
        num_equals = float(url.count("="))
        num_at = float(url.count("@"))
        num_ampersand = float(url.count("&"))

        has_ip_address = 1.0 if _IP_REGEX.search(url) else 0.0
        is_https = 1.0 if lower.startswith("https://") else 0.0

        domain_length = float(len(host))

        # Number of subdomains = (count of dot-separated host parts) - 2.
        # e.g. www.google.com -> 3 parts - 2 = 1; google.com -> 0.
        if host:
            parts = host.split(".")
            num_subdomains = float(max(0, len(parts) - 2))
        else:
            num_subdomains = 0.0

        has_suspicious_keywords = (
            1.0 if any(kw in lower for kw in SUSPICIOUS_KEYWORDS) else 0.0
        )
        has_numbers_in_domain = 1.0 if any(c.isdigit() for c in host) else 0.0

        return [
            url_length,
            num_dots,
            num_hyphens,
            num_underscores,
            num_slashes,
            num_questionmarks,
            num_equals,
            num_at,
            num_ampersand,
            has_ip_address,
            is_https,
            domain_length,
            num_subdomains,
            has_suspicious_keywords,
            has_numbers_in_domain,
        ]
    except Exception:
        # Mirror the Java contract: return float[15]{0f} on any parse error.
        return [0.0] * 15


def extract_features_dataframe(urls):
    """Vectorised helper: build a pandas DataFrame of features for many URLs."""
    import pandas as pd

    rows = [extract_features(u) for u in urls]
    return pd.DataFrame(rows, columns=FEATURE_NAMES)


if __name__ == "__main__":
    # Quick manual check / reference values for cross-language verification.
    samples = [
        "https://www.google.com",
        "http://paypal-verify-account.xyz/login",
        "http://192.168.1.1/bank-login",
    ]
    for s in samples:
        feats = extract_features(s)
        print(s)
        for name, val in zip(FEATURE_NAMES, feats):
            print(f"    {name:<26} = {val}")
        print()

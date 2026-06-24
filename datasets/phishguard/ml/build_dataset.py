"""
build_dataset.py
================
Produces data/phishing_urls.csv with columns: url,label
    label = 0  -> legitimate
    label = 1  -> phishing

REAL DATA:
    If you have a real Kaggle / PhishTank export, drop it in data/ as a CSV
    with a URL column and a label/phishing column. train_model.py will detect
    and prefer it. This generator only runs as a fallback so the whole
    pipeline is runnable offline.

The synthetic URLs are crafted so that the 15 engineered features carry a
realistic, separable signal (phishing URLs tend to use IPs, many hyphens,
suspicious keywords, odd TLDs, long hosts, no HTTPS), while remaining noisy
enough that the task is non-trivial.
"""

import os
import random

random.seed(42)

OUT_DIR = os.path.join(os.path.dirname(__file__), "data")
OUT_PATH = os.path.join(OUT_DIR, "phishing_urls.csv")

# ---- building blocks -------------------------------------------------------

LEGIT_DOMAINS = [
    "google.com", "github.com", "stackoverflow.com", "wikipedia.org",
    "amazon.com", "microsoft.com", "apple.com", "netflix.com",
    "linkedin.com", "youtube.com", "reddit.com", "twitter.com",
    "facebook.com", "instagram.com", "paypal.com", "ebay.com",
    "dropbox.com", "spotify.com", "adobe.com", "nytimes.com",
    "bbc.co.uk", "cnn.com", "medium.com", "cloudflare.com",
    "mozilla.org", "python.org", "oracle.com", "ibm.com",
    "salesforce.com", "atlassian.com", "gitlab.com", "bitbucket.org",
]

LEGIT_SUBDOMAINS = ["www", "", "docs", "mail", "blog", "support", "api", "store", "shop"]
LEGIT_PATHS = [
    "", "/", "/about", "/contact", "/products", "/search?q=phone",
    "/help/articles", "/user/profile", "/news/world", "/watch?v=abc123",
    "/questions/12345/how-to", "/wiki/Main_Page", "/pricing", "/login",
]

# Brands frequently impersonated by phishing pages.
PHISH_BRANDS = [
    "paypal", "amazon", "apple", "microsoft", "netflix", "ebay",
    "bankofamerica", "wellsfargo", "chase", "facebook", "instagram",
    "google", "dropbox", "linkedin", "icloud", "office365",
]
# Cheap / abused TLDs commonly seen in phishing campaigns.
PHISH_TLDS = ["xyz", "tk", "ml", "ga", "cf", "gq", "top", "click", "info", "online", "buzz"]
PHISH_KEYWORDS = [
    "login", "verify", "account", "secure", "update", "confirm",
    "banking", "signin", "webscr", "support", "billing", "unlock",
]
PHISH_PATHS = [
    "/login", "/verify", "/account/confirm", "/secure/update",
    "/signin?account=verify", "/confirm-identity", "/billing/update",
    "/webscr?cmd=_login-run", "/unlock-account", "/secure/login.php",
]


def _rand_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def gen_legit():
    """Generate a realistic legitimate URL."""
    domain = random.choice(LEGIT_DOMAINS)
    sub = random.choice(LEGIT_SUBDOMAINS)
    host = f"{sub}.{domain}" if sub else domain
    scheme = "https" if random.random() < 0.9 else "http"
    path = random.choice(LEGIT_PATHS)
    return f"{scheme}://{host}{path}"


def gen_phish():
    """Generate a phishing-style URL using a few common patterns."""
    pattern = random.random()
    brand = random.choice(PHISH_BRANDS)
    kw = random.choice(PHISH_KEYWORDS)
    tld = random.choice(PHISH_TLDS)
    path = random.choice(PHISH_PATHS)
    scheme = "http" if random.random() < 0.85 else "https"

    if pattern < 0.25:
        # Raw IP address host.
        return f"{scheme}://{_rand_ip()}{path}"
    elif pattern < 0.55:
        # brand-keyword hyphenated host on a cheap TLD.
        host = f"{brand}-{kw}-{random.choice(PHISH_KEYWORDS)}.{tld}"
        return f"{scheme}://{host}{path}"
    elif pattern < 0.78:
        # legit brand used as a subdomain of an attacker domain.
        host = f"{brand}.{kw}-{random.randint(10,9999)}.{tld}"
        return f"{scheme}://{host}{path}"
    else:
        # long query-string heavy URL with '@' obfuscation sometimes.
        at = f"{brand}@" if random.random() < 0.4 else ""
        host = f"{kw}-{brand}{random.randint(1,999)}.{tld}"
        q = f"?email={brand}@mail.com&token={random.randint(100000,999999)}&redirect=secure"
        return f"{scheme}://{at}{host}{path}{q}"


def main(n_legit=3000, n_phish=3000):
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = []
    seen = set()

    def add(url, label):
        if url not in seen:
            seen.add(url)
            rows.append((url, label))

    # Over-generate then dedupe to hit the targets.
    attempts = 0
    while sum(1 for _, l in rows if l == 0) < n_legit and attempts < n_legit * 10:
        add(gen_legit(), 0)
        attempts += 1
    attempts = 0
    while sum(1 for _, l in rows if l == 1) < n_phish and attempts < n_phish * 10:
        add(gen_phish(), 1)
        attempts += 1

    random.shuffle(rows)

    with open(OUT_PATH, "w", encoding="utf-8", newline="") as f:
        f.write("url,label\n")
        for url, label in rows:
            # URLs may contain commas (query strings) -> quote the field.
            safe = url.replace('"', '""')
            f.write(f'"{safe}",{label}\n')

    n0 = sum(1 for _, l in rows if l == 0)
    n1 = sum(1 for _, l in rows if l == 1)
    print(f"Wrote {len(rows)} rows to {OUT_PATH}  (legit={n0}, phishing={n1})")


if __name__ == "__main__":
    main()

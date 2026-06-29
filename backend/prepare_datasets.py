"""
prepare_datasets.py
--------------------
Merges both upstream datasets into a single clean CSV for training.

Datasets used:
  1. datasets/phishguard/ml/data/phishing_urls.csv
       label: 0=legitimate, 1=phishing  (matches our convention -- no flip)

  2. datasets/phiusiil+phishing+url+dataset/PhiUSIIL_Phishing_URL_Dataset.csv
       label: 1=legitimate, 0=phishing  (OPPOSITE -- must flip before merging)

Output: backend/merged_dataset.csv  (url, label  where 1=phishing, 0=legitimate)

Usage:
    python prepare_datasets.py
"""

import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PHISHGUARD_CSV = os.path.join(ROOT, "datasets", "phishguard", "ml", "data", "phishing_urls.csv")
PHIUSIIL_CSV  = os.path.join(ROOT, "datasets", "phiusiil+phishing+url+dataset",
                              "PhiUSIIL_Phishing_URL_Dataset.csv")
OUT_CSV = os.path.join(HERE, "merged_dataset.csv")


def load_phishguard(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    df = df[["url", "label"]].dropna()
    df["label"] = df["label"].astype(int)
    # Convention already correct: 0=legit, 1=phishing
    return df


def load_phiusiil(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, usecols=["URL", "label"])
    df = df.rename(columns={"URL": "url"}).dropna()
    df["label"] = df["label"].astype(int)
    # PhiUSIIL: 1=legitimate, 0=phishing  =>  flip to match our convention
    df["label"] = 1 - df["label"]
    return df


def main():
    frames = []

    if os.path.exists(PHISHGUARD_CSV):
        pg = load_phishguard(PHISHGUARD_CSV)
        print(f"PhishGuard   : {len(pg):>7,} rows  "
              f"(phishing={int(pg.label.sum()):,}  legit={int((pg.label==0).sum()):,})")
        frames.append(pg)
    else:
        print(f"WARNING: PhishGuard dataset not found at {PHISHGUARD_CSV}")

    if os.path.exists(PHIUSIIL_CSV):
        ph = load_phiusiil(PHIUSIIL_CSV)
        print(f"PhiUSIIL     : {len(ph):>7,} rows  "
              f"(phishing={int(ph.label.sum()):,}  legit={int((ph.label==0).sum()):,})")
        frames.append(ph)
    else:
        print(f"WARNING: PhiUSIIL dataset not found at {PHIUSIIL_CSV}")

    if not frames:
        sys.exit("No datasets found. Aborting.")

    merged = pd.concat(frames, ignore_index=True)
    merged = merged.drop_duplicates(subset=["url"])
    merged = merged.sample(frac=1, random_state=42).reset_index(drop=True)

    print(f"\nMerged total : {len(merged):>7,} rows  "
          f"(phishing={int(merged.label.sum()):,}  legit={int((merged.label==0).sum()):,})")

    merged.to_csv(OUT_CSV, index=False)
    print(f"Saved -> {OUT_CSV}")
    return OUT_CSV


if __name__ == "__main__":
    main()

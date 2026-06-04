"""
train_model.py
--------------
Trains a Random Forest classifier to detect phishing URLs.

Splits the data: 80% training, 20% testing (as required).

USAGE:
    python train_model.py --data your_dataset.csv

Your CSV must have two columns:
    url   -> the link text         (e.g. http://paypal-verify.com/login)
    label -> phishing or legit     (accepts: 1/0, phishing/legitimate, bad/good,
                                     malicious/benign, yes/no)

If you don't pass --data, it uses sample_dataset.csv that ships with the project
so you can confirm the pipeline runs end to end.

Output:
    model/phishing_model.joblib   (the trained model + feature names)
"""

import argparse
import os
import sys

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split

from feature_extraction import FEATURE_NAMES, vectorize

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(HERE, "model", "phishing_model.joblib")

# Maps the many ways a label might be written -> 1 (phishing) or 0 (legitimate)
PHISHING_LABELS = {"1", "phishing", "phish", "bad", "malicious", "yes", "spam", "scam"}
LEGIT_LABELS = {"0", "legitimate", "legit", "good", "benign", "no", "ham", "safe"}


def normalize_label(value) -> int:
    s = str(value).strip().lower()
    if s in PHISHING_LABELS:
        return 1
    if s in LEGIT_LABELS:
        return 0
    # Fallback: try to read it as a number
    try:
        return 1 if float(s) >= 0.5 else 0
    except ValueError:
        raise ValueError(f"Could not understand label: {value!r}")


def load_dataset(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]

    # Try to find the url and label columns flexibly
    url_col = next((c for c in df.columns if c in ("url", "urls", "domain", "link")), None)
    label_col = next(
        (c for c in df.columns if c in ("label", "result", "class", "type", "status", "target")),
        None,
    )
    if url_col is None or label_col is None:
        raise ValueError(
            "CSV must contain a URL column (url/link/domain) and a label column "
            f"(label/result/class/type). Found columns: {list(df.columns)}"
        )

    df = df[[url_col, label_col]].rename(columns={url_col: "url", label_col: "label"})
    df = df.dropna(subset=["url", "label"])
    df["label"] = df["label"].apply(normalize_label)
    df = df.drop_duplicates(subset=["url"])
    return df


def main():
    parser = argparse.ArgumentParser(description="Train phishing URL Random Forest")
    parser.add_argument("--data", default=os.path.join(HERE, "sample_dataset.csv"),
                        help="Path to CSV with columns url,label")
    parser.add_argument("--trees", type=int, default=200, help="Number of trees")
    args = parser.parse_args()

    if not os.path.exists(args.data):
        sys.exit(f"Dataset not found: {args.data}")

    print(f"Loading dataset: {args.data}")
    df = load_dataset(args.data)
    print(f"  Rows: {len(df)}  |  phishing={int(df.label.sum())}  legit={int((df.label == 0).sum())}")

    # 1) Convert every URL into its feature vector
    print("Extracting features...")
    X = [vectorize(u) for u in df["url"]]
    y = df["label"].tolist()

    # 2) 80% train / 20% test  (stratify keeps the class balance in both sets)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"  Train: {len(X_train)} samples   Test: {len(X_test)} samples  (80/20)")

    # 3) Train the Random Forest
    print(f"Training RandomForestClassifier ({args.trees} trees)...")
    clf = RandomForestClassifier(
        n_estimators=args.trees,
        max_depth=None,
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=42,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)

    # 4) Evaluate on the held-out 20%
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print("\n================  TEST RESULTS (20% held out)  ================")
    print(f"Accuracy: {acc * 100:.2f}%\n")
    print(classification_report(y_test, y_pred, target_names=["legit", "phishing"]))
    print("Confusion matrix [rows=true, cols=pred]:")
    print(confusion_matrix(y_test, y_pred))

    # Show which features matter most
    importances = sorted(
        zip(FEATURE_NAMES, clf.feature_importances_), key=lambda t: t[1], reverse=True
    )
    print("\nTop features:")
    for name, score in importances[:8]:
        print(f"  {name:28s} {score:.3f}")

    # 5) Save the model bundled with its feature names
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump({"model": clf, "feature_names": FEATURE_NAMES, "accuracy": acc}, MODEL_PATH)
    print(f"\nSaved model -> {MODEL_PATH}")


if __name__ == "__main__":
    main()

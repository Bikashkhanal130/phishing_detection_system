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
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    auc,
    average_precision_score,
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, train_test_split

from feature_extraction import FEATURE_NAMES, vectorize

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(HERE, "model", "phishing_model.joblib")
REPORT_DIR = os.path.join(HERE, "evaluation_report")

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
    cm = confusion_matrix(y_test, y_pred)
    print(cm)

    os.makedirs(REPORT_DIR, exist_ok=True)

    # Confusion matrix plot
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=["Legitimate", "Phishing"],
                yticklabels=["Legitimate", "Phishing"])
    plt.title("Confusion Matrix - Phishing Detection System")
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")
    plt.tight_layout()
    cm_path = os.path.join(REPORT_DIR, "confusion_matrix.png")
    plt.savefig(cm_path, dpi=200)
    plt.close()
    print(f"Saved: {cm_path}")

    # ROC curve + Precision-Recall curve, estimated with 5-fold stratified
    # cross-validation over the whole dataset. A single train/test split can
    # land on an unrealistically perfect (right-angle) curve just because
    # that particular test fold happened to be easy; averaging several folds
    # and shading +/-1 std. dev. gives a curve (and AUC) that reflects the
    # model's typical performance instead of one lucky split.
    print("\nRunning 5-fold cross-validation for ROC / Precision-Recall curves...")
    X_arr = np.array(X)
    y_arr = np.array(y)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    mean_fpr = np.linspace(0, 1, 200)
    mean_recall = np.linspace(0, 1, 200)
    tprs, roc_aucs = [], []
    precisions_interp, pr_aucs = [], []

    for fold_i, (train_idx, test_idx) in enumerate(cv.split(X_arr, y_arr), start=1):
        fold_clf = RandomForestClassifier(
            n_estimators=args.trees,
            max_depth=None,
            min_samples_leaf=2,
            n_jobs=-1,
            random_state=42,
            class_weight="balanced",
        )
        fold_clf.fit(X_arr[train_idx], y_arr[train_idx])
        fold_proba = fold_clf.predict_proba(X_arr[test_idx])[:, 1]

        fpr, tpr, _ = roc_curve(y_arr[test_idx], fold_proba)
        tprs.append(np.interp(mean_fpr, fpr, tpr))
        tprs[-1][0] = 0.0
        roc_aucs.append(auc(fpr, tpr))

        prec, rec, _ = precision_recall_curve(y_arr[test_idx], fold_proba)
        order = np.argsort(rec)
        precisions_interp.append(np.interp(mean_recall, rec[order], prec[order]))
        pr_aucs.append(average_precision_score(y_arr[test_idx], fold_proba))
        print(f"  Fold {fold_i}: ROC AUC = {roc_aucs[-1]:.4f}  PR AUC = {pr_aucs[-1]:.4f}")

    mean_tpr = np.mean(tprs, axis=0)
    mean_tpr[-1] = 1.0
    std_tpr = np.std(tprs, axis=0)
    mean_roc_auc = float(np.mean(roc_aucs))
    std_roc_auc = float(np.std(roc_aucs))

    mean_precision = np.mean(precisions_interp, axis=0)
    std_precision = np.std(precisions_interp, axis=0)
    mean_pr_auc = float(np.mean(pr_aucs))
    std_pr_auc = float(np.std(pr_aucs))

    print(f"5-fold CV ROC AUC: {mean_roc_auc:.4f} +/- {std_roc_auc:.4f}")
    print(f"5-fold CV PR  AUC: {mean_pr_auc:.4f} +/- {std_pr_auc:.4f}")

    # -- ROC curve --
    plt.figure(figsize=(6, 5))
    plt.plot(mean_fpr, mean_tpr, color="#1F6FEB", lw=2,
              label=f"Mean ROC (AUC = {mean_roc_auc:.4f} $\\pm$ {std_roc_auc:.4f})")
    plt.fill_between(mean_fpr,
                      np.clip(mean_tpr - std_tpr, 0, 1),
                      np.clip(mean_tpr + std_tpr, 0, 1),
                      color="#1F6FEB", alpha=0.15, label="± 1 std. dev.")
    plt.plot([0, 1], [0, 1], color="gray", lw=1.2, linestyle="--", label="Random Classifier")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve - Phishing Detection System (5-fold CV)")
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    roc_path = os.path.join(REPORT_DIR, "roc_curve.png")
    plt.savefig(roc_path, dpi=200)
    plt.close()
    print(f"Saved: {roc_path}")

    # -- Precision-Recall (AUC) curve --
    plt.figure(figsize=(6, 5))
    plt.plot(mean_recall, mean_precision, color="#DA3633", lw=2,
              label=f"Mean PR Curve (AUC = {mean_pr_auc:.4f} $\\pm$ {std_pr_auc:.4f})")
    plt.fill_between(mean_recall,
                      np.clip(mean_precision - std_precision, 0, 1),
                      np.clip(mean_precision + std_precision, 0, 1),
                      color="#DA3633", alpha=0.15, label="± 1 std. dev.")
    baseline = float(y_arr.mean())
    plt.axhline(baseline, color="gray", lw=1.2, linestyle="--",
                label=f"Random Classifier ({baseline:.2f})")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve - Phishing Detection System (5-fold CV)")
    plt.legend(loc="lower left")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    pr_path = os.path.join(REPORT_DIR, "pr_curve.png")
    plt.savefig(pr_path, dpi=200)
    plt.close()
    print(f"Saved: {pr_path}")

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

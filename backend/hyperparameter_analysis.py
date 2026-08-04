"""
hyperparameter_analysis.py
---------------------------
Sensitivity / validation analysis for the Random Forest phishing classifier:
  1. 5-Fold Cross-Validation accuracy on the full merged dataset
  2. Accuracy & AUC vs. n_estimators (number of trees), including 198
  3. Accuracy & AUC vs. random_state (model seed), at n_estimators=198

Uses the same 80/20 train/test split as train_model.py so results are
comparable to the main reported numbers.

Usage:
    python hyperparameter_analysis.py --data merged_dataset.csv
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

from feature_extraction import vectorize
from train_model import load_dataset

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(HERE, "evaluation_report")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=os.path.join(HERE, "merged_dataset.csv"))
    args = parser.parse_args()

    os.makedirs(REPORT_DIR, exist_ok=True)

    print(f"Loading dataset: {args.data}")
    df = load_dataset(args.data)
    print(f"  Rows: {len(df)}")

    print("Extracting features (once, reused for every run below)...")
    X = np.array([vectorize(u) for u in df["url"]])
    y = np.array(df["label"].tolist())
    print(f"  Feature matrix: {X.shape}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # ---------- 1. K-Fold Cross-Validation ----------
    print("\n=== 5-Fold Cross-Validation (whole dataset) ===")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    clf_cv = RandomForestClassifier(
        n_estimators=200, min_samples_leaf=2, class_weight="balanced",
        random_state=42, n_jobs=-1,
    )
    fold_scores = cross_val_score(clf_cv, X, y, cv=cv, scoring="accuracy", n_jobs=1)
    print("Fold accuracies:", [f"{s * 100:.2f}%" for s in fold_scores])
    print(f"Mean: {fold_scores.mean() * 100:.2f}%   Std: {fold_scores.std() * 100:.2f}%")

    plt.figure(figsize=(7, 5))
    folds = [f"Fold {i + 1}" for i in range(len(fold_scores))]
    bars = plt.bar(folds, fold_scores * 100, color="#1F6FEB")
    plt.axhline(fold_scores.mean() * 100, color="#E8590C", linestyle="--",
                label=f"Mean = {fold_scores.mean() * 100:.2f}%")
    plt.ylim(min(fold_scores.min() * 100 - 1, 95), 100.5)
    plt.ylabel("Accuracy (%)")
    plt.title("5-Fold Cross-Validation Accuracy - Random Forest")
    plt.legend()
    for bar, score in zip(bars, fold_scores):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                  f"{score * 100:.2f}%", ha="center", fontsize=9)
    plt.tight_layout()
    cv_path = os.path.join(REPORT_DIR, "cross_validation.png")
    plt.savefig(cv_path, dpi=200)
    plt.close()
    print(f"Saved: {cv_path}")

    # ---------- 2. n_estimators sweep ----------
    print("\n=== n_estimators sweep (random_state=42) ===")
    n_values = [50, 100, 150, 198, 250, 300]
    n_acc, n_auc = [], []
    for n in n_values:
        clf = RandomForestClassifier(
            n_estimators=n, min_samples_leaf=2, class_weight="balanced",
            random_state=42, n_jobs=-1,
        )
        clf.fit(X_train, y_train)
        pred = clf.predict(X_test)
        proba = clf.predict_proba(X_test)[:, 1]
        acc = accuracy_score(y_test, pred)
        auc_score = roc_auc_score(y_test, proba)
        n_acc.append(acc)
        n_auc.append(auc_score)
        print(f"  n_estimators={n:>4}  accuracy={acc * 100:.3f}%  AUC={auc_score:.4f}")

    fig, ax1 = plt.subplots(figsize=(7.5, 5))
    ax1.plot(n_values, [a * 100 for a in n_acc], marker="o", color="#1F6FEB", label="Accuracy (%)")
    ax1.set_xlabel("n_estimators (number of trees)")
    ax1.set_ylabel("Accuracy (%)", color="#1F6FEB")
    ax1.tick_params(axis="y", labelcolor="#1F6FEB")
    ax1.axvline(198, color="gray", linestyle=":", alpha=0.7, label="n_estimators = 198")

    ax2 = ax1.twinx()
    ax2.plot(n_values, n_auc, marker="s", color="#E8590C", label="AUC")
    ax2.set_ylabel("AUC", color="#E8590C")
    ax2.tick_params(axis="y", labelcolor="#E8590C")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="lower right")
    plt.title("Accuracy & AUC vs. Number of Trees (n_estimators)")
    fig.tight_layout()
    n_path = os.path.join(REPORT_DIR, "n_estimators_sensitivity.png")
    plt.savefig(n_path, dpi=200)
    plt.close()
    print(f"Saved: {n_path}")

    # ---------- 3. random_state sweep (n_estimators=198) ----------
    print("\n=== random_state sweep (n_estimators=198) ===")
    seeds = [0, 1, 42, 123, 2024]
    s_acc, s_auc = [], []
    for seed in seeds:
        clf = RandomForestClassifier(
            n_estimators=198, min_samples_leaf=2, class_weight="balanced",
            random_state=seed, n_jobs=-1,
        )
        clf.fit(X_train, y_train)
        pred = clf.predict(X_test)
        proba = clf.predict_proba(X_test)[:, 1]
        acc = accuracy_score(y_test, pred)
        auc_score = roc_auc_score(y_test, proba)
        s_acc.append(acc)
        s_auc.append(auc_score)
        print(f"  random_state={seed:>5}  accuracy={acc * 100:.3f}%  AUC={auc_score:.4f}")

    print(f"\n  Accuracy across seeds: mean={np.mean(s_acc) * 100:.3f}%  std={np.std(s_acc) * 100:.4f}%")
    print(f"  AUC across seeds:      mean={np.mean(s_auc):.4f}  std={np.std(s_auc):.5f}")

    fig, ax1 = plt.subplots(figsize=(7.5, 5))
    x_pos = np.arange(len(seeds))
    width = 0.35
    b1 = ax1.bar(x_pos - width / 2, [a * 100 for a in s_acc], width, color="#1F6FEB", label="Accuracy (%)")
    ax1.set_ylabel("Accuracy (%)", color="#1F6FEB")
    ax1.set_ylim(min(s_acc) * 100 - 0.5, min(s_acc) * 100 + 1.0)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels([str(s) for s in seeds])
    ax1.set_xlabel("random_state (model seed)")
    ax1.tick_params(axis="y", labelcolor="#1F6FEB")

    ax2 = ax1.twinx()
    b2 = ax2.bar(x_pos + width / 2, s_auc, width, color="#E8590C", label="AUC")
    ax2.set_ylabel("AUC", color="#E8590C")
    ax2.set_ylim(min(s_auc) - 0.005, min(s_auc) + 0.01)
    ax2.tick_params(axis="y", labelcolor="#E8590C")

    fig.legend([b1, b2], ["Accuracy (%)", "AUC"], loc="upper center",
               bbox_to_anchor=(0.5, 1.02), ncol=2, frameon=False)
    plt.title("Accuracy & AUC across different random_state seeds (n_estimators=198)", pad=28)
    fig.tight_layout()
    s_path = os.path.join(REPORT_DIR, "random_state_sensitivity.png")
    plt.savefig(s_path, dpi=200)
    plt.close()
    print(f"Saved: {s_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()

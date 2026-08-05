"""
auc_calculation.py
-------------------
Produces a worked (manual) AUC calculation, separate from the ROC/PR curve
plots in train_model.py, for use in the report's methodology/calculation
section.

It reproduces the exact 80/20 held-out test split used by train_model.py
(same random_state=42), loads the already-trained model, and:

  1. Computes the full ROC curve (every distinct probability threshold).
  2. Applies the trapezoidal rule by hand, point by point, to derive AUC --
     and shows that this manual sum matches scikit-learn's auc() exactly.
  3. Saves the full point-by-point calculation to a CSV (appendix-grade
     detail) and a condensed, human-readable table (a dozen or so
     representative points spanning the curve) as both CSV and a PNG table
     figure, ready to drop into the report next to the ROC curve.

USAGE:
    python auc_calculation.py --data merged_dataset.csv
"""

import argparse
import os

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import auc, roc_curve
from sklearn.model_selection import train_test_split

from feature_extraction import vectorize
from train_model import MODEL_PATH, REPORT_DIR, load_dataset

HERE = os.path.dirname(os.path.abspath(__file__))

# FPR points at which we sample the curve for the condensed illustration
# table. Denser near 0 because that's where nearly all of this model's ROC
# curve's shape/area is decided.
SAMPLE_FPR = np.array([
    0.000, 0.001, 0.002, 0.005, 0.010, 0.020, 0.050,
    0.100, 0.200, 0.300, 0.500, 0.700, 1.000,
])


def main():
    parser = argparse.ArgumentParser(description="Manual AUC (trapezoidal rule) calculation")
    parser.add_argument("--data", default=os.path.join(HERE, "merged_dataset.csv"))
    args = parser.parse_args()

    if not os.path.exists(MODEL_PATH):
        raise SystemExit(f"No trained model at {MODEL_PATH}. Run train_model.py first.")

    print(f"Loading dataset: {args.data}")
    df = load_dataset(args.data)
    X = [vectorize(u) for u in df["url"]]
    y = df["label"].tolist()

    # Same split as train_model.py -> same held-out test set the reported
    # accuracy / confusion matrix / classification report were computed on.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    bundle = joblib.load(MODEL_PATH)
    clf = bundle["model"]
    y_proba = clf.predict_proba(X_test)[:, 1]

    # ---- 1. Full ROC curve: every distinct threshold sklearn finds -------
    fpr, tpr, thresholds = roc_curve(y_test, y_proba)
    sklearn_auc = auc(fpr, tpr)

    # ---- 2. Manual trapezoidal-rule calculation, point by point ---------
    #   Area of segment i = (FPR_i - FPR_{i-1}) * (TPR_i + TPR_{i-1}) / 2
    d_fpr = np.diff(fpr)
    avg_tpr = (tpr[1:] + tpr[:-1]) / 2.0
    segment_area = d_fpr * avg_tpr
    cumulative_auc = np.concatenate([[0.0], np.cumsum(segment_area)])
    manual_auc = cumulative_auc[-1]

    print(f"Held-out test set size: {len(y_test)}")
    print(f"Distinct ROC threshold points: {len(fpr)}")
    print(f"Manual trapezoidal-rule AUC : {manual_auc:.6f}")
    print(f"scikit-learn auc(fpr, tpr)  : {sklearn_auc:.6f}")
    print(f"Difference                 : {abs(manual_auc - sklearn_auc):.2e}  (matches)")

    os.makedirs(REPORT_DIR, exist_ok=True)

    # ---- 3a. Full point-by-point table (appendix-grade detail) ----------
    full_path = os.path.join(REPORT_DIR, "auc_calculation_full.csv")
    with open(full_path, "w") as f:
        f.write("threshold,fpr,tpr,delta_fpr,avg_tpr,segment_area,cumulative_auc\n")
        f.write(f"{thresholds[0]},{fpr[0]:.6f},{tpr[0]:.6f},,,,{cumulative_auc[0]:.6f}\n")
        for i in range(1, len(fpr)):
            f.write(
                f"{thresholds[i]},{fpr[i]:.6f},{tpr[i]:.6f},"
                f"{d_fpr[i-1]:.6f},{avg_tpr[i-1]:.6f},"
                f"{segment_area[i-1]:.6f},{cumulative_auc[i]:.6f}\n"
            )
    print(f"Saved full calculation: {full_path}  ({len(fpr)} rows)")

    # ---- 3b. Condensed, report-ready table -------------------------------
    # Interpolate TPR at a fixed set of representative FPR points so the
    # table stays short enough to read, while still spanning the whole
    # curve (denser near FPR=0, where this model's curve rises steeply).
    sample_tpr = np.interp(SAMPLE_FPR, fpr, tpr)
    s_d_fpr = np.diff(SAMPLE_FPR)
    s_avg_tpr = (sample_tpr[1:] + sample_tpr[:-1]) / 2.0
    s_area = s_d_fpr * s_avg_tpr
    s_cumulative = np.concatenate([[0.0], np.cumsum(s_area)])
    approx_auc = s_cumulative[-1]

    rows = []
    rows.append(["FPR", "TPR", "ΔFPR", "Avg. TPR", "Segment Area", "Cumulative AUC"])
    rows.append([f"{SAMPLE_FPR[0]:.3f}", f"{sample_tpr[0]:.4f}", "-", "-", "-", f"{s_cumulative[0]:.4f}"])
    for i in range(1, len(SAMPLE_FPR)):
        rows.append([
            f"{SAMPLE_FPR[i]:.3f}",
            f"{sample_tpr[i]:.4f}",
            f"{s_d_fpr[i-1]:.3f}",
            f"{s_avg_tpr[i-1]:.4f}",
            f"{s_area[i-1]:.4f}",
            f"{s_cumulative[i]:.4f}",
        ])

    condensed_csv = os.path.join(REPORT_DIR, "auc_calculation_table.csv")
    with open(condensed_csv, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(",".join(r) + "\n")
    print(f"Saved condensed table: {condensed_csv}")

    # ---- 3c. Render the condensed table as a figure ----------------------
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.axis("off")
    table = ax.table(cellText=rows[1:], colLabels=rows[0], loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.6)
    for c in range(len(rows[0])):
        table[0, c].set_facecolor("#1F6FEB")
        table[0, c].set_text_props(color="white", weight="bold")
    ax.set_title(
        "AUC Calculation - Trapezoidal Rule on Held-Out Test Set\n"
        f"Sum of segment areas = {approx_auc:.4f}   |   "
        f"Full-resolution AUC (all {len(fpr)} thresholds) = {manual_auc:.4f}   |   "
        f"scikit-learn auc() = {sklearn_auc:.4f}",
        fontsize=10.5,
    )
    plt.tight_layout()
    table_path = os.path.join(REPORT_DIR, "auc_calculation_table.png")
    plt.savefig(table_path, dpi=200)
    plt.close()
    print(f"Saved: {table_path}")

    # ---- 3d. Graph: the trapezoids that the table above sums up ----------
    # Full-resolution ROC curve in the background, the coarse sample points
    # connected by straight segments on top (these are exactly the
    # trapezoids in the table), each one shaded and labelled with its area.
    fig, ax = plt.subplots(figsize=(7.5, 6))
    ax.plot(fpr, tpr, color="#8A8F98", lw=1, alpha=0.6, label="Full-resolution ROC curve")
    ax.plot(SAMPLE_FPR, sample_tpr, color="#1F6FEB", lw=2, marker="o", markersize=5,
            label="Sampled points (trapezoid corners)")

    cmap = plt.get_cmap("Blues")
    for i in range(1, len(SAMPLE_FPR)):
        xs = [SAMPLE_FPR[i - 1], SAMPLE_FPR[i], SAMPLE_FPR[i], SAMPLE_FPR[i - 1]]
        ys = [0, 0, sample_tpr[i], sample_tpr[i - 1]]
        shade = 0.25 + 0.5 * (i / len(SAMPLE_FPR))
        ax.fill(xs, ys, color=cmap(shade), alpha=0.55, edgecolor="white", linewidth=0.5)
        if s_area[i - 1] >= 0.015:  # only label segments wide enough to read
            cx = (SAMPLE_FPR[i - 1] + SAMPLE_FPR[i]) / 2
            cy = s_avg_tpr[i - 1] / 2
            ax.annotate(f"{s_area[i-1]:.3f}", (cx, cy), fontsize=7.5,
                        ha="center", va="center", color="#0B3D91")

    ax.plot([0, 1], [0, 1], color="gray", lw=1, linestyle="--", label="Random Classifier")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(
        "AUC Calculation - Area Under the ROC Curve (Trapezoidal Rule)\n"
        f"Sum of shaded segments = {approx_auc:.4f}  (full-resolution AUC = {manual_auc:.4f})"
    )
    ax.legend(loc="lower right", fontsize=8.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    graph_path = os.path.join(REPORT_DIR, "auc_calculation_graph.png")
    plt.savefig(graph_path, dpi=200)
    plt.close()
    print(f"Saved: {graph_path}")


if __name__ == "__main__":
    main()

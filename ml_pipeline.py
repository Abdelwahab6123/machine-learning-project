"""
ml_pipeline.py
==============
Trains three classifiers on the Breast Cancer Wisconsin dataset,
evaluates them, and saves publication-quality chart images.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.ticker import MultipleLocator
import seaborn as sns
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix, roc_curve,
)
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
#  PALETTE  (deep navy + coral + sage + amber)
# ─────────────────────────────────────────────
PALETTE = {
    "Logistic Regression":    "#E05A4E",   # coral-red
    "Random Forest":          "#4A9B7F",   # sage-green
    "Support Vector Machine": "#4A72B0",   # steel-blue
}
BG       = "#F7F6F3"   # warm off-white
NAVY     = "#1C2B3A"
LIGHT_BG = "#EEECEA"
GRID_CLR = "#D8D5D0"
TEXT_CLR = "#2C2C2C"

def apply_base_style():
    plt.rcParams.update({
        "figure.facecolor":  BG,
        "axes.facecolor":    BG,
        "axes.edgecolor":    GRID_CLR,
        "axes.grid":         True,
        "grid.color":        GRID_CLR,
        "grid.linewidth":    0.7,
        "grid.alpha":        0.9,
        "text.color":        TEXT_CLR,
        "axes.labelcolor":   TEXT_CLR,
        "xtick.color":       TEXT_CLR,
        "ytick.color":       TEXT_CLR,
        "font.family":       "DejaVu Sans",
        "axes.spines.top":   False,
        "axes.spines.right": False,
    })

apply_base_style()


# ══════════════════════════════════════════════
#  1 · DATA
# ══════════════════════════════════════════════
data = load_breast_cancer()
X = pd.DataFrame(data.data, columns=data.feature_names)
y = pd.Series(data.target)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
scaler     = StandardScaler()
X_train_s  = scaler.fit_transform(X_train)
X_test_s   = scaler.transform(X_test)

CLASS_NAMES = ["Malignant", "Benign"]


# ══════════════════════════════════════════════
#  2 · MODELS
# ══════════════════════════════════════════════
models = {
    "Logistic Regression": LogisticRegression(max_iter=1000, C=1.0,
                                               solver="lbfgs", random_state=42),
    "Random Forest":       RandomForestClassifier(n_estimators=200, max_depth=None,
                                                   min_samples_split=2, random_state=42),
    "Support Vector Machine": SVC(kernel="rbf", C=1.0, gamma="scale",
                                   probability=True, random_state=42),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
results = {}

for name, model in models.items():
    model.fit(X_train_s, y_train)
    y_pred = model.predict(X_test_s)
    y_prob = model.predict_proba(X_test_s)[:, 1]
    cv_scores = cross_val_score(model, X_train_s, y_train,
                                cv=cv, scoring="accuracy")
    results[name] = {
        "model":     model,
        "y_pred":    y_pred,
        "y_prob":    y_prob,
        "accuracy":  accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall":    recall_score(y_test, y_pred, zero_division=0),
        "f1":        f1_score(y_test, y_pred, zero_division=0),
        "roc_auc":   roc_auc_score(y_test, y_prob),
        "cv_scores": cv_scores,
        "cv_mean":   cv_scores.mean(),
        "cv_std":    cv_scores.std(),
    }
    print(f"  {name:28s}  acc={results[name]['accuracy']:.4f}"
          f"  auc={results[name]['roc_auc']:.4f}"
          f"  cv={results[name]['cv_mean']:.4f}±{results[name]['cv_std']:.4f}")

MODEL_NAMES = list(results.keys())


# ══════════════════════════════════════════════
#  3 · CHART A — Metrics radar / grouped bars
# ══════════════════════════════════════════════
METRICS = ["accuracy", "precision", "recall", "f1", "roc_auc"]
MLABELS = ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC"]

fig, ax = plt.subplots(figsize=(11, 5.5), facecolor=BG)
ax.set_facecolor(BG)

n_metrics = len(METRICS)
n_models  = len(MODEL_NAMES)
x         = np.arange(n_metrics)
total_w   = 0.72
bar_w     = total_w / n_models
offsets   = np.linspace(-(total_w - bar_w) / 2, (total_w - bar_w) / 2, n_models)

# Subtle baseline
ax.axhline(0.90, color=GRID_CLR, lw=1.2, zorder=0)
ax.axhline(0.95, color=GRID_CLR, lw=1.2, zorder=0)
ax.axhline(1.00, color=GRID_CLR, lw=1.2, zorder=0)

for i, name in enumerate(MODEL_NAMES):
    vals = [results[name][m] for m in METRICS]
    bars = ax.bar(
        x + offsets[i], vals, bar_w - 0.04,
        color=PALETTE[name], alpha=0.92,
        label=name, zorder=3,
        linewidth=0,
    )
    for bar, v in zip(bars, vals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.003,
            f"{v:.3f}",
            ha="center", va="bottom",
            fontsize=7.8, fontweight="bold",
            color=PALETTE[name],
        )

ax.set_xticks(x)
ax.set_xticklabels(MLABELS, fontsize=11)
ax.set_ylim(0.88, 1.025)
ax.set_yticks([0.88, 0.90, 0.92, 0.94, 0.96, 0.98, 1.00])
ax.set_yticklabels([f"{v:.0%}" for v in [0.88, 0.90, 0.92, 0.94, 0.96, 0.98, 1.00]], fontsize=9)
ax.set_ylabel("Score", fontsize=10, labelpad=8)
ax.set_title("Performance Metrics — All Models", fontsize=14,
             fontweight="bold", pad=14, color=NAVY)
ax.legend(loc="lower right", framealpha=0.9, fontsize=9,
          edgecolor=GRID_CLR, facecolor=BG)
ax.spines["left"].set_color(GRID_CLR)
ax.spines["bottom"].set_color(GRID_CLR)
ax.set_axisbelow(True)

plt.tight_layout(pad=1.6)
plt.savefig("/home/claude/fig_metrics.png", dpi=160, bbox_inches="tight", facecolor=BG)
plt.close()
print("  fig_metrics.png saved")


# ══════════════════════════════════════════════
#  4 · CHART B — ROC curves
# ══════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(6.5, 6), facecolor=BG)
ax.set_facecolor(BG)

# Diagonal
ax.plot([0, 1], [0, 1], color=GRID_CLR, lw=1.4, linestyle="--", zorder=1, label="Random (AUC = 0.5000)")

for name in MODEL_NAMES:
    fpr, tpr, _ = roc_curve(y_test, results[name]["y_prob"])
    auc_val      = results[name]["roc_auc"]
    ax.plot(fpr, tpr, color=PALETTE[name], lw=2.4,
            label=f"{name}  (AUC = {auc_val:.4f})", zorder=3)
    # shade
    ax.fill_between(fpr, tpr, alpha=0.06, color=PALETTE[name], zorder=2)

ax.set_xlabel("False Positive Rate", fontsize=10, labelpad=6)
ax.set_ylabel("True Positive Rate", fontsize=10, labelpad=6)
ax.set_title("ROC Curves", fontsize=14, fontweight="bold", pad=14, color=NAVY)
ax.legend(loc="lower right", framealpha=0.9, fontsize=8.5,
          edgecolor=GRID_CLR, facecolor=BG)
ax.set_xlim(-0.01, 1.01); ax.set_ylim(-0.01, 1.01)
ax.spines["left"].set_color(GRID_CLR)
ax.spines["bottom"].set_color(GRID_CLR)

plt.tight_layout(pad=1.6)
plt.savefig("/home/claude/fig_roc.png", dpi=160, bbox_inches="tight", facecolor=BG)
plt.close()
print("  fig_roc.png saved")


# ══════════════════════════════════════════════
#  5 · CHART C — Confusion matrices
# ══════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), facecolor=BG)
fig.patch.set_facecolor(BG)

for ax, name in zip(axes, MODEL_NAMES):
    cm   = confusion_matrix(y_test, results[name]["y_pred"])
    color = PALETTE[name]

    # Custom colormap from BG → model colour
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("custom", [BG, color])

    sns.heatmap(
        cm, annot=True, fmt="d", cmap=cmap, ax=ax,
        xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES,
        linewidths=1.5, linecolor=BG, cbar=False,
        annot_kws={"size": 16, "weight": "bold", "color": NAVY},
    )
    ax.set_title(name, fontsize=10.5, fontweight="bold", pad=10, color=color)
    ax.set_xlabel("Predicted", fontsize=9, color=TEXT_CLR)
    ax.set_ylabel("Actual",    fontsize=9, color=TEXT_CLR)
    ax.tick_params(colors=TEXT_CLR, labelsize=8.5)

fig.suptitle("Confusion Matrices", fontsize=14, fontweight="bold",
             color=NAVY, y=1.03)
plt.tight_layout(pad=1.8)
plt.savefig("/home/claude/fig_cm.png", dpi=160, bbox_inches="tight", facecolor=BG)
plt.close()
print("  fig_cm.png saved")


# ══════════════════════════════════════════════
#  6 · CHART D — CV distribution (violin)
# ══════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 4.8), facecolor=BG)
ax.set_facecolor(BG)

cv_list = [results[n]["cv_scores"] for n in MODEL_NAMES]
parts   = ax.violinplot(cv_list, positions=range(len(MODEL_NAMES)),
                        showmeans=False, showextrema=False, widths=0.55)

for i, (pc, name) in enumerate(zip(parts["bodies"], MODEL_NAMES)):
    pc.set_facecolor(PALETTE[name])
    pc.set_edgecolor(NAVY)
    pc.set_alpha(0.75)
    pc.set_linewidth(1.2)
    # scatter raw points
    jitter = np.random.default_rng(42).uniform(-0.06, 0.06, len(cv_list[i]))
    ax.scatter(np.full(len(cv_list[i]), i) + jitter, cv_list[i],
               color=PALETTE[name], s=45, zorder=5, edgecolors=NAVY, linewidths=0.6)
    # mean line
    mean_v = results[name]["cv_mean"]
    ax.hlines(mean_v, i - 0.22, i + 0.22,
              colors=NAVY, linewidths=2.2, zorder=6)
    ax.text(i, mean_v + 0.002, f"{mean_v:.4f}",
            ha="center", va="bottom", fontsize=9,
            fontweight="bold", color=NAVY)

ax.set_xticks(range(len(MODEL_NAMES)))
ax.set_xticklabels([n.replace(" ", "\n") for n in MODEL_NAMES], fontsize=9.5)
ax.set_ylabel("5-Fold CV Accuracy", fontsize=10, labelpad=6)
ax.set_title("Cross-Validation Accuracy Distribution", fontsize=14,
             fontweight="bold", pad=14, color=NAVY)
ax.set_ylim(0.90, 1.005)
ax.spines["left"].set_color(GRID_CLR)
ax.spines["bottom"].set_color(GRID_CLR)
ax.set_axisbelow(True)

plt.tight_layout(pad=1.6)
plt.savefig("/home/claude/fig_cv.png", dpi=160, bbox_inches="tight", facecolor=BG)
plt.close()
print("  fig_cv.png saved")


# ══════════════════════════════════════════════
#  7 · CHART E — Feature importances (RF)
# ══════════════════════════════════════════════
rf_model  = results["Random Forest"]["model"]
importances = pd.Series(rf_model.feature_importances_, index=X.columns)
top12      = importances.nlargest(12).sort_values()

fig, ax = plt.subplots(figsize=(7.5, 5.5), facecolor=BG)
ax.set_facecolor(BG)

colors_fi = [PALETTE["Random Forest"]] * 12
bars = ax.barh(top12.index, top12.values, color=colors_fi, alpha=0.85,
               edgecolor="none", height=0.65)
for bar, v in zip(bars, top12.values):
    ax.text(v + 0.001, bar.get_y() + bar.get_height() / 2,
            f"{v:.3f}", va="center", fontsize=8.5,
            color=PALETTE["Random Forest"], fontweight="bold")

ax.set_xlabel("Gini Importance", fontsize=10, labelpad=6)
ax.set_title("Random Forest — Top 12 Feature Importances",
             fontsize=13, fontweight="bold", pad=14, color=NAVY)
ax.spines["left"].set_color(GRID_CLR)
ax.spines["bottom"].set_color(GRID_CLR)
ax.tick_params(axis="y", labelsize=8.5)
ax.set_axisbelow(True)

plt.tight_layout(pad=1.6)
plt.savefig("/home/claude/fig_fi.png", dpi=160, bbox_inches="tight", facecolor=BG)
plt.close()
print("  fig_fi.png saved")

print("\nAll charts generated successfully.")

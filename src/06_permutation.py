"""
06_permutation.py — SAP §14.1 permutation test.

DEVIATION FROM SAP: 500 permutations (vs 1000 specified) with fixed C=1.0
(no inner CV) and single seed per permutation, to fit available compute window.
This is a supportive analysis; main inferential weight rests on the bootstrap and
DeLong tests in Table 3 which already established p < 0.001 for the primary contrast.
Documented in DEVIATIONS_LOG.md.
"""
import sys, json, time
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.analysis import select_features

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data" / "cohort_locked.parquet"
TABLES = REPO / "results" / "tables"
FIGS = REPO / "results" / "figures"


def fast_oof(X, y, seed=0, do_fs=True):
    """Single 5-fold CV with C=1.0 fixed. Returns OOF predictions."""
    n = len(y)
    oof = np.full(n, np.nan)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=int(seed) % (2**32 - 1))
    for tr, te in skf.split(X, y):
        Xtr, Xte = X[tr].copy(), X[te].copy()
        ytr, yte = y[tr], y[te]
        imp = SimpleImputer(strategy="median")
        Xtr = imp.fit_transform(Xtr); Xte = imp.transform(Xte)
        sc = StandardScaler()
        Xtr = sc.fit_transform(Xtr); Xte = sc.transform(Xte)
        if do_fs and Xtr.shape[1] > 1:
            mask, _ = select_features(Xtr, ytr)
            if mask.sum() == 0:
                oof[te] = ytr.mean(); continue
            Xtr = Xtr[:, mask]; Xte = Xte[:, mask]
        m = LogisticRegression(C=1.0, penalty="l2", solver="liblinear", max_iter=1000)
        m.fit(Xtr, ytr)
        oof[te] = m.predict_proba(Xte)[:, 1]
    return oof


def main(n_perm=500):
    df = pd.read_parquet(DATA)
    y = df["binary_label"].to_numpy()
    feat_cols = [c for c in df.columns if c.startswith("ROI1_") or c.startswith("ROI2_")]
    X_m2 = df[["RF_EI"]].to_numpy(dtype=float)
    X_m7 = df[feat_cols].to_numpy(dtype=float)

    print(f"Permutation test: {n_perm} permutations, fast mode (C=1.0 fixed)")
    print(f"n = {len(y)}, ROI features = {len(feat_cols)}")

    # Observed ΔAUC (primary endpoint)
    oof_m2_obs = fast_oof(X_m2, y, seed=42, do_fs=False)
    oof_m7_obs = fast_oof(X_m7, y, seed=42, do_fs=True)
    auc_m2_obs = roc_auc_score(y, oof_m2_obs)
    auc_m7_obs = roc_auc_score(y, oof_m7_obs)
    obs_delta = auc_m7_obs - auc_m2_obs
    print(f"\nObserved AUC: Model 2 = {auc_m2_obs:.3f}, Model 7 = {auc_m7_obs:.3f}, ΔAUC = {obs_delta:+.3f}")

    # Permutation null
    print(f"\nRunning {n_perm} permutations ...")
    rng = np.random.default_rng(20251102)
    null_deltas = []
    t0 = time.time()
    for i in range(n_perm):
        y_perm = rng.permutation(y)
        oof_m2_p = fast_oof(X_m2, y_perm, seed=i, do_fs=False)
        oof_m7_p = fast_oof(X_m7, y_perm, seed=i, do_fs=True)
        d = roc_auc_score(y_perm, oof_m7_p) - roc_auc_score(y_perm, oof_m2_p)
        null_deltas.append(d)
        if (i + 1) % 50 == 0:
            elapsed = time.time() - t0
            eta = elapsed / (i + 1) * (n_perm - i - 1)
            print(f"  {i+1}/{n_perm} done in {elapsed:.0f}s, ETA {eta:.0f}s")

    null_deltas = np.array(null_deltas)
    p_emp = (1 + np.sum(null_deltas >= obs_delta)) / (1 + n_perm)
    print(f"\nObserved ΔAUC = {obs_delta:+.3f}")
    print(f"Null distribution: mean = {null_deltas.mean():+.4f}, SD = {null_deltas.std():.4f}")
    print(f"Empirical p-value (one-sided): {p_emp:.4f} ({np.sum(null_deltas >= obs_delta)} of {n_perm} ≥ observed)")

    # Save results
    perm_df = pd.DataFrame({
        "Statistic": ["Observed ΔAUC", "Null mean", "Null SD",
                      "Permutations ≥ observed", "Empirical p (one-sided)", "n permutations"],
        "Value": [f"{obs_delta:+.4f}", f"{null_deltas.mean():+.4f}", f"{null_deltas.std():.4f}",
                  int(np.sum(null_deltas >= obs_delta)), f"{p_emp:.4f}", n_perm]
    })
    perm_df.to_csv(TABLES / "Suppl_Table_8_permutation.csv", index=False)

    # Figure
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(null_deltas, bins=40, color="#90A4AE", edgecolor="black", alpha=0.85)
    ax.axvline(obs_delta, color="#C62828", linewidth=2.5, label=f"Observed ΔAUC = {obs_delta:+.3f}")
    ax.axvline(0, color="black", linestyle=":", linewidth=0.8)
    ax.set_xlabel("ΔAUC (Model 7 − Model 2) under label permutation", fontsize=11)
    ax.set_ylabel("Frequency", fontsize=11)
    ax.set_title(f"Permutation null distribution — primary contrast (n_perm = {n_perm})", fontsize=12)
    ax.legend(loc="upper left", fontsize=10)
    ax.text(0.98, 0.95, f"Empirical p = {p_emp:.4f}", transform=ax.transAxes,
            ha="right", va="top", fontsize=11, bbox=dict(boxstyle="round", fc="white", ec="grey"))
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig(FIGS / "Suppl_Figure_3_permutation_null.png", dpi=200, bbox_inches="tight")
    plt.savefig(FIGS / "Suppl_Figure_3_permutation_null.pdf", bbox_inches="tight")
    plt.close()
    print(f"\nFigure written: {FIGS / 'Suppl_Figure_3_permutation_null.png'}")


if __name__ == "__main__":
    n_perm = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    main(n_perm=n_perm)

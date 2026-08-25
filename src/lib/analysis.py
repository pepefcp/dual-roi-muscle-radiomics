"""
Analysis library — SAP v1.1 §8–13 implementation.

Contains:
  - within-fold feature selection (correlation + FDR + fallback)
  - L2 logistic regression with inner-CV hyperparameter tuning
  - participant-level out-of-fold prediction aggregation
  - participant-level BCa bootstrap
  - DeLong test
  - paired bootstrap on AUC differences
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import (roc_auc_score, average_precision_score, brier_score_loss,
                             accuracy_score, f1_score, recall_score, confusion_matrix)
from sklearn.model_selection import StratifiedKFold
from statsmodels.stats.multitest import multipletests


def _safe_seed(seed) -> int:
    """sklearn RandomState requires seed in [0, 2^32-1]."""
    return int(seed) % (2**32 - 1)


# =====================================================================
# Feature selection (SAP §11)
# =====================================================================

def correlation_filter(X: np.ndarray, importance: np.ndarray, threshold: float = 0.95) -> np.ndarray:
    """Iteratively remove features with |r| > threshold, keeping the more important one.
    Returns boolean mask of features to keep."""
    n_feat = X.shape[1]
    keep = np.ones(n_feat, dtype=bool)
    if n_feat < 2:
        return keep
    # Order features by descending importance
    order = np.argsort(-importance)
    # Compute correlation matrix once on training data
    with np.errstate(invalid="ignore", divide="ignore"):
        corr = np.corrcoef(X.T)
    corr = np.nan_to_num(corr, nan=0.0)
    for i, idx_i in enumerate(order):
        if not keep[idx_i]:
            continue
        for j in order[i+1:]:
            if keep[j] and abs(corr[idx_i, j]) > threshold:
                keep[j] = False
    return keep


def fdr_filter(X: np.ndarray, y: np.ndarray, q: float = 0.10, k_fallback: int = 10):
    """Mann-Whitney U + Benjamini-Hochberg FDR. If <k_fallback survive, use top-k by p-value.
    Returns (mask, fallback_triggered, p_values)."""
    n_feat = X.shape[1]
    pvals = np.ones(n_feat)
    for j in range(n_feat):
        a = X[y == 0, j]; b = X[y == 1, j]
        a = a[~np.isnan(a)]; b = b[~np.isnan(b)]
        if len(a) < 2 or len(b) < 2 or np.allclose(a.std(), 0) and np.allclose(b.std(), 0):
            continue
        try:
            _, pvals[j] = stats.mannwhitneyu(a, b, alternative="two-sided")
        except ValueError:
            pvals[j] = 1.0
    rejected, _, _, _ = multipletests(pvals, alpha=q, method="fdr_bh")
    fallback = False
    if rejected.sum() < k_fallback:
        # Fallback: top-k by p-value
        top_idx = np.argsort(pvals)[:k_fallback]
        mask = np.zeros(n_feat, dtype=bool)
        mask[top_idx] = True
        fallback = True
    else:
        mask = rejected
    return mask, fallback, pvals


def select_features(X_train: np.ndarray, y_train: np.ndarray,
                    corr_threshold: float = 0.95, fdr_q: float = 0.10, k_fallback: int = 10):
    """Full SAP §11 selection pipeline. Returns boolean mask + diagnostics."""
    if X_train.shape[1] == 0:
        return np.zeros(0, dtype=bool), {"fallback": False, "n_after_corr": 0, "n_final": 0}
    # Step 1: correlation filter (importance = |t-stat| approx via signal/noise)
    sd = np.nan_to_num(X_train.std(axis=0), nan=1e-9)
    sd[sd == 0] = 1e-9
    mu_diff = np.nan_to_num(X_train[y_train == 1].mean(axis=0) - X_train[y_train == 0].mean(axis=0))
    importance = np.abs(mu_diff) / sd
    keep1 = correlation_filter(X_train, importance, corr_threshold)
    # Step 2: FDR filter on surviving features
    if keep1.sum() == 0:
        return keep1, {"fallback": True, "n_after_corr": 0, "n_final": 0}
    X_red = X_train[:, keep1]
    keep2_local, fallback, _ = fdr_filter(X_red, y_train, fdr_q, k_fallback)
    # Map back to original indices
    keep_final = np.zeros_like(keep1)
    idx_kept = np.where(keep1)[0]
    keep_final[idx_kept[keep2_local]] = True
    return keep_final, {"fallback": fallback, "n_after_corr": int(keep1.sum()),
                        "n_final": int(keep_final.sum())}


# =====================================================================
# Model fitting + CV (SAP §8, §9)
# =====================================================================

def fit_logreg_with_inner_cv(X_train, y_train, n_inner=5, c_grid=(0.01, 0.1, 1.0, 10.0, 100.0), seed=0):
    """L2 logistic regression with inner CV for C selection."""
    if X_train.shape[1] == 0:
        return None
    seed = _safe_seed(seed)
    inner = StratifiedKFold(n_splits=min(n_inner, np.bincount(y_train).min()), shuffle=True, random_state=seed)
    best_c, best_auc = c_grid[0], -np.inf
    for c in c_grid:
        aucs = []
        for tr, va in inner.split(X_train, y_train):
            try:
                m = LogisticRegression(C=c, penalty="l2", solver="liblinear", max_iter=2000)
                m.fit(X_train[tr], y_train[tr])
                proba = m.predict_proba(X_train[va])[:, 1]
                if len(np.unique(y_train[va])) > 1:
                    aucs.append(roc_auc_score(y_train[va], proba))
            except Exception:
                aucs.append(0.5)
        if aucs:
            mean_auc = np.mean(aucs)
            if mean_auc > best_auc:
                best_auc, best_c = mean_auc, c
    final = LogisticRegression(C=best_c, penalty="l2", solver="liblinear", max_iter=2000)
    final.fit(X_train, y_train)
    return final


def run_cv(X: np.ndarray, y: np.ndarray, seeds=(0,), n_folds=5,
           classifier="logreg", do_feature_selection=True,
           corr_threshold=0.95, fdr_q=0.10, k_fallback=10):
    """Stratified K-fold CV at participant level over multiple seeds.
    Returns dict with:
      - 'oof_preds': dict[seed] -> array of length n with predicted probabilities for held-out
      - 'fold_aucs': list of AUCs (one per fold per seed)
      - 'n_fallback_folds': int
      - 'n_features_per_fold': list
    """
    n = X.shape[0]
    oof_by_seed = {}
    fold_aucs = []
    n_fallback = 0
    n_features = []

    for seed in seeds:
        seed_safe = _safe_seed(seed)
        oof = np.full(n, np.nan)
        skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed_safe)
        for tr, te in skf.split(X, y):
            Xtr, Xte = X[tr].copy(), X[te].copy()
            ytr, yte = y[tr], y[te]
            # Imputation (median)
            imp = SimpleImputer(strategy="median")
            Xtr = imp.fit_transform(Xtr)
            Xte = imp.transform(Xte)
            # Standardisation
            sc = StandardScaler()
            Xtr = sc.fit_transform(Xtr)
            Xte = sc.transform(Xte)
            # Feature selection
            if do_feature_selection and Xtr.shape[1] > 1:
                mask, diag = select_features(Xtr, ytr, corr_threshold, fdr_q, k_fallback)
                if diag["fallback"]:
                    n_fallback += 1
                if mask.sum() == 0:
                    # Edge case: no features. Predict prior probability.
                    proba = np.full(len(yte), ytr.mean())
                    oof[te] = proba
                    n_features.append(0)
                    continue
                Xtr = Xtr[:, mask]
                Xte = Xte[:, mask]
                n_features.append(int(mask.sum()))
            else:
                n_features.append(Xtr.shape[1])
            # Model
            if classifier == "logreg":
                model = fit_logreg_with_inner_cv(Xtr, ytr, seed=seed_safe)
            elif classifier == "svm":
                model = SVC(C=1.0, kernel="linear", probability=True, random_state=seed_safe)
                model.fit(Xtr, ytr)
            elif classifier == "rf":
                model = RandomForestClassifier(n_estimators=100, random_state=seed_safe, n_jobs=1)
                model.fit(Xtr, ytr)
            else:
                raise ValueError(f"Unknown classifier: {classifier}")
            if model is None:
                proba = np.full(len(yte), ytr.mean())
            else:
                proba = model.predict_proba(Xte)[:, 1]
            oof[te] = proba
            if len(np.unique(yte)) > 1:
                fold_aucs.append(roc_auc_score(yte, proba))
        oof_by_seed[seed_safe] = oof
    return {
        "oof_by_seed": oof_by_seed,
        "fold_aucs": fold_aucs,
        "n_fallback_folds": n_fallback,
        "n_features_per_fold": n_features,
    }


def aggregate_oof(oof_by_seed: dict) -> np.ndarray:
    """Average per-participant predictions across seeds → one prediction per participant."""
    arr = np.vstack(list(oof_by_seed.values()))
    return np.nanmean(arr, axis=0)


# =====================================================================
# Metrics (SAP §12)
# =====================================================================

def compute_metrics(y_true: np.ndarray, y_proba: np.ndarray, threshold=0.5) -> dict:
    """Discrimination + calibration metrics from participant-level predictions."""
    out = {}
    out["AUC_ROC"] = roc_auc_score(y_true, y_proba)
    out["AUC_PR"] = average_precision_score(y_true, y_proba)
    out["Brier"] = brier_score_loss(y_true, y_proba)
    y_pred = (y_proba >= threshold).astype(int)
    out["Accuracy"] = accuracy_score(y_true, y_pred)
    out["Sensitivity"] = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
    out["Specificity"] = recall_score(y_true, y_pred, pos_label=0, zero_division=0)
    out["F1"] = f1_score(y_true, y_pred, zero_division=0)
    # Calibration slope/intercept (logistic regression of y on logit(p))
    eps = 1e-6
    p = np.clip(y_proba, eps, 1 - eps)
    logit = np.log(p / (1 - p))
    try:
        m = LogisticRegression(C=1e6, solver="liblinear", max_iter=1000)  # essentially unregularised
        m.fit(logit.reshape(-1, 1), y_true)
        out["Cal_intercept"] = float(m.intercept_[0])
        out["Cal_slope"] = float(m.coef_[0, 0])
    except Exception:
        out["Cal_intercept"] = np.nan
        out["Cal_slope"] = np.nan
    return out


# =====================================================================
# BCa bootstrap (SAP §12, §13)
# =====================================================================

def bca_bootstrap_auc(y_true: np.ndarray, y_proba: np.ndarray, n_boot=2000, seed=0):
    """Participant-level BCa bootstrap CI for AUC."""
    rng = np.random.default_rng(seed)
    n = len(y_true)
    boot_aucs = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        if len(np.unique(y_true[idx])) < 2:
            continue
        boot_aucs.append(roc_auc_score(y_true[idx], y_proba[idx]))
    boot_aucs = np.array(boot_aucs)
    obs = roc_auc_score(y_true, y_proba)
    # Bias correction
    z0 = stats.norm.ppf(np.mean(boot_aucs < obs))
    if not np.isfinite(z0):
        z0 = 0.0
    # Acceleration via jackknife
    jack = []
    for i in range(n):
        mask = np.ones(n, dtype=bool); mask[i] = False
        if len(np.unique(y_true[mask])) < 2:
            continue
        jack.append(roc_auc_score(y_true[mask], y_proba[mask]))
    jack = np.array(jack)
    jack_mean = jack.mean()
    num = np.sum((jack_mean - jack) ** 3)
    den = 6 * (np.sum((jack_mean - jack) ** 2) ** 1.5)
    a = num / den if den > 0 else 0.0
    z_lo, z_hi = stats.norm.ppf(0.025), stats.norm.ppf(0.975)
    alpha_lo = stats.norm.cdf(z0 + (z0 + z_lo) / (1 - a * (z0 + z_lo)))
    alpha_hi = stats.norm.cdf(z0 + (z0 + z_hi) / (1 - a * (z0 + z_hi)))
    lo = np.quantile(boot_aucs, alpha_lo)
    hi = np.quantile(boot_aucs, alpha_hi)
    return obs, lo, hi


def paired_bootstrap_delta_auc(y_true: np.ndarray, p_a: np.ndarray, p_b: np.ndarray,
                                n_boot=2000, seed=0):
    """Paired participant-level bootstrap on ΔAUC = AUC(a) − AUC(b). BCa CI + p-value."""
    rng = np.random.default_rng(seed)
    n = len(y_true)
    obs_delta = roc_auc_score(y_true, p_a) - roc_auc_score(y_true, p_b)
    boot_deltas = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        if len(np.unique(y_true[idx])) < 2:
            continue
        d = roc_auc_score(y_true[idx], p_a[idx]) - roc_auc_score(y_true[idx], p_b[idx])
        boot_deltas.append(d)
    boot_deltas = np.array(boot_deltas)
    # BCa
    z0 = stats.norm.ppf(np.mean(boot_deltas < obs_delta))
    if not np.isfinite(z0): z0 = 0.0
    jack = []
    for i in range(n):
        mask = np.ones(n, dtype=bool); mask[i] = False
        if len(np.unique(y_true[mask])) < 2: continue
        jack.append(roc_auc_score(y_true[mask], p_a[mask]) - roc_auc_score(y_true[mask], p_b[mask]))
    jack = np.array(jack)
    num = np.sum((jack.mean() - jack) ** 3)
    den = 6 * (np.sum((jack.mean() - jack) ** 2) ** 1.5)
    a = num / den if den > 0 else 0.0
    z_lo, z_hi = stats.norm.ppf(0.025), stats.norm.ppf(0.975)
    alpha_lo = stats.norm.cdf(z0 + (z0 + z_lo) / (1 - a * (z0 + z_lo)))
    alpha_hi = stats.norm.cdf(z0 + (z0 + z_hi) / (1 - a * (z0 + z_hi)))
    lo, hi = np.quantile(boot_deltas, alpha_lo), np.quantile(boot_deltas, alpha_hi)
    # Two-sided bootstrap p-value
    p_two = 2 * min(np.mean(boot_deltas <= 0), np.mean(boot_deltas >= 0))
    return obs_delta, lo, hi, p_two


def delong_test(y_true: np.ndarray, p_a: np.ndarray, p_b: np.ndarray) -> float:
    """Two-sided DeLong test for paired AUC comparison. Returns p-value."""
    # Implementation following Sun & Xu (2014).
    y = y_true.astype(int)
    pos = (y == 1); neg = (y == 0)
    m, n = pos.sum(), neg.sum()
    def midrank(x):
        order = np.argsort(x)
        ranks = np.empty(len(x))
        i = 0
        while i < len(x):
            j = i
            while j + 1 < len(x) and x[order[j + 1]] == x[order[i]]:
                j += 1
            r = (i + j) / 2 + 1
            for k in range(i, j + 1):
                ranks[order[k]] = r
            i = j + 1
        return ranks
    def auc_var(p):
        tx = midrank(p[pos]); ty = midrank(p[neg])
        tz = midrank(p)
        auc = (tz[pos].sum() - m * (m + 1) / 2) / (m * n)
        v01 = (tz[pos] - tx) / n
        v10 = 1 - (tz[neg] - ty) / m
        sx = np.var(v01, ddof=1) / m
        sy = np.var(v10, ddof=1) / n
        return auc, v01, v10, sx + sy
    aa, va01, va10, _ = auc_var(p_a)
    bb, vb01, vb10, _ = auc_var(p_b)
    cov_pos = np.cov(va01, vb01, ddof=1)[0, 1] / m
    cov_neg = np.cov(va10, vb10, ddof=1)[0, 1] / n
    var_a = np.var(va01, ddof=1)/m + np.var(va10, ddof=1)/n
    var_b = np.var(vb01, ddof=1)/m + np.var(vb10, ddof=1)/n
    var_diff = var_a + var_b - 2 * (cov_pos + cov_neg)
    if var_diff <= 0:
        return 1.0
    z = (aa - bb) / np.sqrt(var_diff)
    return 2 * (1 - stats.norm.cdf(abs(z)))

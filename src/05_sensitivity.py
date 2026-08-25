"""
05_sensitivity.py — SAP §14 sensitivity analyses.

Runs:
  14.3 SMA-excluded (n=52)
  14.4a Age as covariate
  14.4b Age + thickness as covariates
  14.5 Classifier sensitivity (SVM, Random Forest)
"""
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.analysis import run_cv, aggregate_oof, compute_metrics, bca_bootstrap_auc, paired_bootstrap_delta_auc

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data" / "cohort_locked.parquet"
SEEDS_FILE = REPO / "seeds.json"
TABLES = REPO / "results" / "tables"


def get_dual_roi_features(df):
    return [c for c in df.columns if c.startswith("ROI1_") or c.startswith("ROI2_")]


def run_one(name, df, X, y, seeds, classifier, do_fs, n_boot=1000):
    out = run_cv(X, y, seeds=seeds, n_folds=5, classifier=classifier, do_feature_selection=do_fs)
    oof = aggregate_oof(out["oof_by_seed"])
    auc, lo, hi = bca_bootstrap_auc(y, oof, n_boot=n_boot, seed=42)
    m = compute_metrics(y, oof)
    print(f"  {name}: AUC = {auc:.3f} [BCa {lo:.3f}–{hi:.3f}], Brier = {m['Brier']:.3f}")
    return {"name": name, "AUC": auc, "lo": lo, "hi": hi, "oof": oof,
            "Brier": m["Brier"], "F1": m["F1"], "Sensitivity": m["Sensitivity"], "Specificity": m["Specificity"]}


def main(n_seeds=25, n_boot=1000):
    df = pd.read_parquet(DATA)
    seeds = json.loads(SEEDS_FILE.read_text())["seeds"][:n_seeds]
    print(f"Sensitivity analyses with {len(seeds)} seeds, {n_boot} bootstrap resamples\n")

    feat_cols = get_dual_roi_features(df)

    # ====================== 14.3 SMA-excluded ======================
    print("=" * 70)
    print("14.3 — SMA-EXCLUDED SENSITIVITY (n = 52)")
    print("=" * 70)
    df_no_sma = df[~df["subgroup"].isin(["SMA-I", "SMA-II", "SMA-III"])].reset_index(drop=True)
    print(f"  n = {len(df_no_sma)} (healthy {(df_no_sma['binary_label']==0).sum()}, "
          f"pathological {(df_no_sma['binary_label']==1).sum()})\n")
    y2 = df_no_sma["binary_label"].to_numpy()
    res = {}
    res["M2"] = run_one("Model 2 (EI continuous)", df_no_sma,
                        df_no_sma[["RF_EI"]].to_numpy(dtype=float), y2, seeds, "logreg", False, n_boot)
    res["M7"] = run_one("Model 7 (Dual-ROI radiomics)", df_no_sma,
                        df_no_sma[feat_cols].to_numpy(dtype=float), y2, seeds, "logreg", True, n_boot)
    d, lo, hi, p = paired_bootstrap_delta_auc(y2, res["M7"]["oof"], res["M2"]["oof"], n_boot=n_boot, seed=42)
    print(f"\n  >>> Contrast Model 7 vs Model 2 (SMA-excluded): ΔAUC = {d:+.3f} [{lo:+.3f}, {hi:+.3f}], p = {p:.4f}")
    sma_excluded_row = {"Analysis": "14.3 SMA-excluded (n=52)",
                        "Model 2 AUC": f"{res['M2']['AUC']:.3f} [{res['M2']['lo']:.3f}–{res['M2']['hi']:.3f}]",
                        "Model 7 AUC": f"{res['M7']['AUC']:.3f} [{res['M7']['lo']:.3f}–{res['M7']['hi']:.3f}]",
                        "ΔAUC": f"{d:+.3f}", "ΔAUC 95% CI": f"{lo:+.3f} to {hi:+.3f}", "p": f"{p:.4f}"}

    # ====================== 14.4a Age as covariate ======================
    print("\n" + "=" * 70)
    print("14.4a — AGE AS COVARIATE")
    print("=" * 70)
    y = df["binary_label"].to_numpy()
    X_age_only = df[["EDAD"]].to_numpy(dtype=float)
    X_m2_age = df[["RF_EI", "EDAD"]].to_numpy(dtype=float)
    X_m7_age = np.hstack([df[feat_cols].to_numpy(dtype=float), df[["EDAD"]].to_numpy(dtype=float)])
    res2 = {}
    res2["age_only"] = run_one("Age only", df, X_age_only, y, seeds, "logreg", False, n_boot)
    res2["M2_age"]   = run_one("Model 2 + age", df, X_m2_age, y, seeds, "logreg", False, n_boot)
    res2["M7_age"]   = run_one("Model 7 + age", df, X_m7_age, y, seeds, "logreg", True, n_boot)
    d, lo, hi, p = paired_bootstrap_delta_auc(y, res2["M7_age"]["oof"], res2["M2_age"]["oof"], n_boot=n_boot, seed=42)
    print(f"\n  >>> Contrast Model 7+age vs Model 2+age: ΔAUC = {d:+.3f} [{lo:+.3f}, {hi:+.3f}], p = {p:.4f}")
    age_cov_row = {"Analysis": "14.4a Age as covariate",
                   "Model 2 AUC": f"{res2['M2_age']['AUC']:.3f} [{res2['M2_age']['lo']:.3f}–{res2['M2_age']['hi']:.3f}]",
                   "Model 7 AUC": f"{res2['M7_age']['AUC']:.3f} [{res2['M7_age']['lo']:.3f}–{res2['M7_age']['hi']:.3f}]",
                   "ΔAUC": f"{d:+.3f}", "ΔAUC 95% CI": f"{lo:+.3f} to {hi:+.3f}", "p": f"{p:.4f}"}

    # ====================== 14.5 Classifier sensitivity ======================
    print("\n" + "=" * 70)
    print("14.5 — CLASSIFIER SENSITIVITY (Model 7)")
    print("=" * 70)
    X_m7 = df[feat_cols].to_numpy(dtype=float)
    res3 = {}
    res3["logreg"] = run_one("Model 7 — L2 logistic regression (primary)", df, X_m7, y, seeds, "logreg", True, n_boot)
    res3["svm"]    = run_one("Model 7 — Linear SVM", df, X_m7, y, seeds, "svm", True, n_boot)
    res3["rf"]     = run_one("Model 7 — Random Forest", df, X_m7, y, seeds, "rf", True, n_boot)

    classifier_rows = []
    for k, label in [("logreg", "L2 logistic regression (primary)"),
                     ("svm", "Linear SVM"),
                     ("rf", "Random Forest")]:
        r = res3[k]
        classifier_rows.append({"Classifier": label,
                                "AUC": f"{r['AUC']:.3f}",
                                "AUC 95% CI": f"{r['lo']:.3f}–{r['hi']:.3f}",
                                "Brier": f"{r['Brier']:.3f}",
                                "F1": f"{r['F1']:.3f}"})

    # Save tables
    df_sma = pd.DataFrame([sma_excluded_row])
    df_age = pd.DataFrame([age_cov_row])
    df_clf = pd.DataFrame(classifier_rows)
    df_sma.to_csv(TABLES / "Suppl_Table_3_SMA_excluded.csv", index=False)
    df_age.to_csv(TABLES / "Suppl_Table_4_age_covariate.csv", index=False)
    df_clf.to_csv(TABLES / "Suppl_Table_5_classifier_sensitivity.csv", index=False)

    print("\n=== Sensitivity summary ===")
    print(df_sma.to_string(index=False))
    print()
    print(df_age.to_string(index=False))
    print()
    print(df_clf.to_string(index=False))


if __name__ == "__main__":
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    main(n_seeds=n_seeds)

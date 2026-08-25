"""
03_primary_analysis.py — SAP §13 primary endpoint and contrasts.

Runs Models 1–7 with stratified 5-fold CV across 50 seeds.
Computes participant-level aggregated OOF predictions, BCa CIs,
primary contrast (Model 7 vs Model 2), and secondary contrast (Model 4 vs Model 2).
"""
import sys, json, time
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.analysis import (run_cv, aggregate_oof, compute_metrics,
                          bca_bootstrap_auc, paired_bootstrap_delta_auc, delong_test)

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data" / "cohort_locked.parquet"
SEEDS_FILE = REPO / "seeds.json"
TABLES = REPO / "results" / "tables"
FIGS = REPO / "results" / "figures"
LOGS = REPO / "results" / "logs"


def get_feature_groups(df: pd.DataFrame):
    """Identify ROI1/ROI2 feature columns and split first-order vs texture."""
    roi1 = [c for c in df.columns if c.startswith("ROI1_")]
    roi2 = [c for c in df.columns if c.startswith("ROI2_")]
    # Heuristic for first-order: columns that look like global intensity stats.
    # The QUIBIM IBSI feature names often include words like "MEAN", "MEDIAN",
    # "PERCENTILE", "STANDARD", "ENERGY", "ENTROPY (first-order)", "MIN", "MAX",
    # "RANGE", "VARIANCE", "SKEWNESS", "KURTOSIS", "UNIFORMITY", "ROOT MEAN"...
    first_order_kw = ["MEAN", "MEDIAN", "PERCENT", "STANDARD", "RANGE", "MIN", "MAX",
                      "VARIANC", "SKEW", "KURTOS", "UNIFORM", "RMS", "ROOT", "TOTAL ENERGY",
                      "INTERQUART", "MAD", "MEDIA"]
    def is_first_order(name: str) -> bool:
        n = name.upper()
        # Texture matrices contain explicit prefixes — exclude these
        if any(k in n for k in ["GLCM", "GLRLM", "GLSZM", "GLDM", "NGTDM", "RUN", "ZONE",
                                 "DEPENDENCE", "NEIGHBORHOOD", "NEIGHBOURHOOD", "COOC"]):
            return False
        return any(k in n for k in first_order_kw)
    roi1_fo = [c for c in roi1 if is_first_order(c)]
    roi2_fo = [c for c in roi2 if is_first_order(c)]
    roi1_tex = [c for c in roi1 if c not in roi1_fo]
    roi2_tex = [c for c in roi2 if c not in roi2_fo]
    return {
        "ROI1_first_order": roi1_fo, "ROI1_texture": roi1_tex, "ROI1_all": roi1,
        "ROI2_first_order": roi2_fo, "ROI2_texture": roi2_tex, "ROI2_all": roi2,
    }


def model_inputs(df, feat_groups, model_id):
    """Return X array for each of Models 1–7, per SAP §7."""
    if model_id == 1:
        # Heckmatt-analogue grade as ordinal (treat as continuous for logreg)
        return df[["Heckmatt_grade"]].to_numpy(dtype=float)
    if model_id == 2:
        return df[["RF_EI"]].to_numpy(dtype=float)
    if model_id == 3:
        cols = feat_groups["ROI1_first_order"] + feat_groups["ROI2_first_order"]
        return df[cols].to_numpy(dtype=float), cols
    if model_id == 4:
        cols = feat_groups["ROI1_texture"] + feat_groups["ROI2_texture"]
        return df[cols].to_numpy(dtype=float), cols
    if model_id == 5:
        cols = feat_groups["ROI1_all"]
        return df[cols].to_numpy(dtype=float), cols
    if model_id == 6:
        cols = feat_groups["ROI2_all"]
        return df[cols].to_numpy(dtype=float), cols
    if model_id == 7:
        cols = feat_groups["ROI1_all"] + feat_groups["ROI2_all"]
        return df[cols].to_numpy(dtype=float), cols


def main(n_seeds=None, n_boot=2000):
    df = pd.read_parquet(DATA)
    y = df["binary_label"].to_numpy()
    print(f"n = {len(df)}, healthy = {(y==0).sum()}, pathological = {(y==1).sum()}")

    seeds = json.loads(SEEDS_FILE.read_text())["seeds"]
    if n_seeds is not None:
        seeds = seeds[:n_seeds]
    print(f"Using {len(seeds)} seeds, 5-fold CV, paired bootstrap n_boot = {n_boot}")

    feat_groups = get_feature_groups(df)
    print(f"\nFeature groups:")
    for k, v in feat_groups.items():
        print(f"  {k}: {len(v)}")

    model_specs = {
        1: ("Heckmatt-analogue grade (ordinal)", False),
        2: ("RF mean echointensity (continuous)", False),
        3: ("First-order radiomics (ROI1+ROI2)", True),
        4: ("Texture-only radiomics (ROI1+ROI2)", True),
        5: ("ROI1 full radiomics", True),
        6: ("ROI2 full radiomics", True),
        7: ("Dual-ROI full radiomics", True),
    }

    all_oof_preds = {}     # model_id -> aggregated OOF predictions (one per participant)
    all_metrics = {}       # model_id -> metrics dict
    all_bca = {}           # model_id -> (auc, lo, hi)
    all_diagnostics = {}   # model_id -> {fallback_folds, n_features}

    for mid, (name, do_fs) in model_specs.items():
        t0 = time.time()
        print(f"\n[Model {mid}] {name}")
        result = model_inputs(df, feat_groups, mid)
        if isinstance(result, tuple):
            X, _ = result
        else:
            X = result
        print(f"  X shape: {X.shape}")
        out = run_cv(X, y, seeds=seeds, n_folds=5, classifier="logreg",
                     do_feature_selection=do_fs)
        oof_agg = aggregate_oof(out["oof_by_seed"])
        all_oof_preds[mid] = oof_agg
        # Metrics on aggregated OOF
        metrics = compute_metrics(y, oof_agg)
        all_metrics[mid] = metrics
        # BCa CI
        auc, lo, hi = bca_bootstrap_auc(y, oof_agg, n_boot=n_boot, seed=42)
        all_bca[mid] = (auc, lo, hi)
        all_diagnostics[mid] = {
            "fallback_folds": out["n_fallback_folds"],
            "mean_n_features": float(np.mean(out["n_features_per_fold"])) if out["n_features_per_fold"] else 0,
            "fold_auc_mean": float(np.mean(out["fold_aucs"])),
            "fold_auc_sd": float(np.std(out["fold_aucs"])),
        }
        print(f"  AUC (aggregated OOF): {auc:.3f} [BCa 95% CI: {lo:.3f}–{hi:.3f}]")
        print(f"  Fold AUC mean ± SD:   {all_diagnostics[mid]['fold_auc_mean']:.3f} ± {all_diagnostics[mid]['fold_auc_sd']:.3f}")
        print(f"  Brier: {metrics['Brier']:.3f} | Cal slope: {metrics['Cal_slope']:.2f}")
        print(f"  Fallback folds: {all_diagnostics[mid]['fallback_folds']} | mean n_features: {all_diagnostics[mid]['mean_n_features']:.1f}")
        print(f"  Elapsed: {time.time()-t0:.1f}s")

    # === Table 2 — Primary endpoint model hierarchy ===
    rows = []
    for mid, (name, _) in model_specs.items():
        auc, lo, hi = all_bca[mid]
        m = all_metrics[mid]
        d = all_diagnostics[mid]
        rows.append({
            "Model": mid,
            "Specification": name,
            "AUC-ROC": f"{auc:.3f}",
            "AUC 95% CI (BCa)": f"{lo:.3f}–{hi:.3f}",
            "Fold AUC mean ± SD": f"{d['fold_auc_mean']:.3f} ± {d['fold_auc_sd']:.3f}",
            "AUC-PR": f"{m['AUC_PR']:.3f}",
            "Accuracy": f"{m['Accuracy']:.3f}",
            "Sensitivity": f"{m['Sensitivity']:.3f}",
            "Specificity": f"{m['Specificity']:.3f}",
            "F1": f"{m['F1']:.3f}",
            "Brier": f"{m['Brier']:.3f}",
            "Cal slope": f"{m['Cal_slope']:.2f}",
        })
    table2 = pd.DataFrame(rows)
    table2.to_csv(TABLES / "Table_2_primary_endpoint.csv", index=False)
    print("\n=== TABLE 2 — Primary endpoint ===")
    print(table2.to_string(index=False))

    # === Table 3 — Contrasts ===
    print("\n=== TABLE 3 — Primary and secondary contrasts ===")
    contrast_rows = []
    for label, m_a, m_b in [("Primary: Model 7 vs Model 2", 7, 2),
                             ("Secondary: Model 4 vs Model 2", 4, 2),
                             ("Supportive: Model 7 vs Model 1", 7, 1),
                             ("Supportive: Model 7 vs Model 5", 7, 5),
                             ("Supportive: Model 7 vs Model 6", 7, 6)]:
        d, lo, hi, p_boot = paired_bootstrap_delta_auc(y, all_oof_preds[m_a], all_oof_preds[m_b],
                                                       n_boot=n_boot, seed=42)
        try:
            p_dl = delong_test(y, all_oof_preds[m_a], all_oof_preds[m_b])
        except Exception as e:
            p_dl = np.nan
        contrast_rows.append({
            "Contrast": label,
            "ΔAUC": f"{d:+.3f}",
            "BCa 95% CI": f"{lo:+.3f} to {hi:+.3f}",
            "Bootstrap p (two-sided)": f"{p_boot:.4f}",
            "DeLong p (two-sided)": f"{p_dl:.4f}" if not np.isnan(p_dl) else "—",
            "CI excludes 0": "yes" if (lo > 0 or hi < 0) else "no",
        })
    table3 = pd.DataFrame(contrast_rows)
    table3.to_csv(TABLES / "Table_3_contrasts.csv", index=False)
    print(table3.to_string(index=False))

    primary = table3.iloc[0]
    print(f"\n>>> PRIMARY CONTRAST RESULT <<<")
    print(f"    Model 7 (Dual-ROI radiomics) vs Model 2 (mean echointensity)")
    print(f"    ΔAUC = {primary['ΔAUC']}, 95% BCa CI = {primary['BCa 95% CI']}")
    print(f"    Bootstrap p = {primary['Bootstrap p (two-sided)']}, DeLong p = {primary['DeLong p (two-sided)']}")
    if primary['CI excludes 0'] == "yes" and float(primary['ΔAUC']) > 0:
        print(f"    → H₀ REJECTED. Dual-ROI radiomics outperforms scalar echointensity.")
    elif primary['CI excludes 0'] == "yes" and float(primary['ΔAUC']) < 0:
        print(f"    → H₀ REJECTED in opposite direction (radiomics is WORSE).")
    else:
        print(f"    → H₀ NOT REJECTED. CI includes 0.")

    # === Figure 3 — AUC by model with CIs ===
    fig, ax = plt.subplots(figsize=(10, 5.5))
    model_ids = list(model_specs.keys())
    aucs = [all_bca[m][0] for m in model_ids]
    los = [all_bca[m][0] - all_bca[m][1] for m in model_ids]
    his = [all_bca[m][2] - all_bca[m][0] for m in model_ids]
    labels = [f"Model {m}\n{model_specs[m][0].split(' (')[0]}" for m in model_ids]
    colors = ["#90A4AE", "#90A4AE", "#FFA726", "#FB8C00", "#42A5F5", "#26A69A", "#7E57C2"]
    bars = ax.bar(range(len(model_ids)), aucs, yerr=[los, his], capsize=6,
                   color=colors, edgecolor="black", linewidth=0.7,
                   error_kw=dict(ecolor="black", lw=1.2))
    ax.set_xticks(range(len(model_ids)))
    ax.set_xticklabels(labels, fontsize=9, rotation=0)
    ax.set_ylabel("AUC-ROC (BCa 95% CI)", fontsize=11)
    ax.set_ylim(0.4, 1.05)
    ax.axhline(0.5, color="grey", linestyle=":", linewidth=0.8)
    ax.text(0.02, 0.51, "chance", fontsize=8, color="grey", transform=ax.get_yaxis_transform())
    ax.set_title("Primary endpoint — Healthy vs Pathological (n = 62)", fontsize=12)
    # Annotate primary contrast
    ax.annotate("", xy=(6, aucs[6] + his[6] + 0.04), xytext=(1, aucs[6] + his[6] + 0.04),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1))
    ax.text(3.5, aucs[6] + his[6] + 0.06, f"Primary contrast: ΔAUC = {primary['ΔAUC']}, p = {primary['Bootstrap p (two-sided)']}",
            ha="center", fontsize=9, fontweight="bold")
    for i, v in enumerate(aucs):
        ax.text(i, v + 0.005, f"{v:.2f}", ha="center", va="bottom", fontsize=9)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig(FIGS / "Figure_3_primary_endpoint.png", dpi=200, bbox_inches="tight")
    plt.savefig(FIGS / "Figure_3_primary_endpoint.pdf", bbox_inches="tight")
    plt.close()
    print(f"\nFigure 3 written: {FIGS / 'Figure_3_primary_endpoint.png'}")

    # Save predictions for downstream use
    pred_df = pd.DataFrame({f"M{m}": all_oof_preds[m] for m in model_ids})
    pred_df["y"] = y
    pred_df["participant_id"] = df["participant_id"].values
    pred_df["Heckmatt_grade"] = df["Heckmatt_grade"].values
    pred_df["subgroup"] = df["subgroup"].values
    pred_df.to_parquet(REPO / "data" / "primary_oof_predictions.parquet", index=False)

    # Diagnostics log
    with open(LOGS / "03_primary_analysis.log", "w") as f:
        f.write("Primary analysis diagnostics\n" + "=" * 60 + "\n\n")
        f.write(f"n = {len(y)}, seeds = {len(seeds)}, n_boot = {n_boot}\n\n")
        for mid, d in all_diagnostics.items():
            f.write(f"Model {mid} ({model_specs[mid][0]}):\n")
            f.write(f"  fold AUC mean ± SD: {d['fold_auc_mean']:.3f} ± {d['fold_auc_sd']:.3f}\n")
            f.write(f"  mean n_features per fold: {d['mean_n_features']:.1f}\n")
            f.write(f"  fallback folds: {d['fallback_folds']}\n\n")


if __name__ == "__main__":
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(n_seeds=n_seeds)

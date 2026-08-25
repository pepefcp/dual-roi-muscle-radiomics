"""
04_grade2_analysis.py — SAP §15 exploratory subgroup analysis.

Models 2-7 restricted to participants in Heckmatt-analogue Grade 2.
"""
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.analysis import run_cv, aggregate_oof, compute_metrics, bca_bootstrap_auc, paired_bootstrap_delta_auc

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data" / "cohort_locked.parquet"
SEEDS_FILE = REPO / "seeds.json"
TABLES = REPO / "results" / "tables"
FIGS = REPO / "results" / "figures"
LOGS = REPO / "results" / "logs"


def get_feature_groups(df: pd.DataFrame):
    roi1 = [c for c in df.columns if c.startswith("ROI1_")]
    roi2 = [c for c in df.columns if c.startswith("ROI2_")]
    roi1_fo = [c for c in roi1 if c.startswith("ROI1_Primerorden-")]
    roi2_fo = [c for c in roi2 if c.startswith("ROI2_Primerorden-")]
    roi1_tex = [c for c in roi1 if not c.startswith("ROI1_Primerorden-")]
    roi2_tex = [c for c in roi2 if not c.startswith("ROI2_Primerorden-")]
    return {
        "ROI1_first_order": roi1_fo, "ROI1_texture": roi1_tex, "ROI1_all": roi1,
        "ROI2_first_order": roi2_fo, "ROI2_texture": roi2_tex, "ROI2_all": roi2,
    }


def model_inputs(df, feat_groups, model_id):
    if model_id == 2:
        return df[["RF_EI"]].to_numpy(dtype=float), False
    if model_id == 3:
        cols = feat_groups["ROI1_first_order"] + feat_groups["ROI2_first_order"]
        return df[cols].to_numpy(dtype=float), True
    if model_id == 4:
        cols = feat_groups["ROI1_texture"] + feat_groups["ROI2_texture"]
        return df[cols].to_numpy(dtype=float), True
    if model_id == 5:
        cols = feat_groups["ROI1_all"]
        return df[cols].to_numpy(dtype=float), True
    if model_id == 6:
        cols = feat_groups["ROI2_all"]
        return df[cols].to_numpy(dtype=float), True
    if model_id == 7:
        cols = feat_groups["ROI1_all"] + feat_groups["ROI2_all"]
        return df[cols].to_numpy(dtype=float), True


def main(n_seeds=None, n_boot=2000):
    df = pd.read_parquet(DATA)
    g2 = df[df["Heckmatt_grade"] == 2].copy().reset_index(drop=True)
    n_h = (g2["binary_label"] == 0).sum()
    n_p = (g2["binary_label"] == 1).sum()
    print(f"Grade 2 subgroup: n = {len(g2)}  (healthy = {n_h}, pathological = {n_p})")

    # SAP §15 inclusion threshold: ≥6 per class
    if n_h < 6 or n_p < 6:
        print(f"\n⚠️  SAP §15 threshold NOT met (need ≥6 per class).")
        print("    Reporting descriptive statistics only — no AUC, no permutation p.")
        # Descriptive: medians per group for all features
        feats = [c for c in g2.columns if c.startswith("ROI1_") or c.startswith("ROI2_")]
        desc = g2.groupby("binary_label")[feats].agg(["median", lambda x: x.quantile(0.25), lambda x: x.quantile(0.75)])
        desc.to_csv(TABLES / "Table_4_grade2_descriptive_only.csv")
        return
    print(f"✓ SAP §15 inclusion threshold met. Running full inferential analysis.\n")

    seeds = json.loads(SEEDS_FILE.read_text())["seeds"]
    if n_seeds is not None:
        seeds = seeds[:n_seeds]

    feat_groups = get_feature_groups(g2)
    y = g2["binary_label"].to_numpy()

    model_specs = {
        2: "RF mean echointensity (continuous)",
        3: "First-order radiomics (ROI1+ROI2)",
        4: "Texture-only radiomics (ROI1+ROI2)",
        5: "ROI1 full radiomics",
        6: "ROI2 full radiomics",
        7: "Dual-ROI full radiomics",
    }
    all_oof = {}
    all_metrics = {}
    all_bca = {}
    for mid, name in model_specs.items():
        X, do_fs = model_inputs(g2, feat_groups, mid)
        out = run_cv(X, y, seeds=seeds, n_folds=5, classifier="logreg", do_feature_selection=do_fs)
        oof = aggregate_oof(out["oof_by_seed"])
        all_oof[mid] = oof
        m = compute_metrics(y, oof)
        all_metrics[mid] = m
        auc, lo, hi = bca_bootstrap_auc(y, oof, n_boot=n_boot, seed=42)
        all_bca[mid] = (auc, lo, hi)
        print(f"  Model {mid} {name}: AUC = {auc:.3f} [BCa {lo:.3f}–{hi:.3f}], "
              f"Brier = {m['Brier']:.3f}")

    # Table 4
    rows = []
    for mid, name in model_specs.items():
        auc, lo, hi = all_bca[mid]
        m = all_metrics[mid]
        rows.append({
            "Model": mid,
            "Specification": name,
            "n total": len(g2),
            "n healthy": n_h,
            "n pathological": n_p,
            "AUC-ROC": f"{auc:.3f}",
            "AUC 95% CI (BCa)": f"{lo:.3f}–{hi:.3f}",
            "Accuracy": f"{m['Accuracy']:.3f}",
            "Sensitivity": f"{m['Sensitivity']:.3f}",
            "Specificity": f"{m['Specificity']:.3f}",
            "Brier": f"{m['Brier']:.3f}",
        })
    table4 = pd.DataFrame(rows)
    table4.to_csv(TABLES / "Table_4_grade2_subgroup.csv", index=False)
    print("\n=== TABLE 4 — Heckmatt-analogue Grade 2 exploratory subgroup ===")
    print(table4.to_string(index=False))

    # Contrast within Grade 2: Model 7 vs Model 2
    print("\n=== Grade 2 contrasts ===")
    contrast_rows = []
    for label, m_a, m_b in [("Grade 2: Model 7 vs Model 2", 7, 2),
                             ("Grade 2: Model 4 vs Model 2", 4, 2)]:
        d, lo, hi, p = paired_bootstrap_delta_auc(y, all_oof[m_a], all_oof[m_b],
                                                   n_boot=n_boot, seed=42)
        contrast_rows.append({
            "Contrast": label,
            "ΔAUC": f"{d:+.3f}",
            "BCa 95% CI": f"{lo:+.3f} to {hi:+.3f}",
            "Bootstrap p (two-sided)": f"{p:.4f}",
            "CI excludes 0": "yes" if (lo > 0 or hi < 0) else "no",
        })
    contrast_df = pd.DataFrame(contrast_rows)
    contrast_df.to_csv(TABLES / "Table_4b_grade2_contrasts.csv", index=False)
    print(contrast_df.to_string(index=False))

    # Figure 4
    fig, ax = plt.subplots(figsize=(9, 5.5))
    mids = list(model_specs.keys())
    aucs = [all_bca[m][0] for m in mids]
    los = [all_bca[m][0] - all_bca[m][1] for m in mids]
    his = [all_bca[m][2] - all_bca[m][0] for m in mids]
    labels = [f"Model {m}\n{model_specs[m].split(' (')[0]}" for m in mids]
    colors = ["#90A4AE", "#FFA726", "#FB8C00", "#42A5F5", "#26A69A", "#7E57C2"]
    ax.bar(range(len(mids)), aucs, yerr=[los, his], capsize=6, color=colors,
            edgecolor="black", linewidth=0.7, error_kw=dict(ecolor="black", lw=1.2))
    ax.set_xticks(range(len(mids)))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("AUC-ROC (BCa 95% CI)", fontsize=11)
    ax.set_ylim(0.0, 1.05)
    ax.axhline(0.5, color="grey", linestyle=":", linewidth=0.8)
    ax.text(0.02, 0.51, "chance", fontsize=8, color="grey", transform=ax.get_yaxis_transform())
    ax.set_title(f"Heckmatt-analogue Grade 2 subgroup — exploratory analysis (n = {len(g2)}, "
                 f"{n_h} healthy vs {n_p} pathological)", fontsize=11)
    for i, v in enumerate(aucs):
        ax.text(i, v + 0.015, f"{v:.2f}", ha="center", va="bottom", fontsize=9)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig(FIGS / "Figure_4_grade2_subgroup.png", dpi=200, bbox_inches="tight")
    plt.savefig(FIGS / "Figure_4_grade2_subgroup.pdf", bbox_inches="tight")
    plt.close()
    print(f"\nFigure 4 written: {FIGS / 'Figure_4_grade2_subgroup.png'}")

    # Save Grade 2 OOF predictions
    pred = pd.DataFrame({f"M{m}": all_oof[m] for m in mids})
    pred["y"] = y
    pred["participant_id"] = g2["participant_id"].values
    pred.to_parquet(REPO / "data" / "grade2_oof_predictions.parquet", index=False)


if __name__ == "__main__":
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(n_seeds=n_seeds)

"""11_duplicate_pair_sensitivity.py — primary contrast with one member of each
duplicated-image pair removed (n = 60). See DEVIATIONS_LOG.md, "Sensitivity analysis
excluding the duplicated-image pairs". Participant indices refer to the row order of
data/cohort_locked.parquet (0-based): rows 54 and 55 are the second member of the
SMA-II pair (rows 18, 54: platform images IMG-0002-00008B(II)/00009B(II)) and of the control pair
(rows 30, 55: IMG-0001-000012A/000013A) identified in Correction 4. Executed on the corrected matrix."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
from lib.analysis import run_cv, aggregate_oof, bca_bootstrap_auc, paired_bootstrap_delta_auc

DROP = [54, 55]
df = pd.read_parquet(REPO / "data" / "cohort_locked.parquet").drop(index=DROP).reset_index(drop=True)
y = df["binary_label"].to_numpy()
seeds = json.load(open(REPO / "seeds.json"))["seeds"]
feat = [c for c in df.columns if c.startswith(("ROI1_", "ROI2_"))]
print("n", len(df), "healthy", int((y == 0).sum()), "pathological", int((y == 1).sum()))
o2 = aggregate_oof(run_cv(df[["RF_EI"]].to_numpy(float), y, seeds=seeds, n_folds=5, classifier="logreg", do_feature_selection=False)["oof_by_seed"])
o7 = aggregate_oof(run_cv(df[feat].to_numpy(float), y, seeds=seeds, n_folds=5, classifier="logreg", do_feature_selection=True)["oof_by_seed"])
a2 = bca_bootstrap_auc(y, o2, n_boot=2000, seed=42); a7 = bca_bootstrap_auc(y, o7, n_boot=2000, seed=42)
d, lo, hi, p = paired_bootstrap_delta_auc(y, o7, o2, n_boot=2000, seed=42)
row = {"Analysis": "Duplicated-image pairs excluded (n = 60)",
       "Model 2 AUC (95% BCa CI)": f"{a2[0]:.3f} ({a2[1]:.3f}–{a2[2]:.3f})",
       "Model 7 AUC (95% BCa CI)": f"{a7[0]:.3f} ({a7[1]:.3f}–{a7[2]:.3f})",
       "dAUC": f"{d:+.3f}", "95% BCa CI": f"{lo:+.3f} to {hi:+.3f}", "Bootstrap p": f"{p:.4f}"}
print(row)
out = REPO / "results" / "tables"; out.mkdir(parents=True, exist_ok=True)
pd.DataFrame([row]).to_csv(out / "Suppl_Table_6_duplicate_pairs_excluded.csv", index=False)

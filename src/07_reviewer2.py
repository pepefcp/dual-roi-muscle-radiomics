"""
07_reviewer2.py — analisis adicionales pedidos en la revision de Muscle & Nerve.

R2-01  variables retenidas por fold, frecuencia de seleccion en la CV repetida,
       y variabilidad del rendimiento entre semillas.
R2-02  calibracion (Brier, intercepto, pendiente, curva) y sensibilidad,
       especificidad, VPP y VPN en un umbral de decision predefinido.

No modifica el SAP: reutiliza run_cv y la cohorte bloqueada tal cual.
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from lib.analysis import run_cv, select_features
from sklearn.metrics import roc_auc_score, confusion_matrix
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "results" / "tables"
OUT.mkdir(parents=True, exist_ok=True)
THRESHOLD = 0.50            # umbral de decision predefinido
SEEDS = list(range(20))     # 20 semillas x 5 folds = 100 particiones

d = pd.read_parquet(REPO / "data" / "cohort_locked.parquet")
y = (d["subgroup"] != "healthy").astype(int).values
feat = [c for c in d.columns if c.startswith(("ROI1_", "ROI2_"))]
MODELS = {
    "Model 5 — ROI1":    [c for c in feat if c.startswith("ROI1_")],
    "Model 6 — ROI2":    [c for c in feat if c.startswith("ROI2_")],
    "Model 7 — Dual-ROI": feat,
}
print("n=%d  prevalencia=%.3f  variables disponibles=%d\n" % (len(d), y.mean(), len(feat)))

rows, cal_rows, freq_rows = [], [], []
for name, cols in MODELS.items():
    X = d[cols].apply(pd.to_numeric, errors="coerce").values
    res = run_cv(X, y, seeds=SEEDS, n_folds=5)

    # --- R2-01: estabilidad ---
    nf = np.array(res["n_features_per_fold"])
    seed_auc = []
    for s, oof in res["oof_by_seed"].items():
        ok = ~np.isnan(oof)
        seed_auc.append(roc_auc_score(y[ok], oof[ok]))
    seed_auc = np.array(seed_auc)

    # frecuencia de seleccion de cada variable sobre las 100 particiones
    counts = np.zeros(len(cols))
    for s in SEEDS:
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=s)
        for tr, _ in skf.split(X, y):
            Xtr = StandardScaler().fit_transform(
                  SimpleImputer(strategy="median").fit_transform(X[tr]))
            keep, _ = select_features(Xtr, y[tr])
            counts[keep] += 1
    freq = counts / (len(SEEDS) * 5)
    for c, f in sorted(zip(cols, freq), key=lambda t: -t[1])[:15]:
        freq_rows.append({"Model": name, "Feature": c, "Selection frequency": round(f, 3)})

    # --- R2-02: calibracion y metricas al umbral ---
    oof = np.nanmean(np.vstack(list(res["oof_by_seed"].values())), axis=0)
    ok = ~np.isnan(oof)
    p, yy = np.clip(oof[ok], 1e-6, 1-1e-6), y[ok]
    brier = np.mean((p - yy) ** 2)
    import statsmodels.api as sm
    logit = np.log(p / (1 - p))
    gl = sm.GLM(yy, sm.add_constant(logit), family=sm.families.Binomial()).fit()
    cal_int, cal_slope = gl.params[0], gl.params[1]
    pred = (p >= THRESHOLD).astype(int)
    tn, fp, fn, tp = confusion_matrix(yy, pred).ravel()
    sens, spec = tp/(tp+fn), tn/(tn+fp)
    ppv = tp/(tp+fp) if (tp+fp) else float("nan")
    npv = tn/(tn+fn) if (tn+fn) else float("nan")

    rows.append({"Model": name,
        "AUC (mean over seeds)": round(seed_auc.mean(), 3),
        "AUC SD across seeds": round(seed_auc.std(ddof=1), 3),
        "AUC min–max": "%.3f–%.3f" % (seed_auc.min(), seed_auc.max()),
        "Features/fold mean ± SD": "%.1f ± %.1f" % (nf.mean(), nf.std(ddof=1)),
        "Features/fold min–max": "%d–%d" % (nf.min(), nf.max()),
        "Fallback folds n (%)": "%d (%.0f%%)" % (res["n_fallback_folds"],
                                100*res["n_fallback_folds"]/len(nf))})
    cal_rows.append({"Model": name, "Brier": round(brier, 3),
        "Calibration intercept": round(cal_int, 3), "Calibration slope": round(cal_slope, 3),
        "Threshold": THRESHOLD, "Sensitivity": round(sens, 3), "Specificity": round(spec, 3),
        "PPV": round(ppv, 3), "NPV": round(npv, 3),
        "TP": tp, "FP": fp, "FN": fn, "TN": tn})

    # puntos de la curva de calibracion (5 grupos por decil de riesgo)
    q = pd.qcut(p, 5, labels=False, duplicates="drop")
    cal = pd.DataFrame({"bin": q, "pred": p, "obs": yy}).groupby("bin").agg(
        mean_predicted=("pred", "mean"), observed=("obs", "mean"), n=("obs", "size"))
    cal.insert(0, "Model", name)
    cal.to_csv(OUT / ("Suppl_calibration_curve_%s.csv" % name.split()[1]), index=False)
    print("%-22s AUC %.3f ± %.3f | vars/fold %.1f ± %.1f | Brier %.3f | pendiente %.2f"
          % (name, seed_auc.mean(), seed_auc.std(ddof=1), nf.mean(), nf.std(ddof=1), brier, cal_slope))

pd.DataFrame(rows).to_csv(OUT / "Suppl_Table_R2a_stability.csv", index=False)
pd.DataFrame(cal_rows).to_csv(OUT / "Suppl_Table_R2b_calibration_thresholds.csv", index=False)
pd.DataFrame(freq_rows).to_csv(OUT / "Suppl_Table_R2c_selection_frequency.csv", index=False)
print("\n=== R2-01 estabilidad ===");   print(pd.DataFrame(rows).to_string(index=False))
print("\n=== R2-02 calibracion y umbral ==="); print(pd.DataFrame(cal_rows).to_string(index=False))

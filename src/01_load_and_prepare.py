"""
01_load_and_prepare.py — SAP v1.1 §4 cohort assembly.

Loads raw multi-sheet Excel, applies the SAP-locked cohort cleaning record,
adds binary label, computes Heckmatt-analogue grade per SAP §6.2 thresholds,
and writes the SAP-locked feature matrix.

Output: data/cohort_locked.parquet (one row per participant)

NOTE ON SANITIZATION (public release):
    The cohort cleaning record originally referenced participants by their
    medical record numbers (NHC) and surnames. For this public release,
    real NHC values and surnames have been replaced by anonymous identifiers
    (PARTICIPANT_001 ... PARTICIPANT_006) that map to the same rows in the
    locked dataset. The cleaning logic and resulting cohort are unchanged.
    Researchers wishing to reproduce the analysis on the original dataset
    should request access to de-identified data from the corresponding author.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import warnings
warnings.simplefilter("ignore")

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "data" / "raw_data.xlsx"
OUT = REPO / "data" / "cohort_locked.parquet"

ROI1_SHEETS = {
    "sanos ROI 1":               ("healthy",     "healthy"),
    "AME I ROI 1":               ("neurogenic",  "SMA-I"),
    "AME II ROI 1":              ("neurogenic",  "SMA-II"),
    "AME III ROI 1":             ("neurogenic",  "SMA-III"),
    "NEUROGENICOS LA PAZ ROI 1": ("neurogenic",  "neurogenic-LaPaz"),
    "MIÓGENOS LA PAZ ROI1":      ("myogenic",    "myogenic-LaPaz"),
}
ROI2_SHEETS = {
    "sanos ROI 2":               "healthy",
    "AME I ROI2":                "SMA-I",
    "AME II ROI 2":              "SMA-II",
    "AME III ROI 2 ":            "SMA-III",
    "NEUROGENICOS LA PAZ ROI 2": "neurogenic-LaPaz",
    "MIOGENOS LA PAZ ROI2":      "myogenic-LaPaz",
}

# Conventional ultrasound vars (NOT radiomics) — kept as separate clinical comparators
US_VARS = ["RF AREA ", "RF ECOINTENSIDAD", "RF DE", "RF MODE", "RF MINIMO",
           "RF MAXIMO", "RF PERIM", "RF Grosor (MM)", "VI AREA ", "VI ECOINTENSIDAD"]

# Demographic / non-feature columns to discard from feature matrix
NON_FEATURE = set([
    "IMAGEN", "NHC", "Apellido", "APELLIDOS", "Nombre",
    "EDAD", "edad", "genero", "peso",
    "DE ESPAÑA 2010", "<p3>p97", "Altura",
    "DE ESPAÑA 2010.1", "<p3>p97.1", "BMI",
    "DE ESPAÑA 2010.2", "<p3>p97.2",
    "deambulación a lo largo de su vida, ",
    "deambulación a lo largo de su vida. ",
    "Perdida de deambulación", "etiologia de enfermedad de base",
    "Longitud femur", "NUMERO DE COPIAS SMN2",
])


def heckmatt_analogue(ei: float) -> float:
    """SAP §6.2 — locked thresholds. Do not modify."""
    if pd.isna(ei): return np.nan
    if ei < 40: return 1
    if ei < 55: return 2
    if ei < 72: return 3
    return 4


def load_roi(sheets: dict, roi_label: str) -> pd.DataFrame:
    parts = []
    for sheet, info in sheets.items():
        df = pd.read_excel(RAW, sheet_name=sheet)
        df = df.rename(columns={"edad": "EDAD", "APELLIDOS": "Apellido"})
        if isinstance(info, tuple):
            df["group"], df["subgroup"] = info
        else:
            df["subgroup"] = info
        df["source_sheet"] = sheet
        parts.append(df)
    return pd.concat(parts, ignore_index=True)


def apply_cohort_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """SAP §4 — locked cleaning record. Do not modify.

    NOTE (public release): real NHC/names have been replaced with anonymous
    identifiers (PARTICIPANT_001 ... PARTICIPANT_006) for GDPR compliance.
    The cleaning logic and resulting cohort are unchanged.
    """
    log = []

    # 1. Remove PARTICIPANT_001 from healthy (kept in neurogenic)
    m = (df["NHC"] == "PARTICIPANT_001") & (df["subgroup"] == "healthy")
    log.append(f"Removed {m.sum()} row: PARTICIPANT_001 from healthy (kept in neurogenic)")
    df = df.loc[~m].copy()

    # 2. Remove PARTICIPANT_002 (myogenic, age 0.41)
    m = (df["NHC"] == "PARTICIPANT_002")
    log.append(f"Removed {m.sum()} row: PARTICIPANT_002 (age 0.41 y, outside paediatric scope)")
    df = df.loc[~m].copy()

    # 3. Update PARTICIPANT_003 age 0.99 → 2.0
    m = (df["NHC"] == "PARTICIPANT_003")
    log.append(f"Updated {m.sum()} age: PARTICIPANT_003 → 2.0 y")
    df.loc[m, "EDAD"] = 2.0

    # 4. Remove PARTICIPANT_004 (age 22.3, adult)
    m = (df["NHC"] == "PARTICIPANT_004")
    log.append(f"Removed {m.sum()} row: PARTICIPANT_004 (age 22.3 y, adult)")
    df = df.loc[~m].copy()

    # 5. Update PARTICIPANT_005 (date artifact 120.25 → 8.0)
    m = (df["Nombre"] == "PARTICIPANT_005") & (df["EDAD"] > 100)
    log.append(f"Updated {m.sum()} age: PARTICIPANT_005 → 8.0 y")
    df.loc[m, "EDAD"] = 8.0

    # 6. Update PARTICIPANT_006 (date artifact 120.25 → 9.0)
    m = (df["Nombre"] == "PARTICIPANT_006") & (df["EDAD"] > 100)
    log.append(f"Updated {m.sum()} age: PARTICIPANT_006 → 9.0 y")
    df.loc[m, "EDAD"] = 9.0

    # 7. AME age filter: 2 ≤ age < 17
    sma = df["subgroup"].isin(["SMA-I", "SMA-II", "SMA-III"])
    age_ok = (df["EDAD"] >= 2) & (df["EDAD"] < 17)
    drop = sma & ~age_ok
    log.append(f"Removed {drop.sum()} AMEs outside age [2, 17)")
    df = df.loc[~drop].copy().reset_index(drop=True)

    return df, log


def main():
    print("Loading ROI1 sheets ...")
    roi1 = load_roi(ROI1_SHEETS, "ROI1")
    print(f"  {len(roi1)} rows")

    print("Loading ROI2 sheets ...")
    roi2 = load_roi(ROI2_SHEETS, "ROI2")
    print(f"  {len(roi2)} rows")

    print("\nApplying cohort cleaning (SAP §4) ...")
    roi1_clean, log = apply_cohort_cleaning(roi1)
    for line in log: print(f"  • {line}")
    print(f"  Final ROI1 cohort: n = {len(roi1_clean)}")

    roi2_clean, _ = apply_cohort_cleaning(roi2)
    print(f"  Final ROI2 cohort: n = {len(roi2_clean)}")

    assert len(roi1_clean) == len(roi2_clean), "ROI1 and ROI2 cohort sizes diverge!"

    # Sort both by NHC + subgroup so they align row-by-row
    def make_key(df):
        return df["NHC"].fillna(-1).astype(str) + "|" + df["Apellido"].astype(str) + "|" + df["subgroup"]

    roi1_clean["_key"] = make_key(roi1_clean)
    roi2_clean["_key"] = make_key(roi2_clean)
    roi1_clean = roi1_clean.sort_values("_key").reset_index(drop=True)
    roi2_clean = roi2_clean.sort_values("_key").reset_index(drop=True)
    assert (roi1_clean["_key"] == roi2_clean["_key"]).all(), "ROI1/ROI2 keys do not align"

    # Identify radiomic feature columns (intersection of ROI1 and ROI2)
    nonfeat = NON_FEATURE | set(US_VARS) | {"group", "subgroup", "source_sheet", "_key"}
    roi1_feats = [c for c in roi1_clean.columns if c not in nonfeat]
    roi2_feats = [c for c in roi2_clean.columns if c not in nonfeat]
    common = [c for c in roi1_feats if c in roi2_feats]
    # Restrict to numeric columns only
    common = [c for c in common
              if pd.api.types.is_numeric_dtype(roi1_clean[c]) and pd.api.types.is_numeric_dtype(roi2_clean[c])]
    # CRITICAL FILTER (SAP §6.3 conformance): keep ONLY IBSI radiomic features.
    # The Excel includes contaminating columns (clinical motor scales like Hammersmith/RULM,
    # morphometric measurements like VI*/GROSOR*, clinical events). These are NOT IBSI features
    # and would leak disease severity directly into the classifier.
    IBSI_PREFIXES = ("GLCM-", "GLDM-", "GLRLM-", "GLSZM-", "NGTDM-", "Primerorden-")
    SHAPE_PREFIX = "Forma-"  # Shape features — excluded per SAP §6.3 from primary analysis
    common = [str(c) for c in common]
    ibsi_only = [c for c in common if any(c.startswith(p) for p in IBSI_PREFIXES)]
    shape_excluded = [c for c in common if c.startswith(SHAPE_PREFIX)]
    print(f"\nRadiomic feature columns:")
    print(f"  ROI1 raw: {len(roi1_feats)}, ROI2 raw: {len(roi2_feats)}, common numeric: {len(common)}")
    print(f"  IBSI features kept: {len(ibsi_only)}")
    print(f"  Shape features excluded (per SAP §6.3): {len(shape_excluded)}")
    print(f"  Contaminating non-IBSI columns excluded: {len(common) - len(ibsi_only) - len(shape_excluded)}")
    common = ibsi_only

    # Build feature matrix with suffixes
    f_roi1 = roi1_clean[common].add_prefix("ROI1_")
    f_roi2 = roi2_clean[common].add_prefix("ROI2_")

    # Clinical / label / comparator columns (from ROI1 sheet, canonical)
    clin = roi1_clean[["NHC", "Apellido", "Nombre", "EDAD", "genero", "group", "subgroup"] + US_VARS].copy()
    clin["binary_label"] = (clin["group"] != "healthy").astype(int)
    clin["Heckmatt_grade"] = clin["RF ECOINTENSIDAD"].apply(heckmatt_analogue)
    clin = clin.rename(columns={"RF ECOINTENSIDAD": "RF_EI", "RF Grosor (MM)": "RF_thickness_mm"})
    clin.insert(0, "participant_id", range(1, len(clin) + 1))

    # Combine
    cohort = pd.concat([clin, f_roi1, f_roi2], axis=1)

    # Force string dtype for object columns to avoid mixed-type parquet issues
    for col in ["Apellido", "Nombre", "group", "subgroup"]:
        cohort[col] = cohort[col].astype(str)
    print(f"\nFinal cohort matrix: {cohort.shape[0]} participants × {cohort.shape[1]} columns "
          f"(of which {f_roi1.shape[1] + f_roi2.shape[1]} are radiomic features)")

    # Sanity checks against SAP §4
    n_total = len(cohort)
    n_healthy = (cohort["binary_label"] == 0).sum()
    n_path    = (cohort["binary_label"] == 1).sum()
    sub_counts = cohort["subgroup"].value_counts().to_dict()

    print(f"\nSAP §4 conformance check:")
    print(f"  Total n: {n_total} (expected 62) — {'OK' if n_total == 62 else 'MISMATCH'}")
    print(f"  Healthy: {n_healthy} (expected 23) — {'OK' if n_healthy == 23 else 'MISMATCH'}")
    print(f"  Pathological: {n_path} (expected 39) — {'OK' if n_path == 39 else 'MISMATCH'}")
    expected_sub = {"healthy": 23, "myogenic-LaPaz": 16, "neurogenic-LaPaz": 13,
                    "SMA-I": 3, "SMA-II": 4, "SMA-III": 3}
    for sg, exp in expected_sub.items():
        got = sub_counts.get(sg, 0)
        print(f"  {sg:18s}: {got} (expected {exp}) — {'OK' if got == exp else 'MISMATCH'}")

    # Write parquet (compact, fast)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cohort.to_parquet(OUT, index=False)
    print(f"\nWritten: {OUT}")

    # Save loading log
    log_path = REPO / "results" / "logs" / "01_load_and_prepare.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        f.write("01_load_and_prepare.py — SAP §4 cohort assembly\n")
        f.write("=" * 60 + "\n\n")
        for line in log:
            f.write(f"  - {line}\n")
        f.write(f"\nFinal n = {n_total}; healthy {n_healthy}; pathological {n_path}\n")
        f.write(f"Subgroup counts: {sub_counts}\n")
        f.write(f"Radiomic features: {f_roi1.shape[1] + f_roi2.shape[1]} ({f_roi1.shape[1]} ROI1 + {f_roi2.shape[1]} ROI2)\n")
    print(f"Log written: {log_path}")


if __name__ == "__main__":
    main()

"""12_covariate_pairing_correction.py — apply Correction 4 (DEVIATIONS_LOG.md) to the locked matrix.

Five myopathic images had been uploaded to the extraction platform under each other's
participant codes, as a closed cycle: the row labelled with each code below holds the
image (and therefore the radiomic features) of the participant labelled with the next
code. The correction keeps the features where they are and moves the participant
identity and all per-participant variables (age, sex, echointensity comparator,
stratum, morphometry, record identifiers) to the row that holds that participant's
image. Group labels are identical for all five rows (myopathic), so no label changes.

Input : data/cohort_locked.parquet (as produced by 01_load_and_prepare.py; not
        distributed — contains record identifiers) and the raw workbook sheet that
        carries the platform image codes.
Output: data/cohort_locked.parquet overwritten with the corrected pairing; the
        uncorrected matrix is kept as data/cohort_locked_uncorrected_pairing.parquet.
Executed at revision (2026-11-04) before re-running 03, 04, 05, 07 and 11.
"""
import sys
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "data" / "raw_data.xlsx"
MATRIX = REPO / "data" / "cohort_locked.parquet"
SHEET = "MIÓGENOS LA PAZ ROI1"

# row labelled with key  ->  holds the image of the participant labelled with value
CYCLE = {
    "IMG-0004-00009(E)":  "IMG-0004-000013(E)",
    "IMG-0004-000010(E)": "IMG-0004-00009(E)",
    "IMG-0004-000011(E)": "IMG-0004-000010(E)",
    "IMG-0004-000012(E)": "IMG-0004-000011(E)",
    "IMG-0004-000013(E)": "IMG-0004-000012(E)",
}

raw = pd.read_excel(RAW, sheet_name=SHEET)
key = lambda d: d["NHC"].astype(str) + "|" + d["Apellido"].astype(str) + "|" + d["Nombre"].astype(str)
code_to_key = dict(zip(raw["IMAGEN"].astype(str), key(raw)))

m = pd.read_parquet(MATRIX)
mk = key(m)
row_of = {k: i for i, k in enumerate(mk)}
feature_cols = [c for c in m.columns if c.startswith(("ROI1_", "ROI2_"))]
label_cols = ["group", "subgroup", "binary_label"]
move_cols = [c for c in m.columns if c not in feature_cols + label_cols]

corrected = m.copy()
for nominal_code, owner_code in CYCLE.items():
    dst = row_of[code_to_key[nominal_code]]   # row that holds the owner's image
    src = row_of[code_to_key[owner_code]]     # row that carries the owner's variables
    assert m.loc[dst, "subgroup"] == m.loc[src, "subgroup"] == "myogenic-LaPaz"
    corrected.loc[dst, move_cols] = m.loc[src, move_cols].values
    print(f"{nominal_code}: row {dst} now carries the variables of the participant whose image it holds (from row {src})")

assert (corrected[feature_cols].values == m[feature_cols].values).all()
assert (corrected[label_cols] == m[label_cols]).all().all()
m.to_parquet(REPO / "data" / "cohort_locked_uncorrected_pairing.parquet", index=False)
corrected.to_parquet(MATRIX, index=False)
changed = sorted(set(m.index[m["Heckmatt_grade"] == 2]) ^ set(corrected.index[corrected["Heckmatt_grade"] == 2]))
print("stratum-2 membership changed for rows:", changed)
print("done")

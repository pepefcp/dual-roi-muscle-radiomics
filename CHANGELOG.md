# Changelog

## 2026-11-04 — Revision audit: feature-family correction, corrected-pairing re-execution, locked seeds

**Corrected**
- `src/03_primary_analysis.py` — first-order features were identified by English keywords against
Spanish feature names, so Model 3 received 8 of 18 first-order features per region and Model 4
kept the other 10. Family assignment now uses the `Primerorden-` prefix, as in `src/04_grade2_analysis.py`.
Models 3 and 4 re-executed (50 seeds): Model 3 AUC 0.955 → 0.975, Model 4 0.926 → 0.901,
secondary contrast +0.193 → +0.167 (95% BCa CI +0.061 to +0.306). Primary contrast and Models
1, 2, 5–7 unchanged. `DEVIATIONS_LOG.md`, Correction 6.
- Two methodological statements of the submitted manuscript (segmentation without access to group
labels; image-level aggregation) did not describe the executed procedure. `DEVIATIONS_LOG.md`, Correction 5.

**Changed**
- `src/12_covariate_pairing_correction.py` (new) applies Correction 4 to the locked matrix by platform image code; `src/03`, `04`, `05` (50 seeds, 2,000 resamples), `07` and `11` re-executed on the corrected matrix. Primary contrast +0.215 → +0.217 (+0.116 to +0.351); stratum-2 composition changed by four participants (Model 2 within stratum 0.266 → 0.391; contrasts +0.672 → +0.562 and +0.656 → +0.531, both p = 0.001). `DEVIATIONS_LOG.md`, "Resolution of Correction 4".
- `src/13_exclusion_analyses.py` (new) — primary contrast with each enrolment group excluded in turn (Supplementary Table 6).
- `src/07_reviewer2.py` — now uses the 50 locked seeds (SAP §14.2) instead of integers 0–19 and
covers Models 3–7; `results/tables/Suppl_Table_R2*.csv` and `Suppl_calibration_curve_*.csv` regenerated.

**Added**
- `src/11_duplicate_pair_sensitivity.py` — primary contrast with one member of each duplicated-image
pair removed (n = 60): ΔAUC +0.219 (+0.112 to +0.359). `DEVIATIONS_LOG.md`, "Sensitivity analysis excluding the duplicated-image pairs".
- Deviation 3 — age-residualization (SAP §14.4c) executed as a cohort-wide fit rather than within training folds on controls.
- Notes on earlier entries (Correction 2 transcription error in the submitted table; the √2 statement in Deviation 1; fallback-rule activation table superseded).

**Unchanged**
- The Statistical Analysis Plan, the locked cohort (n = 62), the primary contrast and its result.

**Note on `results/figures/`** — the PNG/PDF plots in this folder are derived from the tables and were not re-uploaded in this update; `python src/03_primary_analysis.py` and `python src/04_grade2_analysis.py` regenerate them from the corrected matrix. The committed CSV tables are authoritative.

## 2026-11-03 — Record of the 50-seed execution and covariate correction

**Recorded**
- The prespecified analyses committed on 2026-08-25 (Tables 3–5, Figures 2–3) were executed with the
full locked list of 50 seeds (SAP §9.2), resolving Deviation 1 of the original 25-seed execution.
Differences from the submitted manuscript are ≤ 0.011 in AUC in the full cohort (primary contrast
+0.220 → +0.215) and change no conclusion. See `DEVIATIONS_LOG.md`, "Resolution of Deviation 1".
- Correction 4 (covariate–image pairing of five myogenic participants, 2026-09-29) and the
sensitivity analysis excluding upper motor neuron causes (50 seeds) are documented in `DEVIATIONS_LOG.md`.
- `RESULTS_SYNTHESIS.md` updated to the 50-seed values.

## 2026-08-22 — Post-review update

Prepared while responding to peer review at *Muscle & Nerve* (manuscript 8417492).
The locked Statistical Analysis Plan, registered at https://doi.org/10.17605/OSF.IO/AX74E
on 4 May 2026, is unchanged and is not affected by anything in this update.

**Corrected**
- `src/02_descriptives.py` — female participants were counted against the wrong code
  (`genero == 2`; the column is coded 0/1), so the sex row read zero in every group.
- Table 1 — morphometric variables re-derived from the reviewed source records after a
  unit-recording inconsistency (centimetres recorded as millimetres) was identified in
  two groups and in two individual control records.

**Added**
- `src/07_reviewer2.py` — per-fold feature counts, selection frequency, across-seed
  variability, calibration and threshold metrics, requested by Reviewer 2.
- `src/09_table1_final.py` — Table 1 regenerated with the corrections above.
- Sensitivity analysis excluding upper motor neuron cases.

**Unchanged**
- The Statistical Analysis Plan, the cohort definition, the primary contrast and the
  classifier configuration. The primary result (ΔAUC +0.22 for combined-region radiomics
  over mean echointensity) is unaffected by any correction in this update. (Note added
  2026-11-03: the estimates in this update are those of the full 50-seed execution;
  see the entry above and `DEVIATIONS_LOG.md`.)

See `DEVIATIONS_LOG.md` for the itemised record.

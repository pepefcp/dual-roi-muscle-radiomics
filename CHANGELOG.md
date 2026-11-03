# Changelog

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

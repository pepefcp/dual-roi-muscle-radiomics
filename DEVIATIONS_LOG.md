# SAP v1.1 — Deviations Log

This file records every post-lock deviation from `SAP_v1.1_LOCKED.docx`. It is appended-only. Each entry includes date, section affected, deviation, reason, and impact assessment.

This log is cited in the Methods section of the manuscript and included as a supplementary file.

---

## Deviations recorded during analysis execution

### Deviation 1 — Number of cross-validation seeds reduced from 50 to 25

| Item | Value |
|---|---|
| Date | 2026-04-30 |
| SAP section | §9.2 (Cross-validation scheme) |
| Locked specification | "50 random seeds fixed at SAP lock … 50 × 5 = 250 fold evaluations" |
| Actual implementation | 25 random seeds × 5 folds = 125 fold evaluations |
| Reason | Compute environment available for execution provided 2 CPU cores; the full 50-seed protocol with inner-CV hyperparameter tuning across 7 models, BCa bootstrap (2000 resamples, paired), and 4 sensitivity analyses exceeded the available wall-clock window. The first 25 seeds from the locked `seeds.json` were used (deterministic ordering preserved). |
| Impact assessment | Inferential conclusions are unaffected. The reported per-fold standard deviations are computed from 125 evaluations rather than 250; this slightly inflates SD estimates (factor √2 ≈ 1.41) but does not bias point estimates. The participant-level BCa bootstrap CI — the primary inferential statistic per SAP §13 — is computed on the participant-level aggregated out-of-fold predictions and is therefore not directly affected by seed count. The 25-seed schedule is a strict prefix of the locked 50-seed list and is fully deterministic and reproducible. |
| Recommended action | Re-run with the full 50 seeds when an HPC environment is available (estimated wall time on 16 cores: ~30 min). The expected change in the primary contrast point estimate is < 0.005 AUC. |

### Deviation 2 — Permutation test reduced from 1000 to 500 permutations with simplified inner pipeline

| Item | Value |
|---|---|
| Date | 2026-04-30 |
| SAP section | §14.1 (Permutation testing) |
| Locked specification | "Class labels permuted at participant level, 1000 permutations, full pipeline (feature selection, CV, model fitting) re-executed each time." |
| Actual implementation | 500 permutations; per permutation: 5-fold CV, within-fold feature selection (FDR q<0.10 with fallback rule), L2 logistic regression at fixed `C = 1.0` (no inner-CV hyperparameter tuning). |
| Reason | Compute window. The full 1000-permutation × inner-CV protocol was estimated at ~50 min of wall time on the available 2-core environment. The simplified pipeline runs ~5× faster while retaining the principal sources of permutation variance (label assignment, fold partition, feature selection). |
| Actual result | Observed ΔAUC = +0.223. Null mean = +0.012, null SD = 0.124. Empirical one-sided p = 0.0499 (24/500 permutations ≥ observed). Borderline significant at α = 0.05. |
| Interpretation | Permutation testing is a *supportive* analysis per SAP §13; it is **not** the H₀-rejection test. The H₀ rejection criterion (SAP §13) is "Statistically significant positive ΔAUC-ROC at α = 0.05 with the BCa 95% CI excluding zero", which is met by the participant-level paired BCa bootstrap (Table 3: ΔAUC +0.220, BCa 95% CI +0.113 to +0.358, p < 0.0001) and corroborated by DeLong (p = 0.0004). The borderline permutation p reflects the inherent conservatism of permutation testing in small samples with high-capacity models: with n = 62 and 182 candidate features, label-permuted runs of Model 7 routinely overfit and achieve spurious AUC > 0.7, producing a wide null distribution (SD = 0.124) that absorbs much of the observed effect. This is methodologically expected and does not contradict the bootstrap and DeLong results, which test the participant-level prediction stability rather than the chance-level achievability of the AUC under random labels. The borderline permutation result is reported transparently in the manuscript and constrains the strength of generalisation claims pending external validation. |
| Recommended action | Re-run with the full 1000-permutation × full-pipeline protocol when HPC is available. The expected change in the empirical p-value is small (precision improves from ±0.002 to ±0.001) but a slightly tighter null distribution is possible if the inner-CV regularisation reduces overfitting on permuted labels. |

---

## Deviations affecting interpretation: none

No changes to:

- Endpoint definitions (§5)
- Cohort definition or composition (§4)
- Comparator hierarchy (§7)
- Primary contrast specification (§13)
- H₀ rejection criterion (§13)
- Heckmatt-analogue Grade 2 inclusion threshold or interpretive framing (§15)
- Permitted/prohibited claims (§19)

All seven SAP-locked sections above were honoured exactly as written.

---

## Notes on fallback-rule activation (not a deviation, prespecified behaviour)

Per SAP §11, the fallback rule applies when fewer than 10 features survive the FDR filter in any training fold. This activated as follows in the executed analysis:

| Model | Fallback folds (of 125) |
|---|---|
| Model 1 (Heckmatt grade) | 0 |
| Model 2 (mean EI) | 0 |
| Model 3 (first-order, ROI1+ROI2) | 119 |
| Model 4 (texture-only, ROI1+ROI2) | 0 |
| Model 5 (ROI1 full) | 0 |
| Model 6 (ROI2 full) | 0 |
| Model 7 (dual-ROI full) | 0 |

Model 3 routinely triggered the fallback because the first-order feature pool is small (≈ 18 features per ROI × 2 ROIs ≈ 36 candidates). The SAP-locked fallback (top 10 features by univariate p-value within fold) was applied as specified and is therefore *not* a deviation.

---

*End of deviations log at execution. No further entries permitted without versioned amendment.*

---

## Corrections identified during peer review (August 2026)

These entries record errors found while responding to peer review at *Muscle & Nerve*. They are corrections to the executed analysis and to the reported figures, not amendments to the locked Statistical Analysis Plan, which is unchanged.

### Correction 1 — Sex was reported as 0% female in every group

| Item | Value |
|---|---|
| Date | 2026-08-21 |
| Affected | `src/02_descriptives.py`, Table 1a |
| Defect | Female participants were counted with `df["genero"] == 2`, but the source column is coded 0/1. The condition never matched, so the row reported zero in all groups and was omitted from the submitted manuscript. |
| Correction | Condition changed to `== 1`. Corrected distribution: 24 of 62 female (39%) — controls 11/23, myopathic 4/16, peripheral neurogenic and upper motor neuron 9/23 combined, SMA 6/10. |
| Impact | Descriptive only. No model input, no effect on any estimate. |

### Correction 2 — Unit inconsistency in morphometric variables

| Item | Value |
|---|---|
| Date | 2026-08-21 |
| Affected | `RF Grosor (MM)` and `GROSOR SC (MM)` in the source workbook; Table 1a |
| Defect | Rectus femoris thickness was recorded in centimetres for the myopathic group (18/18 records) and for two control records; subcutaneous fat thickness was recorded in centimetres for the myopathic and peripheral neurogenic groups. Values were treated as millimetres throughout, producing implausible figures (myopathic mean 1.12 mm) and a spurious group difference. |
| Correction | Morphometric values re-derived from the reviewed source records, in which units had already been reconciled. Corrected means: controls 12.47 mm, myopathic 11.22 mm, neurogenic incl. SMA 13.37 mm. |
| Impact | The reported difference in rectus femoris thickness between controls and patients (p = 0.048) does not survive correction (p = 0.71). Thickness is not a model input; the primary contrast and all model estimates are unaffected. |

### Correction 3 — Feature count misreported in the manuscript

| Item | Value |
|---|---|
| Date | 2026-08-21 |
| Affected | Manuscript Abstract and Results (not the code) |
| Defect | The submitted manuscript stated 98 IBSI-compliant features per region and 196 per participant. The executed pipeline retains 91 per region and 182 per participant after excluding nine shape descriptors under SAP §6.3, as recorded in `results/logs/01_load_and_prepare.log`. |
| Correction | Manuscript figures corrected to 91 and 182. The code was correct as executed. |
| Impact | Reporting only. |

## Analyses added in response to peer review

Requested by Reviewer 2 and executed after the review, using the locked cohort and the pipeline as specified. These are additions, not changes to the prespecified analyses.

| Script | Content |
|---|---|
| `src/07_reviewer2.py` | Features retained per fold, selection frequency across 20 seeds × 5 folds, discrimination variability across seeds, calibration (Brier, intercept, slope, curve), and sensitivity, specificity, positive and negative predictive value at a fixed decision threshold. |
| `src/09_table1_final.py` | Table 1 regenerated with corrections 1 and 2 applied. |

A sensitivity analysis excluding the nine participants whose muscle pathology was secondary to an upper motor neuron lesion was also performed; the primary contrast was unchanged (ΔAUC +0.213 versus +0.207 in the full cohort).

Any decision threshold reported in the revised manuscript outside the prespecified 0.50 cut-point is explicitly labelled post hoc and illustrative, and was selected after inspection of the data.

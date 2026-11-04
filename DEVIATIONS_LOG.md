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

### Correction 4 — Covariate–image pairing crossed for five myogenic participants (platform-upload mislabeling)

| Item | Value |
|---|---|
| Date | 2026-09-29 |
| Affected | Demographic covariates (age, sex), echointensity comparator and subcutaneous-fat value of participants 13, 28, 42, 43 and 55 (all myogenic); `results/tables/Suppl_Table_4_age_covariate.csv`; Supplementary Table 7 of the manuscript |
| Defect | During the segmentation-robustness audit (Supplementary Methods 3 of the revised manuscript), image-by-image verification against the archived source images — by unique pixel dimensions and, where in doubt, normalized cross-correlation — revealed that five myogenic images had been uploaded to the analysis platform in 2023 under each other's participant codes (a closed 5-cycle). The radiomic features of each of these five rows therefore belonged to the image of another participant of the same diagnostic group, while age, sex and the ImageJ echointensity comparator belonged to the nominal participant. Group labels are unaffected, so the primary contrast and all group-level analyses are unaffected by construction. The same verification found two pairs of participants sharing a duplicated stored image (one control pair, one SMA-II pair): the 62 participants rest on 60 unique images. |
| Correction | The covariate–image pairing was corrected by reassigning age, sex, echointensity and subcutaneous fat within the five rows (42←28, 43←42, 13←43, 55←13, 28←55, features fixed). The full pipeline was independently re-executed from the raw workbook and reproduced every published value exactly before the correction was applied. Analyses 14.4a–c (the only ones that use per-participant covariates) were recomputed; the table file is updated. |
| Impact | 14.4a: ΔAUC +0.161 → +0.162 (p < 0.001). 14.4b: +0.179 → +0.176 (p < 0.001). 14.4c: +0.192 → +0.174 (+0.054 to +0.314), p = 0.004 → 0.008; combined-model AUC 0.910 → 0.893. No change in the direction or significance of any contrast. |

### Resolution of Deviation 1 — Full 50-seed protocol executed at revision

| Item | Value |
|---|---|
| Date | 2026-08-25 (executed); 2026-11-03 (recorded) |
| Affected | `results/tables/Table_3_primary_endpoint.csv`, `Table_4_contrasts.csv`, `Table_5_stratum2_subgroup.csv`, `Table_5b_stratum2_contrasts.csv`, `results/figures/`; Tables 3–5, Figures 2–3, Abstract and Results of the revised manuscript |
| What was done | The prespecified analyses (`src/03_primary_analysis.py`, `src/04_grade2_analysis.py`) were re-executed with the full locked list of 50 seeds, as SAP §9.2 specifies, instead of the 25-seed prefix used in the original execution (Deviation 1). The results committed on 2026-08-25 and reported in the revised manuscript are those of the 50-seed execution. This entry records that fact, which the August commit did not state. |
| Impact | Relative to the 25-seed execution (submitted manuscript): Model 7 AUC 0.952 (0.875–0.984) → 0.949 (0.871–0.983); primary contrast ΔAUC +0.220 (+0.113 to +0.358) → +0.215 (+0.109 to +0.348); Model 7 vs Model 5 +0.021 (p = 0.568) → +0.010 (p = 0.788); stratum-2 Model 7 AUC 0.953 → 0.938, Model 2 0.297 → 0.266. No estimate in the full cohort changed by more than 0.011 in AUC, none in the exploratory stratum by more than 0.031, and no contrast changed direction or significance. Both executions are reproducible from the archived code and seed list (`python src/03_primary_analysis.py 25` and `python src/03_primary_analysis.py`). The sensitivity analyses of SAP §14.3–14.5 (`src/05_sensitivity.py`, `src/10_age_adiposity_sensitivity.py`) retain the 25-seed, 1,000-resample configuration; the reviewer-requested analyses (`src/07_reviewer2.py`) use 20 seeds (integers 0–19) rather than the locked list, a choice made at execution and stated in the supplementary tables. |
| Note on Deviation 2 | The values quoted in the "Interpretation" row of Deviation 2 (Table 3: ΔAUC +0.220, +0.113 to +0.358) are those of the 25-seed execution current at the time of writing; under the 50-seed execution they are +0.215 (+0.109 to +0.348), with the same conclusion. |

## Analyses added in response to peer review

Requested by Reviewer 2 and executed after the review, using the locked cohort and the pipeline as specified. These are additions, not changes to the prespecified analyses.

| Script | Content |
|---|---|
| `src/07_reviewer2.py` | Features retained per fold, selection frequency, discrimination variability across seeds, calibration (Brier, intercept, slope, curve), and sensitivity, specificity, positive and negative predictive value at a fixed decision threshold. First executed with 20 seeds (integers 0–19, not the locked list); re-executed on 2026-11-04 with the 50 locked seeds and extended to Models 3–7 (see "Entries added at revision" below). |
| `src/09_table1_final.py` | Table 1 regenerated with corrections 1 and 2 applied. |

A sensitivity analysis excluding the nine participants whose muscle pathology was secondary to an upper motor neuron lesion was also performed; the primary contrast was unchanged (50 locked seeds, 2,000 resamples: ΔAUC +0.232, 95% BCa CI +0.113 to +0.391, p < 0.001, versus +0.215 in the full cohort; Supplementary Table 6 of the revised manuscript).

Any decision threshold reported in the revised manuscript outside the prespecified 0.50 cut-point is explicitly labelled post hoc and illustrative, and was selected after inspection of the data.

---

## Entries added at revision (November 2026)

Recorded on 2026-11-04 after an independent re-verification of the revised manuscript against the archived analysis. Earlier entries are left as written; where one of them is superseded, the note below says so.

### Correction 5 — Two methodological statements in the submitted manuscript did not describe the executed procedure

| Item | Value |
|---|---|
| Date | 2026-11-04 |
| Affected | Methods of the submitted manuscript (Image acquisition; Region-of-interest segmentation; Radiomic feature extraction). No data, code or estimate. |
| Defect | The submitted manuscript stated that the two regions of interest were segmented "by the same operator without access to clinical group labels at the time of segmentation" and that the feature set per participant was obtained "after image-level aggregation to the participant level" (mean of the three acquisitions). Neither statement describes what was done: one image per participant — the acquisition of highest technical quality, chosen before any measurement — was segmented and analyzed, values were not averaged across acquisitions, and the single operator who acquired, selected and segmented the images was not formally blinded to clinical status. The SAP registration (OSF AX74E, "Study design") carries the same two statements. |
| Correction | The revised Methods state the executed procedure and list the absence of formal blinding as a limitation; a post hoc segmentation-robustness analysis (Supplementary Methods 2 of the revised manuscript) was added as partial mitigation. The aggregation rule of SAP §6 (mean over acquisitions) was never invoked because each participant contributed one analyzed image. |
| Impact | None on any estimate. Affects the description of the study, not its execution. |

### Correction 6 — Feature-family assignment defect in `src/03_primary_analysis.py` (Models 3 and 4)

| Item | Value |
|---|---|
| Date | 2026-11-04 |
| Affected | `src/03_primary_analysis.py` (function `get_feature_groups`); Models 3 (first-order radiomics) and 4 (texture-only radiomics) in `results/tables/Table_3_primary_endpoint.csv` and `Table_4_contrasts.csv`, `results/figures/Figure_3_primary_endpoint.*`; Table 3, Table 4 (secondary contrast) and Figure 2 of the manuscript. Models 1, 2, 5, 6 and 7, the primary contrast, the stratum analysis (`src/04_grade2_analysis.py`, which assigns families by the `Primerorden-` prefix) and all sensitivity analyses are unaffected. |
| Defect | The primary-analysis script identified first-order features by matching English keywords (MEAN, MEDIAN, PERCENT, RANGE, VARIANC, SKEW, KURTOS, …) against feature names that the extraction platform exports in Spanish (Curtosis, Asimetría, Varianza, Rango, Máximo, Mínimo, Energía, Entropía, Rangointercuartil, Energíatotal). Only 8 of the 18 first-order features per region matched; the other 10 were assigned to the texture family. Model 3 was therefore fitted on 16 instead of 36 features, and Model 4 on 166 features that included 20 first-order descriptors, contrary to SAP §7 (Model 4 excludes first-order features). The defect also explains the fallback-rule activation recorded for Model 3 (119 of 125 folds at 25 seeds; 241 of 250 at 50 seeds): with 16 candidates, fewer than 10 features survived the FDR filter in most folds. |
| Correction | Family assignment now uses the platform prefix (`Primerorden-` = first-order; all other families = texture), as in `src/04_grade2_analysis.py`. Models 3 and 4 were re-executed with the 50 locked seeds and 2,000 resamples; all other models reproduced their previous values exactly. |
| Impact | 50-seed execution, before → after: Model 3 AUC 0.955 (0.879–0.988) → 0.975 (0.920–0.995), Brier 0.132 → 0.091, F1 0.895 → 0.933, fallback folds 241 → 0; Model 4 AUC 0.926 (0.836–0.972) → 0.901 (0.801–0.957), Brier 0.114 → 0.132, F1 0.833 → 0.827; secondary contrast (Model 4 vs Model 2) ΔAUC +0.193 (+0.082 to +0.333; bootstrap p = 0.003, DeLong p = 0.002) → +0.167 (+0.061 to +0.306; p = 0.006, p = 0.007). The submitted (25-seed) values were Model 3 0.958, Model 4 0.932 and secondary contrast +0.200. The secondary contrast keeps its direction and significance. The statement in the submitted Results that first-order and texture-only models performed similarly is withdrawn: first-order features alone discriminate at least as well as the full feature set, and texture-only features less well, while still outperforming mean echointensity. |

### Deviation 3 — Age-residualization (SAP §14.4c) executed as a cohort-wide fit

| Item | Value |
|---|---|
| Date | 2026-11-04 (recorded); analysis executed 2026-09 (`src/10_age_adiposity_sensitivity.py`) |
| SAP section | §14.4c |
| Deviation | SAP §14.4c specifies per-feature linear residualization against age estimated on the healthy controls of each training fold and applied within the fold. As executed, the linear fit of each feature (and of the echointensity comparator) on age was estimated once on the full cohort, without reference to group labels, before cross-validation. |
| Reason | Implementation simplicity (the cross-validation machinery was reused unchanged). The fit uses age only, never the outcome, so no label information leaks; the age–label association itself is declared in Table 1. |
| Impact | Supplementary Table 7 (age-residualized row: Model 2 0.719, Model 7 0.893, ΔAUC +0.174, +0.054 to +0.314, p = 0.008) reports the analysis as executed and now states the deviation. Conclusions unchanged. |

### Re-execution of the reviewer-requested analyses with the locked seeds

| Item | Value |
|---|---|
| Date | 2026-11-04 |
| Affected | `src/07_reviewer2.py`; `results/tables/Suppl_Table_R2a_stability.csv`, `Suppl_Table_R2b_calibration_thresholds.csv`, `Suppl_Table_R2c_selection_frequency.csv`, `Suppl_calibration_curve_*.csv`; Supplementary Tables 3–5 and 9 of the revised manuscript |
| What was done | Inter-seed stability (prespecified in SAP §14.2 over the 50 locked seeds) had been executed at review with 20 arbitrary seeds (integers 0–19). The script now reads the locked seed list, uses the corrected family assignment (Correction 6) and covers Models 3–7 (Models 1 and 2 have a single predictor and no feature selection). Supplementary Table 5 (calibration and threshold metrics) is therefore computed on the same aggregated out-of-fold predictions as Table 3 of the manuscript. |
| Impact | Values in Supplementary Tables 3–5 updated; the set of features selected in every partition of the combined-region model is given in Supplementary Table 4 and its segmentation-robustness in Supplementary Table 9. No conclusion changes. |

### Sensitivity analysis excluding the duplicated-image pairs (n = 60)

| Item | Value |
|---|---|
| Date | 2026-11-04 |
| Script | `src/11_duplicate_pair_sensitivity.py` |
| Rationale | Correction 4 recorded two pairs of participants (one control pair, one SMA-II pair) whose stored images are duplicates; in the locked matrix the feature vectors of each pair are near-identical (Euclidean distance between standardized vectors 1.0 and 1.9, against a median nearest-neighbour distance of 9.5), so the two pairs may act as repeated observations across folds. |
| What was done | The primary contrast was re-executed with one member of each pair removed (the rows holding platform images IMG-0001-000013A and IMG-0002-00009B(II); 50 locked seeds, 2,000 resamples, corrected matrix). |
| Result | n = 60 (22 controls, 38 pathological): Model 2 AUC 0.732 (0.586–0.842), Model 7 0.952 (0.877–0.984), ΔAUC +0.220 (+0.117 to +0.362), p < 0.001, versus +0.217 in the full cohort. Reported in Supplementary Table 6 of the revised manuscript. The locked cohort (n = 62) remains the primary analysis, as SAP §4 does not permit post-lock removal of participants. |


### Resolution of Correction 4 — re-execution of all analyses on the corrected pairing

| Item | Value |
|---|---|
| Date | 2026-11-04 |
| Script | `src/12_covariate_pairing_correction.py` (applies the five-row cycle to `data/cohort_locked.parquet`, keeping the uncorrected matrix as `data/cohort_locked_uncorrected_pairing.parquet`) |
| Why | Correction 4 (2026-09-29) recomputed only the covariate analyses (SAP §14.4). The mis-paired variables include the echointensity comparator (Model 2 input) and the stratum assignment, so the paired inference of the primary contrast and the composition of the stratum-2 subgroup also depend on the pairing. The five rows are the platform images IMG-0004-00009(E) to IMG-0004-000013(E), a closed cycle in which each code held the image of the next; the identifiers quoted in Correction 4 (13, 28, 42, 43, 55) are `participant_id` values of the repository matrix, not row positions; the image codes are the stable reference. Check: applying `src/12_covariate_pairing_correction.py` and running `src/10_age_adiposity_sensitivity.py` reproduces Supplementary Table 7 exactly (14.4b +0.176, +0.089 to +0.299; 14.4c +0.174, +0.054 to +0.314), confirming that the script and the September correction are the same correction. |
| What was done | `src/03_primary_analysis.py`, `src/04_grade2_analysis.py`, `src/05_sensitivity.py` (50 seeds, 2,000 resamples), `src/07_reviewer2.py` and `src/11_duplicate_pair_sensitivity.py` were re-executed on the corrected matrix. `src/10_age_adiposity_sensitivity.py` had already been executed on the corrected pairing (Correction 4). The permutation test (`src/06_permutation.py`, Deviation 2) was not re-executed. |
| Impact (50-seed values, before → after re-pairing) | Model 1 AUC 0.649 (0.486–0.783) → 0.648 (0.489–0.779); Model 2 0.734 (0.589–0.841) → 0.731 (0.588–0.840); Models 3–7 unchanged (features and labels unchanged); primary contrast +0.215 (+0.109 to +0.348), DeLong p = 0.0004 → +0.217 (+0.116 to +0.351), p = 0.0002; secondary contrast +0.167 (+0.061 to +0.306) → +0.169 (+0.069 to +0.293); Model 7 vs Model 1 +0.300 (+0.170 to +0.451) → +0.301 (+0.177 to +0.452). Stratum 2: two of the five participants left and two entered the stratum (membership still 8 controls, 8 pathological); Model 2 within the stratum 0.266 → 0.391 (0.125–0.716); Model 3 0.938 → 0.922; Model 4 0.906 → 0.922; Model 5 0.969 → 0.953; Model 6 0.609 → 0.719; Model 7 0.953 → 0.953; contrasts Model 7 vs 2 +0.672 (+0.348 to +0.905) → +0.562 (+0.206 to +0.857), Model 4 vs 2 +0.656 (+0.293 to +0.902) → +0.531 (+0.167 to +0.833), both p = 0.001. No contrast changed direction or significance. |

### Exclusion analyses of the primary contrast (Supplementary Table 6 of the revised manuscript)

| Analysis | n (controls / pathological) | Model 2 AUC (95% BCa CI) | Model 7 AUC (95% BCa CI) | ΔAUC (95% BCa CI), bootstrap p |
|---|---|---|---|---|
| SMA excluded (SAP §14.3; `src/05_sensitivity.py`) | 52 (23 / 29) | 0.643 (0.483–0.796) | 0.976 (0.896–0.997) | +0.333 (+0.187 to +0.498), < 0.001 |
| Upper motor neuron causes excluded | 53 (23 / 30) | 0.728 (0.564–0.849) | 0.959 (0.874–0.989) | +0.232 (+0.120 to +0.384), < 0.001 |
| Duplicated-image pairs, one member of each excluded (`src/11_duplicate_pair_sensitivity.py`) | 60 (22 / 38) | 0.732 (0.586–0.842) | 0.952 (0.877–0.984) | +0.220 (+0.117 to +0.362), < 0.001 |
| Myopathic enrolment group excluded | 46 (23 / 23) | 0.811 (0.641–0.911) | 0.953 (0.852–0.990) | +0.142 (+0.053 to +0.282), 0.001 |
| Peripheral nerve causes excluded | 57 (23 / 34) | 0.756 (0.614–0.871) | 0.953 (0.875–0.985) | +0.197 (+0.090 to +0.331), < 0.001 |

All rows: 50 locked seeds, 2,000 resamples, corrected matrix (`src/11_duplicate_pair_sensitivity.py` and `src/13_exclusion_analyses.py`). The classifier sensitivity analysis (SAP §14.5, `src/05_sensitivity.py`) was re-executed in the same configuration: L2 logistic regression 0.949 (0.871–0.983), linear SVM 0.977 (0.925–0.994), random forest 0.946 (0.869–0.983).

### Notes on earlier entries

1. **Correction 2.** The text says the uncorrected myopathic rectus femoris thickness was "1.12 mm"; this is the value in the locked matrix (16 records, 1.12 ± 0.33). The submitted Table 1A printed "6.12 ± 0.33" for that cell, a transcription error in the table that the correction also removes.
2. **Correction 4.** The identifiers 13, 28, 42, 43 and 55 are `participant_id` values of the repository matrix (not row positions); the five rows are the platform images IMG-0004-00009(E) to IMG-0004-000013(E) (see "Resolution of Correction 4"). "Supplementary Methods 3 of the revised manuscript" in that entry is now Supplementary Methods 2 after the supplement was reordered at revision. The row in "Resolution of Deviation 1" stating that `src/07_reviewer2.py` uses 20 seeds is superseded by the entry above.
3. **Correction 1.** The denominators read "peripheral neurogenic and upper motor neuron 9/23 combined, SMA 6/10": 9/23 is the neurogenic column of Table 1 including SMA, of which the 6 SMA females are a subset (3/13 in the non-SMA neurogenic group); total 24/62.
4. **Correction 2.** "18/18 records" counts the rows of the myopathic source sheet; 16 of them are in the locked cohort.
5. **Deviation 1.** The impact assessment states that computing per-fold standard deviations from 125 rather than 250 evaluations "inflates SD estimates (factor √2 ≈ 1.41)". That is incorrect: halving the number of evaluations widens the uncertainty of the SD estimate but does not change its expected value (the √2 factor applies to the standard error of a mean). The 50-seed execution recorded above makes the point moot.
6. **Fallback-rule activation.** The table above (Model 3: 119 of 125 folds) reflects the defect of Correction 6. After correction, the fallback rule was not invoked in any fold of any model in the 50-seed execution.
7. **Seed configurations in the revised manuscript.** Tables 3–5 and Figures 2–3 of the manuscript, Supplementary Tables 3–6 and 8: 50 locked seeds, 2,000 resamples, corrected matrix. Supplementary Table 7: first 25 locked seeds, 1,000 resamples, corrected pairing (configuration of the original execution). Permutation test: 500 permutations, before the re-pairing (Deviation 2). Each table states its configuration.
8. **Structure of this log.** The closing line of the execution-phase section ("No further entries permitted without versioned amendment") referred to that phase; corrections and analyses identified during peer review are appended below it under the same append-only rule. The heading "Corrections identified during peer review (August 2026)" also covers Correction 4 (September 2026) and the record of the 50-seed execution (November 2026).

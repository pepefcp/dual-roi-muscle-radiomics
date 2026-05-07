---
title: "Statistical Analysis Plan v1.1 — LOCKED"
subtitle: "Dual-ROI radiomic ultrasound for detecting pathological muscle in children: a prespecified analysis with a Heckmatt-analogue Grade 2 ambiguity-zone subgroup"
author: "José Fernández-Cuesta Peñafiel, MD"
date: "Locked: [DATE OF DEPOSIT]"
---

# Statistical Analysis Plan v1.1 — LOCKED

**Working title.** Dual-ROI radiomic ultrasound for detecting pathological muscle in children: a prespecified analysis with a Heckmatt-analogue Grade 2 ambiguity-zone subgroup.

**Author.** José Fernández-Cuesta Peñafiel, MD.
ORCID: 0000-0003-3080-1100.

**Date locked.** [DATE OF DEPOSIT].

**Status.** **LOCKED.** No changes to primary or secondary endpoints, model definitions, comparator hierarchy, or analysis protocol are permitted after this version. Any deviation will be documented in a deviations log appended to the supplement and explicitly flagged in the manuscript.

**Version history.** v0.1 (initial draft, internal). v1.0 (first complete version, internal). **v1.1 — locked for OSF deposit before any classification model is fit on the SAP-locked final cohort under the locked endpoint definitions, comparator hierarchy, and analysis protocol described herein.**

**Reporting standards.** TRIPOD+AI for prediction-model reporting; IBSI for radiomic feature definitions and preprocessing.

---

## 0. Pre-registration disclosure

This SAP is a prospective analysis lock for the revised final cohort (n = 62, see section 4). Preliminary exploratory analyses were conducted on earlier dataset versions and on prior cohort definitions before SAP finalisation; those analyses informed the conceptual framing of the present study (in particular, the choice of binary endpoint over multi-class etiologic classification and the recognition of Heckmatt-analogue Grade 2 as a clinically relevant ambiguity zone). They are disclosed as exploratory and are not treated as confirmatory. No classification model has been fit on the locked final cohort under the analysis protocol described herein at the time of OSF deposit.

---

## 1. Background and scope

This study evaluates whether an IBSI-compliant radiomic analysis of standardised paediatric anterior-thigh ultrasound improves detection of pathological muscle compared with conventional scalar echointensity assessment. The primary endpoint is global discrimination of healthy versus pathological muscle. A prespecified secondary analysis examines model behaviour within the Heckmatt-analogue Grade 2 subgroup, where scalar echointensity is range-restricted and expected to be less informative.

The study is **not** designed to establish:

- definitive etiologic classification (myogenic versus neurogenic);
- disease-specific diagnosis;
- treatment-response prediction;
- replacement of electromyography or muscle biopsy;
- a clinically deployable biomarker.

These boundaries constrain manuscript claims and are restated in section 19.

---

## 2. Scientific question and hypotheses

**Primary scientific question.** In children undergoing standardised anterior-thigh muscle ultrasound, does dual-ROI radiomic texture analysis improve detection of pathological muscle compared with continuous mean echointensity?

**H₁ (alternative).** Dual-ROI radiomic features yield a higher AUC-ROC for healthy-versus-pathological classification than continuous mean rectus femoris echointensity.

**H₀ (null).** Dual-ROI radiomic features do not yield a higher AUC-ROC than continuous mean rectus femoris echointensity.

**Secondary scientific question (exploratory).** Within the Heckmatt-analogue Grade 2 subgroup, do radiomic features retain discriminative signal where echointensity is range-restricted?

The secondary analysis is exploratory by design and is not powered for confirmatory inference.

---

## 3. Study design

Single-centre, prospective imaging study (Hospital Universitario La Paz, Madrid, 2017–2023) with retrospective etiologic group assignment. IRB approval Ref. HULP/PI-248-2017. Image acquisition, anonymisation, and storage have been completed prior to SAP lock.

---

## 4. Study population

**Final analytic cohort: n = 62.**

| Group        | Subgroup          | n  | Role in primary analysis    |
|--------------|-------------------|----|-----------------------------|
| Healthy      | healthy           | 23 | negative class              |
| Pathological | myogenic-LaPaz    | 16 | positive class              |
| Pathological | neurogenic-LaPaz  | 13 | positive class              |
| Pathological | SMA-I             | 3  | positive class              |
| Pathological | SMA-II            | 4  | positive class              |
| Pathological | SMA-III           | 3  | positive class              |
| **Total**    |                   | **62** | 23 healthy / 39 pathological |

**Inclusion criteria.** Age 2–17 years at acquisition; etiologic confirmation by genetic testing, muscle biopsy, electromyography/nerve conduction studies, or muscle MRI for pathological cases.

**Cohort cleaning record (immutable).**

- One participant who appeared duplicated as both healthy and neurogenic in the source dataset was retained as neurogenic only.
- One myogenic case with age 0.41 y excluded (outside paediatric scope).
- One myogenic case with age 0.99 y corrected to 2.0 y per clinical record review.
- One myogenic case with age 22.3 y excluded (adult).
- Two myogenic cases with date-artifact ages of 120.25 y corrected to 8 y and 9 y respectively per clinical record review.
- One neurogenic case at 17.19 y retained as borderline-included by clinical judgement.
- All SMA cases with age outside [2, 17) excluded (n = 9 dropped).

Subgroup labels are retained for descriptive reporting only; they are not classifier targets.

---

## 5. Endpoints

### 5.1 Primary endpoint

Healthy versus pathological muscle classification across the full cohort (n = 62). Negative class: healthy (n = 23). Positive class: pathological, pooled across myogenic and neurogenic subgroups (n = 39).

### 5.2 Secondary endpoint (prespecified, exploratory)

Healthy versus pathological classification restricted to the Heckmatt-analogue Grade 2 subgroup. Anticipated n at SAP lock: 16 (8 healthy, 8 pathological). Final subgroup composition is fixed by the SAP-locked thresholds applied to the SAP-locked cohort; no participant reassignment is permitted.

### 5.3 Sensitivity endpoint

Healthy versus pathological classification with all SMA cases excluded (n = 52). Isolates comparator behaviour from a subgroup in which scalar echointensity is already near-perfect (all SMA cases fall in Heckmatt-analogue Grade 4) and confirms the radiomic advantage is not driven by easy cases.

---

## 6. Variables

### 6.1 Clinical and demographic (descriptive only)

Age, sex, weight, height, BMI, RF thickness, subcutaneous fat thickness, etiologic subgroup, specific diagnosis, SMN2 copy number, ambulation status.

### 6.2 Conventional ultrasound variables

- **Continuous comparator (Model 2).** RF mean echointensity (a.u.).
- **Ordinal comparator (Model 1).** Heckmatt-analogue grade derived from RF mean echointensity using thresholds prespecified in the prior project SAP (v0.1) and carried forward unchanged into v1.1:

| Grade | Echointensity range (a.u.) |
|-------|----------------------------|
| 1     | < 40                       |
| 2     | 40–55                      |
| 3     | 55–72                      |
| 4     | > 72                       |

These thresholds were not re-derived from the v1.1 cohort distribution. The variable is named *echointensity-derived grade (Heckmatt-analogue)* throughout the manuscript to avoid implying equivalence with the visual semiquantitative Heckmatt scale, which is a separate clinical instrument.

### 6.3 Radiomic variables

Two manually segmented ROIs:

- **ROI1.** Intramuscular rectus femoris (microstructure).
- **ROI2.** Full anterior-thigh compartment, femoral cortex to superficial fascia (macro-architecture).

Extraction with QUIBIM QP-Discovery (CE-marked, IBSI-compliant). Preprocessing: z-score intensity normalisation across the full dataset, Gaussian noise reduction (σ = 1.0), isotropic resampling where required, fixed intensity window 0–255, fixed bin width 25. Feature families: first-order, GLCM, GLRLM, GLSZM, GLDM, NGTDM. Shape features excluded from the primary analysis (reserved for optional sensitivity analysis).

| Feature set   | Definition                                                  |
|---------------|-------------------------------------------------------------|
| First-order   | intensity-distribution features only                        |
| Texture-only  | GLCM + GLRLM + GLSZM + GLDM + NGTDM; first-order excluded   |
| ROI1          | all ROI1 features (first-order + texture)                   |
| ROI2          | all ROI2 features (first-order + texture)                   |
| Dual-ROI      | ROI1 + ROI2 concatenated                                    |

---

## 7. Comparator model hierarchy

| Model | Inputs                                | Role                                     |
|-------|---------------------------------------|------------------------------------------|
| 1     | Heckmatt-analogue grade (ordinal)     | conventional ordinal comparator          |
| 2     | RF mean echointensity (continuous)    | scalar continuous comparator             |
| 3     | First-order radiomics (ROI1+ROI2)     | intensity-distribution radiomics         |
| 4     | Texture-only radiomics (ROI1+ROI2)    | spatial texture beyond intensity         |
| 5     | ROI1 full radiomics                   | intramuscular signal                     |
| 6     | ROI2 full radiomics                   | compartment-level signal                 |
| 7     | Dual-ROI full radiomics               | combined radiomic model                  |

**Primary statistical contrast.** Model 7 vs Model 2.

**Secondary mechanistic contrast (prespecified, supportive).** Model 4 vs Model 2.

All other pairwise comparisons are exploratory, presented without formal multiplicity correction, and labelled as such.

---

## 8. Classifier specification

**Primary classifier for radiomic models (Models 3–7).** L2-regularised logistic regression with internal hyperparameter tuning (regularisation strength C selected on a 5-value log-grid by inner cross-validation within each training fold).

**Comparator scalar models (Models 1 and 2).** Univariate logistic regression, ensuring all models share probabilistic output for AUC, calibration, and pairwise comparison.

**Sensitivity classifiers (supplementary only).** Linear support vector machine with Platt scaling; Random Forest (100 trees). Not used for the primary contrast.

---

## 9. Cross-validation and leakage prevention

### 9.1 Unit of analysis

Participant-level. Image-level radiomic vectors are averaged at participant level before model training. The unit of all CV operations is therefore one participant per row.

### 9.2 Cross-validation scheme

Stratified 5-fold cross-validation at participant level, stratified on the binary label, repeated with **50 random seeds fixed at SAP lock**. All metrics reported as mean ± SD across the 50 × 5 = 250 fold evaluations.

A supplementary image-level sensitivity analysis (if implemented) will use Stratified GroupKFold with `groups = participant_id` to prevent within-participant leakage.

### 9.3 Operations restricted to the training fold

- median imputation for missing continuous variables;
- z-score standardisation of features;
- correlation filtering (|r| > 0.95);
- univariate filtering by association with the binary label, FDR-corrected at q < 0.10 (with fallback rule, section 11);
- regularisation hyperparameter tuning by inner CV;
- model fitting.

The held-out fold remains untouched until prediction generation.

---

## 10. Adjustment for age

**Age is not included in the primary image-only models.** The primary analysis evaluates radiomic discrimination from the image alone, without adjustment.

Age handling is assigned to sensitivity analyses (see section 14.4).

Rationale for moving age out of the primary pipeline: residualisation requires per-fold estimation from healthy controls within the training fold, which is unstable with the available number of controls per fold and could introduce variability not attributable to the imaging signal. The sensitivity analyses test whether results are robust to age handling.

---

## 11. Feature selection

Within each training fold:

1. **Correlation filter.** Iterative removal of features with |Pearson r| > 0.95, retention prioritised by univariate effect size against the binary label.
2. **Univariate filter.** Mann–Whitney U test, two-sided, Benjamini–Hochberg FDR correction. Retain features with q < 0.10.

**Fallback rule.** If fewer than 10 features survive the FDR filter in any training fold, the model uses the **top 10 features ranked by univariate p-value** within that fold instead, and the fold is flagged in the supplement as having triggered the fallback. The number of folds (out of 250) that triggered the fallback is reported.

The L2 regulariser provides additional shrinkage on the surviving feature set.

**Stability reporting (supplementary).** Across all 250 folds, per feature: selection frequency, ROI of origin, feature family, mean signed effect direction, top-20 most frequently retained features.

---

## 12. Performance metrics

For every model and every endpoint:

- **Discrimination (primary).** AUC-ROC, AUC-PR, accuracy, sensitivity, specificity, F1.
- **Calibration (descriptive only, given n = 62).** Brier score in main tables; calibration intercept, calibration slope, and calibration plot in supplement.
- **Uncertainty.** Mean ± SD across 250 fold evaluations.

Bootstrap confidence intervals are computed at the **participant level**, not the fold-evaluation level. For each participant, the out-of-fold predicted probabilities across the 50 repetitions are averaged into a single per-participant prediction; bias-corrected and accelerated (BCa) bootstrap CIs are then computed on this participant-level prediction set with 2000 resamples.

Positive class throughout: pathological.

---

## 13. Primary statistical contrast

**Model 7 (Dual-ROI radiomics) versus Model 2 (continuous mean echointensity).**

**Primary test.** Paired bootstrap on the difference in AUC-ROC computed from the participant-level aggregated out-of-fold predictions (one prediction per participant per model). 2000 resamples at the participant level, BCa intervals, two-sided, α = 0.05.

**Secondary equivalent statistic.** DeLong test on the same participant-level aggregated predictions.

**Rejection criterion for H₀.** Statistically significant positive ΔAUC-ROC (Model 7 − Model 2) at α = 0.05 with the BCa 95% CI excluding zero. **Calibration is reported descriptively to inform clinical interpretability and is not part of the H₀-rejection criterion.**

The same testing framework is applied to the secondary mechanistic contrast (Model 4 vs Model 2), which is supportive and not used to reject the primary H₀.

---

## 14. Robustness and sensitivity analyses

### 14.1 Permutation testing

Class labels permuted at participant level, 1000 permutations, full pipeline (feature selection, CV, model fitting) re-executed each time. Empirical p-value for the primary contrast.

### 14.2 Inter-seed stability

Variance in performance across 50 random seeds reported. Models whose performance depends critically on a small subset of seeds will be flagged in the supplement.

### 14.3 SMA-excluded sensitivity (n = 52)

Full primary analysis re-run with all SMA cases excluded.

### 14.4 Age sensitivity (three variants)

- **14.4a — Age as covariate.** Primary models re-fit with age added as a predictor.
- **14.4b — Age + subcutaneous fat as covariates.** Tests joint effect of age and acoustic-attenuation confounding.
- **14.4c — Age-residualised features.** Per-feature linear residualisation against age, estimated from training-fold healthy controls only, applied to all training and held-out features within the fold.

These three variants test whether the primary result is robust to age handling. Disagreement between variants is reported and discussed.

### 14.5 Classifier sensitivity

Primary contrast re-run with linear SVM (Platt-scaled) and Random Forest. Reported in supplement.

### 14.6 Optional shape-feature sensitivity

If reviewer requests, primary models re-fit with shape features added.

---

## 15. Heckmatt-analogue Grade 2 ambiguity-zone analysis (prespecified, exploratory)

**Subgroup definition.** Participants with 40 ≤ RF mean echointensity < 55 (Heckmatt-analogue Grade 2). Anticipated n at SAP lock: 16 (8 healthy, 8 pathological).

**Inclusion threshold for inferential metrics.** Full classification metrics (AUC, BCa CI, permutation p) are reported only if both classes contain ≥ 6 participants. If either class falls below 6, the analysis is reported as descriptive only (medians and IQRs of selected features by class), with no AUC, no accuracy, and no permutation test.

**Models compared (subgroup-restricted).** Models 2, 3, 4, 5, 6, 7. Model 1 is excluded (Heckmatt-analogue grade is constant within Grade 2).

**Outputs.** AUC-ROC mean ± SD, BCa 95% CI where computable, permutation p-value (1000 permutations).

**Permitted interpretive framing.**

> "Within the Heckmatt-analogue Grade 2 subgroup — where scalar echointensity is range-restricted and expected to be less informative — radiomic features retained discriminative signal. Because of subgroup size, this analysis is exploratory and requires external validation."

**Prohibited interpretive framing (excluded a priori regardless of result direction or magnitude).**

- "Radiomics resolves Heckmatt Grade 2."
- "Radiomics replaces echointensity grading."
- "Radiomics provides a clinically deployable Grade 2 biomarker."
- "The Grade 2 result is confirmatory."

---

## 16. Planned tables

**Table 1.** Cohort characteristics — healthy versus pathological. Variables: n, age, sex, RF thickness, subcutaneous fat thickness, RF mean echointensity, Heckmatt-analogue grade distribution, pathological subgroup composition.

**Table 2.** Primary endpoint — model hierarchy performance (Models 1–7). Columns: AUC-ROC (mean ± SD, 95% participant-level BCa CI), AUC-PR, accuracy, sensitivity, specificity, F1, Brier.

**Table 3.** Primary contrast (Model 7 vs Model 2) and secondary mechanistic contrast (Model 4 vs Model 2): point estimate of ΔAUC, BCa 95% CI, bootstrap p, DeLong p, permutation p.

**Table 4.** Heckmatt-analogue Grade 2 exploratory subgroup — Models 2, 3, 4, 5, 6, 7. Columns: n total, n healthy, n pathological, AUC, 95% CI where computable, permutation p.

**Supplementary Table 1.** Diagnosis-level breakdown of pathological group.

**Supplementary Table 2.** Feature-selection stability across 250 folds, including fallback-trigger frequency.

**Supplementary Table 3.** SMA-excluded sensitivity (n = 52).

**Supplementary Table 4.** Age sensitivity variants 14.4a–c.

**Supplementary Table 5.** Classifier sensitivity (SVM, RF) for Model 7.

**Supplementary Table 6.** Calibration metrics (intercept, slope) for all models.

**Supplementary Table 7.** Cohort cleaning record.

---

## 17. Planned figures

**Figure 1.** Study design and model hierarchy schematic.

**Figure 2.** Echointensity ambiguity figure — distribution of RF mean echointensity by binary label, with Heckmatt-analogue threshold lines and shaded Grade 2 zone. *Manuscript hook figure.*

**Figure 3.** Primary endpoint — AUC by model, with participant-level BCa 95% CIs and primary-contrast annotation.

**Figure 4.** Heckmatt-analogue Grade 2 exploratory subgroup — performance comparison.

**Supplementary Figure 1.** Calibration plots for Models 2 and 7.

**Supplementary Figure 2.** Feature-selection frequency heatmap.

**Supplementary Figure 3.** Permutation null distributions for primary and secondary contrasts.

**Supplementary Figure 4.** PCA and LDA visualisations of the dual-ROI feature space.

---

## 18. Reproducibility and transparency

- **Code release.** GitHub + Zenodo DOI prior to manuscript submission.
- **Data release.** De-identified SAP-locked feature matrix and binary labels alongside code, subject to GDPR review. Raw DICOM not released; access on reasonable request and IRB approval.
- **Environment.** Python 3.10; scikit-learn ≥ 1.3; numpy, pandas, scipy, statsmodels at versions pinned in `requirements.txt`. Random seed master list deposited with code.
- **Pre-registration.** This SAP v1.1, in its locked form, deposited at OSF with timestamped DOI before any classification model is fit on the SAP-locked final cohort under the locked protocol. Prior exploratory analyses on earlier cohort versions are disclosed in section 0.

---

## 19. Permitted and prohibited claims

### 19.1 Permitted

- Radiomic models improved detection of pathological muscle in this paediatric cohort (if observed).
- Texture-only radiomics retained signal beyond mean echointensity (if observed).
- Heckmatt-analogue Grade 2 is a clinically relevant ambiguity zone where scalar echointensity is range-restricted and expected to be less informative.
- Within Grade 2, radiomic features retained discriminatory signal in this exploratory subgroup analysis (if observed).
- Findings require external validation in a larger, multicentre paediatric cohort before clinical translation.

### 19.2 Prohibited regardless of result

- Radiomics demonstrates etiologic classification (myogenic vs neurogenic).
- Radiomics replaces electromyography, nerve conduction studies, or muscle biopsy.
- Radiomics is ready for clinical deployment.
- ROI2 has a proven biological mechanism beyond what the data supports.
- The model is externally generalisable.
- The biomarker is validated.
- The Grade 2 subgroup analysis is confirmatory.

---

## 20. Deviations and amendments

Any deviation from this SAP after lock — thresholds, model definitions, contrast specification, interpretive framing — will be documented in a deviations log appended to the supplement and explicitly flagged in the manuscript text. Post-hoc analyses prompted by data inspection will be reported separately and labelled "post-hoc, exploratory".

---

**End of SAP v1.1 — LOCKED.**

*Signed (electronic).* José Fernández-Cuesta Peñafiel, MD — ORCID 0000-0003-3080-1100.

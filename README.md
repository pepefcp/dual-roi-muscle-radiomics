# dual-roi-muscle-radiomics

**Radiomic analysis of muscle ultrasound improves detection of pathological muscle in children: a single-center proof-of-concept study**

*(Title of the revised manuscript, November 2026; submitted in May 2026 as "Dual-region-of-interest radiomic muscle ultrasound for detection of pathological muscle in children: a single-center proof-of-concept study".)*

This repository contains the locked Statistical Analysis Plan (SAP), analysis code, and derived results for the manuscript currently under review at *Muscle & Nerve*.

---

## Pre-registration

The Statistical Analysis Plan (`SAP_v1.1_LOCKED.docx` / `SAP_v1.1_LOCKED.md`) was finalized and locked **before any model was fitted on the locked cohort**. The analyses were executed from 30 April 2026, and the plan was registered at the Open Science Framework on 4 May 2026, before submission.

- **OSF Registration DOI:** https://doi.org/10.17605/OSF.IO/AX74E (registered 4 May 2026)
- **OSF Project URL:** https://osf.io/9pc4g

Any deviation from the SAP is recorded in `DEVIATIONS_LOG.md` and explicitly flagged in the manuscript text. Post-hoc analyses are labelled as such.

---

## Cohort summary

| Group | n |
|---|---|
| Healthy controls | 23 |
| Pathological — myogenic | 16 |
| Pathological — neurogenic | 13 |
| Pathological — SMA-I/II/III | 3 + 4 + 3 |
| **Total** | **62** |

---

## Endpoints (locked, see SAP §5)

| Endpoint | Definition | n | Status |
|---|---|---|---|
| Primary | Healthy vs Pathological detection, full cohort | 62 | confirmatory |
| Exploratory | Healthy vs Pathological within echointensity stratum Grade 2 | 16 | exploratory |
| Sensitivity | Healthy vs Pathological, SMA excluded | 52 | sensitivity |

**Primary contrast.** Model 7 (Dual-ROI full radiomics) vs Model 2 (continuous mean echointensity).

**Inferential test.** Participant-level paired bootstrap on aggregated out-of-fold predictions, BCa 95% CI, 2000 resamples, two-sided α = 0.05.

**Primary result (revised manuscript).** ΔAUC = +0.217 (BCa 95% CI +0.116 to +0.351; bootstrap p < 0.001; DeLong p < 0.001), full 50-seed protocol on the matrix with the corrected covariate pairing. The submitted version reported the 25-seed execution, +0.220 (+0.113 to +0.358). Null hypothesis rejected per the prespecified criterion under both. See `DEVIATIONS_LOG.md` and `CHANGELOG.md`.

---

## Repository structure

```
.
├── SAP_v1.1_LOCKED.docx         # Locked Statistical Analysis Plan (Word)
├── SAP_v1.1_LOCKED.md           # Locked SAP (markdown source)
├── DEVIATIONS_LOG.md            # Post-lock deviations record
├── RESULTS_SYNTHESIS.md         # Plain-text synthesis of all results
├── requirements.txt             # Pinned Python environment
├── seeds.json                   # 50 random seeds (locked at SAP deposit)
├── README.md
├── LICENSE
├── src/
│   ├── 01_load_and_prepare.py   # Cohort assembly per SAP §4
│   ├── 12_covariate_pairing_correction.py  # Correction 4 applied to the locked matrix (run after 01)
│   ├── 02_descriptives.py       # Descriptives (superseded for Table 1 by 09)
│   ├── 03_primary_analysis.py   # Models 1–7, primary endpoint, primary contrast (Correction 6 applied)
│   ├── 04_grade2_analysis.py    # Intermediate echointensity stratum (stratum 2), exploratory
│   ├── 05_sensitivity.py        # SMA-excluded, age covariate, classifier sensitivity (args: n_seeds n_boot)
│   ├── 06_permutation.py        # Permutation null distribution (supportive)
│   ├── 07_reviewer2.py          # Stability, selection frequency, calibration (50 locked seeds, Models 3–7)
│   ├── 09_table1_final.py       # Table 1 with Corrections 1–2
│   ├── 10_age_adiposity_sensitivity.py  # SAP 14.4b–c
│   ├── 11_duplicate_pair_sensitivity.py # Duplicated-image pairs excluded (n = 60)
│   ├── 13_exclusion_analyses.py # Each enrolment group excluded in turn
│   └── lib/
│       └── analysis.py          # CV, feature selection, models, metrics, contrasts
└── results/
    ├── tables/                  # Tables 1–4 + supplementary (CSV)
    ├── figures/                 # Figures 2–4 + supplementary (PNG/PDF)
    └── logs/                    # Execution logs
```

---

## Reproducibility

All preprocessing, feature selection, and hyperparameter tuning operations are restricted to the training fold within each cross-validation iteration to prevent data leakage. The analysis pipeline is deterministic given the seeds in `seeds.json`.

```bash
# 1. Create environment
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Run analysis pipeline (configuration of the revised manuscript)
python src/01_load_and_prepare.py
python src/12_covariate_pairing_correction.py   # Correction 4
python src/09_table1_final.py                   # Table 1
python src/03_primary_analysis.py               # Tables 3-4, 50 locked seeds, 2,000 resamples
python src/04_grade2_analysis.py                # Table 5
python src/07_reviewer2.py                      # Suppl. Tables 3-5
python src/06_permutation.py                    # Suppl. Figure 2 (Deviation 2)
# Suppl. Table 7 (25 seeds, 1,000 resamples): 05 writes the age-covariate row, 10 appends rows 14.4b-c
python src/05_sensitivity.py 25 1000
python src/10_age_adiposity_sensitivity.py
cp results/tables/Suppl_Table_4_age_covariate.csv results/tables/Suppl_Table_4_age_covariate.keep.csv
# Suppl. Tables 6 (SMA row) and 8 (50 seeds, 2,000 resamples); this run also rewrites the
# age-covariate file with a 50-seed row that is not used, hence the copy above
python src/05_sensitivity.py 50 2000
mv results/tables/Suppl_Table_4_age_covariate.keep.csv results/tables/Suppl_Table_4_age_covariate.csv
python src/11_duplicate_pair_sensitivity.py
python src/13_exclusion_analyses.py             # Suppl. Table 6
# Submitted (May 2026) values: python src/03_primary_analysis.py 25 without step 12 (Models 1, 2 and 5-7;
# Models 3-4 differ by Correction 6)
```

All outputs are written to `results/`.

---

## Correspondence between repository names and the revised manuscript

| Repository | Revised manuscript |
|---|---|
| Model 1, "Heckmatt-analogue grade" | Echointensity stratum (ordinal comparator) |
| Model 2, RF mean echointensity | Mean echointensity (comparator) |
| Model 3 / Model 4 | First-order radiomics / texture-only radiomics |
| Model 5 / Model 6 | ROI1 (intramuscular) / ROI2 (full thickness) |
| Model 7, "Dual-ROI full radiomics" | Combined-region radiomics |
| "Grade 2" subgroup | Intermediate echointensity stratum (stratum 2) |
| `myogenic-LaPaz` / `neurogenic-LaPaz` | Myopathic / neurogenic enrolment groups |
| `results/tables/Table_3_primary_endpoint.csv`, `Table_4_contrasts.csv`, `Table_5_stratum2_*.csv` | Tables 3, 4 and 5 |
| `Suppl_Table_R2a/R2c/R2b_*.csv` | Supplementary Tables 3, 4 and 5 |
| `Suppl_Table_3_SMA_excluded.csv`, `Suppl_Table_6_*.csv` | Supplementary Table 6 |
| `Suppl_Table_4_age_covariate.csv` | Supplementary Table 7 |
| `Suppl_Table_5_classifier_sensitivity.csv` | Supplementary Table 8 |
| `Suppl_Table_8_permutation.csv` | Supplementary Figure 2 |

Plots in `results/figures/` are regenerated by the scripts; the CSV tables are authoritative.

---

## Data availability

This repository **does not contain raw patient data**.

- **De-identified summary tables** with aggregated cohort statistics are provided in `results/tables/`.
- **Raw DICOM ultrasound images** are not released under the IRB approval (Ref. HULP/PI-248-2017) and the Spanish Biomedical Research Law 14/2007 framework. Access on reasonable request to the corresponding author and subject to ethical review.
- **Cohort cleaning script** (`src/01_load_and_prepare.py`) references participants by anonymous identifiers (`PARTICIPANT_001` … `PARTICIPANT_006`) in the public release. The cleaning logic is unchanged from the locked SAP record.

---

## Citation

*[To be added on manuscript acceptance.]*

---

## License

- **Code:** MIT License (see `LICENSE`)
- **Statistical Analysis Plan and manuscript text:** CC-BY 4.0

---

## Corresponding author

**José Fernández-Cuesta Peñafiel, MD**
ORCID: [0000-0003-3080-1100](https://orcid.org/0000-0003-3080-1100)

---

## Acknowledgments

This work was supported by a research grant from the **Sociedad Española de Neurología Pediátrica (SENEP)**. Radiomic feature extraction used the **QUIBIM QP-Discovery** platform (QUIBIM S.L., Valencia, Spain).

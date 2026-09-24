# dual-roi-muscle-radiomics

**Dual-ROI radiomic muscle ultrasound for detection of pathological muscle in children: a single-center proof-of-concept study**

This repository contains the locked Statistical Analysis Plan (SAP), analysis code, and derived results for the manuscript currently under review at *Muscle & Nerve*.

---

## Pre-registration

The Statistical Analysis Plan (`SAP_v1.1_LOCKED.docx` / `SAP_v1.1_LOCKED.md`) was finalized **before model fitting on the locked final cohort under the locked protocol**, and was archived at the Open Science Framework prior to analysis.

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

**Primary result.** ΔAUC = +0.220 (BCa 95% CI +0.113 to +0.358; bootstrap p<0.001; DeLong p<0.001). Null hypothesis rejected per the prespecified criterion.

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
│   ├── 02_descriptives.py       # Table 1 + Figure 2
│   ├── 03_primary_analysis.py   # Models 1–7, primary endpoint, primary contrast
│   ├── 04_grade2_analysis.py    # echointensity stratum Grade 2 exploratory analysis
│   ├── 05_sensitivity.py        # SMA-excluded, age covariate, classifier sensitivity
│   ├── 06_permutation.py        # Permutation null distribution (supportive)
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

# 2. Run analysis pipeline
python src/01_load_and_prepare.py
python src/02_descriptives.py
python src/03_primary_analysis.py
python src/04_grade2_analysis.py
python src/05_sensitivity.py
python src/06_permutation.py
```

All outputs are written to `results/`.

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

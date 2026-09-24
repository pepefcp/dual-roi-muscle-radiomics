# Revision update 2 — age and adiposity sensitivity analyses

Adds `src/10_age_adiposity_sensitivity.py`, which extends SAP §14.4 with two
post-hoc, reviewer-prompted analyses (labeled as such in the manuscript):

- 14.4b — age + subcutaneous fat thickness appended as covariates to Model 2 and Model 7.
- 14.4c — all radiomic features and the echointensity comparator replaced by their
  residuals from a linear regression on age (estimated on the full cohort without
  reference to group labels).

`results/tables/Suppl_Table_4_age_covariate.csv` now carries the three rows
(14.4a/b/c) reported in Supplementary Table 7 of the revised manuscript.
Subcutaneous fat per participant (`data/fat_by_participant.csv`, anonymous
participant_id + millimeters only) derives from the author-reviewed source
records used for Table 1.

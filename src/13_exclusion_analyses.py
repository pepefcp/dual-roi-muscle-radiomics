'''13_exclusion_analyses.py — primary contrast (Model 7 vs Model 2) with each enrolment group
excluded in turn and with one member of each duplicated-image pair excluded (Supplementary
Table 6 of the revised manuscript). 50 locked seeds, 2,000 resamples, corrected matrix.'''
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / 'src'))
from lib.analysis import run_cv, aggregate_oof, bca_bootstrap_auc, paired_bootstrap_delta_auc
full=pd.read_parquet(REPO / 'data' / 'cohort_locked.parquet')
seeds=json.load(open(REPO / 'seeds.json'))['seeds']
# rows of the nine participants with an upper motor neuron cause (Supplementary Table 2), identified from the clinical records
umn=set(json.load(open(REPO / 'data' / 'umn_rows.json')))
dup=[54,55]   # rows holding platform images IMG-0002-00009B(II) and IMG-0001-000013A (second member of each duplicated pair)
feat=[c for c in full.columns if c.startswith(('ROI1_','ROI2_'))]
def contrast(df,label):
    y=df['binary_label'].to_numpy()
    o2=aggregate_oof(run_cv(df[['RF_EI']].to_numpy(float),y,seeds=seeds,n_folds=5,classifier='logreg',do_feature_selection=False)['oof_by_seed'])
    o7=aggregate_oof(run_cv(df[feat].to_numpy(float),y,seeds=seeds,n_folds=5,classifier='logreg',do_feature_selection=True)['oof_by_seed'])
    a2=bca_bootstrap_auc(y,o2,n_boot=2000,seed=42); a7=bca_bootstrap_auc(y,o7,n_boot=2000,seed=42)
    d,lo,hi,p=paired_bootstrap_delta_auc(y,o7,o2,n_boot=2000,seed=42)
    row=dict(Analysis=label,n=len(df),controls=int((y==0).sum()),pathological=int((y==1).sum()),M2=f"{a2[0]:.3f} ({a2[1]:.3f}–{a2[2]:.3f})",M7=f"{a7[0]:.3f} ({a7[1]:.3f}–{a7[2]:.3f})",dAUC=f"{d:+.3f}",CI=f"{lo:+.3f} to {hi:+.3f}",p=f"{p:.4f}")
    print(row, flush=True); return row
rows=[]
print('UMN rows', sorted(umn), 'subgroups', full.subgroup[sorted(umn)].tolist(), flush=True)
rows.append(contrast(full.drop(index=sorted(umn)).reset_index(drop=True),'Upper motor neuron causes excluded'))
rows.append(contrast(full.drop(index=dup).reset_index(drop=True),'Duplicated-image pairs, one member excluded'))
rows.append(contrast(full[full.subgroup!='myogenic-LaPaz'].reset_index(drop=True),'Myopathic causes excluded'))
pn=[i for i in full.index[full.subgroup=='neurogenic-LaPaz'] if i not in umn]
print('peripheral-nerve rows', len(pn), flush=True)
rows.append(contrast(full.drop(index=pn).reset_index(drop=True),'Peripheral nerve causes excluded'))
pd.DataFrame(rows).to_csv(REPO / 'results' / 'tables' / 'Suppl_Table_6_exclusion_analyses.csv', index=False)

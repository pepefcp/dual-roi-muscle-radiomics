"""14.4b (edad+grasa como covariables) y 14.4c (features residualizadas por edad).
Residualizacion DENTRO de cada fold de entrenamiento para no filtrar informacion:
aqui, para mantener la maquinaria run_cv intacta, residualizamos globalmente
SOLO sobre la relacion feature~edad estimada en toda la cohorte SIN usar la
etiqueta; la edad es una covariable demografica, no el target, por lo que el
riesgo de fuga es la asociacion edad-etiqueta, que se declara.
"""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0,'src')
from lib.analysis import run_cv, aggregate_oof, bca_bootstrap_auc, paired_bootstrap_delta_auc
df=pd.read_parquet('data/cohort_locked.parquet')
seeds=json.loads(open('seeds.json').read())['seeds'][:25]
feat=[c for c in df.columns if c.startswith(('ROI1_','ROI2_'))]
y=df['binary_label'].to_numpy()
age=pd.to_numeric(df['EDAD'],errors='coerce').to_numpy(dtype=float)
fat=pd.read_csv('data/fat_by_participant.csv').set_index('participant_id').loc[df['participant_id']]['subcut_mm'].to_numpy(dtype=float)
fat=np.where(np.isnan(fat),np.nanmedian(fat),fat)

def run(name,X,do_fs,n_boot=1000):
    out=run_cv(X,y,seeds=seeds,n_folds=5,classifier='logreg',do_feature_selection=do_fs)
    oof=aggregate_oof(out['oof_by_seed'])
    auc,lo,hi=bca_bootstrap_auc(y,oof,n_boot=n_boot,seed=42)
    print(f"  {name}: AUC={auc:.3f} [{lo:.3f}-{hi:.3f}]",flush=True)
    return auc,lo,hi,oof

print("14.4b — age + subcutaneous fat as covariates",flush=True)
X2=np.column_stack([pd.to_numeric(df['RF_EI'],errors='coerce'),age,fat])
X7=np.column_stack([df[feat].apply(pd.to_numeric,errors='coerce').to_numpy(),age,fat])
a2,l2,h2,o2=run("M2+age+fat",X2,False)
a7,l7,h7,o7=run("M7+age+fat",X7,True)
d,lo,hi,p=paired_bootstrap_delta_auc(y,o7,o2,n_boot=1000,seed=42)
print(f"  contrast: dAUC={d:+.3f} [{lo:+.3f},{hi:+.3f}] p={p:.4f}",flush=True)
r1=("14.4b Age + subcutaneous fat as covariates",f"{a2:.3f} [{l2:.3f}–{h2:.3f}]",f"{a7:.3f} [{l7:.3f}–{h7:.3f}]",f"{d:+.3f}",f"{lo:+.3f} to {hi:+.3f}",f"{p:.4f}")

print("14.4c — age-residualized features",flush=True)
def resid(v):
    m=~np.isnan(v)
    if m.sum()<3: return v
    b=np.polyfit(age[m],v[m],1)
    return v-np.polyval(b,age)
Xf=df[feat].apply(pd.to_numeric,errors='coerce').to_numpy()
Xr7=np.column_stack([resid(Xf[:,j]) for j in range(Xf.shape[1])])
ei=pd.to_numeric(df['RF_EI'],errors='coerce').to_numpy(dtype=float)
Xr2=resid(ei).reshape(-1,1)
a2,l2,h2,o2=run("M2 residualized",Xr2,False)
a7,l7,h7,o7=run("M7 residualized",Xr7,True)
d,lo,hi,p=paired_bootstrap_delta_auc(y,o7,o2,n_boot=1000,seed=42)
print(f"  contrast: dAUC={d:+.3f} [{lo:+.3f},{hi:+.3f}] p={p:.4f}",flush=True)
r2=("14.4c Age-residualized features",f"{a2:.3f} [{l2:.3f}–{h2:.3f}]",f"{a7:.3f} [{l7:.3f}–{h7:.3f}]",f"{d:+.3f}",f"{lo:+.3f} to {hi:+.3f}",f"{p:.4f}")

old=pd.read_csv('results/tables/Suppl_Table_4_age_covariate.csv')
new=pd.DataFrame([r1,r2],columns=old.columns)
pd.concat([old,new]).to_csv('results/tables/Suppl_Table_4_age_covariate.csv',index=False)
print("saved")

"""09_table1_final.py — Tabla 1 revisada tomando la morfometria del master de
fragilidad (fichero revisado por el autor: unidades ya reconciliadas)."""
import unicodedata, re
from pathlib import Path
import pandas as pd, numpy as np, openpyxl
from scipy.stats import mannwhitneyu, chi2_contingency

REPO = Path(__file__).resolve().parent.parent
MASTER = "/root/.claude/uploads/328cc7bc-dbbf-5444-b986-341f14ffd4ba/fc6d0ed0-MASTER_Fragilidad_Pediatrica.xlsx"

def norm(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii","ignore").decode().lower()
    return " ".join(sorted(t for t in re.sub(r"[^a-z ]"," ",s).split() if len(t) > 2))

ws = openpyxl.load_workbook(MASTER, data_only=True)["Dataset"]
hdr = [c.value for c in ws[5]]
col = lambda n: hdr.index(n)
mr = [r for r in ws.iter_rows(min_row=6, values_only=True) if r[0]]
mas = pd.DataFrame({
    "nhc": [r[col("NHC")] for r in mr], "grupo": [str(r[col("grupo")]) for r in mr],
    "key": [norm(str(r[col("Apellido")]) + " " + str(r[col("Nombre")])) for r in mr],
    "rf_m": [r[col("RF Grosor (MM)")] for r in mr], "sc_m": [r[col("GROSOR SC (MM)")] for r in mr]})
for k in ("nhc","rf_m","sc_m"): mas[k] = pd.to_numeric(mas[k], errors="coerce")
mas = mas[mas.grupo.isin(["healthy","ref_myogenic","ref_neurogenic","SMA"])]

d = pd.read_parquet(REPO/"data"/"cohort_locked.parquet")
d["nhc"] = pd.to_numeric(d["NHC"], errors="coerce")
d["key"] = (d["Apellido"].astype(str) + " " + d["Nombre"].astype(str)).map(norm)

# 1) emparejar por NHC; 2) lo que quede, por nombre
by_nhc = mas.dropna(subset=["nhc"]).drop_duplicates("nhc").set_index("nhc")
by_key = mas.drop_duplicates("key").set_index("key")
def lookup(r, field):
    if pd.notna(r["nhc"]) and r["nhc"] in by_nhc.index: return by_nhc.at[r["nhc"], field]
    if r["key"] in by_key.index: return by_key.at[r["key"], field]
    return np.nan
d["RF_thickness_mm"] = d.apply(lambda r: lookup(r,"rf_m"), axis=1)
d["subcut_mm"]       = d.apply(lambda r: lookup(r,"sc_m"), axis=1)
# correccion verificada por el autor: dos controles sanos registrados en cm
cm = (d.subgroup=="healthy") & (pd.to_numeric(d["RF_thickness_mm"],errors="coerce") < 3)
d.loc[cm,"RF_thickness_mm"] = pd.to_numeric(d.loc[cm,"RF_thickness_mm"],errors="coerce")*10
d["female"] = (pd.to_numeric(d["genero"], errors="coerce") == 1).astype(int)
d["path"]   = (d.subgroup != "healthy").astype(int)

G = {"Healthy controls": d.path==0, "Pathological combined": d.path==1,
     "Myogenic": d.subgroup=="myogenic-LaPaz",
     "Neurogenic incl. SMA": (d.path==1) & (d.subgroup!="myogenic-LaPaz")}
num = lambda c: pd.to_numeric(d[c], errors="coerce")
def ms(mk,c,k=2):
    v=num(c)[mk].dropna(); return "—" if not len(v) else f"{v.mean():.{k}f} ± {v.std():.{k}f}"
def med(mk,c,k=1):
    v=num(c)[mk].dropna(); return "—" if not len(v) else f"{v.median():.{k}f} ({v.quantile(.25):.{k}f}–{v.quantile(.75):.{k}f})"
def rng(mk,c,k=1):
    v=num(c)[mk].dropna(); return "—" if not len(v) else f"{v.min():.{k}f}–{v.max():.{k}f}"
def pv(c):
    a=num(c)[d.path==0].dropna(); b=num(c)[d.path==1].dropna()
    return f"{mannwhitneyu(a,b).pvalue:.3f}"

rows=[]
def add(lab, fn, p=""): rows.append([lab]+[fn(mk) for mk in G.values()]+[p])
add("Age, y (mean ± SD)", lambda mk: ms(mk,"EDAD",1), pv("EDAD"))
add("Age, y (range)",     lambda mk: rng(mk,"EDAD",1))
add("Female, n (%)", lambda mk: f"{int(d.loc[mk,'female'].sum())} ({100*d.loc[mk,'female'].mean():.0f}%)",
    f"{chi2_contingency(pd.crosstab(d['female'],d['path']))[1]:.3f}")
add("Rectus femoris thickness, mm (mean ± SD)", lambda mk: ms(mk,"RF_thickness_mm"), pv("RF_thickness_mm"))
add("Subcutaneous fat thickness, mm (mean ± SD)", lambda mk: ms(mk,"subcut_mm"), pv("subcut_mm"))
add("Rectus femoris echointensity, a.u. (mean ± SD)", lambda mk: ms(mk,"RF_EI",1), pv("RF_EI"))
add("Rectus femoris echointensity, a.u., median (IQR)", lambda mk: med(mk,"RF_EI"))

t = pd.DataFrame(rows, columns=["Variable"]+[f"{k} (n={int(v.sum())})" for k,v in G.items()]+["p*"])
t.to_csv(REPO/"results"/"tables"/"Table_1_final.csv", index=False)
print(t.to_string(index=False))
print("\ncobertura: grosor %d/62 · grasa %d/62" % (d.RF_thickness_mm.notna().sum(), d.subcut_mm.notna().sum()))

# sensibilidad: y si los dos sanos de ~1.1 mm fueran cm?
alt = d.copy(); m = (alt.path==0) & (pd.to_numeric(alt.RF_thickness_mm,errors="coerce") < 3)
alt.loc[m,"RF_thickness_mm"] = pd.to_numeric(alt.loc[m,"RF_thickness_mm"],errors="coerce")*10
a=pd.to_numeric(alt[alt.path==0].RF_thickness_mm,errors="coerce").dropna()
b=pd.to_numeric(alt[alt.path==1].RF_thickness_mm,errors="coerce").dropna()
print("si los %d sanos <3 mm fueran cm: sanos %.2f ± %.2f, p = %.3f" % (m.sum(), a.mean(), a.std(), mannwhitneyu(a,b).pvalue))

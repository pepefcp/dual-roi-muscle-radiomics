"""
02_descriptives.py — SAP §16 Table 1 + SAP §17 Figure 2.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data" / "cohort_locked.parquet"
TABLES = REPO / "results" / "tables"
FIGS = REPO / "results" / "figures"


def fmt(x, d=1):
    return f"{x:.{d}f}" if pd.notna(x) else "—"


def descriptive_row(df, label):
    n = len(df)
    age = df["EDAD"]
    fem = (df["genero"] == 1).sum()   # corregido: la columna esta codificada 0/1, no 1/2
    rf_th = df["RF_thickness_mm"]
    sf = df["VI AREA "]  # not subcutaneous fat — use what's available
    ei = df["RF_EI"]
    return {
        "Variable": label,
        "n": n,
        "Age, y (mean ± SD)": f"{fmt(age.mean())} ± {fmt(age.std())}",
        "Age, y (range)": f"{fmt(age.min())}–{fmt(age.max())}",
        "Female, n (%)": f"{fem} ({fem/n*100:.0f}%)",
        "RF thickness, mm (mean ± SD)": f"{fmt(rf_th.mean(), 2)} ± {fmt(rf_th.std(), 2)}",
        "RF EI, a.u. (mean ± SD)": f"{fmt(ei.mean())} ± {fmt(ei.std())}",
        "RF EI, a.u. (median)": f"{fmt(ei.median())}",
    }


def heckmatt_row(df, label):
    n = len(df)
    counts = df["Heckmatt_grade"].value_counts().reindex([1, 2, 3, 4], fill_value=0)
    return {
        "Group": label,
        "n": n,
        "Grade 1, n (%)": f"{counts[1]} ({counts[1]/n*100:.0f}%)",
        "Grade 2, n (%)": f"{counts[2]} ({counts[2]/n*100:.0f}%)",
        "Grade 3, n (%)": f"{counts[3]} ({counts[3]/n*100:.0f}%)",
        "Grade 4, n (%)": f"{counts[4]} ({counts[4]/n*100:.0f}%)",
    }


def main():
    df = pd.read_parquet(DATA)
    print(f"Loaded n={len(df)} participants.")

    h = df[df["binary_label"] == 0]
    p = df[df["binary_label"] == 1]
    myo = df[df["subgroup"] == "myogenic-LaPaz"]
    neu = df[df["subgroup"].isin(["neurogenic-LaPaz", "SMA-I", "SMA-II", "SMA-III"])]

    # Table 1a — main descriptives
    rows = [
        descriptive_row(h, "Healthy controls"),
        descriptive_row(p, "Pathological (combined)"),
        descriptive_row(myo, "  Myogenic"),
        descriptive_row(neu, "  Neurogenic (incl. SMA)"),
    ]
    table1a = pd.DataFrame(rows).T
    table1a.to_csv(TABLES / "Table_1a_descriptives.csv", header=False)
    print("\n=== Table 1a — Descriptives ===")
    print(table1a.to_string(header=False))

    # Group comparisons — healthy vs pathological
    print("\n=== Group comparisons (healthy vs pathological) ===")
    comparisons = []
    for var, label in [("EDAD", "Age"), ("RF_EI", "RF EI"), ("RF_thickness_mm", "RF thickness")]:
        a = h[var].dropna()
        b = p[var].dropna()
        # Mann-Whitney U
        u, pval = stats.mannwhitneyu(a, b, alternative="two-sided")
        comparisons.append({
            "Variable": label,
            "Healthy median (IQR)": f"{a.median():.2f} ({a.quantile(.25):.2f}–{a.quantile(.75):.2f})",
            "Pathological median (IQR)": f"{b.median():.2f} ({b.quantile(.25):.2f}–{b.quantile(.75):.2f})",
            "Mann-Whitney U p": f"{pval:.4f}",
        })
    # Sex
    cont = pd.crosstab(df["genero"], df["binary_label"])
    chi2, pval, _, _ = stats.chi2_contingency(cont)
    fem_h = (h["genero"] == 1).sum(); n_h = len(h)
    fem_p = (p["genero"] == 1).sum(); n_p = len(p)
    comparisons.append({
        "Variable": "Female n (%)",
        "Healthy median (IQR)": f"{fem_h} ({fem_h/n_h*100:.0f}%)",
        "Pathological median (IQR)": f"{fem_p} ({fem_p/n_p*100:.0f}%)",
        "Mann-Whitney U p": f"{pval:.4f} (chi2)",
    })
    df_comp = pd.DataFrame(comparisons)
    df_comp.to_csv(TABLES / "Table_1b_group_comparison.csv", index=False)
    print(df_comp.to_string(index=False))

    # Table 1c — Heckmatt distribution by group
    print("\n=== Table 1c — Heckmatt-analogue grade distribution ===")
    rows = [
        heckmatt_row(h, "Healthy"),
        heckmatt_row(myo, "Myogenic"),
        heckmatt_row(neu, "Neurogenic (incl. SMA)"),
        heckmatt_row(p, "All pathological"),
        heckmatt_row(df, "Total"),
    ]
    table1c = pd.DataFrame(rows)
    table1c.to_csv(TABLES / "Table_1c_heckmatt_distribution.csv", index=False)
    print(table1c.to_string(index=False))

    # ===== FIGURE 2 — Echointensity ambiguity (the hook figure) =====
    fig, ax = plt.subplots(figsize=(9, 6))

    # Shaded grade zones
    zones = [(0, 40, "#E8F5E9", "Grade 1"),
             (40, 55, "#FFF9C4", "Grade 2"),  # Highlighted
             (55, 72, "#FFE0B2", "Grade 3"),
             (72, 175, "#FFCDD2", "Grade 4")]
    for lo, hi, col, lbl in zones:
        ax.axvspan(lo, hi, alpha=0.4 if lbl == "Grade 2" else 0.18, color=col, zorder=0)

    # Vertical threshold lines
    for x in [40, 55, 72]:
        ax.axvline(x, color="grey", linestyle="--", linewidth=0.8, zorder=1)

    # Strip / scatter of EI by binary label
    rng = np.random.default_rng(42)
    h_ei = h["RF_EI"].values
    p_ei = p["RF_EI"].values
    ax.scatter(h_ei, np.full_like(h_ei, 1.0) + rng.uniform(-.15, .15, len(h_ei)),
               s=70, alpha=0.85, color="#1976D2", edgecolor="white", linewidth=0.8,
               label=f"Healthy (n={len(h_ei)})", zorder=3)
    ax.scatter(p_ei, np.full_like(p_ei, 0.4) + rng.uniform(-.15, .15, len(p_ei)),
               s=70, alpha=0.85, color="#C62828", edgecolor="white", linewidth=0.8,
               label=f"Pathological (n={len(p_ei)})", zorder=3)

    # Grade labels at top
    for lo, hi, _, lbl in zones:
        x = (lo + hi) / 2 if hi < 175 else 90
        weight = "bold" if lbl == "Grade 2" else "normal"
        size = 12 if lbl == "Grade 2" else 11
        ax.text(x, 1.55, lbl, ha="center", va="center", fontsize=size, fontweight=weight,
                color="black" if lbl == "Grade 2" else "#555")

    # Annotation arrow for Grade 2
    g2 = df[df["Heckmatt_grade"] == 2]
    g2_h = (g2["binary_label"] == 0).sum()
    g2_p = (g2["binary_label"] == 1).sum()
    ax.annotate(f"Ambiguity zone\n{g2_h} healthy vs {g2_p} pathological",
                xy=(47.5, 0.05), xytext=(95, -0.05),
                fontsize=11, ha="left",
                arrowprops=dict(arrowstyle="->", color="#555", lw=1.2),
                bbox=dict(boxstyle="round,pad=0.5", fc="#FFF9C4", ec="#888", lw=1))

    ax.set_xlim(20, 170)
    ax.set_ylim(-0.3, 1.8)
    ax.set_yticks([0.4, 1.0])
    ax.set_yticklabels(["Pathological", "Healthy"], fontsize=11)
    ax.set_xlabel("Rectus femoris mean echointensity (a.u.)", fontsize=12)
    ax.set_title("Heckmatt-analogue grading: scalar echointensity is ambiguous in Grade 2",
                 fontsize=13, pad=15)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(left=False)
    ax.grid(False)

    plt.tight_layout()
    plt.savefig(FIGS / "Figure_2_echointensity_ambiguity.png", dpi=200, bbox_inches="tight")
    plt.savefig(FIGS / "Figure_2_echointensity_ambiguity.pdf", bbox_inches="tight")
    plt.close()
    print(f"\nFigure 2 written: {FIGS / 'Figure_2_echointensity_ambiguity.png'}")


if __name__ == "__main__":
    main()

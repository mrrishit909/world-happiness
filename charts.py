"""Step 3: charts from results/.

    ./venv/bin/python charts.py   -> charts/01_change.png, 02_beyond.png, 03_easterlin.png, 04_types.png
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
INK, DIM, GRID, BG, BLUE, ORANGE = "#f2f2f0", "#8a8a87", "#1d1d1d", "#0b0b0b", "#3987e5", "#d95926"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG, "text.color": INK,
    "axes.edgecolor": "#3a3a3a", "axes.labelcolor": DIM, "xtick.color": DIM, "ytick.color": DIM,
    "axes.grid": True, "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 1,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.family": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": 11, "axes.titlesize": 13,
    "axes.titlelocation": "left", "axes.titlepad": 12,
})
R = HERE / "results"


def save(fig, name):
    fig.tight_layout()
    fig.savefig(HERE / "charts" / name, dpi=150)
    plt.close(fig)


def main():
    (HERE / "charts").mkdir(exist_ok=True)

    ch = pd.read_csv(R / "change.csv", index_col=0)
    ch.columns = ch.columns.astype(str)
    sel = pd.concat([ch.nsmallest(10, "change"), ch.nlargest(10, "change").iloc[::-1]])
    fig, ax = plt.subplots(figsize=(10, 6.2))
    y = np.arange(len(sel))
    for i, (_, r) in enumerate(sel.iterrows()):
        ax.plot([r["2012"], r["2025"]], [i, i], color=BLUE if r["change"] > 0 else ORANGE, linewidth=2)
    ax.scatter(sel["2012"], y, color=DIM, s=28, zorder=3, label="2010-12")
    ax.scatter(sel["2025"], y, color=INK, s=40, zorder=3, label="2023-25 (line: blue = rose, orange = fell)")
    ax.set_yticks(y, [f"{n} ({c:+.2f})" for n, c in zip(sel.index, sel["change"])])
    ax.axhline(9.5, color="#2a2a2a")
    ax.set_xlabel("life evaluation, 0-10")
    ax.grid(axis="y", visible=False)
    ax.legend(frameon=False, labelcolor=INK, loc="lower right")
    ax.set_title(f"Biggest risers and fallers, 2010-12 to 2023-25 ({int((ch['change'] > 0).sum())} of {len(ch)} countries rose)")
    save(fig, "01_change.png")

    b = pd.read_csv(R / "beyond_factors.csv", index_col=0).iloc[:, 0]
    sel = pd.concat([b.nsmallest(10), b.nlargest(10).iloc[::-1]])
    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.barh(sel.index, sel.values, color=[BLUE if v > 0 else ORANGE for v in sel.values], height=0.6)
    ax.axvline(0, color=DIM, linewidth=1)
    ax.set_xlabel("life evaluation above (+) or below (-) what the six factors predict, vs the average country")
    ax.grid(axis="y", visible=False)
    ax.set_title("Happier or less happy than the report's six factors predict (2023-25)")
    save(fig, "02_beyond.png")

    s = json.loads((R / "summary.json").read_text())["easterlin"]
    c25 = pd.read_csv(R / "countries_2025.csv").dropna(subset=["gdp_pc_ppp"])
    fd = pd.read_csv(R / "easterlin_first_differences.csv", index_col=0)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    x = np.log(c25["gdp_pc_ppp"])
    axes[0].scatter(x, c25["ladder"], s=14, color=BLUE, alpha=0.7)
    xs = np.linspace(x.min(), x.max(), 2)
    k = s["cross_section_2025"]["slope"]
    axes[0].plot(xs, c25["ladder"].mean() + k * (xs - x.mean()), color=INK, linewidth=1.5)
    axes[0].set_xlabel("log GDP per capita (PPP), 2023-25")
    axes[0].set_ylabel("life evaluation")
    axes[0].set_title(f"Across countries: slope {k:.2f}", fontsize=12)
    axes[1].scatter(fd["d_log_gdp"], fd["d_ladder"], s=14, color=BLUE, alpha=0.7)
    k2 = s["first_difference_2012_2025"]["slope"]
    xs = np.linspace(fd["d_log_gdp"].min(), fd["d_log_gdp"].max(), 2)
    axes[1].plot(xs, fd["d_ladder"].mean() + k2 * (xs - fd["d_log_gdp"].mean()), color=INK, linewidth=1.5)
    for n in ["Afghanistan", "Lebanon", "Serbia", "Bulgaria", "Venezuela"]:
        if n in fd.index:
            axes[1].annotate(n, (fd.loc[n, "d_log_gdp"], fd.loc[n, "d_ladder"]), textcoords="offset points", xytext=(5, 3), color=DIM, fontsize=9)
    axes[1].axhline(0, color="#2a2a2a")
    axes[1].axvline(0, color="#2a2a2a")
    axes[1].set_xlabel("change in log GDP per capita, 2010-12 to 2023-25")
    axes[1].set_ylabel("change in life evaluation")
    axes[1].set_title(f"Within countries over time: slope {k2:.2f}", fontsize=12)
    save(fig, "03_easterlin.png")

    t = pd.read_csv(R / "types.csv", index_col=0)
    factors = ["Log GDP per capita", "Social support", "Healthy life expectancy", "Freedom to make life choices", "Generosity", "Perceptions of corruption"]
    short = ["Income", "Social support", "Healthy life exp.", "Freedom", "Generosity", "Low corruption"]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    width, colors = 0.26, [BLUE, "#8fb8e8", DIM]
    for j, (typ, row) in enumerate(t.iterrows()):
        ax.bar(np.arange(6) + (j - 1) * width, row[factors].values, width=width * 0.95, color=colors[j],
               label=f"Type {int(typ)}: avg {row['ladder']:.1f}, {int(row['countries'])} countries (e.g. {', '.join(row['examples'].split(', ')[:3])})")
    ax.set_xticks(np.arange(6), short)
    ax.set_ylabel("points of life evaluation attributed")
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, labelcolor=INK, fontsize=9, loc="upper right")
    ax.set_ylim(0, 2.6)
    ax.set_title("Three country types from the six factors (k-means, 2023-25)")
    save(fig, "04_types.png")
    print("charts/01_change.png, 02_beyond.png, 03_easterlin.png, 04_types.png")


if __name__ == "__main__":
    main()

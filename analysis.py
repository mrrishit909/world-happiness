"""Step 2: what goes with a happier country, and does getting richer make a country happier?

    ./venv/bin/python analysis.py

Uses non-overlapping 3-year windows (2010-12, 2014-16, 2017-19, 2020-22, 2023-25; labelled by last year).
  A. Change: life evaluations 2010-12 vs 2023-25.
  B. Happier than predicted: the report's "dystopia + residual" (the part its six factors don't explain), 2023-25.
  C. Country types: k-means on the six factor contributions, 2023-25 (k chosen by silhouette, 3-6).
  D. An independent model: life evaluation vs open World Bank data (log GDP per capita, life expectancy, unemployment).
  E. Easterlin paradox: across countries richer = happier; within a country over time, does growth raise happiness?
     Cross-section slope vs within-country slopes (first differences 2010-12 -> 2023-25, and country fixed effects).
Writes results/*.json|csv.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).parent
RAW = HERE / "data" / "raw"
WINDOWS = [2012, 2016, 2019, 2022, 2025]          # the file has no 2013 label (there was no 2014 report)
FACTORS = ["Log GDP per capita", "Social support", "Healthy life expectancy", "Freedom to make life choices",
           "Generosity", "Perceptions of corruption"]
TO_WB = {"Congo": "Congo, Rep.", "DR Congo": "Congo, Dem. Rep.", "Côte d’Ivoire": "Cote d'Ivoire", "Egypt": "Egypt, Arab Rep.",
         "Gambia": "Gambia, The", "Hong Kong SAR of China": "Hong Kong SAR, China", "Iran": "Iran, Islamic Rep.",
         "Kyrgyzstan": "Kyrgyz Republic", "Puerto Rico": "Puerto Rico (US)", "Republic of Korea": "Korea, Rep.",
         "Republic of Moldova": "Moldova", "Slovakia": "Slovak Republic", "Somalia": "Somalia, Fed. Rep.",
         "State of Palestine": "West Bank and Gaza", "Swaziland": "Eswatini", "Syria": "Syrian Arab Republic",
         "Türkiye": "Turkiye", "Venezuela": "Venezuela, RB", "Yemen": "Yemen, Rep."}


def load_whr():
    w = pd.read_excel(RAW / "WHR26_Data_Figure_2.1.xlsx")
    w = w.rename(columns={"Country name": "country", "Year": "year", "Life evaluation (3-year average)": "ladder",
                          "Dystopia + residual": "dystopia_residual", **{f"Explained by: {f}": f for f in FACTORS}})
    return w[["country", "year", "ladder", "dystopia_residual", *FACTORS]]


def load_wb():
    countries = json.loads((RAW / "wb_countries.json").read_text())
    meta = {c["name"]: {"iso3": c["id"], "region": c["region"]["value"], "income": c["incomeLevel"]["value"]}
            for c in countries if c["region"]["value"] != "Aggregates"}
    frames = []
    for name in ["gdp_pc_ppp", "life_expectancy", "unemployment"]:
        rows = json.loads((RAW / f"wb_{name}.json").read_text())
        frames.append(pd.DataFrame([{"wb_name": r["country"]["value"], "year": int(r["date"]), name: r["value"]} for r in rows]))
    wb = frames[0].merge(frames[1], on=["wb_name", "year"]).merge(frames[2], on=["wb_name", "year"])
    return wb[wb["wb_name"].isin(meta)], meta


def window_means(wb):
    """World Bank values averaged over each 3-year window, to match the report's 3-year averages."""
    out = []
    for end in WINDOWS:
        part = wb[wb["year"].between(end - 2, end)].groupby("wb_name")[["gdp_pc_ppp", "life_expectancy", "unemployment"]].mean()
        out.append(part.assign(year=end).reset_index())
    return pd.concat(out)


def main():
    w = load_whr()
    wb, meta = load_wb()
    w["wb_name"] = w["country"].map(lambda c: TO_WB.get(c, c))
    w["region"] = w["wb_name"].map(lambda n: meta.get(n, {}).get("region"))
    panel = w[w["year"].isin(WINDOWS)].merge(window_means(wb), on=["wb_name", "year"], how="left")
    panel["log_gdp"] = np.log(panel["gdp_pc_ppp"])
    (HERE / "results").mkdir(exist_ok=True)
    out = {}

    # A. change between the first and last window
    a = panel.pivot_table(index="country", columns="year", values="ladder")[[2012, 2025]].dropna()
    a["change"] = a[2025] - a[2012]
    a.sort_values("change").to_csv(HERE / "results" / "change.csv")
    out["change"] = {"countries": len(a), "rose": int((a["change"] > 0).sum()),
                     "top": a["change"].nlargest(5).round(2).to_dict(), "bottom": a["change"].nsmallest(5).round(2).to_dict(),
                     "sd_2012": round(float(a[2012].std()), 3), "sd_2025": round(float(a[2025].std()), 3)}

    # B. happier (or less happy) than the six factors predict, 2023-25
    now = panel[panel["year"] == 2025].copy()
    now["beyond_factors"] = now["dystopia_residual"] - now["dystopia_residual"].mean()
    b = now.set_index("country")["beyond_factors"].sort_values()
    b.round(3).to_csv(HERE / "results" / "beyond_factors.csv")
    reg_mean = now.groupby("region")["beyond_factors"].mean().sort_values()
    out["beyond_factors"] = {"top": b.nlargest(8).round(2).to_dict(), "bottom": b.nsmallest(8).round(2).to_dict(),
                             "by_region": reg_mean.round(2).to_dict()}

    # C. country types from the six factor contributions
    X = StandardScaler().fit_transform(now[FACTORS].dropna())
    keep = now[FACTORS].dropna().index
    sil = {k: silhouette_score(X, KMeans(k, n_init=20, random_state=0).fit_predict(X)) for k in range(3, 7)}
    k = max(sil, key=sil.get)
    labels = KMeans(k, n_init=20, random_state=0).fit_predict(X)
    now.loc[keep, "cluster"] = labels
    order = now.groupby("cluster")["ladder"].mean().sort_values(ascending=False).index
    rank = {c: i + 1 for i, c in enumerate(order)}
    now["type"] = now["cluster"].map(rank)
    prof = now.groupby("type")[["ladder", *FACTORS]].mean().round(3)
    prof["countries"] = now.groupby("type").size()
    prof["examples"] = now.sort_values("ladder", ascending=False).groupby("type")["country"].apply(lambda s: ", ".join(s.head(5)))
    prof.to_csv(HERE / "results" / "types.csv")
    now[["country", "region", "ladder", "beyond_factors", "type", *FACTORS, "gdp_pc_ppp", "life_expectancy", "unemployment"]].to_csv(
        HERE / "results" / "countries_2025.csv", index=False)
    out["types"] = {"k": k, "silhouette": {str(kk): round(v, 3) for kk, v in sil.items()}}

    # D. independent model with open data, 2023-25
    d = now.dropna(subset=["log_gdp", "life_expectancy", "unemployment"])
    m_gdp = smf.ols("ladder ~ log_gdp", d).fit(cov_type="HC1")
    m_all = smf.ols("ladder ~ log_gdp + life_expectancy + unemployment", d).fit(cov_type="HC1")
    out["independent_model"] = {"countries": len(d), "r2_gdp_only": round(m_gdp.rsquared, 3), "r2_three": round(m_all.rsquared, 3),
                                "coef": {k: [round(v, 4), round(m_all.bse[k], 4)] for k, v in m_all.params.items()},
                                "gdp_only_slope": [round(m_gdp.params["log_gdp"], 3), round(m_gdp.bse["log_gdp"], 3)]}

    # E. Easterlin: across countries vs within countries over time
    p = panel.dropna(subset=["ladder", "log_gdp"])
    cross = smf.ols("ladder ~ log_gdp", p[p["year"] == 2025]).fit(cov_type="HC1")
    fd = p.pivot_table(index="country", columns="year", values=["ladder", "log_gdp"])
    fd = pd.DataFrame({"d_ladder": fd[("ladder", 2025)] - fd[("ladder", 2012)],
                       "d_log_gdp": fd[("log_gdp", 2025)] - fd[("log_gdp", 2012)]}).dropna()
    first_diff = smf.ols("d_ladder ~ d_log_gdp", fd).fit(cov_type="HC1")
    fe = smf.ols("ladder ~ log_gdp + C(country) + C(year)", p).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(p["country"])[0]})
    fd.to_csv(HERE / "results" / "easterlin_first_differences.csv")
    collapses = ["Afghanistan", "Venezuela", "Lebanon", "Zimbabwe", "Yemen"]
    robust = {"gdp_grew_only": smf.ols("d_ladder ~ d_log_gdp", fd[fd["d_log_gdp"] > 0]).fit(cov_type="HC1"),
              "without_5_collapses": smf.ols("d_ladder ~ d_log_gdp", fd[~fd.index.isin(collapses)]).fit(cov_type="HC1")}
    huber = smf.rlm("d_ladder ~ d_log_gdp", fd).fit()
    ci = lambda m, k: [round(m.params[k] - 1.96 * m.bse[k], 3), round(m.params[k] + 1.96 * m.bse[k], 3)]
    out["easterlin"] = {
        "cross_section_2025": {"slope": round(cross.params["log_gdp"], 3), "ci95": ci(cross, "log_gdp"), "countries": int(cross.nobs)},
        "first_difference_2012_2025": {"slope": round(first_diff.params["d_log_gdp"], 3), "ci95": ci(first_diff, "d_log_gdp"),
                                       "countries": int(first_diff.nobs), "mean_d_log_gdp": round(float(fd["d_log_gdp"].mean()), 3)},
        "fixed_effects_5_windows": {"slope": round(fe.params["log_gdp"], 3), "ci95": ci(fe, "log_gdp"), "observations": int(fe.nobs)},
        "robustness": {**{k: {"slope": round(m.params["d_log_gdp"], 3), "ci95": ci(m, "d_log_gdp"), "countries": int(m.nobs)} for k, m in robust.items()},
                       "huber_robust_regression": {"slope": round(huber.params["d_log_gdp"], 3), "se": round(huber.bse["d_log_gdp"], 3)}},
    }
    (HERE / "results" / "summary.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print(prof.to_string())


if __name__ == "__main__":
    main()

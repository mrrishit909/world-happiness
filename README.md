# World happiness: what goes with a happier country, and does growth help?

A social-science look at the World Happiness Report: how life satisfaction changed across 141 countries from
2010–12 to 2023–25, which countries are happier than their circumstances predict, what "types" of country emerge,
and a test of a famous claim, the Easterlin paradox, using open World Bank data.

Build log: https://mrrishit909.github.io/projects/world-happiness/

## Data

- **World Happiness Report 2026**, data for Figure 2.1 (official file:
  https://files.worldhappiness.report/WHR26_Data_Figure_2.1.xlsx). These are life evaluations: the Gallup World Poll's
  0–10 "ladder" question, as 3-year averages labelled by their last year, 2011–2025. Each score is split into six
  factors plus "dystopia + residual".
  The raw country-year panel sits behind the report's data portal API, which requires a token, so only the published
  file is used.
- **World Bank WDI** (open API): GDP per capita (PPP, constant 2021 $), life expectancy, unemployment.
- 165 of 168 countries match World Bank names (North Cyprus, Somaliland and Taiwan aren't in World Bank data).

## Steps

| Step | File | What it does |
|---|---|---|
| 1 | `download.py` | the WHR file and three World Bank indicators (not committed) |
| 2 | `analysis.py` | non-overlapping windows 2010–12, 14–16, 17–19, 20–22, 23–25; five analyses below |
| 3 | `charts.py`, `check.py` | charts; checks that the report's split adds up, the windows, country matching, and the slopes |

## Findings

**1. Most countries got happier, unevenly.** 86 of 141 rose between 2010–12 and 2023–25. Eastern Europe led: Serbia
+1.88, Bulgaria +1.72, Kosovo +1.69, Romania +1.60. Afghanistan fell 2.59 points, Zimbabwe 1.48, Venezuela 1.28 and
Lebanon 1.21.

**2. Some countries are happier than their circumstances predict.** The report explains each score with income, social
support, healthy life expectancy, freedom, generosity and corruption. What's left over is largest in Latin America
(+0.59 on average vs the average country): Venezuela, Guatemala, Costa Rica, Mexico. It's most negative in South Asia
(−0.50), and for Hong Kong, Sri Lanka and Botswana.

**3. Three country types (k-means on the six factors).** Type 1, Nordic-style (24 countries, average 6.9): high income,
support, health and trust. Type 2 (70 countries, 6.1): middle income with strong social support. Type 3 (51, 4.4): low
on almost everything. The clusters are a convenient summary, not natural groups; the silhouette score is only 0.28.

**4. An independent check with open data.** Across 141 countries, log GDP per capita alone explains 63% of the variation
in life evaluations. Adding life expectancy and unemployment raises that to 67%. Each extra point of unemployment goes
with 0.04 lower life evaluation, while life expectancy adds little once income is known.

**5. The Easterlin paradox doesn't show up here.** Easterlin (1974) argued that richer countries are happier but countries
don't get happier as they grow. In this data:

| Relationship of life evaluation to log GDP per capita | Slope | 95% CI |
|---|---:|---:|
| Across countries, 2023–25 | 0.79 | 0.69 – 0.89 |
| Within countries: change 2010–12 → 2023–25 | 1.49 | 0.92 – 2.07 |
| Within countries: fixed effects, 5 windows | 1.40 | 0.75 – 2.06 |
| Within, only countries that grew (120) | 1.48 | 0.79 – 2.16 |
| Within, without the 5 collapses (Afghanistan, Venezuela, Lebanon, Zimbabwe, Yemen) | 1.26 | 0.74 – 1.77 |

Growth and rising life satisfaction went together over these 13 years, at least as strongly as across countries.
That's consistent with later work such as Stevenson & Wolfers (2008). Much of it comes from Eastern Europe, where fast
growth and big happiness gains happened together (possibly both driven by EU integration and recovery), so this is an
association, not proof that growth causes happiness.

## Limits

- The report's six-factor split is its own model, so regressing scores on it would be circular. Section 4 uses independent
  World Bank data instead.
- 3-year averages smooth shocks. Only 13 years separate the first and last windows, and Easterlin argues the paradox
  holds over longer horizons.
- Country-level averages can't say anything about individuals.

## Run it

```
python3 -m venv venv && ./venv/bin/pip install pandas openpyxl scikit-learn statsmodels matplotlib
./venv/bin/python download.py && ./venv/bin/python analysis.py && ./venv/bin/python charts.py && ./venv/bin/python check.py
```

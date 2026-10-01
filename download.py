"""Step 1: the official World Happiness Report 2026 figure data + three open World Bank indicators.

    ./venv/bin/python download.py

- WHR 2026, data for Figure 2.1: life evaluations (Cantril ladder, 0-10; 3-year averages, labelled by their last
  year, 2011-2025) and the report's split of each score into six factors. Gallup World Poll data, published by the
  Wellbeing Research Centre (Oxford) via files.worldhappiness.report.
- World Bank WDI API: GDP per capita (PPP, constant 2021 $), life expectancy, unemployment, plus country codes.
Raw files go to data/raw/ (not committed).
"""
import json
import ssl
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE / "data" / "raw"
CTX = ssl.create_default_context(cafile="/etc/ssl/cert.pem")
WHR = "https://files.worldhappiness.report/WHR26_Data_Figure_2.1.xlsx"
WB = {"gdp_pc_ppp": "NY.GDP.PCAP.PP.KD", "life_expectancy": "SP.DYN.LE00.IN", "unemployment": "SL.UEM.TOTL.ZS"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (student research script)"})
    return urllib.request.urlopen(req, context=CTX, timeout=120).read()


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "WHR26_Data_Figure_2.1.xlsx").write_bytes(get(WHR))
    for name, code in WB.items():
        rows = json.loads(get(f"https://api.worldbank.org/v2/country/all/indicator/{code}?format=json&date=2008:2025&per_page=20000"))[1]
        (RAW / f"wb_{name}.json").write_text(json.dumps(rows))
    countries = json.loads(get("https://api.worldbank.org/v2/country?format=json&per_page=400"))[1]
    (RAW / "wb_countries.json").write_text(json.dumps(countries))
    print("downloaded WHR 2026 figure data and", len(WB), "World Bank indicators")


if __name__ == "__main__":
    main()

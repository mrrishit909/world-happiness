"""The project's check.

    ./venv/bin/python check.py

1. The report's split adds up: life evaluation = six factor contributions + dystopia/residual, for every row.
2. Windows don't overlap and are the ones intended (2010-12 ... 2023-25).
3. Country matching: every World Bank match is a real World Bank country; only 3 report countries are unmatched.
4. The headline numbers recompute from the saved per-country files.
"""
import json

import numpy as np
import pandas as pd

from analysis import FACTORS, HERE, TO_WB, WINDOWS, load_wb, load_whr


def main():
    w = load_whr()
    parts = w[FACTORS].sum(axis=1) + w["dystopia_residual"]
    ok = w.dropna(subset=FACTORS)
    assert np.allclose(parts.loc[ok.index], ok["ladder"], atol=0.006), (parts - w["ladder"]).abs().max()
    assert all(b - a >= 3 for a, b in zip(WINDOWS, WINDOWS[1:])) and set(WINDOWS) <= set(w["year"])

    wb, meta = load_wb()
    names = set(w["country"])
    unmatched = sorted(n for n in names if TO_WB.get(n, n) not in meta)
    assert unmatched == ["North Cyprus", "Somaliland Region", "Taiwan Province of China"], unmatched
    assert all(v in meta for v in TO_WB.values())

    s = json.loads((HERE / "results" / "summary.json").read_text())
    ch = pd.read_csv(HERE / "results" / "change.csv", index_col=0)
    assert s["change"]["rose"] == int((ch["change"] > 0).sum()) and s["change"]["countries"] == len(ch)
    fd = pd.read_csv(HERE / "results" / "easterlin_first_differences.csv", index_col=0)
    slope = np.polyfit(fd["d_log_gdp"], fd["d_ladder"], 1)[0]
    assert abs(slope - s["easterlin"]["first_difference_2012_2025"]["slope"]) < 0.001
    c = pd.read_csv(HERE / "results" / "countries_2025.csv").dropna(subset=["gdp_pc_ppp"])
    cross = np.polyfit(np.log(c["gdp_pc_ppp"]), c["ladder"], 1)[0]
    assert abs(cross - s["easterlin"]["cross_section_2025"]["slope"]) < 0.001
    print(f"OK: factor split adds up on {len(ok):,} rows; windows {WINDOWS}; 3 unmatched countries as expected; "
          f"slopes recompute (across {cross:.2f}, within {slope:.2f})")


if __name__ == "__main__":
    main()

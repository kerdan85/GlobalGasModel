# ==========================================================
# lng_terminals.py
#
# Derives LNG infrastructure requirements from the optimised
# trade flows: how much liquefaction (export) and
# regasification (import) capacity each region needs per
# period, and how many NEW terminals must be built beyond the
# current (2025) fleet, given an average terminal size.
#
# Attribution rules (per LNG-type link, flow f):
#   USA -> US_LNG            : liquefaction at USA           (US export build)
#   US_LNG -> destination    : regasification at destination (import build)
#   direct A -> B (LNG)      : liquefaction at A AND regasification at B
#
# "Current" fleet = the calibrated 2025 throughput, so the
# buildout is the growth in terminal capacity above 2025.
#
# Outputs (outputs/):
#   lng_buildout.csv          (per region per year)
#   lng_buildout_summary.csv  (global totals per year)
#   figures/LNG_Terminal_Buildout.png
# ==========================================================

import os
import math
from collections import defaultdict

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.config import MARKETS, AVG_LIQ_BCM, AVG_REGAS_BCM


def _region_of(node, market):
    return node if node in MARKETS else market.get(node, node)


def lng_terminal_report():
    if not os.path.exists("outputs/trade_flows.csv"):
        print("  ! Skipping LNG terminals: outputs/trade_flows.csv not found.")
        return

    trade = pd.read_csv("outputs/trade_flows.csv")
    links = pd.read_csv("data/links.csv")
    lng_routes = set(links.loc[links["Type"].str.upper() == "LNG", "Name"])
    producers = pd.read_csv("data/producers.csv")
    market = {r["Node"]: r["MarketBus"] for _, r in producers.iterrows()}

    years = sorted(trade["Year"].unique())

    liq = {y: defaultdict(float) for y in years}     # liquefaction throughput
    reg = {y: defaultdict(float) for y in years}     # regasification throughput
    for r in trade.itertuples(index=False):
        if r.Route not in lng_routes or r.Flow <= 0:
            continue
        f, t = r.From, r.To
        if t == "US_LNG":                              # USA -> US_LNG (liquefaction)
            liq[r.Year]["USA"] += r.Flow
        elif f == "US_LNG":                            # US_LNG -> dest (regas)
            reg[r.Year][_region_of(t, market)] += r.Flow
        else:                                          # direct LNG export
            liq[r.Year][_region_of(f, market)] += r.Flow
            reg[r.Year][_region_of(t, market)] += r.Flow

    base = years[0]                                    # 2025 = current fleet
    base_liq = dict(liq[base])
    base_reg = dict(reg[base])
    regions = sorted(set().union(*[set(liq[y]) | set(reg[y]) for y in years]))

    def n_term(cap, avg):
        return int(math.ceil(cap / avg - 1e-9)) if cap > 1e-9 else 0

    rows = []
    for y in years:
        for rg in regions:
            lt = liq[y].get(rg, 0.0)
            rt = reg[y].get(rg, 0.0)
            bl = base_liq.get(rg, 0.0)
            br = base_reg.get(rg, 0.0)
            new_l = max(0.0, lt - bl)
            new_r = max(0.0, rt - br)
            rows.append(dict(
                Year=y, Region=rg,
                LiqThroughput=round(lt, 1), RegasThroughput=round(rt, 1),
                CurrentLiqCap=round(bl, 1), CurrentRegasCap=round(br, 1),
                NewLiqCap=round(new_l, 1), NewRegasCap=round(new_r, 1),
                NewLiqTerminals=n_term(new_l, AVG_LIQ_BCM),
                NewRegasTerminals=n_term(new_r, AVG_REGAS_BCM),
            ))
    df = pd.DataFrame(rows)
    df.to_csv("outputs/lng_buildout.csv", index=False)

    # ---- global summary per year ----
    cur_liq_term = sum(n_term(v, AVG_LIQ_BCM) for v in base_liq.values())
    cur_reg_term = sum(n_term(v, AVG_REGAS_BCM) for v in base_reg.values())
    summ = []
    for y in years:
        sub = df[df.Year == y]
        summ.append(dict(
            Year=y,
            TotalLiqThroughput=round(sub.LiqThroughput.sum(), 1),
            TotalRegasThroughput=round(sub.RegasThroughput.sum(), 1),
            NewLiqCap=round(sub.NewLiqCap.sum(), 1),
            NewRegasCap=round(sub.NewRegasCap.sum(), 1),
            NewLiqTerminals=int(sub.NewLiqTerminals.sum()),
            NewRegasTerminals=int(sub.NewRegasTerminals.sum()),
            CurrentLiqTerminals=cur_liq_term,
            CurrentRegasTerminals=cur_reg_term,
        ))
    summary = pd.DataFrame(summ)
    summary.to_csv("outputs/lng_buildout_summary.csv", index=False)

    # ---- figure ----
    os.makedirs("outputs/figures", exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    x = summary["Year"].astype(str)
    w = 0.38
    import numpy as np
    xi = np.arange(len(x))
    ax1.bar(xi - w / 2, summary.NewLiqTerminals, w, label="Liquefaction (export)", color="#d1495b")
    ax1.bar(xi + w / 2, summary.NewRegasTerminals, w, label="Regasification (import)", color="#1f6fb2")
    ax1.set_xticks(xi); ax1.set_xticklabels(x)
    ax1.set_ylabel("New terminals vs 2025 (count)")
    ax1.set_title(f"New LNG terminals beyond current fleet\n(avg {AVG_LIQ_BCM:.0f} / {AVG_REGAS_BCM:.0f} BCM per liq/regas terminal)")
    ax1.legend(); ax1.grid(axis="y", alpha=0.3)

    last = df[df.Year == years[-1]].copy()
    last = last[(last.NewLiqTerminals + last.NewRegasTerminals) > 0]
    last = last.sort_values("NewRegasTerminals", ascending=True)
    yi = np.arange(len(last))
    ax2.barh(yi - w / 2, last.NewLiqTerminals, w, label="Liquefaction", color="#d1495b")
    ax2.barh(yi + w / 2, last.NewRegasTerminals, w, label="Regasification", color="#1f6fb2")
    ax2.set_yticks(yi); ax2.set_yticklabels(last.Region, fontsize=8)
    ax2.set_xlabel("New terminals by 2045 (count)")
    ax2.set_title("New terminals by region (2045 vs 2025)")
    ax2.legend(); ax2.grid(axis="x", alpha=0.3)

    plt.tight_layout()
    plt.savefig("outputs/figures/LNG_Terminal_Buildout.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    tot_l = int(summary.NewLiqTerminals.iloc[-1])
    tot_r = int(summary.NewRegasTerminals.iloc[-1])
    print(f"LNG terminal buildout: by {years[-1]}, +{tot_l} liquefaction and "
          f"+{tot_r} regasification terminals beyond the 2025 fleet "
          f"({cur_liq_term} liq / {cur_reg_term} regas current).")


if __name__ == "__main__":
    lng_terminal_report()

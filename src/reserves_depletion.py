# ==========================================================
# reserves_depletion.py
#
# Tracks cumulative gas extraction (2025-2045) against real
# regional reserves (data/reserves.csv) split by:
#   - resource type:  Conventional vs Unconventional (shale/tight)
#   - maturity:        Proved reserves vs Potential resources
#
# Reports, per region & type: cumulative extraction, % of
# proved consumed, % of (proved+potential), remaining volumes,
# reserves-to-production (R/P) years, and a "pressure" flag for
# regions that exhaust proved reserves and must tap potential
# or whose remaining cover is short.
#
# Cumulative extraction integrates the 5-yearly model snapshots
# trapezoidally (BCM/yr -> BCM over the 20-year horizon).
#
# Outputs (outputs/):
#   reserves_depletion.csv
#   figures/Reserves_Depletion.png
# ==========================================================

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.config import YEARS

UNCONV_TECH = {"SHALE", "SHALE_MATURE"}


def _category(tech):
    return "Unconventional" if tech in UNCONV_TECH else "Conventional"


def _cumulative(series_by_year):
    """Trapezoidal integral of an annual rate sampled at YEARS (BCM)."""
    ys = sorted(series_by_year)
    tot = 0.0
    for a, b in zip(ys[:-1], ys[1:]):
        tot += (b - a) * 0.5 * (series_by_year[a] + series_by_year[b])
    return tot


def reserves_depletion_report():
    if not os.path.exists("data/reserves.csv"):
        print("  ! Skipping reserves: data/reserves.csv not found.")
        return

    reserves = pd.read_csv("data/reserves.csv").set_index("Region")
    producers = pd.read_csv("data/producers.csv")
    market = {r["Node"]: r["MarketBus"] for _, r in producers.iterrows()}

    # production by (region, category, year)
    prod = {}     # (region, cat) -> {year: BCM/yr}
    p2045 = {}    # (region, cat) -> 2045 rate
    for y in YEARS:
        f = f"outputs/production_nodes_{y}.csv"
        if not os.path.exists(f):
            print(f"  ! Skipping reserves: {f} not found (run the model first).")
            return
        df = pd.read_csv(f)
        for _, r in df.iterrows():
            node = r["Node"]
            if node not in market:        # skip slack / non-producers
                continue
            reg = market[node]
            cat = _category(r["Technology"])
            prod.setdefault((reg, cat), {}).setdefault(y, 0.0)
            prod[(reg, cat)][y] += float(r["Production"])

    rows = []
    for reg in reserves.index:
        for cat in ("Conventional", "Unconventional"):
            series = prod.get((reg, cat), {y: 0.0 for y in YEARS})
            series = {y: series.get(y, 0.0) for y in YEARS}
            cum = _cumulative(series)
            rate45 = series[max(YEARS)]
            if cat == "Conventional":
                proved, pot = reserves.loc[reg, "ConvProved"], reserves.loc[reg, "ConvPotential"]
            else:
                proved, pot = reserves.loc[reg, "UnconvProved"], reserves.loc[reg, "UnconvPotential"]
            proved = float(proved); pot = float(pot); total = proved + pot
            if cum < 1e-6 and total < 1e-6:
                continue
            proved_rem = max(0.0, proved - cum)
            pot_used = max(0.0, cum - proved)
            pot_rem = max(0.0, pot - pot_used)
            rp = (proved / rate45) if rate45 > 1e-6 else float("inf")
            rp_total = (total / rate45) if rate45 > 1e-6 else float("inf")
            pressure = (cum > proved + 1e-6) or (rp_total < 25 and rate45 > 1e-6)
            rows.append(dict(
                Region=reg, Type=cat,
                ProvedReserves=round(proved), PotentialResources=round(pot),
                CumExtraction_25_45=round(cum, 1), Rate2045=round(rate45, 1),
                ProvedRemaining=round(proved_rem), PotentialRemaining=round(pot_rem),
                PctProvedConsumed=round(100 * cum / proved, 1) if proved > 0 else None,
                PctTotalConsumed=round(100 * cum / total, 1) if total > 0 else None,
                RP_proved_yrs=round(rp, 1) if rp != float("inf") else None,
                RP_total_yrs=round(rp_total, 1) if rp_total != float("inf") else None,
                Pressure=bool(pressure),
            ))
    out = pd.DataFrame(rows)
    out.to_csv("outputs/reserves_depletion.csv", index=False)

    # ---- figure ----
    os.makedirs("outputs/figures", exist_ok=True)
    reg_tot = out.groupby("Region").agg(
        cum=("CumExtraction_25_45", "sum"),
        proved=("ProvedReserves", "sum"),
        potential=("PotentialResources", "sum"),
        rate45=("Rate2045", "sum")).reset_index()
    reg_tot = reg_tot[reg_tot.cum > 0.5].copy()
    reg_tot["pct_proved"] = 100 * reg_tot.cum / reg_tot.proved.replace(0, float("nan"))
    reg_tot["rp_total"] = (reg_tot.proved + reg_tot.potential) / reg_tot.rate45.replace(0, float("nan"))
    reg_tot = reg_tot.sort_values("pct_proved", ascending=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
    colors = ["#b22222" if p > 100 else "#e0a030" if p > 50 else "#3a7d44"
              for p in reg_tot.pct_proved]
    ax1.barh(reg_tot.Region, reg_tot.pct_proved, color=colors)
    ax1.axvline(100, color="black", lw=1, ls="--")
    ax1.set_xlabel("Cumulative 2025–2045 extraction as % of PROVED reserves")
    ax1.set_title("Reserve drawdown by region\n(red >100% = proved exhausted, taps potential)")
    ax1.grid(axis="x", alpha=0.3)

    rp = reg_tot.sort_values("rp_total", ascending=True)
    rpcol = ["#b22222" if v < 25 else "#e0a030" if v < 50 else "#3a7d44" for v in rp.rp_total]
    ax2.barh(rp.Region, rp.rp_total, color=rpcol)
    ax2.axvline(25, color="black", lw=1, ls="--")
    ax2.set_xlabel("Reserves-to-production at 2045 rate, proved+potential (years)")
    ax2.set_title("Years of remaining cover\n(red <25 yrs = under pressure)")
    ax2.grid(axis="x", alpha=0.3)
    plt.suptitle("Gas reserve depletion & regions under pressure (real reserves)",
                 fontsize=15, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig("outputs/figures/Reserves_Depletion.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    pressured = sorted(out[out.Pressure].Region.unique())
    print(f"Reserve depletion report written. Regions under pressure: "
          f"{', '.join(pressured) if pressured else 'none'}.")


if __name__ == "__main__":
    reserves_depletion_report()

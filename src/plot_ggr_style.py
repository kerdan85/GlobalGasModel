# -*- coding: utf-8 -*-
"""
=====================================================================
plot_ggr_style.py  --  GGR-styled exhibits from OUR model data
Ivan Garcia Kerdan (Tec de Monterrey)
=====================================================================
Four Nature-quality panels styled after the IGU/Snam/Rystad Global Gas
Report 2025 exhibits, but drawn entirely from THIS model's inputs and
solved outputs (no third-party figures reproduced):

  G1  arbitrage_merit_order   -> delivered-to-Asia US gas supply curve
                                  vs the coal-parity wall  [MAIN TEXT]
  G2  regional_demand         -> gas demand trajectory by region [SI]
  G3  net_trade_ranking       -> net exporters/importers, solved 2025 [SI]
  G4  us_supply_curve         -> US wellhead cost curve + export headroom [SI]

All read from data/ and outputs/; each degrades gracefully if a CSV is
missing. Palette matches Figure 1 (teal / terracotta / sage / gold).

Run:  python -m src.plot_ggr_style      (from repo root)
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA = os.path.join(_ROOT, "data")
_OUT = os.path.join(_ROOT, "outputs")
_FIG = os.path.join(_OUT, "figures")

# ---- palette (matches Fig 1) --------------------------------------
TEAL      = "#1b6f6b"
TERRA     = "#c0623f"
SAGE      = "#7a9b76"
GOLD      = "#d9a441"
SLATE     = "#3f4a4c"
GREYFILL  = "#d9dcdc"
LIGHTGREY = "#ececec"

plt.rcParams.update({
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#555555", "figure.dpi": 120,
})

# delivered-to-Asia cost adders (model $/MMBtu-equiv), from
# data/us_supply_curve.csv header: tranche cost + 0.2 liq + 0.5 capital + 1.8 ship
LIQ, CAPEX, SHIP = 0.2, 0.5, 1.8
COAL_PARITY = 6.5           # config.COAL_PARITY
ASIA_LO, ASIA_HI = 10.0, 15.0   # GGR 2025 NE Asia spot band (USD/MMBtu, 2024-25)


def _save(fig, name):
    os.makedirs(_FIG, exist_ok=True)
    p = os.path.join(_FIG, name)
    fig.savefig(p + ".png", bbox_inches="tight", dpi=300)
    fig.savefig(p + ".pdf", bbox_inches="tight")
    plt.close(fig)
    print("  ->", p + ".png")
    return p


# ===================================================================
# G1  -- delivered-to-Asia US supply curve vs coal-parity wall [MAIN]
# ===================================================================
def arbitrage_merit_order():
    try:
        sc = pd.read_csv(os.path.join(_DATA, "us_supply_curve.csv"), comment="#")
    except Exception as e:
        print("  [G1] skip:", e); return None
    sc["delivered"] = sc["MarginalCost"] + LIQ + CAPEX + SHIP
    sc = sc.sort_values("delivered").reset_index(drop=True)
    sc["cum0"] = sc["Capacity"].cumsum() - sc["Capacity"]
    sc["cum1"] = sc["Capacity"].cumsum()

    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    # Asian price band (what buyers would otherwise pay)
    ax.axhspan(ASIA_LO, ASIA_HI, color=TEAL, alpha=0.10, zorder=0)
    ax.text(sc["cum1"].max(), (ASIA_LO + ASIA_HI) / 2,
            " Asian spot band\n (GGR 2025)", va="center", ha="left",
            fontsize=8.5, color=TEAL)
    # coal-parity wall
    ax.axhline(COAL_PARITY, color=TERRA, lw=1.6, ls="--", zorder=3)
    ax.text(5, COAL_PARITY + 0.15, "Coal-parity wall (6.5)", color=TERRA,
            fontsize=9, fontweight="bold")

    for _, r in sc.iterrows():
        below = r["delivered"] <= COAL_PARITY
        ax.bar(r["cum0"], r["delivered"], width=r["Capacity"], align="edge",
               color=(SAGE if below else GREYFILL),
               edgecolor="white", linewidth=0.8, zorder=2)
    # crossover
    prof = sc[sc["delivered"] <= COAL_PARITY]["Capacity"].sum()
    ax.axvline(prof, color=SLATE, lw=1.0, ls=":", zorder=4)
    ax.annotate(f"export-profitable\nheadroom  ≈ {prof:.0f} Bcm",
                xy=(prof, 3.0), xytext=(prof + 120, 2.2),
                fontsize=8.5, color=SLATE,
                arrowprops=dict(arrowstyle="->", color=SLATE, lw=0.9))

    ax.set_xlabel("Cumulative US export supply (Bcm yr$^{-1}$)")
    ax.set_ylabel("Delivered-to-Asia cost (model \$/MMBtu-equiv.)")
    ax.set_title("US gas clears into Asia only below the coal-parity wall")
    ax.set_ylim(0, ASIA_HI + 1)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(fc=SAGE, label="clears coal parity → leakage channel open"),
                       Patch(fc=GREYFILL, label="priced out above the wall")],
              loc="upper left", frameon=False, fontsize=8.5)
    return _save(fig, "GGR_G1_arbitrage_merit_order")


# ===================================================================
# G2  -- regional gas demand trajectory 2025-2045 [SI]
# ===================================================================
def regional_demand():
    try:
        d = pd.read_csv(os.path.join(_DATA, "demand.csv")).set_index("Node")
    except Exception as e:
        print("  [G2] skip:", e); return None
    yrs = [c for c in d.columns if c.isdigit()]
    d = d[yrs]
    d = d[d.sum(axis=1) > 0]
    order = d[yrs[-1]].sort_values(ascending=False).index.tolist()
    top = order[:7]
    rest = order[7:]
    lab = {"USA": "USA", "CHINA": "China", "RUSSIA": "Russia", "EUROPE": "Europe",
           "GULF_STATES": "Gulf states", "IRAN": "Iran", "SOUTHEAST_ASIA": "SE Asia",
           "SOUTH_ASIA": "South Asia", "NORTH_AFRICA": "N. Africa"}
    cols = [TEAL, TERRA, SAGE, GOLD, SLATE, "#8c6d9c", "#5b8ca5"]
    x = np.array([int(y) for y in yrs])
    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    for i, reg in enumerate(top):
        ax.plot(x, d.loc[reg, yrs].values, "-o", ms=4, lw=2,
                color=cols[i % len(cols)], label=lab.get(reg, reg.title()))
    if rest:
        ax.plot(x, d.loc[rest, yrs].sum().values, "-o", ms=3, lw=1.4,
                color="#b0b0b0", label="rest of world")
    ax.set_xlabel("Year")
    ax.set_ylabel("Gas demand (Bcm yr$^{-1}$)")
    ax.set_title("Modelled regional gas demand diverges: Asia up, Europe down")
    ax.set_xticks(x)
    ax.legend(frameon=False, fontsize=8.5, ncol=2, loc="upper left")
    ax.grid(axis="y", alpha=0.25)
    return _save(fig, "GGR_G2_regional_demand")


# ===================================================================
# G3  -- net exporters / importers, solved 2025 [SI]
# ===================================================================
def net_trade_ranking(year=2025):
    p = os.path.join(_OUT, f"regional_balance_{year}.csv")
    try:
        b = pd.read_csv(p)
    except Exception as e:
        print("  [G3] skip:", e); return None
    b = b[b["Region"] != "US_LNG"].copy()
    b["net"] = b["NetExports"].round(1)
    b = b.sort_values("net")
    lab = {"USA": "USA", "CHINA": "China", "RUSSIA": "Russia", "EUROPE": "Europe",
           "MEXICO": "Mexico", "GULF_STATES": "Gulf states", "QATAR": "Qatar",
           "NORTHEAST_ASIA": "NE Asia", "SOUTHEAST_ASIA": "SE Asia",
           "SOUTH_ASIA": "South Asia", "LATIN_AMERICA": "Latin America",
           "NORTH_AFRICA": "N. Africa", "SUBSAHARAN_AFRICA": "Sub-Sah. Africa",
           "CANADA": "Canada", "IRAN": "Iran", "CENTRAL_ASIA": "Central Asia",
           "CASPIAN_REGION": "Caspian", "AUSTRALIA": "Australia"}
    names = [lab.get(r, r.title()) for r in b["Region"]]
    colors = [TEAL if v >= 0 else TERRA for v in b["net"]]
    fig, ax = plt.subplots(figsize=(8.0, 6.2))
    ax.barh(names, b["net"], color=colors, edgecolor="white")
    ax.axvline(0, color="#555", lw=0.8)
    for y, v, r in zip(range(len(b)), b["net"], b["Region"]):
        ax.text(v + (4 if v >= 0 else -4), y, f"{v:+.0f}",
                va="center", ha="left" if v >= 0 else "right", fontsize=7.5)
    # highlight Mexico + China as the sovereignty premise / reabsorption sink
    for r, tag in (("MEXICO", "GGR: 68 Bcm imp."), ("CHINA", "GGR: 175 Bcm imp.")):
        if r in list(b["Region"]):
            yi = list(b["Region"]).index(r)
            ax.get_yticklabels()[yi].set_fontweight("bold")
    ax.set_xlabel("Net exports (Bcm yr$^{-1}$)   —   negative = net importer")
    ax.set_title(f"Modelled net gas trade balance, {year}")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(fc=TEAL, label="net exporter"),
                       Patch(fc=TERRA, label="net importer")],
              loc="lower right", frameon=False, fontsize=8.5)
    return _save(fig, "GGR_G3_net_trade_ranking")


# ===================================================================
# G4  -- US wellhead cost curve + spare export headroom [SI]
# ===================================================================
def us_supply_curve():
    try:
        sc = pd.read_csv(os.path.join(_DATA, "us_supply_curve.csv"), comment="#")
    except Exception as e:
        print("  [G4] skip:", e); return None
    sc = sc.sort_values("MarginalCost").reset_index(drop=True)
    sc["cum0"] = sc["Capacity"].cumsum() - sc["Capacity"]
    parity_wellhead = COAL_PARITY - (LIQ + CAPEX + SHIP)   # ~4.0
    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    for _, r in sc.iterrows():
        below = r["MarginalCost"] <= parity_wellhead
        ax.bar(r["cum0"], r["MarginalCost"], width=r["Capacity"], align="edge",
               color=(TEAL if below else GREYFILL), edgecolor="white",
               linewidth=0.8)
    ax.axhline(parity_wellhead, color=TERRA, lw=1.5, ls="--")
    ax.text(5, parity_wellhead + 0.12,
            "wellhead cost that clears coal parity after LNG chain (≈4.0)",
            color=TERRA, fontsize=8.5, fontweight="bold")
    # us_supply_scale headroom band
    base = sc[sc["MarginalCost"] <= parity_wellhead]["Capacity"].sum()
    ax.axvspan(base * 0.85, base * 1.30, color=GOLD, alpha=0.15)
    ax.text(base * 1.07, 5.6, "us_supply_scale\nsweep (0.85–1.3)",
            ha="center", fontsize=8, color="#8a6d1f")
    ax.set_xlabel("Cumulative US production (Bcm yr$^{-1}$)")
    ax.set_ylabel("Wellhead marginal cost (model \$/MMBtu)")
    ax.set_title("US step supply curve sets the exportable, coal-clearing headroom")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(fc=TEAL, label="exportable below coal parity"),
                       Patch(fc=GREYFILL, label="high-cost tranches (the wall)")],
              loc="upper left", frameon=False, fontsize=8.5)
    return _save(fig, "GGR_G4_us_supply_curve")


def run():
    print("GGR-styled figures from model data:")
    arbitrage_merit_order()
    regional_demand()
    net_trade_ranking()
    us_supply_curve()


if __name__ == "__main__":
    run()

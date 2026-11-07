# -*- coding: utf-8 -*-
"""
=====================================================================
plot_us_lng_destinations.py  --  US LNG exports by receiving market
Ivan Garcia Kerdan (Tec de Monterrey)
=====================================================================
US LNG exports by destination, drawn directly from the solved model
(outputs/trade_flows.csv). US LNG serves EUROPE (security-driven, declining
as the post-2022 surge eases), LATIN AMERICA (proximity), and a CONTRACTED
floor to NE Asia (Japan + Korea long-term SPAs). It does NOT competitively
reach the Chinese coal-switching market under present-day economics, because
delivered US LNG neither undercuts Asian coal nor beats the incumbent Asian
suppliers (Qatar, Australia, Russia) on delivered cost. That is the central
ESL~0 result: freed US gas reaches China and displaces coal only once the
reliability-premium or carbon-price threshold is crossed.

Run:  python -m src.plot_us_lng_destinations
Output: outputs/figures/F5_us_lng_destinations.{png,pdf}
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OUT = os.path.join(_ROOT, "outputs")
_FIG = os.path.join(_OUT, "figures")

PRETTY = {"EUROPE": "Europe", "LATIN_AMERICA": "Latin America",
          "CHINA": "China", "NORTHEAST_ASIA": "NE Asia",
          "SOUTHEAST_ASIA": "SE Asia", "SOUTH_ASIA": "South Asia"}
COLORS = {"Europe": "#c0623f", "Latin America": "#1b6f6b", "China": "#6c3483",
          "NE Asia": "#8a6d1f", "SE Asia": "#4a7ba6", "South Asia": "#9a9a9a"}


def plot_us_lng_destinations():
    os.makedirs(_FIG, exist_ok=True)
    path = os.path.join(_OUT, "trade_flows.csv")
    if not os.path.exists(path):
        print("  ! trade_flows.csv not found -- run the model first."); return
    t = pd.read_csv(path)
    f = t[(t["From"] == "US_LNG") & (t["Flow"] > 0.5)].copy()
    if f.empty:
        print("  ! no US_LNG outbound flows found."); return
    f["Dest"] = f["To"].map(lambda r: PRETTY.get(r, str(r).title()))
    piv = f.pivot_table(index="Year", columns="Dest", values="Flow",
                        aggfunc="sum").fillna(0).sort_index()
    years = piv.index.astype(int).tolist()
    order = piv.sum().sort_values(ascending=False).index.tolist()

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    bottom = np.zeros(len(years))
    for d in order:
        vals = piv[d].values
        ax.bar(years, vals, bottom=bottom, width=3.0, label=d,
               color=COLORS.get(d, "#777777"), edgecolor="white", lw=0.6, zorder=2)
        bottom += vals
    ax.set_xticks(years)
    ax.set_xlabel("Year")
    ax.set_ylabel("US LNG exports (BCM yr$^{-1}$)")
    ax.set_ylim(0, max(bottom) * 1.28 + 2)
    ax.set_title("US LNG exports by destination")
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    fig.text(0.015, -0.02,
             "US LNG serves Europe (declining), Latin America, and a contracted "
             "floor to NE Asia (Japan/Korea long-term SPAs). It does not "
             "competitively reach the Chinese coal-switching market under present-day "
             "economics—delivered US LNG neither undercuts Asian coal nor beats "
             "incumbent suppliers (Qatar, Australia, Russia). Freed US gas reaches "
             "China only above the leakage threshold.",
             ha="left", va="top", fontsize=7, color="#666666", wrap=True)
    fig.tight_layout()
    out = os.path.join(_FIG, "F5_us_lng_destinations")
    fig.savefig(out + ".png", dpi=300, bbox_inches="tight")
    fig.savefig(out + ".pdf", bbox_inches="tight")
    plt.close(fig)
    print("wrote", out + ".png")
    print(piv.round(0).to_string())


if __name__ == "__main__":
    plot_us_lng_destinations()

# -*- coding: utf-8 -*-
"""
plot_methane_contingency.py -- the climate sign of leakage vs upstream methane
Ivan Garcia Kerdan (Tec de Monterrey)

Delivered shale-LNG lifecycle intensity I_gas(r) = a + b*r as a function of the
upstream methane-leakage rate r, against the fixed intensity of the Asian coal
it displaces, at both GWP horizons. The swept methane range (1.5-3.7%) is shown
as a shaded band; the break-even rates (where shale-LNG crosses coal) are marked.
Below its break-even gas is cleaner than coal (leakage lowers emissions); above
it, dirtier (leakage raises them). This is the single contingency on which the
climate sign of ESL turns.

Run:  python -m src.plot_methane_contingency
Output: outputs/figures/Methane_contingency.{png,pdf}
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIG = os.path.join(_ROOT, "outputs", "figures")

# Lifecycle-intensity parameters (Methods; src/config.py): I_gas = a + b*r
A = 74.5                      # methane-independent (combustion + non-CH4 upstream + LNG chain)
B = {"GWP100": 6.1, "GWP20": 16.8}   # per-% upstream methane
I_COAL = {"GWP100": 108.0, "GWP20": 126.0}
R_CENTRAL = 2.5
R_LO, R_HI = 1.5, 3.7         # swept methane range
STYLE = {"GWP100": dict(c="#1b7f72", label="100-year GWP"),
         "GWP20":  dict(c="#c7901f", label="20-year GWP")}


def plot_methane_contingency():
    os.makedirs(_FIG, exist_ok=True)
    r = np.linspace(0, 6, 400)
    fig, ax = plt.subplots(figsize=(7.4, 4.8))

    # swept methane range as a shaded band
    ax.axvspan(R_LO, R_HI, color="0.80", alpha=0.35, zorder=0)
    ax.text((R_LO + R_HI) / 2, 62.5, "swept methane range (1.5–3.7%)",
            ha="center", va="bottom", fontsize=8, color="0.35")
    ax.axvline(R_CENTRAL, color="0.45", ls=":", lw=1.2, zorder=1)
    ax.text(R_CENTRAL, 120, " central 2.5%", fontsize=8, color="0.35",
            rotation=90, va="top", ha="left")

    for h in ("GWP20", "GWP100"):
        col = STYLE[h]["c"]
        igas = A + B[h] * r
        ax.plot(r, igas, color=col, lw=2.2, zorder=3, label=f"shale-LNG, {STYLE[h]['label']}")
        ax.axhline(I_COAL[h], color=col, ls="--", lw=1.3, alpha=0.8, zorder=2)
        ax.text(5.95, I_COAL[h] + 0.6, f"coal {STYLE[h]['label']} ({I_COAL[h]:.0f})",
                ha="right", va="bottom", fontsize=8, color=col)
        # break-even: where shale-LNG == coal
        r_be = (I_COAL[h] - A) / B[h]
        ax.scatter([r_be], [I_COAL[h]], s=55, color=col, edgecolor="white",
                   zorder=5, clip_on=False)
        ax.annotate(f"break-even {r_be:.1f}%", (r_be, I_COAL[h]),
                    xytext=(r_be + 0.15, I_COAL[h] - 7), fontsize=8, color=col,
                    arrowprops=dict(arrowstyle="-", lw=0.5, color=col))

    ax.set_xlim(0, 6); ax.set_ylim(60, 140)
    ax.set_xlabel("Upstream methane-leakage rate (% of throughput)")
    ax.set_ylabel("Lifecycle intensity (gCO$_2$e MJ$^{-1}$)")
    ax.set_title("The climate sign of leakage turns on the upstream methane rate")
    ax.legend(loc="lower right", fontsize=8, frameon=False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(alpha=0.25, zorder=0)
    # cleaner / dirtier zone annotations, placed in open space
    ax.text(0.15, 72, "below break-even:\nshale-LNG cleaner than coal\n(leakage lowers emissions)",
            fontsize=7.5, color="#2e7d32", va="top")
    ax.text(0.15, 139, "above break-even: dirtier than coal\n(leakage raises emissions)",
            fontsize=7.5, color="#b2182b", va="top")

    fig.tight_layout()
    out = os.path.join(_FIG, "Methane_contingency")
    fig.savefig(out + ".png", dpi=300, bbox_inches="tight")
    fig.savefig(out + ".pdf", bbox_inches="tight")
    plt.close(fig)
    print("wrote", out + ".png")
    for h in ("GWP20", "GWP100"):
        print(f"  {h}: I_gas(2.5%)={A+B[h]*R_CENTRAL:.1f}, coal={I_COAL[h]:.0f}, "
              f"break-even={(I_COAL[h]-A)/B[h]:.2f}%")


if __name__ == "__main__":
    plot_methane_contingency()

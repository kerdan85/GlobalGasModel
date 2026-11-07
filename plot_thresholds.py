# ==========================================================
# plot_thresholds.py
#
# Builds Fig. "ESL_thresholds": leakage as a THRESHOLD phenomenon along the
# two forces that move delivered US LNG across the coal-parity wall:
#   (a) the reliability premium  (from outputs/esl_results_by_regime.csv)
#   (b) a carbon price on coal   (from outputs/carbon_sweep.csv)
#
# Each panel shows the individual-year points (2035-2045) and their mean, with
# the below-threshold region shaded. The wide above-threshold spread is shown
# honestly -- it is the evidence that leakage is a conditional switch, not a
# single number.
#
#   python src/plot_thresholds.py
# Output: outputs/figures/ESL_thresholds.png
# ==========================================================

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PT = "#D85A30"      # individual-year points (coral)
MEAN = "#185FA5"    # mean line (blue)
SHADE = "0.85"      # below-threshold shading

# below-threshold extents (premium $/MMBtu ; carbon price $/tCO2)
PREMIUM_THRESHOLD = 1.5
CARBON_THRESHOLD = 20.0
YEAR_COLS = ["ESL_2035", "ESL_2040", "ESL_2045"]


def plot_thresholds():
    os.makedirs("outputs/figures", exist_ok=True)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))

    # ---- panel a: ESL vs reliability premium -------------------------
    fa = "outputs/esl_results_by_regime.csv"
    if os.path.exists(fa):
        d = pd.read_csv(fa)
        late = d[d["Year"] >= 2035]
        ax[0].axvspan(late["reliability_premium"].min() - 0.1, PREMIUM_THRESHOLD,
                      color=SHADE, alpha=0.5, zorder=0)
        ax[0].scatter(late["reliability_premium"], late["ESL_pct"],
                      color=PT, alpha=0.6, s=30, zorder=3, label="individual years")
        m = (late.groupby("reliability_premium")["ESL_pct"].mean()
             .reset_index().sort_values("reliability_premium"))
        ax[0].plot(m["reliability_premium"], m["ESL_pct"], "o-",
                   color=MEAN, lw=2.3, ms=6, zorder=4, label="mean 2035-45")
        ax[0].text(0.3, ax[0].get_ylim()[1] * 0.92, "below\nthreshold",
                   fontsize=8, color="0.4", va="top")
    else:
        ax[0].text(0.5, 0.5, "esl_results_by_regime.csv\nnot found",
                   ha="center", va="center", transform=ax[0].transAxes)
    ax[0].axhline(0, color="black", lw=0.6)
    ax[0].set_xlabel("reliability premium ($/MMBtu)")
    ax[0].set_ylabel("Energy Sovereignty Leakage (%)")
    ax[0].set_title("a  Reliability premium", loc="left", fontweight="bold")
    ax[0].grid(alpha=0.3)
    ax[0].legend(fontsize=8, frameon=False)

    # ---- panel b: ESL vs carbon price --------------------------------
    fb = "outputs/carbon_sweep.csv"
    if os.path.exists(fb):
        c = pd.read_csv(fb).sort_values("carbon_price_USD_tCO2")
        xs = c["carbon_price_USD_tCO2"]
        ax[1].axvspan(xs.min() - 1, CARBON_THRESHOLD, color=SHADE, alpha=0.5, zorder=0)
        for col in YEAR_COLS:
            if col in c.columns:
                ax[1].scatter(xs, c[col], color=PT, alpha=0.6, s=30, zorder=3)
        ax[1].plot(xs, c["mean_ESL_2035_45"], "o-",
                   color=MEAN, lw=2.3, ms=6, zorder=4, label="mean 2035-45")
        ax[1].text(3, ax[1].get_ylim()[1] * 0.92, "below\nthreshold",
                   fontsize=8, color="0.4", va="top")
    else:
        ax[1].text(0.5, 0.5, "carbon_sweep.csv\nnot found",
                   ha="center", va="center", transform=ax[1].transAxes)
    ax[1].axhline(0, color="black", lw=0.6)
    ax[1].set_xlabel(r"carbon price (\$/tCO$_2$)")
    ax[1].set_ylabel("Energy Sovereignty Leakage (%)")
    ax[1].set_title("b  Carbon price on coal", loc="left", fontweight="bold")
    ax[1].grid(alpha=0.3)
    ax[1].legend(fontsize=8, frameon=False)

    plt.tight_layout()
    out = "outputs/figures/ESL_thresholds.png"
    plt.savefig(out, dpi=300)
    plt.close(fig)
    print(f"Saved {out}")


if __name__ == "__main__":
    plot_thresholds()

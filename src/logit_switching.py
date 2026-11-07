# -*- coding: utf-8 -*-
"""
=====================================================================
logit_switching.py  --  Threshold robustness under a non-least-cost rule
Ivan Garcia Kerdan (Tec de Monterrey)
=====================================================================
Reviewer robustness check (no solver, no new data): does the leakage
THRESHOLD survive if the coal-to-gas switching channel is represented by
SMOOTH inter-supplier substitution (a logit market share) instead of the
model's least-cost merit-order tipping?

We isolate the switching channel that the main model resolves market-by-
market and re-express it two ways, over the SAME delivered-cost margin
m = (delivered US LNG  -  local coal-parity price)   [$/MMBtu]:

  * LEAST-COST (as in the main model): each of the heterogeneous coal
    sub-fleets (config.COAL_PARITY_SPREAD, 13 offsets over +/-2 $/MMBtu
    around config.COAL_PARITY) switches to gas iff delivered gas is below
    its own parity, i.e. a hard step  1[delta_k > m].
  * LOGIT (smooth substitution): the same sub-fleet switches with
    probability  sigma((delta_k - m)/tau),  a continuous share.

The switched volume maps to Energy Sovereignty Leakage by attributing the
freed US gas to the switched market (scaled so the above-threshold plateau
matches the ~45% top of the main-model conditional range). The point of the
figure is NOT the plateau height but the CROSSING: under both rules ESL
turns on as m crosses zero (delivered gas crosses coal parity). The logit
rule removes the discrete jumps -- the source of the non-convergent
magnitude in the main results -- WITHOUT moving the threshold.

Output:
  outputs/logit_threshold.csv
  outputs/figures/Threshold_logit_vs_leastcost.png (+ .pdf)

Run:  python -m src.logit_switching   (from repo root)
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

TEAL   = "#1b6f6b"     # logit (smooth)
TERRA  = "#c0623f"     # least-cost (step)
SLATE  = "#3f4a4c"
SHADE  = "#e8ece9"

# ESL plateau (%) far above the threshold -- the top of the main-model
# conditional range (10--45%); used only to scale the shared switch curve so
# the two rules are compared on the same axis.
ESL_PLATEAU = 45.0
TAU = 0.6              # logit temperature ($/MMBtu): fleet-response smoothness


def _spread():
    """The heterogeneous coal-fleet parity offsets (config.COAL_PARITY_SPREAD)."""
    try:
        from src import config
        return np.array(config.COAL_PARITY_SPREAD, dtype=float)
    except Exception:
        # config default: 13 steps over -2..+2 around coal parity
        return np.array([round(-2.0 + 4.0 * k / 12, 4) for k in range(13)])


def switched_share(m, rule, delta, tau=TAU):
    """Fraction of the heterogeneous coal fleet that switches to gas at a
    delivered-cost margin m = delivered_gas - coal_parity ($/MMBtu).
    rule = 'leastcost' (hard step) or 'logit' (smooth share)."""
    m = np.atleast_1d(m)[:, None]                # (M,1)
    d = delta[None, :]                            # (1,K)
    if rule == "leastcost":
        sw = (d > m).astype(float)               # switch iff delivered below its parity
    else:
        sw = 1.0 / (1.0 + np.exp((m - d) / tau))  # logit share
    return sw.mean(axis=1)                        # (M,)


def compute(margins=None):
    delta = _spread()
    if margins is None:
        margins = np.linspace(2.0, -3.0, 251)     # gas expensive -> cheap
    lc = switched_share(margins, "leastcost", delta) * ESL_PLATEAU
    lg = switched_share(margins, "logit", delta) * ESL_PLATEAU
    df = pd.DataFrame({"delivered_margin_usd_mmbtu": margins,
                       "ESL_leastcost_pct": np.round(lc, 3),
                       "ESL_logit_pct": np.round(lg, 3)})
    return df


def _threshold_location(df):
    """Margin at which each rule reaches half its plateau (the 'switch-on' point)."""
    out = {}
    for col in ("ESL_leastcost_pct", "ESL_logit_pct"):
        y = df[col].values
        x = df["delivered_margin_usd_mmbtu"].values
        half = ESL_PLATEAU / 2.0
        i = np.argmin(np.abs(y - half))
        out[col] = x[i]
    return out


def run():
    os.makedirs(_FIG, exist_ok=True)
    df = compute()
    p_csv = os.path.join(_OUT, "logit_threshold.csv")
    df.to_csv(p_csv, index=False)
    thr = _threshold_location(df)

    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    # below-threshold region (gas above parity -> no leakage)
    ax.axvspan(0.0, df["delivered_margin_usd_mmbtu"].max(), color=SHADE, zorder=0)
    ax.axvline(0.0, color=SLATE, lw=1.2, ls=":", zorder=2)
    ax.text(0.06, ESL_PLATEAU * 0.96, "coal-parity wall\n(delivered gas = coal)",
            fontsize=8.5, color=SLATE, va="top")

    x = df["delivered_margin_usd_mmbtu"]
    ax.step(x, df["ESL_leastcost_pct"], where="mid", color=TERRA, lw=2.0,
            label="least-cost merit order (main model)")
    ax.plot(x, df["ESL_logit_pct"], color=TEAL, lw=2.4,
            label="logit market share (smooth substitution)")

    ax.set_xlim(2.0, -3.0)   # decreasing rightward: increasing decarbonisation pressure
    ax.set_ylim(0, ESL_PLATEAU + 4)
    ax.set_xlabel("Delivered US LNG relative to coal parity  (model \$/MMBtu)\n"
                  "$\\leftarrow$ lower (security premium / carbon price)      higher $\\rightarrow$")
    ax.set_ylabel("Energy Sovereignty Leakage (%)")
    ax.set_title("The leakage threshold survives smooth inter-supplier substitution")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.annotate("threshold at the same\ndelivered-cost crossing",
                xy=(0.0, ESL_PLATEAU / 2), xytext=(-1.6, ESL_PLATEAU * 0.62),
                fontsize=8.5, color=SLATE,
                arrowprops=dict(arrowstyle="->", color=SLATE, lw=0.9))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    out = os.path.join(_FIG, "Threshold_logit_vs_leastcost")
    fig.savefig(out + ".png", dpi=300, bbox_inches="tight")
    fig.savefig(out + ".pdf", bbox_inches="tight")
    plt.close(fig)

    print("logit-vs-least-cost threshold check:")
    print(f"  half-plateau crossing (least-cost): m = {thr['ESL_leastcost_pct']:+.2f} $/MMBtu")
    print(f"  half-plateau crossing (logit):      m = {thr['ESL_logit_pct']:+.2f} $/MMBtu")
    print(f"  -> {p_csv}\n  -> {out}.png")
    return df


if __name__ == "__main__":
    run()

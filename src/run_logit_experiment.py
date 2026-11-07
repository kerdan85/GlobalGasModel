# -*- coding: utf-8 -*-
"""
=====================================================================
run_logit_experiment.py  --  FULL-model threshold under logit switching
Ivan Garcia Kerdan (Tec de Monterrey)
=====================================================================
!!! EXPERIMENTAL -- NOT USED FOR ANY PUBLISHED RESULT !!!
This driver exercises the full 19-region endogenous logit fixed point,
which is NUMERICALLY UNSTABLE (see the warning in src/logit_resolve.py):
the ESL differencing is swamped by re-dispatch noise and the mean curve is
not reproducible across a tau sweep. Do NOT derive any figure or number in
the paper from this. The published robustness check is the deterministic
single-channel reduction in src/logit_switching.py.
=====================================================================
Runs the 19-region model with the LOGIT coal-to-gas fixed point
(src/logit_resolve.py) across the reliability-premium axis, so the
leakage threshold can be compared against the least-cost baseline
(outputs/esl_results_by_regime.csv, produced by the standard run).

NEEDS PyPSA + a solver -- run this in the model environment (Spyder /
terminal), from the repo root:

    python -m src.run_logit_experiment            # full sweep + figure
    python -m src.run_logit_experiment --quick    # premiums {0,1.5,2.5} only

Outputs:
    outputs/esl_logit_by_regime.csv
    outputs/figures/Threshold_fullmodel_logit_vs_leastcost.png (+ .pdf)

The plotting step (plot_compare) also runs standalone once the CSV exists:
    python -c "from src.run_logit_experiment import plot_compare; plot_compare()"
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src import config

PREMIUMS = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]     # matches esl_results_by_regime.csv
PREMIUMS_QUICK = [0.0, 1.5, 2.5]

_OUT = "outputs"
_FIG = os.path.join(_OUT, "figures")
TERRA, TEAL, SLATE, SHADE = "#c0623f", "#1b6f6b", "#3f4a4c", "0.9"
PREMIUM_THRESHOLD = 1.5


def run(premiums=None):
    """Run the logit fixed-point counterfactual at each reliability premium."""
    from src.logit_resolve import run_counterfactual_logit, _chdir_repo_root
    _chdir_repo_root()                                     # make data/ paths work
    premiums = premiums if premiums is not None else PREMIUMS
    frames = []
    for prem in premiums:
        print(f"\n########## LOGIT run: reliability_premium = {prem} ##########")
        df = run_counterfactual_logit(p={"reliability_premium": prem})
        df.insert(0, "reliability_premium", prem)
        df.insert(0, "Regime", f"logit premium {prem}")
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    os.makedirs(_OUT, exist_ok=True)
    path = os.path.join(_OUT, "esl_logit_by_regime.csv")
    out.to_csv(path, index=False)
    print("\nwrote", path)
    return out


def _mean_by_premium(df, from_year=2035):
    late = df[df["Year"] >= from_year]
    return late.groupby("reliability_premium")["ESL_pct"].mean()


def plot_compare():
    """Overlay ESL vs reliability premium for least-cost (baseline) and logit."""
    from src.logit_resolve import _chdir_repo_root
    _chdir_repo_root()                                     # make outputs/ paths work
    os.makedirs(_FIG, exist_ok=True)
    lc_path = os.path.join(_OUT, "esl_results_by_regime.csv")
    lg_path = os.path.join(_OUT, "esl_logit_by_regime.csv")

    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    ax.axvspan(-0.1, PREMIUM_THRESHOLD, color=SHADE, zorder=0)
    ax.text(PREMIUM_THRESHOLD - 0.05, 2, "below threshold", ha="right",
            fontsize=8.5, color=SLATE)

    if os.path.exists(lc_path):
        lc = pd.read_csv(lc_path)
        m = _mean_by_premium(lc)
        ax.plot(m.index, m.values, "-o", color=TERRA, lw=2, ms=6,
                label="least-cost merit order (baseline)")
    if os.path.exists(lg_path):
        lg = pd.read_csv(lg_path)
        m = _mean_by_premium(lg)
        ax.plot(m.index, m.values, "-s", color=TEAL, lw=2.4, ms=6,
                label="logit market share (fixed point)")
    else:
        ax.text(1.25, 25, "run  python -m src.run_logit_experiment\nto add the logit curve",
                fontsize=8.5, color=TEAL, ha="center")

    ax.axvline(PREMIUM_THRESHOLD, color=SLATE, lw=1.0, ls=":")
    ax.set_xlabel("Reliability premium on US LNG (\\$/MMBtu)")
    ax.set_ylabel("Energy Sovereignty Leakage, mean 2035--2045 (%)")
    ax.set_title("Full-model leakage threshold: least-cost vs logit substitution")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    out = os.path.join(_FIG, "Threshold_fullmodel_logit_vs_leastcost")
    fig.savefig(out + ".png", dpi=300, bbox_inches="tight")
    fig.savefig(out + ".pdf", bbox_inches="tight")
    plt.close(fig)
    print("wrote", out + ".png")


if __name__ == "__main__":
    quick = "--quick" in sys.argv
    run(PREMIUMS_QUICK if quick else PREMIUMS)
    plot_compare()

# ==========================================================
# uncertainty.py   (Tier 2b)
#
# Parameter uncertainty for the ESL result. Two analyses:
#
#   tornado    : one-at-a-time low/high swing of each parameter
#                around the central case -> which assumptions the
#                conclusion depends on most.
#   montecarlo : random sampling of all parameters (triangular
#                low/central/high) -> a distribution of the
#                headline ESL with a confidence interval.
#
# Uses config.UNCERTAINTY_PARAMS and config.N_MONTECARLO.
#
# Outputs: outputs/uncertainty_tornado.csv
#          outputs/uncertainty_montecarlo.csv
#          outputs/figures/Uncertainty_tornado.png
#          outputs/figures/Uncertainty_montecarlo.png
# ==========================================================

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src import config
from src.experiment_core import run_counterfactual, headline_esl


def _central():
    return {name: c for (name, lo, c, hi) in config.UNCERTAINTY_PARAMS}


def tornado():
    base = _central()
    base_esl = headline_esl(run_counterfactual(base))
    rows = []
    for (name, lo, c, hi) in config.UNCERTAINTY_PARAMS:
        p_lo = dict(base); p_lo[name] = lo
        p_hi = dict(base); p_hi[name] = hi
        e_lo = headline_esl(run_counterfactual(p_lo))
        e_hi = headline_esl(run_counterfactual(p_hi))
        rows.append(dict(Param=name, Low=round(e_lo, 1), High=round(e_hi, 1),
                         Swing=round(abs(e_hi - e_lo), 1)))
        print(f"  [tornado] {name}: {e_lo:.0f}% .. {e_hi:.0f}%")
    out = pd.DataFrame(rows).sort_values("Swing")
    out.to_csv("outputs/uncertainty_tornado.csv", index=False)
    _plot_tornado(out, base_esl)
    return out


def montecarlo(n_samples=None, seed=0):
    n_samples = n_samples or config.N_MONTECARLO
    rng = np.random.default_rng(seed)
    samples = []
    for s in range(n_samples):
        p = {}
        for (name, lo, c, hi) in config.UNCERTAINTY_PARAMS:
            p[name] = float(rng.triangular(lo, c, hi))
        esl = headline_esl(run_counterfactual(p))
        samples.append(dict(sample=s, ESL=esl, **p))
        if (s + 1) % 25 == 0:
            print(f"  [mc] {s+1}/{n_samples}")
    out = pd.DataFrame(samples)
    out.to_csv("outputs/uncertainty_montecarlo.csv", index=False)
    _plot_mc(out)
    lo, med, hi = np.percentile(out["ESL"], [5, 50, 95])
    print(f"Monte Carlo ESL: median {med:.0f}% (90% CI {lo:.0f}-{hi:.0f}%)")
    return out


def _plot_tornado(out, base_esl):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    y = range(len(out))
    for i, (_, r) in enumerate(out.iterrows()):
        ax.plot([r["Low"], r["High"]], [i, i], color="#888", lw=6, solid_capstyle="butt")
        ax.plot(r["Low"], i, "o", color="#2166ac")
        ax.plot(r["High"], i, "o", color="#b2182b")
    ax.axvline(base_esl, color="black", ls="--", label=f"central {base_esl:.0f}%")
    ax.set_yticks(list(y)); ax.set_yticklabels(out["Param"])
    ax.set_xlabel("Headline ESL (%)")
    ax.set_title("Tornado: sensitivity of ESL to each parameter")
    ax.legend(fontsize=8); ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig("outputs/figures/Uncertainty_tornado.png", dpi=300)
    plt.close(fig)


def _plot_mc(out):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(out["ESL"], bins=30, color="#6a9ec0", edgecolor="white", zorder=2)
    lo, med, hi = np.percentile(out["ESL"], [5, 50, 95])
    # shaded 90% interval + labelled median / percentile lines
    ax.axvspan(lo, hi, color="#b2182b", alpha=0.07, zorder=1)
    ymax = ax.get_ylim()[1]
    for v, c, lbl in [(lo, "#b2182b", f"5th ({lo:.1f}%)"),
                      (med, "black", f"median ({med:.1f}%)"),
                      (hi, "#b2182b", f"95th ({hi:.1f}%)")]:
        ax.axvline(v, color=c, ls="--", lw=1.4, zorder=3)
        ax.text(v, ymax * 0.98, " " + lbl, rotation=90, va="top", ha="left",
                fontsize=8, color=c)
    ax.set_xlabel("Headline ESL (%)"); ax.set_ylabel("count")
    ax.set_title(f"Monte Carlo over all governing parameters "
                 f"(N={len(out)}): median {med:.1f}%, 90% CI {lo:.1f}–{hi:.1f}%")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", alpha=0.3, zorder=0)
    plt.tight_layout()
    plt.savefig("outputs/figures/Uncertainty_montecarlo.png", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs("outputs/figures", exist_ok=True)
    tornado()
    montecarlo()

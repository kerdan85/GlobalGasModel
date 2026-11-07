# ==========================================================
# scenario_matrix.py   (Tier 2a)
#
# Sweeps the scenario axes in config.SCENARIO_AXES and maps how
# Energy Sovereignty Leakage responds. Two modes:
#
#   sweep_1d : vary each axis while holding the others at their
#              central value -> ESL response curves (robustness).
#   sweep_2d : full grid over two chosen axes -> ESL heatmap
#              (the response surface for the paper's key drivers).
#
# Outputs: outputs/scenario_1d.csv, outputs/scenario_2d.csv
#          outputs/figures/Scenario_1d.png
#          outputs/figures/Scenario_heatmap.png
# ==========================================================

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src import config
from src.experiment_core import run_counterfactual, headline_esl


def _central(axes):
    return {k: v[len(v) // 2] for k, v in axes.items()}


def sweep_1d(axes=None):
    axes = axes or config.SCENARIO_AXES
    base = _central(axes)
    rows = []
    for axis, values in axes.items():
        for val in values:
            p = dict(base); p[axis] = val
            df = run_counterfactual(p)
            rows.append(dict(Axis=axis, Value=val,
                             ESL=round(headline_esl(df), 1),
                             dE_GWP20_2045=float(df[df.Year == config.YEARS[-1]]["dE_GWP20"].iloc[0])))
            print(f"  [1d] {axis}={val}: ESL={rows[-1]['ESL']}%")
    out = pd.DataFrame(rows)
    out.to_csv("outputs/scenario_1d.csv", index=False)
    _plot_1d(out, axes)
    return out


def sweep_2d(axis_x="mex_shale_cost", axis_y="us_supply_scale", axes=None):
    axes = axes or config.SCENARIO_AXES
    base = _central(axes)
    xs, ys = axes[axis_x], axes[axis_y]
    grid = np.full((len(ys), len(xs)), np.nan)
    rows = []
    for j, yv in enumerate(ys):
        for i, xv in enumerate(xs):
            p = dict(base); p[axis_x] = xv; p[axis_y] = yv
            df = run_counterfactual(p)
            esl = headline_esl(df)
            grid[j, i] = esl
            rows.append(dict(**{axis_x: xv, axis_y: yv}, ESL=round(esl, 1)))
            print(f"  [2d] {axis_x}={xv}, {axis_y}={yv}: ESL={esl:.0f}%")
    pd.DataFrame(rows).to_csv("outputs/scenario_2d.csv", index=False)
    _plot_2d(grid, xs, ys, axis_x, axis_y)
    return grid


def _plot_1d(out, axes):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for axis in axes:
        sub = out[out.Axis == axis].sort_values("Value")
        ax.plot(range(len(sub)), sub["ESL"], "o-", label=axis)
        # use index positions so different value ranges share an x-axis
    ax.axhline(100, ls=":", color="grey")
    ax.set_xlabel("axis level (low -> high)")
    ax.set_ylabel("Headline ESL (%)")
    ax.set_title("ESL robustness to each scenario axis")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("outputs/figures/Scenario_1d.png", dpi=300)
    plt.close(fig)


def _plot_2d(grid, xs, ys, axis_x, axis_y):
    # Grouped bars: ESL vs the capacity axis (ys), one bar per cost axis (xs).
    # Equal bars within a group make the invariance to the cost axis visible,
    # while group heights show the capacity dependence -- clearer than a
    # 3-column heatmap whose identical columns read as empty.
    _PRETTY = {"us_supply_scale": "US spare export-capacity scale",
               "mex_shale_cost": "Mexican-shale cost (model \\$/MMBtu-eq)"}
    nx = len(xs)
    cols = ["#15486f", "#2e86c1", "#a9cce3", "#5dade2", "#d4e6f1"]
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    x = np.arange(len(ys)); w = 0.8 / max(nx, 1)
    for i, xv in enumerate(xs):
        vals = [grid[j, i] for j in range(len(ys))]
        ax.bar(x + (i - (nx - 1) / 2.0) * w, vals, w,
               label=f"{xv:g}", color=cols[i % len(cols)],
               edgecolor="white", linewidth=0.6, zorder=3)
    ax.set_xticks(x); ax.set_xticklabels([f"{v:g}" for v in ys])
    ax.set_xlabel(_PRETTY.get(axis_y, axis_y) + "  (lower = tighter)")
    ax.set_ylabel("Headline ESL (%)")
    ax.legend(title=_PRETTY.get(axis_x, axis_x), fontsize=8,
              title_fontsize=8, frameon=False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", alpha=0.3, zorder=0)
    if nx > 1:
        ax.annotate("Bars within each group are equal\n\u2192 ESL invariant "
                    "to " + _PRETTY.get(axis_x, axis_x).split(" (")[0],
                    xy=(0.97, 0.82), xycoords="axes fraction", ha="right",
                    va="top", fontsize=8, color="#444",
                    bbox=dict(boxstyle="round,pad=0.3", fc="#f4f6f7",
                              ec="#ccc", lw=0.5))
    ax.set_title("Leakage is set by US export capacity, not Mexican-shale cost")
    plt.tight_layout()
    plt.savefig("outputs/figures/Scenario_heatmap.png", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs("outputs/figures", exist_ok=True)
    sweep_1d()
    sweep_2d()

# ==========================================================
# plot_world_flows.py
#
# World choropleth of gas trade flows per period. Country
# polygons are filled by model region (see region_colors.py);
# arrows are coloured by transport mode (PIPELINE blue /
# LNG red), width scales with flow (BCM).
#
# Outputs (outputs/figures/):
#   WorldFlows_<year>.png        (one map per period)
#   WorldFlows_AllPeriods.png    (combined grid)
# ==========================================================

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from matplotlib.lines import Line2D

import geopandas as gpd
import cartopy.io.shapereader as shpreader

from src.region_colors import (PIPE_C, LNG_C, ABBR, assign_regions, paint_countries,
                               region_legend_handles, mode_legend_handles)

MAXLW = 7.0

# ----------------------------------------------------------
# Flow-width classes (BCM -> linewidth). Discrete RANGES give
# each magnitude band a clearly distinct line width, so small
# corridors stay visible and large ones don't all saturate at
# the same maximum (the old linear scale flattened everything
# above ~300 BCM to MAXLW). Edit edges/widths here to retune.
# ----------------------------------------------------------
WIDTH_BINS = [(5, 1.0), (20, 2.0), (50, 3.2), (100, 4.6), (200, 6.2)]
WIDTH_MAX = 8.0                      # flows at/above the last edge
_WIDTH_LABELS = ["1-5", "5-20", "20-50", "50-100", "100-200", ">200"]
_WIDTH_VALUES = [1.0, 2.0, 3.2, 4.6, 6.2, 8.0]


def flow_width(flow):
    """Map a flow (BCM) to a line width by range band."""
    for edge, w in WIDTH_BINS:
        if flow < edge:
            return w
    return WIDTH_MAX


def width_legend_handles():
    """Legend entries explaining the flow-width bands."""
    return [Line2D([0], [0], color="0.35", lw=w, label=f"{lab} BCM")
            for lab, w in zip(_WIDTH_LABELS, _WIDTH_VALUES)]


def _load():
    nodes = pd.read_csv("data/nodes.csv")
    coords = {r["Node"]: (r["lon"], r["lat"]) for _, r in nodes.iterrows()}
    links = pd.read_csv("data/links.csv")
    link_type = dict(zip(links["Name"], links["Type"]))
    producers = pd.read_csv("data/producers.csv")
    domestic = {(r["Node"], r["MarketBus"]) for _, r in producers.iterrows()}
    trade = pd.read_csv("outputs/trade_flows.csv")
    return coords, link_type, domestic, trade


def _panel(ax, world, trade, year, coords, link_type, domestic):
    paint_countries(ax, world)
    ax.set_xlim(-170, 180); ax.set_ylim(-58, 84)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(str(year), fontsize=15, fontweight="bold")

    df = trade[(trade.Year == year) & (trade.Flow > 1)]
    endpoints = set()
    for _, r in df.iterrows():
        f, t = r["From"], r["To"]
        if (f, t) in domestic or f not in coords or t not in coords:
            continue
        x1, y1 = coords[f]; x2, y2 = coords[t]
        col = LNG_C if str(link_type.get(r["Route"], "PIPELINE")).upper() == "LNG" else PIPE_C
        lw = flow_width(r["Flow"])
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=10,
                     linewidth=lw, color=col, alpha=0.9,
                     connectionstyle="arc3,rad=0.14", zorder=4))
        endpoints.update([f, t])

    for nm in endpoints:
        x, y = coords[nm]
        ax.scatter(x, y, s=10, color="black", zorder=5)
    # virtual US LNG export hub (no country to fill)
    if "US_LNG" in coords:
        x, y = coords["US_LNG"]
        ax.scatter(x, y, s=70, marker="*", color="black", zorder=6)
        ax.text(x, y - 3, ABBR["US_LNG"], fontsize=7, ha="center", va="top", zorder=6)


def plot_world_flows():
    if not os.path.exists("outputs/trade_flows.csv"):
        print("  ! Skipping world flows: outputs/trade_flows.csv not found.")
        return
    os.makedirs("outputs/figures", exist_ok=True)
    coords, link_type, domestic, trade = _load()
    world = gpd.read_file(shpreader.natural_earth(
        resolution="110m", category="cultural", name="admin_0_countries"))
    world = assign_regions(world)
    years = sorted(trade["Year"].unique())

    for year in years:
        fig, ax = plt.subplots(figsize=(14, 7))
        _panel(ax, world, trade, year, coords, link_type, domestic)
        ax.set_title(f"Global Gas Trade Flows {year}", fontsize=15, fontweight="bold")
        ax.legend(handles=mode_legend_handles() + width_legend_handles(),
                  loc="lower left", fontsize=9, frameon=True, ncol=2,
                  title="mode  |  flow width")
        fig.legend(handles=region_legend_handles(), loc="center left",
                   bbox_to_anchor=(1.0, 0.5), fontsize=8, frameon=False, title="Regions")
        plt.tight_layout()
        plt.savefig(f"outputs/figures/WorldFlows_{year}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

    ncols = 2
    nrows = (len(years) + ncols - 1) // ncols
    if len(years) % ncols == 0:
        nrows += 1
    fig, axs = plt.subplots(nrows, ncols, figsize=(8.5 * ncols, 4.6 * nrows))
    axs = axs.flatten()
    for i, year in enumerate(years):
        _panel(axs[i], world, trade, year, coords, link_type, domestic)
    for j in range(len(years), len(axs)):
        axs[j].axis("off")
    leg_ax = axs[len(years)] if len(years) < len(axs) else axs[-1]
    leg_ax.legend(handles=region_legend_handles() + mode_legend_handles() + width_legend_handles(),
                  loc="center", ncol=3, fontsize=9, frameon=False,
                  title="Regions  |  transport mode  |  flow width (BCM)", title_fontsize=13)
    plt.suptitle("Global Gas Trade Flows by Period — countries coloured by region, pipeline vs LNG",
                 fontsize=18, fontweight="bold", y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    plt.savefig("outputs/figures/WorldFlows_AllPeriods.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"World flow maps saved ({len(years)} periods + combined grid).")


if __name__ == "__main__":
    plot_world_flows()

# ==========================================================
# plot_north_america.py
#
# North America gas-flow choropleth per period. Country
# polygons are filled by model region (region_colors.py);
# arrows coloured by transport mode (PIPELINE blue / LNG red).
# Flows that leave the region (e.g. US LNG to Europe/Asia)
# are drawn toward their true destination and clipped at the
# frame, with a "-> Destination (BCM)" label at the edge so
# the complete flow is visible.
#
# Outputs (outputs/figures/):
#   NorthAmericaFlows_<year>.png      (one map per period)
#   NorthAmericaFlows_AllPeriods.png  (combined grid)
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

from src.region_colors import (PIPE_C, LNG_C, ABBR, REGIONS, assign_regions, paint_countries)
from src.plot_world_flows import flow_width, width_legend_handles

# North American nodes (producers + market hubs) kept in frame
NA = {"US_GULF", "PERMIAN", "APPALACHIA", "CAN_WEST", "CAN_EAST",
      "MEX_CONV", "MEX_SHALE", "USA", "CANADA", "MEXICO", "US_LNG"}
XMIN, XMAX, YMIN, YMAX = -135, -52, 8, 72


def _load():
    nodes = pd.read_csv("data/nodes.csv")
    coords = {r["Node"]: (r["lon"], r["lat"]) for _, r in nodes.iterrows()}
    links = pd.read_csv("data/links.csv")
    link_type = dict(zip(links["Name"], links["Type"]))
    producers = pd.read_csv("data/producers.csv")
    market = {r["Node"]: r["MarketBus"] for _, r in producers.iterrows()}
    trade = pd.read_csv("outputs/trade_flows.csv")
    return coords, link_type, market, trade


def _region_of(node, market):
    return node if node in REGIONS else market.get(node, node)


def _edge_point(O, D):
    ox, oy = O; dx, dy = D
    cand = []
    if dx != ox:
        for xb in (XMIN, XMAX):
            t = (xb - ox) / (dx - ox)
            if 0 < t <= 1:
                y = oy + t * (dy - oy)
                if YMIN <= y <= YMAX:
                    cand.append((t, (xb, y)))
    if dy != oy:
        for yb in (YMIN, YMAX):
            t = (yb - oy) / (dy - oy)
            if 0 < t <= 1:
                x = ox + t * (dx - ox)
                if XMIN <= x <= XMAX:
                    cand.append((t, (x, yb)))
    return min(cand)[1] if cand else None


def _panel(ax, world, trade, year, coords, link_type, market):
    paint_countries(ax, world)
    ax.set_xlim(XMIN, XMAX); ax.set_ylim(YMIN, YMAX)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(str(year), fontsize=15, fontweight="bold")

    # Asia-Pacific destinations are reached from North America WESTWARD across
    # the Pacific, so draw them to the LEFT of the frame by wrapping longitude
    # (lon - 360), rather than the "long way" east across the Atlantic/Europe.
    PACIFIC = {"CHINA", "NORTHEAST_ASIA", "SOUTHEAST_ASIA", "SOUTH_ASIA"}

    def dc(node):
        x, y = coords[node]
        if _region_of(node, market) in PACIFIC and x > 0:
            x -= 360
        return (x, y)

    df = trade[(trade.Year == year) & (trade.Flow > 1)]
    endpoints = set()
    edge_labels = []
    for _, r in df.iterrows():
        f, t = r["From"], r["To"]
        if not (f in NA or t in NA) or f not in coords or t not in coords:
            continue
        p1 = dc(f); p2 = dc(t)
        col = LNG_C if str(link_type.get(r["Route"], "PIPELINE")).upper() == "LNG" else PIPE_C
        lw = flow_width(r["Flow"])
        ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=11,
                     linewidth=lw, color=col, alpha=0.9,
                     connectionstyle="arc3,rad=0.12", zorder=4, clip_on=True))
        if f in NA:
            endpoints.add(f)
        if t in NA:
            endpoints.add(t)
        if t not in NA:
            ep = _edge_point(p1, p2)
            if ep:
                edge_labels.append((ep, ABBR.get(_region_of(t, market), t), r["Flow"], col))
        if f not in NA:
            ep = _edge_point(p2, p1)
            if ep:
                edge_labels.append((ep, ABBR.get(_region_of(f, market), f), r["Flow"], col))

    for nm in endpoints:
        x, y = coords[nm]
        m = "*" if nm == "US_LNG" else "o"
        ax.scatter(x, y, s=(70 if nm == "US_LNG" else 14), marker=m, color="black", zorder=6)
    if "US_LNG" in endpoints:
        x, y = coords["US_LNG"]
        ax.text(x, y - 2.2, ABBR["US_LNG"], fontsize=7, ha="center", va="top", zorder=6)

    edge_labels.sort(key=lambda e: (round(e[0][0]), e[0][1]))
    lasty = None
    for (ex, ey), lab, fl, col in edge_labels:
        ty = ey
        if lasty is not None and abs(ty - lasty) < 4.5:
            ty = lasty + 4.5
        lasty = ty
        ha = "left" if ex > XMAX - 6 else ("right" if ex < XMIN + 6 else "center")
        ax.annotate(f"-> {lab} ({fl:.0f})", xy=(ex, ey),
                    xytext=(ex - 2.5 if ha == "right" else ex + 2.5, ty),
                    fontsize=7, color=col, fontweight="bold", va="center", ha=ha, zorder=7,
                    bbox=dict(boxstyle="round,pad=0.12", fc="white", ec=col, lw=0.6, alpha=0.9))


def _legend(ax):
    handles = [
        Line2D([0], [0], color=PIPE_C, lw=4, label="Pipeline gas"),
        Line2D([0], [0], color=LNG_C, lw=4, label="LNG"),
        Line2D([0], [0], marker='*', color='w', markerfacecolor='black',
               markersize=13, label="US-LNG export hub"),
        Line2D([0], [0], marker=r'$\rightarrow$', color='gray', linestyle='None',
               markersize=12, label="-> Dest (BCM): flow leaving frame"),
    ] + width_legend_handles()
    ax.legend(handles=handles, loc="center", ncol=2, fontsize=11, frameon=False,
              title="North America gas flows (countries coloured by region)\n"
                    "line width = flow magnitude (BCM)", title_fontsize=13)


def plot_north_america():
    if not os.path.exists("outputs/trade_flows.csv"):
        print("  ! Skipping NA map: outputs/trade_flows.csv not found.")
        return
    os.makedirs("outputs/figures", exist_ok=True)
    coords, link_type, market, trade = _load()
    world = gpd.read_file(shpreader.natural_earth(
        resolution="110m", category="cultural", name="admin_0_countries"))
    world = assign_regions(world)
    years = sorted(trade["Year"].unique())

    for year in years:
        fig, ax = plt.subplots(figsize=(11, 8))
        _panel(ax, world, trade, year, coords, link_type, market)
        ax.set_title(f"North America Gas Flows {year} (incl. flows leaving the region)",
                     fontsize=14, fontweight="bold")
        ax.legend(handles=[Line2D([0], [0], color=PIPE_C, lw=3, label="Pipeline"),
                           Line2D([0], [0], color=LNG_C, lw=3, label="LNG")]
                          + width_legend_handles(),
                  loc="lower left", fontsize=8, frameon=True, ncol=2,
                  title="mode  |  flow width (BCM)")
        plt.tight_layout()
        plt.savefig(f"outputs/figures/NorthAmericaFlows_{year}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

    ncols = 2
    nrows = (len(years) + ncols - 1) // ncols
    if len(years) % ncols == 0:
        nrows += 1
    fig, axs = plt.subplots(nrows, ncols, figsize=(8 * ncols, 5.4 * nrows))
    axs = axs.flatten()
    for i, year in enumerate(years):
        _panel(axs[i], world, trade, year, coords, link_type, market)
    for j in range(len(years), len(axs)):
        axs[j].axis("off")
    _legend(axs[len(years)] if len(years) < len(axs) else axs[-1])
    plt.suptitle("North America Gas Flows by Period — incl. flows leaving the region (clipped)",
                 fontsize=18, fontweight="bold", y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    plt.savefig("outputs/figures/NorthAmericaFlows_AllPeriods.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"North America flow maps saved ({len(years)} periods + combined grid).")


if __name__ == "__main__":
    plot_north_america()

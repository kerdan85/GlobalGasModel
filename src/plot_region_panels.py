# ==========================================================
# plot_region_panels.py
#
# Comparative, region-by-region figures (small multiples) from the
# model's regional balance output (outputs/regional_balance_{year}.csv,
# columns: Year, Region, Production, Imports, Demand, Exports,
# NetExports, ...). Three publication-style panels:
#
#   1. demand_small_multiples() -- a grid of per-region gas-demand
#      trajectories 2025-2045 (who grows, who shrinks).
#   2. supply_demand_panels()   -- per region: production (area) vs
#      demand (line), so importer/producer status is visible at a glance.
#   3. net_trade_dumbbell()     -- net exports 2025 vs 2045 by region,
#      showing who deepens import dependence (Mexico) and who ramps
#      exports (US) -- the paper's core reallocation in one chart.
#
# Location-independent; writes to <project root>/outputs/figures/.
# ==========================================================

import os
import glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OUT = os.path.join(_ROOT, "outputs")
_FIG = os.path.join(_OUT, "figures")

PRETTY = {
    "USA": "United States", "CANADA": "Canada", "MEXICO": "Mexico",
    "EUROPE": "Europe", "CHINA": "China", "SOUTH_ASIA": "South Asia",
    "SOUTHEAST_ASIA": "Southeast Asia", "NORTHEAST_ASIA": "Northeast Asia",
    "LATIN_AMERICA": "Latin America", "RUSSIA": "Russia", "IRAN": "Iran",
    "GULF_STATES": "Gulf States", "QATAR": "Qatar", "NORTH_AFRICA": "North Africa",
    "SUBSAHARAN_AFRICA": "Sub-Saharan Africa", "CENTRAL_ASIA": "Central Asia",
    "CASPIAN_REGION": "Caspian", "AUSTRALIA": "Australia", "US_LNG": "US-LNG hub",
}
FOCUS = {"MEXICO", "USA"}
NAVY, RED, GREY, LIGHT = "#1f3b57", "#b2222a", "#8a8a8a", "#c9d6e2"


def load_balance():
    """Concatenate per-year regional_balance files (ignore OneDrive
    '-MacBook Pro' conflict copies); fall back to the master file."""
    files = [f for f in glob.glob(os.path.join(_OUT, "regional_balance_20*.csv"))
             if "MacBook" not in f]
    if files:
        df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    else:
        df = pd.read_csv(os.path.join(_OUT, "regional_balance.csv"))
    return df.sort_values(["Region", "Year"])


def _theme(ax, base=10):
    ax.tick_params(labelsize=base - 2, length=3)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# ----------------------------------------------------------
def demand_small_multiples():
    os.makedirs(_FIG, exist_ok=True)
    df = load_balance()
    df = df[df.Region != "US_LNG"]
    order = (df[df.Year == df.Year.max()].sort_values("Demand", ascending=False)
             ["Region"].tolist())
    n = len(order); ncol = 5; nrow = -(-n // ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(2.4 * ncol, 1.9 * nrow),
                             sharex=True)
    axes = axes.ravel()
    for i, reg in enumerate(order):
        ax = axes[i]
        d = df[df.Region == reg]
        focus = reg in FOCUS
        col = RED if focus else NAVY
        ax.fill_between(d.Year, d.Demand, color=col, alpha=0.12)
        ax.plot(d.Year, d.Demand, color=col, lw=2 if focus else 1.4)
        ax.set_title(PRETTY.get(reg, reg), fontsize=9,
                     fontweight="bold" if focus else "normal",
                     color=col if focus else "black")
        peak = d.Demand.iloc[-1]
        ax.annotate(f"{peak:.0f}", (d.Year.iloc[-1], peak), fontsize=7,
                    color=col, ha="right", va="bottom")
        ax.set_ylim(0, d.Demand.max() * 1.25)
        ax.set_xticks([2025, 2035, 2045])
        _theme(ax)
    for j in range(n, len(axes)):
        axes[j].set_visible(False)
    fig.suptitle("Gas demand by region, 2025--2045 (BCM per year)",
                 x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.supylabel("Demand (BCM yr$^{-1}$)", fontsize=10)
    fig.text(0.99, 0.005, "Panels share time axis; y-axis scaled per region "
             "(note differing magnitudes). US and Mexico highlighted.",
             ha="right", fontsize=7, color="#777")
    plt.tight_layout(rect=[0.02, 0.02, 1, 0.96])
    plt.savefig(os.path.join(_FIG, "Region_demand_panels.png"), dpi=300)
    plt.savefig(os.path.join(_FIG, "Region_demand_panels.pdf"))
    plt.close(fig)


# ----------------------------------------------------------
def supply_demand_panels():
    os.makedirs(_FIG, exist_ok=True)
    df = load_balance()
    df = df[df.Region != "US_LNG"]
    order = (df[df.Year == df.Year.max()].sort_values("Demand", ascending=False)
             ["Region"].tolist())
    n = len(order); ncol = 5; nrow = -(-n // ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(2.4 * ncol, 2.0 * nrow),
                             sharex=True)
    axes = axes.ravel()
    for i, reg in enumerate(order):
        ax = axes[i]; d = df[df.Region == reg]; focus = reg in FOCUS
        ax.fill_between(d.Year, d.Production, color=NAVY, alpha=0.85,
                        label="Production", linewidth=0)
        ax.plot(d.Year, d.Demand, color=RED, lw=1.8, label="Demand")
        ax.set_title(PRETTY.get(reg, reg), fontsize=9,
                     fontweight="bold" if focus else "normal",
                     color=RED if focus else "black")
        top = max(d.Production.max(), d.Demand.max()) * 1.2
        ax.set_ylim(0, top); ax.set_xticks([2025, 2035, 2045]); _theme(ax)
        if focus:
            for s in ("left", "bottom"):
                ax.spines[s].set_color(RED); ax.spines[s].set_linewidth(1.3)
    for j in range(n, len(axes)):
        axes[j].set_visible(False)
    axes[0].legend(fontsize=7, loc="upper left", frameon=False)
    fig.suptitle("Production versus demand by region, 2025--2045",
                 x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.text(0.99, 0.005, "Filled = production; line = demand. A gap below the "
             "line is met by imports; above, by exports. US/Mexico highlighted.",
             ha="right", fontsize=7, color="#777")
    plt.tight_layout(rect=[0.01, 0.02, 1, 0.96])
    plt.savefig(os.path.join(_FIG, "Region_supply_demand_panels.png"), dpi=300)
    plt.savefig(os.path.join(_FIG, "Region_supply_demand_panels.pdf"))
    plt.close(fig)


# ----------------------------------------------------------
def net_trade_dumbbell():
    os.makedirs(_FIG, exist_ok=True)
    df = load_balance()
    df = df[df.Region != "US_LNG"]
    y0, y1 = df.Year.min(), df.Year.max()
    a = df[df.Year == y0].set_index("Region")["NetExports"]
    b = df[df.Year == y1].set_index("Region")["NetExports"]
    reg = b.sort_values().index.tolist()
    fig, ax = plt.subplots(figsize=(7.5, 7))
    for i, r in enumerate(reg):
        x0, x1 = a.get(r, 0), b.get(r, 0)
        focus = r in FOCUS
        ax.plot([x0, x1], [i, i], color=(RED if focus else GREY),
                lw=2.2 if focus else 1.3, zorder=2, alpha=0.9)
        ax.scatter(x0, i, color=LIGHT, edgecolor="#555", s=34, zorder=3)
        ax.scatter(x1, i, color=(RED if focus else NAVY), s=46, zorder=4)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(range(len(reg)))
    ax.set_yticklabels([PRETTY.get(r, r) for r in reg],
                       fontsize=8)
    for t, r in zip(ax.get_yticklabels(), reg):
        if r in FOCUS:
            t.set_color(RED); t.set_fontweight("bold")
    ax.set_xlabel("Net exports (BCM yr$^{-1}$)  --  importers left, exporters right")
    ax.set_title(f"Who imports, who exports: net trade position, {y0} vs {y1}",
                 loc="left", fontsize=13, fontweight="bold")
    ax.scatter([], [], color=LIGHT, edgecolor="#555", s=34, label=str(y0))
    ax.scatter([], [], color=NAVY, s=46, label=str(y1))
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    plt.savefig(os.path.join(_FIG, "Region_net_trade_dumbbell.png"), dpi=300)
    plt.savefig(os.path.join(_FIG, "Region_net_trade_dumbbell.pdf"))
    plt.close(fig)


STEEL = "#6a9ec0"

# ----------------------------------------------------------
# Detailed per-region gas balance: stacked sources vs demand.
#   bars  = domestic production + imports + coal/backstop (total supply)
#   line  = demand.  For an exporter, production rises above the demand
#           line and the surplus is exported; for an importer, imports
#           (and any coal backstop) fill the gap up to demand.
# ----------------------------------------------------------
def _region_balance(ax, d, region, show_legend=False, base=10):
    yrs = d.Year.values; w = 3.2
    prod, imp, back = d.Production.values, d.Imports.values, d.Backstop.values
    ax.bar(yrs, prod, w, color=NAVY, label="Domestic production", zorder=2)
    ax.bar(yrs, imp, w, bottom=prod, color=STEEL, label="Imports", zorder=2)
    ax.bar(yrs, back, w, bottom=prod + imp, color=GREY, label="Coal / backstop",
           zorder=2)
    ax.plot(yrs, d.Demand.values, color=RED, lw=1.9, marker="o", ms=3.5,
            label="Demand", zorder=4)
    focus = region in FOCUS
    ax.set_title(PRETTY.get(region, region), fontsize=9,
                 fontweight="bold" if focus else "normal",
                 color=RED if focus else "black")
    ax.set_xticks([2025, 2035, 2045])
    top = max((prod + imp + back).max(), d.Demand.max()) * 1.18
    ax.set_ylim(0, top)
    _theme(ax, base)
    if focus:
        for s in ("left", "bottom"):
            ax.spines[s].set_color(RED); ax.spines[s].set_linewidth(1.3)
    if show_legend:
        ax.legend(fontsize=7, loc="upper left", frameon=False)


def region_balance_grid():
    """Combined figure: the detailed balance panel for every region."""
    os.makedirs(_FIG, exist_ok=True)
    df = load_balance()
    df = df[df.Region != "US_LNG"]
    order = (df[df.Year == df.Year.max()].sort_values("Demand", ascending=False)
             ["Region"].tolist())
    n = len(order); ncol = 5; nrow = -(-n // ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(2.5 * ncol, 2.0 * nrow),
                             sharex=True)
    axes = axes.ravel()
    # Shift the last (partial) row to the RIGHT so the bottom-LEFT slots open up
    # to host the shared legend without overlapping any panel.
    total = nrow * ncol; empties = total - n; lrs = (nrow - 1) * ncol
    slot = lambda i: i if i < lrs else i + empties
    for i, reg in enumerate(order):
        _region_balance(axes[slot(i)], df[df.Region == reg], reg, show_legend=False)
    for j in range(lrs, lrs + empties):
        axes[j].axis("off")
    h, l = axes[0].get_legend_handles_labels()
    if empties > 0:
        axes[lrs].legend(h, l, loc="center left", fontsize=9, frameon=False,
                         title="Supply vs demand", title_fontsize=9,
                         labelspacing=0.8, borderaxespad=0.2)
    else:
        fig.legend(h, l, loc="lower left", bbox_to_anchor=(0.03, 0.0), ncol=4,
                   fontsize=9, frameon=False)
    fig.suptitle("Gas balance by region, 2025--2045: supply composition versus demand",
                 x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.supylabel("BCM yr$^{-1}$", fontsize=10)
    fig.text(0.99, 0.005, "Bars: domestic production + imports + coal/backstop "
             "(total supply). Line: demand. Surplus above the line is exported. "
             "US/Mexico highlighted.", ha="right", fontsize=7, color="#777")
    plt.tight_layout(rect=[0.02, 0.02, 1, 0.96])
    plt.savefig(os.path.join(_FIG, "Region_balance_grid.png"), dpi=300)
    plt.savefig(os.path.join(_FIG, "Region_balance_grid.pdf"))
    plt.close(fig)


def region_balance_single(regions=None):
    """One standalone detailed chart per region (own file)."""
    os.makedirs(os.path.join(_FIG, "regions"), exist_ok=True)
    df = load_balance()
    regions = regions or [r for r in df.Region.unique() if r != "US_LNG"]
    for reg in regions:
        fig, ax = plt.subplots(figsize=(4.2, 3.2))
        _region_balance(ax, df[df.Region == reg], reg, show_legend=True, base=11)
        ax.set_ylabel("BCM yr$^{-1}$", fontsize=9)
        plt.tight_layout()
        out = os.path.join(_FIG, "regions", f"balance_{reg}.png")
        plt.savefig(out, dpi=300); plt.close(fig)
    print(f"  per-region charts -> {os.path.join(_FIG, 'regions')}")


GOLD, TEAL = "#e0a030", "#1b6f6b"

# ----------------------------------------------------------
# Per-region LIFECYCLE EMISSIONS over time (from the PyPSA x Brightway
# coupling, outputs/emissions_by_region.csv): GWP100 and GWP20 trajectories.
# ----------------------------------------------------------
def emissions_grid():
    os.makedirs(_FIG, exist_ok=True)
    path = os.path.join(_OUT, "emissions_by_region.csv")
    if not os.path.exists(path):
        print("  emissions_by_region.csv not found -- run src/lca_link.py first.")
        return
    df = pd.read_csv(path)
    df = df[df.Region != "US_LNG"]
    order = (df[df.Year == df.Year.max()].sort_values("Emissions_GWP20_Mt", ascending=False)
             ["Region"].tolist())
    n = len(order); ncol = 5; nrow = -(-n // ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(2.5 * ncol, 1.95 * nrow), sharex=True)
    axes = axes.ravel()
    total = nrow * ncol; empties = total - n; lrs = (nrow - 1) * ncol
    slot = lambda i: i if i < lrs else i + empties
    for i, reg in enumerate(order):
        ax = axes[slot(i)]; d = df[df.Region == reg].sort_values("Year"); focus = reg in FOCUS
        ax.fill_between(d.Year, d.Emissions_GWP20_Mt, color=GOLD, alpha=0.18)
        ax.plot(d.Year, d.Emissions_GWP20_Mt, color=GOLD, lw=1.8, label="GWP20")
        ax.plot(d.Year, d.Emissions_GWP100_Mt, color=TEAL, lw=1.8, label="GWP100")
        ax.set_title(PRETTY.get(reg, reg), fontsize=9,
                     fontweight="bold" if focus else "normal",
                     color=RED if focus else "black")
        ax.set_xticks([2025, 2035, 2045]); _theme(ax)
        ax.set_ylim(0, d.Emissions_GWP20_Mt.max() * 1.2 + 1)
    # bottom-left empty slots host the legend, clear of every panel
    for j in range(lrs, lrs + empties):
        axes[j].axis("off")
    h, l = axes[0].get_legend_handles_labels()
    if empties > 0:
        axes[lrs].legend(h, l, loc="center left", fontsize=9, frameon=False,
                         title="GWP horizon", title_fontsize=9, labelspacing=0.9,
                         borderaxespad=0.2)
    else:
        fig.legend(h, l, loc="lower left", bbox_to_anchor=(0.03, 0.0), ncol=2,
                   fontsize=9, frameon=False)
    fig.suptitle("Lifecycle GHG emissions by region, 2025--2045 (PyPSA $\\times$ Brightway)",
                 x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.supylabel("Mt CO$_2$e yr$^{-1}$", fontsize=10)
    fig.text(0.99, 0.005, "ecoinvent-based lifecycle emissions from modelled dispatch; "
             "gold = 20-yr GWP, teal = 100-yr GWP. y-axis per region.",
             ha="right", fontsize=7, color="#777")
    plt.tight_layout(rect=[0.02, 0.02, 1, 0.96])
    plt.savefig(os.path.join(_FIG, "Region_emissions_panels.png"), dpi=300)
    plt.savefig(os.path.join(_FIG, "Region_emissions_panels.pdf"))
    plt.close(fig)


# ----------------------------------------------------------
# Per-region RESERVE depletion (from outputs/reserves_depletion.csv):
# % of the resource base consumed 2025-2045, conventional vs unconventional,
# with regions "under pressure" flagged.
# ----------------------------------------------------------
def reserves_grid():
    os.makedirs(_FIG, exist_ok=True)
    path = os.path.join(_OUT, "reserves_depletion.csv")
    if not os.path.exists(path):
        print("  reserves_depletion.csv not found -- run run_model.py first.")
        return
    d = pd.read_csv(path)
    col = "PctTotalConsumed" if "PctTotalConsumed" in d.columns else "PctProvedConsumed"
    regions = [r for r in d["Region"].unique() if r != "US_LNG"]
    # order by max depletion
    regions = (d[d.Region.isin(regions)].groupby("Region")[col].max()
               .sort_values(ascending=False).index.tolist())
    n = len(regions); ncol = 5; nrow = -(-n // ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(2.4 * ncol, 1.9 * nrow), sharex=True)
    axes = axes.ravel()
    for i, reg in enumerate(regions):
        ax = axes[i]; sub = d[d.Region == reg]; focus = reg in FOCUS
        types = sub["Type"].tolist(); vals = sub[col].tolist()
        pressure = bool(sub["Pressure"].any()) if "Pressure" in sub else False
        colors = ["#b2222a" if pressure else NAVY for _ in types]
        ax.bar(range(len(types)), vals, color=colors, width=0.6)
        ax.axhline(100, ls=":", color="grey", lw=0.8)
        ax.set_xticks(range(len(types)))
        ax.set_xticklabels([t[:4] for t in types], fontsize=7)
        ax.set_title(PRETTY.get(reg, reg), fontsize=9,
                     fontweight="bold" if (focus or pressure) else "normal",
                     color=RED if focus else ("#b2222a" if pressure else "black"))
        ax.set_ylim(0, max(120, max(vals) * 1.15 if vals else 120)); _theme(ax)
    for j in range(n, len(axes)):
        axes[j].set_visible(False)
    fig.suptitle("Resource depletion by region: \\% of gas resource consumed 2025--2045",
                 x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.supylabel("\\% consumed", fontsize=10)
    fig.text(0.99, 0.005, "Bars: conventional (Conv) and unconventional (Unco) resource "
             "consumed; dotted line = 100\\%. Red = region under depletion pressure.",
             ha="right", fontsize=7, color="#777")
    plt.tight_layout(rect=[0.02, 0.02, 1, 0.96])
    plt.savefig(os.path.join(_FIG, "Region_reserves_panels.png"), dpi=300)
    plt.savefig(os.path.join(_FIG, "Region_reserves_panels.pdf"))
    plt.close(fig)


def run_all():
    demand_small_multiples()
    supply_demand_panels()
    net_trade_dumbbell()
    region_balance_grid()
    region_balance_single()
    emissions_grid()
    reserves_grid()
    print(f"Region panels written to {_FIG}")


if __name__ == "__main__":
    run_all()

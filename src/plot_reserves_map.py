# ==========================================================
# plot_reserves_map.py
#
# Publication-grade world map of unconventional (shale) gas
# resources, in the paper's restrained style. Countries are
# shaded by development STATUS (producer / planned / frontier /
# conventional potential) and the largest shale-gas resource
# holders are labelled with their technically-recoverable
# resource (TRR). The paper's focus countries -- the United
# States and Mexico -- are accented.
#
# This is an ORIGINAL figure built from public data
# (EIA/ARI technically-recoverable shale resource estimates;
# Energy Institute Statistical Review). It is not a reproduction
# of any copyrighted infographic.
#
# Dependencies (install on your machine):
#     pip install geopandas matplotlib shapely pandas
# World geometry is loaded from geopandas' bundled dataset, or
# downloaded once from the Natural Earth CDN if not bundled.
#
# Run (working dir = project root):
#     python -m src.plot_reserves_map
# Output: outputs/figures/Fig_unconventional_gas_map.{png,pdf}
# ==========================================================

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

# Resolve output dir to the PROJECT ROOT (one level up from src/),
# so the figure lands in <root>/outputs/figures regardless of the
# working directory Spyder/Python is launched from.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OUTDIR = os.path.join(_ROOT, "outputs", "figures")

# ----------------------------------------------------------
# Data: shale-gas technically-recoverable resource (TRR, tcm)
# and development status, keyed by ISO-3166 alpha-3 code.
# Sources: EIA/ARI (2013) world shale assessment; status after
# Energy Institute Statistical Review. Values are public and
# approximate -- adjust/extend as needed.
# ----------------------------------------------------------
STATUS_PRODUCER   = "Current unconventional producer"
STATUS_PLANNED    = "Planned production"
STATUS_FRONTIER   = "Frontier potential"
STATUS_CONV       = "Conventional-gas potential"

DATA = {
    # iso3: (shale_gas_tcm, status)
    "USA": (17.6, STATUS_PRODUCER),
    "CAN": (16.2, STATUS_PRODUCER),
    "CHN": (31.6, STATUS_PRODUCER),
    "ARG": (22.7, STATUS_PRODUCER),
    "AUS": (12.2, STATUS_PRODUCER),
    "MEX": (15.4, STATUS_FRONTIER),
    "DZA": (20.0, STATUS_FRONTIER),
    "ZAF": (11.0, STATUS_FRONTIER),
    "POL": (4.1,  STATUS_FRONTIER),
    "TUR": (0.7,  STATUS_FRONTIER),
    "GBR": (0.7,  STATUS_FRONTIER),
    "SAU": (17.0, STATUS_PLANNED),
    "ARE": (5.8,  STATUS_PLANNED),
    "RUS": (8.1,  STATUS_CONV),
    "IRN": (0.0,  STATUS_CONV),
    "QAT": (0.0,  STATUS_CONV),
    "MOZ": (0.0,  STATUS_CONV),
    "TZA": (0.0,  STATUS_CONV),
}

# Sequential warm (YlOrBr-style) ramp for development status: darkest =
# current producer, fading to light for frontier/conventional. Reads as
# "development intensity" and sits clearly against a cool ocean.
FILL = {
    STATUS_PRODUCER: "#99340a",   # dark burnt orange
    STATUS_PLANNED:  "#e6550d",   # orange
    STATUS_FRONTIER: "#fdae6b",   # light orange
    STATUS_CONV:     "#fee6ce",   # pale tan
}
NODATA     = "#dfe3e6"   # light warm grey land (contrasts with the ocean)
OCEAN      = "#cde0ea"   # soft blue ocean panel
LAND_EDGE  = "#4a4f54"   # dark grey country borders -> continents stay visible
ACCENT     = "#2b2b2b"   # US / Mexico accent edge (near-black, stands out on warm fills)

# countries to label with their TRR (largest holders + focus)
LABELS = ["USA", "MEX", "CAN", "ARG", "CHN", "AUS", "DZA", "SAU", "ZAF", "RUS"]
ISO_NAME = {"USA": "United States", "MEX": "Mexico", "CAN": "Canada",
            "ARG": "Argentina", "CHN": "China", "AUS": "Australia",
            "DZA": "Algeria", "SAU": "Saudi Arabia", "ZAF": "South Africa",
            "RUS": "Russia"}


def load_world():
    import geopandas as gpd
    # 1) bundled dataset (older geopandas)
    try:
        return gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    except Exception:
        pass
    # 2) Natural Earth CDN (downloaded once; needs internet)
    url = ("https://naciscdn.org/naturalearth/110m/cultural/"
           "ne_110m_admin_0_countries.zip")
    return gpd.read_file(url)


def iso_column(world):
    for c in ("iso_a3", "ISO_A3", "ISO_A3_EH", "ADM0_A3", "SOV_A3"):
        if c in world.columns:
            return c
    raise KeyError("no ISO-3 column found in world geometry")


def main():
    os.makedirs(_OUTDIR, exist_ok=True)
    world = load_world()
    iso = iso_column(world)
    world = world[world[iso] != "ATA"]  # drop Antarctica

    world["status"] = world[iso].map(lambda k: DATA.get(k, (None, None))[1])
    world["fill"] = world["status"].map(FILL).fillna(NODATA)

    # Flat, equirectangular (Plate Carree) view: keep the native lon/lat CRS so
    # the map is a clean RECTANGULAR world with straight meridians -- no curved
    # Robinson edges. The projection is therefore the identity.
    world = world.to_crs("EPSG:4326")

    def proj(lon, lat):
        return lon, lat

    fig, ax = plt.subplots(figsize=(13, 6.6))
    # soft blue ocean panel + a light graticule give a clean cartographic base
    ax.add_patch(Rectangle((-180, -58), 360, 143, facecolor=OCEAN,
                           edgecolor="#9fb8c6", lw=0.8, zorder=0))
    for gl in range(-120, 181, 60):
        ax.plot([gl, gl], [-58, 85], color="#b9d0dc", lw=0.4, zorder=0)
    for gt in range(-30, 61, 30):
        ax.plot([-180, 180], [gt, gt], color="#b9d0dc", lw=0.4, zorder=0)
    # every country gets a dark thin border so continents read clearly
    world.plot(ax=ax, color=world["fill"], edgecolor=LAND_EDGE, linewidth=0.35,
               zorder=1)
    focus = world[world[iso].isin(["USA", "MEX"])]
    focus.boundary.plot(ax=ax, edgecolor=ACCENT, linewidth=1.6, zorder=3)

    # labels with TRR (representative points are already in Robinson coords)
    for code in LABELS:
        sub = world[world[iso] == code]
        if sub.empty:
            continue
        pt = sub.geometry.representative_point().iloc[0]
        tcm, _ = DATA[code]
        txt = f"{ISO_NAME.get(code, code)}\n{tcm:.0f} tcm" if tcm > 0 else ISO_NAME.get(code, code)
        ax.annotate(txt, xy=(pt.x, pt.y), ha="center", va="center",
                    fontsize=7.5, fontweight="bold", color="#1a1a1a",
                    bbox=dict(boxstyle="round,pad=0.25", fc="white",
                              ec="#bbbbbb", lw=0.5, alpha=0.92), zorder=5)

    # --- regional gas hub prices: the arbitrage that drives leakage ---
    # Illustrative recent $/MMBtu levels (Henry Hub cheap; Asian/European
    # LNG dear). VERIFY levels before submission.
    prices = [(-70, 12, "Henry Hub\n~\\$2.5", "#145a8a"),
              (12, 60, "Europe TTF\n~\\$10", "#0e6b5c"),
              (150, 28, "Asia JKM\n~\\$12", "#6c3483")]
    for lon, lat, lab, col in prices:
        x, y = proj(lon, lat)
        ax.annotate(lab, xy=(x, y), ha="center", va="center", fontsize=7.5,
                    style="italic", color=col, zorder=6,
                    bbox=dict(boxstyle="round,pad=0.28", fc="white", ec=col,
                              lw=1.0, alpha=0.95))
    ax.set_axis_off()
    ax.set_xlim(-182, 182)
    ax.set_ylim(-58, 85)      # trim deep south / far north
    ax.set_aspect(1.15)       # gentle flat aspect (equirectangular world)
    # title + subtitle stacked clear of the map (no overlap)
    ax.text(0, 1.10, "Unconventional gas is a global resource",
            transform=ax.transAxes, fontsize=15, fontweight="bold", va="bottom")
    ax.text(0, 1.035,
            "Shale-gas resource (tcm) and development status by country; regional "
            "hub prices show the west-to-east arbitrage that drives re-export",
            transform=ax.transAxes, fontsize=9, color="#555555", va="bottom")

    legend = [Patch(facecolor=FILL[s], edgecolor="white", label=s)
              for s in (STATUS_PRODUCER, STATUS_PLANNED, STATUS_FRONTIER, STATUS_CONV)]
    legend.append(Patch(facecolor=NODATA, edgecolor="white", label="No major assessed resource"))
    legend.append(Patch(facecolor="white", edgecolor=ACCENT, label="Study focus (US, Mexico)"))
    ax.legend(handles=legend, loc="lower left", frameon=False, fontsize=8,
              bbox_to_anchor=(0.0, 0.0), ncol=1)

    ax.text(1.0, -0.02, "Data: EIA/ARI world shale assessment; Energy Institute Statistical Review.",
            transform=ax.transAxes, ha="right", va="top", fontsize=7, color="#888888")

    plt.tight_layout()
    png = os.path.join(_OUTDIR, "Fig_unconventional_gas_map.png")
    pdf = os.path.join(_OUTDIR, "Fig_unconventional_gas_map.pdf")
    plt.savefig(png, dpi=400, bbox_inches="tight")
    plt.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {png}\n      {pdf}")


if __name__ == "__main__":
    main()

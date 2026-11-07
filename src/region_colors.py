# ==========================================================
# region_colors.py
#
# Shared region definitions, colours, and a country -> region
# mapper for choropleth maps (fills Natural Earth country
# polygons by model region).
# ==========================================================

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

PIPE_C = "#1f6fb2"
LNG_C  = "#d1495b"

REGIONS = ["USA", "CANADA", "MEXICO", "EUROPE", "RUSSIA", "CHINA", "SOUTH_ASIA",
           "SOUTHEAST_ASIA", "NORTHEAST_ASIA", "LATIN_AMERICA", "NORTH_AFRICA",
           "SUBSAHARAN_AFRICA", "IRAN", "GULF_STATES", "QATAR", "CENTRAL_ASIA",
           "CASPIAN_REGION", "AUSTRALIA", "US_LNG"]

ABBR = {"USA": "USA", "CANADA": "Canada", "MEXICO": "Mexico", "EUROPE": "Europe",
        "RUSSIA": "Russia", "CHINA": "China", "SOUTH_ASIA": "S.Asia",
        "SOUTHEAST_ASIA": "SE.Asia", "NORTHEAST_ASIA": "NE.Asia", "LATIN_AMERICA": "Lat.Am",
        "NORTH_AFRICA": "N.Africa", "SUBSAHARAN_AFRICA": "Sub-Sah.Africa", "IRAN": "Iran",
        "GULF_STATES": "Gulf", "QATAR": "Qatar", "CENTRAL_ASIA": "C.Asia",
        "CASPIAN_REGION": "Caspian", "AUSTRALIA": "Australia/Oceania", "US_LNG": "US-LNG hub"}

# ----------------------------------------------------------
# Palette. "gray" = subtle shades of grey (neutral basemap so
# the coloured pipeline/LNG flow arrows stand out); "color" =
# the original tab20 qualitative palette. Switch here.
# ----------------------------------------------------------
PALETTE = "gray"

_n = len(REGIONS)
if PALETTE == "gray":
    _shades = plt.get_cmap("Greys")(np.linspace(0.10, 0.60, _n))
    # interleave low/high shades so legend-adjacent regions contrast
    _half = (_n + 1) // 2
    _order = []
    for _i in range(_half):
        _order.append(_i)
        if _i + _half < _n:
            _order.append(_i + _half)
    RCOL = {REGIONS[k]: _shades[_order[k]] for k in range(_n)}
    UNMAPPED_C = "#f4f4f4"   # near-white: de-emphasised, non-modelled countries
else:
    _PAL = plt.get_cmap("tab20")(np.linspace(0, 1, 20))
    RCOL = {r: _PAL[i] for i, r in enumerate(REGIONS)}
    UNMAPPED_C = "#e8e8e8"

# ---- explicit country -> region (lowercased; many NE name variants) ----
_LISTS = {
    "USA": ["united states of america", "united states", "usa"],
    "CANADA": ["canada"],
    "MEXICO": ["mexico"],
    "EUROPE": ["austria", "belgium", "bosnia and herz.", "bosnia and herzegovina",
               "bulgaria", "croatia", "czechia", "czech republic", "denmark", "estonia",
               "finland", "france", "germany", "greece", "hungary", "ireland", "italy",
               "kosovo", "latvia", "lithuania", "luxembourg", "moldova", "montenegro",
               "north macedonia", "macedonia", "netherlands", "poland", "portugal",
               "romania", "serbia", "republic of serbia", "slovakia", "slovenia", "spain",
               "sweden", "switzerland", "united kingdom", "ukraine", "belarus"],
    "RUSSIA": ["russia"],
    "CHINA": ["china"],
    "SOUTH_ASIA": ["india", "pakistan", "bangladesh", "nepal", "bhutan", "sri lanka", "maldives"],
    "SOUTHEAST_ASIA": ["indonesia", "malaysia", "singapore", "thailand", "vietnam",
                       "cambodia", "laos", "myanmar", "brunei", "philippines",
                       "timor-leste", "east timor"],
    "NORTHEAST_ASIA": ["japan", "south korea", "republic of korea", "korea", "north korea",
                       "dem. rep. korea", "taiwan", "mongolia"],
    "LATIN_AMERICA": ["argentina", "brazil", "chile", "bolivia", "peru", "colombia",
                      "venezuela", "ecuador", "paraguay", "uruguay", "guyana", "suriname",
                      "french guiana", "belize", "guatemala", "honduras", "el salvador",
                      "nicaragua", "costa rica", "panama", "cuba", "dominican rep.",
                      "dominican republic", "haiti", "jamaica", "trinidad and tobago",
                      "the bahamas", "bahamas", "barbados", "puerto rico"],
    "NORTH_AFRICA": ["algeria", "libya", "tunisia", "morocco", "egypt",
                     "w. sahara", "western sahara"],
    "IRAN": ["iran"],
    "GULF_STATES": ["saudi arabia", "united arab emirates", "kuwait", "oman", "bahrain"],
    "QATAR": ["qatar"],
    "CENTRAL_ASIA": ["turkmenistan", "uzbekistan", "kazakhstan", "kyrgyzstan", "tajikistan"],
    "CASPIAN_REGION": ["azerbaijan", "georgia", "armenia"],
    "AUSTRALIA": ["australia", "new zealand", "papua new guinea"],
}
COUNTRY_REGION = {name: reg for reg, names in _LISTS.items() for name in names}
_NORTH_AFRICA = set(_LISTS["NORTH_AFRICA"])


def _norm(s):
    return str(s).strip().lower() if s is not None else ""


def assign_regions(gdf):
    """Add a 'region' column to a Natural Earth GeoDataFrame.

    Matches on common name columns; any unmatched African country falls
    back to SUBSAHARAN_AFRICA (catch-all). Returns the same gdf.
    """
    name_cols = [c for c in ["NAME", "NAME_LONG", "ADMIN", "SOVEREIGNT", "name", "admin"]
                 if c in gdf.columns]
    cont_col = next((c for c in ["CONTINENT", "continent"] if c in gdf.columns), None)

    def _region(row):
        for c in name_cols:
            r = COUNTRY_REGION.get(_norm(row[c]))
            if r:
                return r
        # catch-all: any sub-Saharan African country
        if cont_col and _norm(row[cont_col]) == "africa":
            for c in name_cols:
                if _norm(row[c]) in _NORTH_AFRICA:
                    return "NORTH_AFRICA"
            return "SUBSAHARAN_AFRICA"
        return None

    gdf = gdf.copy()
    gdf["region"] = gdf.apply(_region, axis=1)
    return gdf


def paint_countries(ax, gdf):
    """Fill country polygons by region; unmapped countries light grey."""
    gdf = assign_regions(gdf)
    gdf[gdf["region"].isna()].plot(ax=ax, color=UNMAPPED_C,
                                   edgecolor="white", linewidth=0.2, zorder=0)
    for reg in REGIONS:
        if reg == "US_LNG":
            continue
        sub = gdf[gdf["region"] == reg]
        if len(sub):
            sub.plot(ax=ax, color=RCOL[reg], edgecolor="white",
                     linewidth=0.2, alpha=0.85, zorder=0)


def region_legend_handles():
    return [Patch(facecolor=RCOL[r], edgecolor="none", label=ABBR[r])
            for r in REGIONS if r != "US_LNG"]


def mode_legend_handles():
    return [Line2D([0], [0], color=PIPE_C, lw=4, label="Pipeline gas"),
            Line2D([0], [0], color=LNG_C, lw=4, label="LNG")]

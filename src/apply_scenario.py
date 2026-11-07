# ==========================================================
# apply_scenario.py
# Applies the per-year policy levers from data/scenarios.csv
# plus explicit per-year route capacities for LNG corridors,
# Russia's Asian pivot, Sub-Saharan LNG, and a sanctioned
# Iran. All non-pinned links/generators grow with SupplyGrowth.
# ==========================================================

import pandas as pd

from src.config import (SCENARIO, US_PRODUCERS, US_PLATEAU, US_LNG_ENDOGENOUS)

# Contracted LNG that runs at ~full capacity (must-run, p_min_pu).
# Only used in the legacy (non-endogenous) configuration.
US_LNG_UTIL = 1.0

# Reference-case Mexico: keeps importing US gas (no shale build-out).
REF_MEX_SHALE = 3      # negligible Mexican shale
REF_US_MEXICO = 66     # US->Mexico pipeline stays at ~real 2024 level

# ---- per-year route capacities (BCM) ----
# US LNG destination ramp (Europe/LatAm capped so US LNG also reaches Asia)
US_LNG_DEST = {
    2025: dict(US_LNG_EUROPE=60,  US_LNG_CHINA=40,  US_LNG_SOUTH_ASIA=30,
               US_LNG_SOUTHEAST_ASIA=30,  US_LNG_NORTHEAST_ASIA=30,  US_LNG_LATIN_AMERICA=15),
    2030: dict(US_LNG_EUROPE=75,  US_LNG_CHINA=50,  US_LNG_SOUTH_ASIA=40,
               US_LNG_SOUTHEAST_ASIA=40,  US_LNG_NORTHEAST_ASIA=40,  US_LNG_LATIN_AMERICA=20),
    2035: dict(US_LNG_EUROPE=95,  US_LNG_CHINA=65,  US_LNG_SOUTH_ASIA=50,
               US_LNG_SOUTHEAST_ASIA=50,  US_LNG_NORTHEAST_ASIA=50,  US_LNG_LATIN_AMERICA=25),
    2040: dict(US_LNG_EUROPE=120, US_LNG_CHINA=85,  US_LNG_SOUTH_ASIA=70,
               US_LNG_SOUTHEAST_ASIA=70,  US_LNG_NORTHEAST_ASIA=70,  US_LNG_LATIN_AMERICA=30),
    2045: dict(US_LNG_EUROPE=150, US_LNG_CHINA=110, US_LNG_SOUTH_ASIA=90,
               US_LNG_SOUTHEAST_ASIA=90,  US_LNG_NORTHEAST_ASIA=90,  US_LNG_LATIN_AMERICA=35),
}
# Canada west-coast LNG to Asia (LNG Canada etc.)
CANADA_LNG = {
    2025: dict(CAN_WEST_NORTHEAST_ASIA=3,  CAN_WEST_CHINA=2,  CAN_WEST_SOUTHEAST_ASIA=1),
    2030: dict(CAN_WEST_NORTHEAST_ASIA=9,  CAN_WEST_CHINA=5,  CAN_WEST_SOUTHEAST_ASIA=4),
    2035: dict(CAN_WEST_NORTHEAST_ASIA=15, CAN_WEST_CHINA=9,  CAN_WEST_SOUTHEAST_ASIA=6),
    2040: dict(CAN_WEST_NORTHEAST_ASIA=21, CAN_WEST_CHINA=13, CAN_WEST_SOUTHEAST_ASIA=8),
    2045: dict(CAN_WEST_NORTHEAST_ASIA=26, CAN_WEST_CHINA=16, CAN_WEST_SOUTHEAST_ASIA=10),
}
# Sub-Saharan Africa LNG to Asia (Mozambique/Tanzania/Nigeria)
SUBSAH_ASIA = {
    2025: dict(SUBSAHARAN_CHINA=4,  SUBSAHARAN_SOUTH_ASIA=3,  SUBSAHARAN_NORTHEAST_ASIA=3),
    2030: dict(SUBSAHARAN_CHINA=12, SUBSAHARAN_SOUTH_ASIA=9,  SUBSAHARAN_NORTHEAST_ASIA=9),
    2035: dict(SUBSAHARAN_CHINA=20, SUBSAHARAN_SOUTH_ASIA=15, SUBSAHARAN_NORTHEAST_ASIA=15),
    2040: dict(SUBSAHARAN_CHINA=26, SUBSAHARAN_SOUTH_ASIA=20, SUBSAHARAN_NORTHEAST_ASIA=19),
    2045: dict(SUBSAHARAN_CHINA=32, SUBSAHARAN_SOUTH_ASIA=24, SUBSAHARAN_NORTHEAST_ASIA=24),
}
# Contracted US LNG to NE Asia (Japan + South Korea). Both hold long-term
# (20-yr) US offtake SPAs and were the 4th/5th-largest US LNG destinations in
# 2023 (~0.8 Bcf/d each, ~17 BCM combined; EIA). Imposed as a must-run floor so
# the baseline reproduces observed US->Asia trade, which a single-shot least-cost
# solve omits (US LNG loses the Asian spot cost race to Qatar/Australia but still
# ships there under contract). Floor only: more can flow if economic.
US_LNG_NEASIA_CONTRACT = {2025: 17, 2030: 25, 2035: 32, 2040: 40, 2045: 45}

# Russia Asian pivot: Power-of-Siberia pipeline to China, Arctic/Sakhalin LNG
# (must-run, contracted), and a declining residual EU LNG route.
RUSSIA_CHINA_CAP   = {2025: 55, 2030: 70, 2035: 85, 2040: 95, 2045: 100}
RUSSIA_NEASIA_LNG  = {2025: 20, 2030: 25, 2035: 30, 2040: 35, 2045: 40}
RUSSIA_EU_LNG      = {2025: 20, 2030: 10, 2035: 5,  2040: 0,  2045: 0}
# Central Asia -> China pipeline (realistic; keeps China importing LNG)
TURKM_CHINA_CAP    = {2025: 55, 2030: 60, 2035: 65, 2040: 70, 2045: 75}
# Iran: sanctioned export ceiling (held flat)
IRAN_EXPORT = dict(IRAN_CHINA=25, IRAN_SOUTH_ASIA=20, IRAN_SOUTHEAST_ASIA=0)

# US liquefaction build-out ceiling (BCM/yr) for the ENDOGENOUS US-LNG link.
# 2025 is pinned near observed/announced US LNG export capacity (~150 BCM, EIA)
# to keep the calibration baseline realistic. Later years rise to a generous but
# defensible ceiling reflecting the large under-construction + announced US LNG
# build-out, so that SPARE liquefaction capacity exists. That headroom is what
# lets the sovereignty counterfactual re-export Mexico's freed gas (the leakage
# channel): a flat/binding cap forces lng_ref == lng_sov and suppresses leakage
# artificially. The model still only builds UP TO these ceilings when economic.
US_LIQ_CAP = {2025: 150, 2030: 280, 2035: 400, 2040: 520, 2045: 640}

# Links set explicitly (do NOT scale with the generic SupplyGrowth factor).
PINNED_LINKS = {
    "RUSSIA_EUROPE", "US_GULF_MEXICO", "PERMIAN_MEXICO", "USA_US_LNG",
    "NORTH_AFRICA_LATIN_AMERICA", "SUBSAHARAN_LATIN_AMERICA",
    "RUSSIA_CHINA", "RUSSIA_NORTHEAST_ASIA", "RUSSIA_EUROPE_LNG",
    "TURKMENISTAN_CHINA",
    "IRAN_CHINA", "IRAN_SOUTH_ASIA", "IRAN_SOUTHEAST_ASIA",
} | set().union(*[set(d) for d in US_LNG_DEST.values()]) \
  | set().union(*[set(d) for d in CANADA_LNG.values()]) \
  | set().union(*[set(d) for d in SUBSAH_ASIA.values()])

PINNED_GENS = {"MEX_CONV", "MEX_SHALE"}


def apply_scenario(n, year, scenario=None, us_plateau=None):

    scenario = scenario or SCENARIO
    if us_plateau is None:
        us_plateau = US_PLATEAU
    scenarios = pd.read_csv("data/scenarios.csv")
    s = scenarios[scenarios["Year"] == year].iloc[0]
    g = float(s["SupplyGrowth"])

    # --- global supply-capacity growth (2025 = 1.0) ---
    # US producers are held at a PLATEAU (not grown) when us_plateau=True, so
    # US supply is constrained — the condition under which sovereignty leaks.
    for gen in n.generators.index:
        if gen in PINNED_GENS or gen.endswith("_slack") or gen.endswith("_coal"):
            continue
        if us_plateau and gen in US_PRODUCERS:
            continue
        n.generators.loc[gen, "p_nom"]     *= g
        n.generators.loc[gen, "p_nom_max"] *= g
    for link in n.links.index:
        if link in PINNED_LINKS:
            continue
        n.links.loc[link, "p_nom"] *= g

    # --- Russia -> Europe pipeline (EU phase-out) ---
    if "RUSSIA_EUROPE" in n.links.index:
        n.links.loc["RUSSIA_EUROPE", "p_nom"] = s["RussiaEU"]

    # --- Mexico sovereignty lever (the counterfactual) ---
    #   sovereignty: domestic shale ramps, US->Mexico pipeline phased to 0
    #   reference:   Mexico keeps importing US gas, no shale build-out
    if scenario == "reference":
        mex_shale_cap = REF_MEX_SHALE
        us_mexico_cap = REF_US_MEXICO
    else:  # sovereignty
        mex_shale_cap = s["MexicoShaleCap"]
        us_mexico_cap = s["USMexicoLimit"]

    if "US_GULF_MEXICO" in n.links.index:
        n.links.loc["US_GULF_MEXICO", "p_nom"] = us_mexico_cap
    if "PERMIAN_MEXICO" in n.links.index:
        n.links.loc["PERMIAN_MEXICO", "p_nom"] = 0

    if "MEX_CONV" in n.generators.index:
        n.generators.loc["MEX_CONV", "p_nom"]     = 40
        n.generators.loc["MEX_CONV", "p_nom_max"] = 40
    if "MEX_SHALE" in n.generators.index:
        n.generators.loc["MEX_SHALE", "p_nom"]     = mex_shale_cap
        n.generators.loc["MEX_SHALE", "p_nom_max"] = mex_shale_cap

    # --- US LNG export capacity ---
    if US_LNG_ENDOGENOUS:
        # USA_US_LNG is extendable (built endogenously in build_network), but
        # cap its build-out to a realistic per-year liquefaction ceiling so the
        # base year reproduces observed US LNG (~120-150 BCM) rather than an
        # unconstrained ~415 BCM. Destination/shipping routes are kept ample so
        # liquefaction (not shipping) remains the binding constraint.
        if "USA_US_LNG" in n.links.index:
            n.links.loc["USA_US_LNG", "p_nom_max"] = US_LIQ_CAP[year]
        for nm in US_LNG_DEST[year]:
            if nm in n.links.index:
                n.links.loc[nm, "p_nom"] = 500
    else:
        if "USA_US_LNG" in n.links.index:
            n.links.loc["USA_US_LNG", "p_nom"]    = s["USLNGCap"]
            n.links.loc["USA_US_LNG", "p_min_pu"] = US_LNG_UTIL
        for nm, cap in US_LNG_DEST[year].items():
            if nm in n.links.index:
                n.links.loc[nm, "p_nom"] = cap

    # --- Contracted US LNG floor to NE Asia (Japan + Korea long-term SPAs) ---
    # Applied in both configurations; p_min_pu set from the route's current p_nom
    # so at least the contracted volume must flow, while leaving headroom above.
    if "US_LNG_NORTHEAST_ASIA" in n.links.index:
        pnom = n.links.loc["US_LNG_NORTHEAST_ASIA", "p_nom"]
        if pnom and pnom > 0:
            n.links.loc["US_LNG_NORTHEAST_ASIA", "p_min_pu"] = min(
                1.0, US_LNG_NEASIA_CONTRACT[year] / pnom)

    # --- Canada west-coast LNG to Asia ---
    for nm, cap in CANADA_LNG[year].items():
        if nm in n.links.index:
            n.links.loc[nm, "p_nom"] = cap

    # --- Sub-Saharan Africa LNG to Asia ---
    for nm, cap in SUBSAH_ASIA[year].items():
        if nm in n.links.index:
            n.links.loc[nm, "p_nom"] = cap

    # --- Russia: Power of Siberia pipeline + Arctic LNG (must-run) + EU LNG ---
    if "RUSSIA_CHINA" in n.links.index:
        n.links.loc["RUSSIA_CHINA", "p_nom"] = RUSSIA_CHINA_CAP[year]
    if "RUSSIA_NORTHEAST_ASIA" in n.links.index:
        n.links.loc["RUSSIA_NORTHEAST_ASIA", "p_nom"]    = RUSSIA_NEASIA_LNG[year]
        n.links.loc["RUSSIA_NORTHEAST_ASIA", "p_min_pu"] = 1.0   # contracted Sakhalin/Arctic
    if "RUSSIA_EUROPE_LNG" in n.links.index:
        n.links.loc["RUSSIA_EUROPE_LNG", "p_nom"] = RUSSIA_EU_LNG[year]

    # --- Central Asia -> China pipeline (realistic level) ---
    if "TURKMENISTAN_CHINA" in n.links.index:
        n.links.loc["TURKMENISTAN_CHINA", "p_nom"] = TURKM_CHINA_CAP[year]

    # --- Iran: sanctioned export ceiling ---
    for nm, cap in IRAN_EXPORT.items():
        if nm in n.links.index:
            n.links.loc[nm, "p_nom"] = cap

    return n

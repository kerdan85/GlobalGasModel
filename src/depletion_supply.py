# ==========================================================
# depletion_supply.py   (Tier 1a)
#
# Replaces the flat US producer block + binary plateau with a
# RISING marginal-cost step supply curve, so US supply tightness
# -- and therefore Energy Sovereignty Leakage -- emerges from the
# resource base rather than being imposed by hand.
#
# Each US producer node is given several generator "tranches":
#   tranche 0 = current capacity at ~Henry Hub cost,
#   higher tranches = incremental resource at rising breakeven.
# As US gas is pulled into export markets, dispatch climbs the
# curve and the marginal cost of the next US molecule rises -- an
# endogenous plateau. The US_SUPPLY_SLOPE multiplier scales the
# increment above tranche 0 (shallow curve ~ spare capacity;
# steep curve ~ hard plateau), replacing the old on/off switch.
#
# Pipeline:  build_network -> apply_scenario -> add_us_supply_curve
# build_network skips the US producers when USE_DEPLETION_CURVE,
# so this module is the sole US supply representation.
# ==========================================================

import os
import pandas as pd

from src.config import US_PRODUCERS, US_GAS_COST

_TECH = {"US_GULF": "CONVENTIONAL", "PERMIAN": "SHALE", "APPALACHIA": "SHALE_MATURE"}
_CSV = "data/us_supply_curve.csv"


def add_us_supply_curve(n, year, slope=1.0, cap_scale=1.0, market_bus="USA"):
    """Add US production as rising-cost tranches at each producer node.

    slope:     multiplier on the cost increment above tranche 0.
    cap_scale: multiplier on tranche CAPACITIES -- the US spare
               export-capacity / tightness knob (the scenario axis
               us_supply_scale; <1 tightens, >1 loosens).
    Returns the network (modified in place).
    """
    if not os.path.exists(_CSV):
        raise FileNotFoundError(f"{_CSV} not found (needed for depletion curve).")
    curve = pd.read_csv(_CSV, comment="#")

    for node in curve["Node"].unique():
        # remove any pre-existing single generator at this node
        if node in n.generators.index:
            n.remove("Generator", node)

        sub = curve[curve["Node"] == node].sort_values("Tranche")
        base_cost = float(sub.iloc[0]["MarginalCost"])

        for _, row in sub.iterrows():
            cost = float(row["MarginalCost"])
            # scale only the increment above tranche 0 by the slope
            cost = base_cost + slope * (cost - base_cost)
            name = f"{node}_t{int(row['Tranche'])}"
            n.add(
                "Generator", name,
                bus=node, carrier="gas",
                p_nom=float(row["Capacity"]) * cap_scale,
                p_nom_extendable=False,
                marginal_cost=cost,
            )
            n.generators.loc[name, "node_type"]  = "us_supply"
            n.generators.loc[name, "tech"]       = _TECH.get(node, "SHALE")
            n.generators.loc[name, "market_bus"] = market_bus
            n.generators.loc[name, "co2_factor"] = 56.0
            n.generators.loc[name, "ch4_leakage"] = 2.5
            n.generators.loc[name, "lng_penalty"] = 0.0

        # ensure the node can deliver to its market bus
        link = f"{node}_{market_bus}"
        if node != market_bus and link not in n.links.index:
            n.add("Link", link, bus0=node, bus1=market_bus, carrier="gas",
                  p_nom=1e6, p_nom_extendable=False, marginal_cost=0.1, efficiency=1)

    return n


def us_supply_is_active():
    """True if the depletion curve should be used (config flag)."""
    from src.config import USE_DEPLETION_CURVE
    return bool(USE_DEPLETION_CURVE)

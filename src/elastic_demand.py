# ==========================================================
# elastic_demand.py   (Tier 1b)
#
# Generalises the coal-switch backstop into a price-elastic
# demand curve for every region. A fraction of each region's
# base gas demand is allowed to drop out as the delivered price
# rises (substitution / demand destruction), approximated by a
# stack of backstop generators at increasing "choke" prices.
#
# Mechanics (LP-friendly, same idea as the coal backstop):
#   For a region with base demand D and reference price P0, the
#   elastic portion f*D is split into DEMAND_STEPS steps. Step k
#   gets a backstop generator priced at a choke price p_k > P0.
#   If delivered gas is cheaper than p_k the step is served by
#   real gas; if gas is dearer, the backstop serves it -- i.e.
#   that gas demand is NOT met by gas (it is substituted away).
#   The result is a downward-sloping, piecewise-linear demand
#   curve consistent with the region's price elasticity.
#
# This lets us test whether ~100% reabsorption (ESL) survives
# realistic demand response, instead of assuming inelastic demand.
#
# Backstop generators are tagged node_type="demand_curve" so the
# ESL diagnostics exclude them from "gas produced".
# ==========================================================

import os
import pandas as pd

from src.config import (DEMAND_ELASTICITY, DEMAND_STEPS, DEMAND_REF_PRICE)

_CSV = "data/demand_elasticity.csv"


def _params(region, table):
    """Return (elasticity, ref_price, max_fraction) for a region."""
    if table is not None and region in table.index:
        r = table.loc[region]
        return float(r["Elasticity"]), float(r["RefPrice"]), float(r["MaxElasticFraction"])
    return DEMAND_ELASTICITY, DEMAND_REF_PRICE, 0.30


def add_elastic_demand(n, year, coal_multiplier=1.0):
    """Attach a piecewise-linear elastic-demand curve to each region.

    Operates on the fixed Loads already in the network (base demand).
    coal_multiplier scales any existing coal-switch loads/backstops
    (used by the scenario matrix's 'coal_demand' axis).
    """
    table = None
    if os.path.exists(_CSV):
        table = pd.read_csv(_CSV, comment="#").set_index("Region")

    # optional scaling of the coal-switch channel (scenario axis). Handles the
    # spread sub-tranches "{reg}_coalswitch{k}" / backstop "{reg}_coal{k}".
    if coal_multiplier != 1.0:
        for ld in list(n.loads.index):
            if "_coalswitch" in ld:
                n.loads.loc[ld, "p_set"] *= coal_multiplier
                gen = ld.replace("coalswitch", "coal")   # {reg}_coalswitch{k} -> {reg}_coal{k}
                if gen in n.generators.index:
                    n.generators.loc[gen, "p_nom"] *= coal_multiplier

    # base (region) loads only: names equal to a bus, no suffix
    base_loads = [ld for ld in n.loads.index
                  if ld in n.buses.index and "_coalswitch" not in ld]

    for reg in base_loads:
        D = float(n.loads.loc[reg, "p_set"])
        if D <= 0:
            continue
        e, p0, fmax = _params(reg, table)
        e = abs(e)
        if e == 0 or fmax <= 0:
            continue

        # price span over which the elastic fraction is exhausted.
        # linear demand: q(p) = D*(1 - e*(p/p0 - 1)); the elastic
        # fraction fmax is gone when p reaches p0*(1 + fmax/e).
        p_top = p0 * (1.0 + fmax / e)
        step_q = (fmax * D) / DEMAND_STEPS
        for k in range(1, DEMAND_STEPS + 1):
            # choke price at the midpoint of step k
            frac = (k - 0.5) / DEMAND_STEPS
            p_k = p0 + frac * (p_top - p0)
            name = f"{reg}_dem{k}"
            if name in n.generators.index:
                n.remove("Generator", name)
            n.add("Generator", name, bus=reg, carrier="gas",
                  p_nom=step_q, marginal_cost=p_k)
            n.generators.loc[name, "node_type"] = "demand_curve"
            n.generators.loc[name, "tech"] = "SUBSTITUTE"

    return n


def elastic_demand_is_active():
    from src.config import ELASTIC_DEMAND
    return bool(ELASTIC_DEMAND)

# ==========================================================
# build_network.py
# Global Gas Model
# ==========================================================

import os
import pypsa
import pandas as pd

from src.config import (US_GAS_COST, US_PRODUCERS, COAL_PARITY, COAL_PARITY_SPREAD,
                        US_LNG_ENDOGENOUS, US_LNG_CAPITAL,
                        USE_DEPLETION_CURVE)


def build_network(year, coalswitch_override=None):
    """Build the 19-region gas-trade network for `year`.

    coalswitch_override : None (default) or dict {region: switched_volume_BCM}.
        None -> least-cost merit order: the coal-to-gas switchable volume is
                split into COAL_PARITY_SPREAD sub-tranches and the LP decides
                which switch (the paper's baseline representation).
        dict -> logit / smooth-substitution mode: the given switched volume is
                committed to gas (a fixed load on the region bus) and the
                unswitched remainder stays on coal (isolated bus + coal
                backstop). The switching decision is made OUTSIDE the LP by the
                fixed-point in src/logit_resolve.py. The coal-backstop
                generation still equals the unswitched volume, so diag() and the
                ESL/emissions ledger in experiment_core are unchanged.
    """

    # ------------------------------------------------------
    # Create network
    # ------------------------------------------------------
    n = pypsa.Network()
    n.set_snapshots([year])

    # ------------------------------------------------------
    # Read data
    # ------------------------------------------------------
    nodes      = pd.read_csv("data/nodes.csv")
    producers  = pd.read_csv("data/producers.csv")
    technology = pd.read_csv("data/technology.csv")
    demand     = pd.read_csv("data/demand.csv")
    links      = pd.read_csv("data/links.csv")
    slack      = pd.read_csv("data/slack.csv")

    # technology attributes (marginal/capital cost, extendable, emissions)
    producers = producers.merge(technology, on="Technology", how="left")

    missing = producers[producers["Extendable"].isna()]
    if len(missing):
        print("WARNING: producers with no matching technology row:")
        print(missing[["Node", "Technology"]])

    # ------------------------------------------------------
    # Carrier
    # ------------------------------------------------------
    n.add("Carrier", "gas")

    # ------------------------------------------------------
    # Buses
    # ------------------------------------------------------
    for _, row in nodes.iterrows():
        n.add("Bus", row["Node"], x=row["lon"], y=row["lat"], carrier="gas")

    # ------------------------------------------------------
    # Producers (capacity is an upper bound; SHALE is extendable)
    # ------------------------------------------------------
    for _, row in producers.iterrows():

        # Under the depletion curve, US producers are added later as
        # rising-cost tranches (src/depletion_supply.py), so skip them here.
        if USE_DEPLETION_CURVE and row["Node"] in US_PRODUCERS:
            continue

        extendable = int(row["Extendable"]) == 1

        # US gas carries its real Henry Hub cost advantage (cheap swing supply)
        mc = US_GAS_COST if row["Node"] in US_PRODUCERS else row["MarginalCost"]

        n.add(
            "Generator",
            row["Node"],
            bus=row["Node"],
            carrier="gas",
            p_nom=row["Capacity"],
            p_nom_extendable=extendable,
            p_nom_min=0,
            p_nom_max=row["Capacity"],
            marginal_cost=mc,
            capital_cost=row["CapitalCost"],
        )

        n.generators.loc[row["Node"], "node_type"]   = "producer"
        n.generators.loc[row["Node"], "tech"]         = row["Technology"]
        n.generators.loc[row["Node"], "market_bus"]   = row["MarketBus"]
        n.generators.loc[row["Node"], "co2_factor"]   = row["CO2Factor"]
        n.generators.loc[row["Node"], "ch4_leakage"]  = row["CH4Leakage"]
        n.generators.loc[row["Node"], "lng_penalty"]  = row["LNGEnergyPenalty"]

    # ------------------------------------------------------
    # Slack generators (high-cost backstop so every bus balances)
    # ------------------------------------------------------
    for _, row in slack.iterrows():
        n.add(
            "Generator",
            f"{row['Node']}_slack",
            bus=row["Node"],
            carrier="gas",
            p_nom=row["Capacity"],
            marginal_cost=row["Cost"],
        )

    # ------------------------------------------------------
    # Demand
    # ------------------------------------------------------
    year_column = str(year)
    for _, row in demand.iterrows():
        n.add(
            "Load",
            row["Node"],
            bus=row["Node"],
            carrier="gas",
            p_set=row[year_column],
        )

    # ------------------------------------------------------
    # Coal-to-gas switching demand (price-elastic via a coal backstop).
    # Coal-heavy importers can absorb extra gas ONLY if delivered gas
    # undercuts a coal-parity price; otherwise the demand stays on coal.
    # This is the channel through which freed US gas leaks (displaces coal).
    # ------------------------------------------------------
    coal_path = "data/coal_switch.csv"
    if os.path.exists(coal_path):
        coal = pd.read_csv(coal_path)
        spread = COAL_PARITY_SPREAD or [0.0]
        nsub = len(spread)
        for _, row in coal.iterrows():
            reg = row["Region"]
            dc = float(row[year_column]) if year_column in coal.columns else 0.0
            if reg not in n.buses.index or dc <= 0:
                continue

            if coalswitch_override is None:
                # ---- LEAST-COST (baseline): heterogeneous fleet, LP decides ----
                # Split the switchable volume into sub-tranches at a spread of
                # parity prices, so coal->gas switching responds gradually to the
                # delivered gas price (smooth leakage, not an all-or-nothing step).
                sub = dc / nsub
                for k, off in enumerate(spread):
                    n.add("Load", f"{reg}_coalswitch{k}", bus=reg,
                          carrier="gas", p_set=sub)
                    g = f"{reg}_coal{k}"
                    n.add("Generator", g, bus=reg, carrier="gas",
                          p_nom=sub, marginal_cost=COAL_PARITY + off)
                    n.generators.loc[g, "node_type"] = "coal_backstop"
                    n.generators.loc[g, "tech"] = "COAL"
            else:
                # ---- LOGIT (smooth substitution): switching set outside the LP ----
                # `sw` is committed to gas (fixed load on the region bus); the
                # unswitched remainder stays on coal on an ISOLATED bus so the
                # split holds regardless of the delivered price. Coal-backstop
                # generation == unswitched volume, so downstream ESL/emissions
                # diagnostics (diag(), run_counterfactual) are unchanged.
                sw = float(coalswitch_override.get(reg, 0.0))
                sw = max(0.0, min(sw, dc))
                unsw = dc - sw
                if sw > 0:
                    n.add("Load", f"{reg}_coalswitchL", bus=reg,
                          carrier="gas", p_set=sw)
                stay_bus = f"{reg}_coalstay"
                n.add("Bus", stay_bus, carrier="gas")
                n.add("Load", f"{reg}_coalstayL", bus=stay_bus,
                      carrier="gas", p_set=unsw)
                g = f"{reg}_coal0"
                n.add("Generator", g, bus=stay_bus, carrier="gas",
                      p_nom=max(unsw, 1e-3), marginal_cost=COAL_PARITY)
                n.generators.loc[g, "node_type"] = "coal_backstop"
                n.generators.loc[g, "tech"] = "COAL"

    # ------------------------------------------------------
    # Links (inter-regional pipelines + LNG routes)
    # ------------------------------------------------------
    for _, row in links.iterrows():
        # US liquefaction (USA -> US_LNG hub) is an ENDOGENOUS investment:
        # the model builds export capacity (with a capital cost) when it pays.
        endo = US_LNG_ENDOGENOUS and row["Name"] == "USA_US_LNG"
        n.add(
            "Link",
            row["Name"],
            bus0=row["From"],
            bus1=row["To"],
            carrier="gas",
            p_nom=row["Capacity"],
            p_nom_extendable=endo,
            p_nom_min=0,
            p_nom_max=(1e4 if endo else row["Capacity"]),
            marginal_cost=row["Cost"],
            capital_cost=(US_LNG_CAPITAL if endo else 0),
            efficiency=row["Efficiency"],
        )

    # ------------------------------------------------------
    # Domestic delivery links (TOPOLOGY FIX)
    # Every producer must be able to reach its home market bus.
    # If links.csv doesn't already connect producer -> MarketBus,
    # add a cheap high-capacity delivery link. This is what was
    # missing for MIDDLE_EAST/TURKMENISTAN/AZERBAIJAN (their home
    # demand previously fell back to slack) and supports the new
    # domestic producers (CHINA_DOM, SOUTH_ASIA_DOM, SEA_DOM).
    # ------------------------------------------------------
    existing = set(zip(links["From"], links["To"]))
    for _, row in producers.iterrows():
        node = row["Node"]
        mkt  = row["MarketBus"]
        if node != mkt and (node, mkt) not in existing:
            n.add(
                "Link",
                f"{node}_{mkt}",
                bus0=node,
                bus1=mkt,
                carrier="gas",
                p_nom=1e6,
                p_nom_extendable=False,
                marginal_cost=0.1,
                efficiency=1,
            )

    return n
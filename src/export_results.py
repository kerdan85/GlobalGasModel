# ==========================================================
# export_results.py
# Export model outputs
# ==========================================================

import os
import pandas as pd
from src.config import MARKETS


def _region_map(n):
    """Producer nodes belonging to each market bus, from MarketBus."""
    rm = {}
    if "market_bus" in n.generators.columns:
        for gen, mkt in n.generators["market_bus"].dropna().items():
            rm.setdefault(mkt, []).append(gen)
    return rm


def _region_buses(n):
    """Set of buses 'owned' by each market region.

    A region owns its own demand bus plus every producer bus whose
    generators are assigned to it via market_bus. This is bus-based
    (not generator-name based) so it stays correct when a single bus
    carries several generators -- e.g. the US depletion-curve tranches
    (US_GULF_t0, US_GULF_t1, ...) all sitting on bus US_GULF, or the
    elastic-demand / coal backstops sitting on a region bus.
    """
    from src.config import MARKETS
    rb = {r: {r} for r in MARKETS}
    if "market_bus" in n.generators.columns:
        for g in n.generators.index:
            mkt = n.generators.loc[g, "market_bus"]
            if pd.notna(mkt):
                rb.setdefault(mkt, {mkt}).add(n.generators.loc[g, "bus"])
    return rb


# Generator node_type buckets used by the regional balance.
_REAL_TYPES = ("producer", "us_supply")          # actual gas produced
_BACKSTOP_TYPES = ("demand_curve", "coal_backstop")  # demand substituted away


def export_results(n, year):

    os.makedirs("outputs", exist_ok=True)

    # gen-level production (exclude slack from "production")
    gen_prod = n.generators_t.p.sum()                       # per generator
    is_slack = n.generators.index.str.endswith("_slack")
    prod_only = gen_prod[~is_slack]
    slack_prod = gen_prod[is_slack]

    REGION_MAP = _region_map(n)

    # =====================================================
    # GENERATOR PRODUCTION
    # =====================================================
    gen_prod.to_csv(f"outputs/production_{year}.csv", header=["Production"])

    prod = pd.DataFrame({
        "Node": prod_only.index,
        "Production": prod_only.values,
        "Technology": n.generators.loc[prod_only.index, "tech"].values,
        "Bus": n.generators.loc[prod_only.index, "bus"].values,
    })
    prod["Year"] = year
    prod.to_csv(f"outputs/production_nodes_{year}.csv", index=False)

    # =====================================================
    # INTERNAL CONSUMPTION
    # =====================================================
    consumption = n.loads_t.p.sum()
    consumption.to_csv(f"outputs/consumption_{year}.csv", header=["Consumption"])

    # =====================================================
    # TRADE FLOWS (per link)
    # =====================================================
    flows = n.links_t.p0.sum()
    flows.to_csv(f"outputs/trade_{year}.csv", header=["Flow"])

    # =====================================================
    # REGIONAL BALANCE  (bus-based; closes exactly)
    #   Production + Imports + Slack + Backstop - Exports - Demand = 0
    #
    # Classification is done on BUSES, not generator names, so it is
    # correct when a bus carries multiple generators (US tranches) and
    # when demand/coal backstops sit on a region bus. A link is an
    # import/export only if it crosses the region's bus boundary;
    # intra-region delivery links (producer bus -> demand bus) net out.
    # =====================================================
    REGION_BUSES = _region_buses(n)
    node_type = n.generators["node_type"] if "node_type" in n.generators.columns else None

    def _gen_out(g):
        return n.generators_t.p[g].sum() if g in n.generators_t.p.columns else 0.0

    def _ntype(g):
        if node_type is None:
            return None
        val = node_type.get(g)
        return val if pd.notna(val) else None

    balances = []
    for region in MARKETS:
        buses = REGION_BUSES.get(region, {region})

        # generators physically located on this region's buses
        gens_here = [g for g in n.generators.index
                     if n.generators.loc[g, "bus"] in buses]

        production = sum(_gen_out(g) for g in gens_here
                         if _ntype(g) in _REAL_TYPES)
        backstop   = sum(_gen_out(g) for g in gens_here
                         if _ntype(g) in _BACKSTOP_TYPES)
        slack      = sum(_gen_out(g) for g in gens_here
                         if g.endswith("_slack"))

        imports = 0.0
        exports = 0.0
        for link in n.links.index:
            origin = n.links.loc[link, "bus0"]
            dest   = n.links.loc[link, "bus1"]
            flow   = n.links_t.p0[link].sum()
            o_in = origin in buses
            d_in = dest in buses
            if d_in and not o_in:
                imports += flow
            elif o_in and not d_in:
                exports += flow

        # all loads attached to this region's buses (base demand +
        # any coal-switch tranches living on those buses)
        demand = sum(n.loads_t.p[ld].sum() for ld in n.loads.index
                     if ld in n.loads_t.p.columns
                     and n.loads.loc[ld, "bus"] in buses)

        balances.append({
            "Year": year,
            "Region": region,
            "Production": production,
            "Imports": imports,
            "Slack": slack,
            "Backstop": backstop,
            "Demand": demand,
            "Exports": exports,
            "NetExports": exports - imports,
            "Residual": production + imports + slack + backstop - exports - demand,
        })

    balances = pd.DataFrame(balances)
    balances.to_csv(f"outputs/regional_balance_{year}.csv", index=False)

    # =====================================================
    # INSTALLED CAPACITY
    # =====================================================
    n.generators.p_nom_opt.to_csv(f"outputs/capacity_{year}.csv", header=["Capacity"])

    # =====================================================
    # PRODUCTION BY TECHNOLOGY  (fixed: per-generator production)
    # =====================================================
    tech = pd.DataFrame({
        "Technology": n.generators.loc[prod_only.index, "tech"].values,
        "Production": prod_only.values,
    }).groupby("Technology").sum()
    tech.to_csv(f"outputs/technology_mix_{year}.csv")

    # =====================================================
    # CO2 + METHANE
    # =====================================================
    co2 = (prod_only * n.generators.loc[prod_only.index, "co2_factor"]).rename("CO2")
    co2.to_csv(f"outputs/co2_{year}.csv", header=["CO2"])
    ch4 = (prod_only * n.generators.loc[prod_only.index, "ch4_leakage"]).rename("CH4")
    ch4.to_csv(f"outputs/ch4_{year}.csv", header=["CH4"])

    # =====================================================
    # MEXICO SUPPLY MIX
    # =====================================================
    imports_mx = n.links_t.p0["US_GULF_MEXICO"].sum() if "US_GULF_MEXICO" in n.links.index else 0.0
    if "PERMIAN_MEXICO" in n.links.index:
        imports_mx += n.links_t.p0["PERMIAN_MEXICO"].sum()
    conventional = n.generators_t.p["MEX_CONV"].sum() if "MEX_CONV" in n.generators_t.p.columns else 0.0
    shale = n.generators_t.p["MEX_SHALE"].sum() if "MEX_SHALE" in n.generators_t.p.columns else 0.0

    mexico = pd.DataFrame({"Year": [year], "Imports": [imports_mx],
                           "Conventional": [conventional], "Shale": [shale]})
    if os.path.exists("outputs/mexico_supply_mix.csv"):
        mexico = pd.concat([pd.read_csv("outputs/mexico_supply_mix.csv"), mexico], ignore_index=True)
    mexico.to_csv("outputs/mexico_supply_mix.csv", index=False)
    pd.DataFrame({"Year": [year], "Imports": [imports_mx], "Conventional": [conventional],
                  "Shale": [shale]}).to_csv(f"outputs/mexico_supply_mix_{year}.csv", index=False)

    # =====================================================
    # SUMMARY
    # =====================================================
    summary = pd.DataFrame({
        "Year": [year],
        "Total Production": [prod_only.sum()],
        "Total Slack": [slack_prod.sum()],
        "Total CO2": [co2.sum()],
        "Total CH4": [ch4.sum()],
    })
    summary.to_csv(f"outputs/summary_{year}.csv", index=False)

    # =====================================================
    # MASTER FILES (appended across years)
    # =====================================================
    trade_master = pd.DataFrame([{
        "Year": year, "Route": link,
        "From": n.links.loc[link, "bus0"], "To": n.links.loc[link, "bus1"],
        "Flow": n.links_t.p0[link].sum(),
    } for link in n.links.index])
    if os.path.exists("outputs/trade_flows.csv"):
        trade_master = pd.concat([pd.read_csv("outputs/trade_flows.csv"), trade_master], ignore_index=True)
    trade_master.to_csv("outputs/trade_flows.csv", index=False)

    tech_export = tech.reset_index()
    tech_export["Year"] = year
    if os.path.exists("outputs/technology_mix.csv"):
        tech_export = pd.concat([pd.read_csv("outputs/technology_mix.csv"), tech_export], ignore_index=True)
    tech_export.to_csv("outputs/technology_mix.csv", index=False)

    cons = consumption.reset_index()
    cons.columns = ["Region", "Consumption"]
    cons["Year"] = year
    if os.path.exists("outputs/consumption.csv"):
        cons = pd.concat([pd.read_csv("outputs/consumption.csv"), cons], ignore_index=True)
    cons.to_csv("outputs/consumption.csv", index=False)

    if os.path.exists("outputs/regional_balance.csv"):
        balances = pd.concat([pd.read_csv("outputs/regional_balance.csv"), balances], ignore_index=True)
    balances.to_csv("outputs/regional_balance.csv", index=False)

    return

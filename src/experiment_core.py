# ==========================================================
# experiment_core.py
#
# Central, parameterised "solve one case / run one counterfactual"
# used by the scenario matrix and the uncertainty modules. It wires
# together the Tier-1 features (depletion curve, elastic demand,
# capacity persistence) and computes the ESL ratio and the marginal
# emissions ledger for an arbitrary parameter set.
#
# A parameter set `p` is a dict; any key absent falls back to config:
#   mex_shale_cost, us_supply_slope, coal_demand, us_gas_cost,
#   coal_parity, us_lng_capital, methane_rate, lng_penalty
# ==========================================================

import pandas as pd

from src import config
from src.build_network import build_network
from src.apply_scenario import apply_scenario
from src.solve import solve
from src.depletion_supply import add_us_supply_curve, us_supply_is_active
from src.elastic_demand import add_elastic_demand, elastic_demand_is_active
from src.liquefaction_supply import (add_liquefaction_curve, liq_curve_is_active,
                                     us_liquefaction_flow)
from src.persistence import apply_capacity_floor, record_capacity

_US_BASE0 = 2.3   # nominal tranche-0 cost in us_supply_curve.csv


def _get(p, key):
    return p.get(key, getattr(config, key.upper(), None))


def gas_lca(gwp_key, methane_rate, lng_penalty=None):
    """Lifecycle intensity of the leaked molecule (US shale gas as LNG),
    gCO2e/MJ, ecoinvent-calibrated: a methane-independent part (combustion +
    upstream CO2 + LNG chain) plus a per-% upstream-methane term. The
    lng_penalty arg is retained for signature compatibility but unused."""
    return config.GAS_NONMETHANE[gwp_key] + config.GAS_METHANE_PER_PCT[gwp_key] * methane_rate


def diag(n):
    """gas produced, coal displaced-channel served, US->Mexico flow."""
    gp = n.generators_t.p.sum()
    nt = n.generators["node_type"] if "node_type" in n.generators else None
    gas = coal = 0.0
    for nm in gp.index:
        t = (nt.get(nm) if nt is not None else None)
        if t in ("producer", "us_supply"):
            gas += float(gp[nm])
        elif t == "coal_backstop":
            coal += float(gp[nm])
    # Mexican demand served by SUBSTITUTE backstops (i.e. demand
    # destroyed when domestic shale is dear). Used to isolate true
    # leakage from Mexico's own demand response.
    mex_sub = 0.0
    for nm in gp.index:
        if nm.startswith("MEXICO_dem"):
            mex_sub += float(gp[nm])
    us_mex = 0.0
    for l in ("US_GULF_MEXICO", "PERMIAN_MEXICO"):
        if l in n.links.index:
            us_mex += float(n.links_t.p0[l].sum())
    us_lng = us_liquefaction_flow(n)
    return dict(gas=gas, coal=coal, us_mex=us_mex, mex_sub=mex_sub, us_lng=us_lng)


def solve_case(year, scenario, p, built, coalswitch_override=None):
    n = build_network(year, coalswitch_override=coalswitch_override)
    n = apply_scenario(n, year, scenario=scenario)

    # US liquefaction as a rising marginal-cost supply curve: replaces the
    # single hard-capped USA->US_LNG link so the sovereignty case can expand
    # exports smoothly and partially over the reference (stable leakage)
    # instead of the bimodal 0%/80% a hard cap produces.
    if liq_curve_is_active():
        add_liquefaction_curve(n, year)

    # Reliability / security premium: importers' willingness to pay extra for
    # reliable US LNG versus geopolitically-exposed supply (Russia, Iran, Gulf).
    # Applied as a delivered-cost advantage on US LNG export routes, so freed US
    # gas is re-absorbed abroad even when pure economics would leave it at the
    # coal-parity margin -- the security-driven leakage channel. At 0 -> pure
    # least cost (leakage ~0). Sweepable via p["reliability_premium"].
    prem = p.get("reliability_premium", getattr(config, "RELIABILITY_PREMIUM", 0.0))
    if prem:
        for l in n.links.index:
            if n.links.loc[l, "bus0"] == "US_LNG":
                n.links.loc[l, "marginal_cost"] = n.links.loc[l, "marginal_cost"] - prem

    # depletion-curve US supply (with slope + optional cost shift)
    if us_supply_is_active():
        add_us_supply_curve(n, year,
                            slope=_get(p, "us_supply_slope") or 1.0,
                            cap_scale=p.get("us_supply_scale", 1.0))
        ug = p.get("us_gas_cost")
        if ug is not None:
            for nm in n.generators.index:
                if n.generators.loc[nm].get("node_type") == "us_supply":
                    n.generators.loc[nm, "marginal_cost"] += (ug - _US_BASE0)

    # elastic demand (and coal-demand multiplier)
    if elastic_demand_is_active():
        add_elastic_demand(n, year, coal_multiplier=p.get("coal_demand", 1.0))

    # parameter overrides that act on the LP
    if "mex_shale_cost" in p and "MEX_SHALE" in n.generators.index:
        n.generators.loc["MEX_SHALE", "marginal_cost"] = p["mex_shale_cost"]
    if "coal_parity" in p:
        # Shift the whole coal-parity SPREAD by the delta (preserves the
        # heterogeneous-fleet tranches "{reg}_coal{k}"). Raising coal parity
        # represents a carbon price on coal -> gas beats coal more easily ->
        # more coal-to-gas switching and more leakage.
        delta = float(p["coal_parity"]) - config.COAL_PARITY
        nt = n.generators["node_type"] if "node_type" in n.generators.columns else None
        if nt is not None and delta:
            for nm in n.generators.index:
                if nt.get(nm) == "coal_backstop":
                    n.generators.loc[nm, "marginal_cost"] += delta
    if p.get("us_lng_capital") is not None and "USA_US_LNG" in n.links.index:
        if bool(n.links.loc["USA_US_LNG", "p_nom_extendable"]):
            n.links.loc["USA_US_LNG", "capital_cost"] = p["us_lng_capital"]

    # LIFECYCLE-COMPLETE carbon price: charge the GAS that would be leaked for
    # its full lifecycle CO2e (upstream methane + LNG chain + combustion), so
    # the carbon price is symmetric across fuels rather than falling on coal
    # alone. gas_carbon_charge is in $/MMBtu-equivalent and is added to the
    # marginal cost of real gas production (producer + US-supply tranches).
    gcc = p.get("gas_carbon_charge", 0.0)
    if gcc:
        ntg = n.generators["node_type"] if "node_type" in n.generators.columns else None
        if ntg is not None:
            for nm in n.generators.index:
                if ntg.get(nm) in ("producer", "us_supply"):
                    n.generators.loc[nm, "marginal_cost"] += gcc

    # Strict convexity: a per-generator quadratic cost (slope / p_nom) gives each
    # supplier a gently rising marginal cost, making the objective strictly
    # convex so the optimum is UNIQUE and varies SMOOTHLY with the reliability
    # premium -- the cure for the system-wide LP degeneracy that kept ESL
    # bimodal. Needs PyPSA marginal_cost_quadratic + a QP solver (Gurobi).
    qslope = getattr(config, "QUADRATIC_SLOPE", 0.0)
    if qslope:
        coef = []
        for g in n.generators.index:
            pn = float(n.generators.loc[g, "p_nom"])
            coef.append(0.0 if (g.endswith("_slack") or pn <= 0) else qslope / pn)
        n.generators["marginal_cost_quadratic"] = coef

    if config.CAPACITY_PERSISTENCE:
        apply_capacity_floor(n, built)
    n = solve(n)
    built = record_capacity(n, built) if config.CAPACITY_PERSISTENCE else built
    return n, built


def run_counterfactual(p=None, years=None):
    """Reference vs sovereignty over all years; returns a tidy DataFrame."""
    p = dict(p or {})
    years = years or config.YEARS
    mrate = p.get("methane_rate", config.US_METHANE_RATE)
    lpen = p.get("lng_penalty", config.LNG_EMIS_PENALTY)

    built_ref, built_sov = {}, {}
    rows = []
    for year in years:
        ref, built_ref = solve_case(year, "reference", p, built_ref)
        sov, built_sov = solve_case(year, "sovereignty", p, built_sov)
        dr, ds = diag(ref), diag(sov)
        disp = dr["us_mex"] - ds["us_mex"]
        # raw change in global gas produced (includes Mexico's own
        # demand response, which is NOT leakage)
        d_gas_raw = ds["gas"] - dr["gas"]
        # Mexican demand destroyed when domestic shale is dear: add it
        # back so ESL isolates reabsorption OUTSIDE Mexico (true leakage).
        mex_loss = ds["mex_sub"] - dr["mex_sub"]
        leak = d_gas_raw + mex_loss
        d_coal = dr["coal"] - ds["coal"]
        esl = (leak / disp * 100.0) if disp > 1e-6 else 0.0
        esl_raw = (d_gas_raw / disp * 100.0) if disp > 1e-6 else 0.0
        # emissions ledger uses the leaked (re-exported) gas
        e100 = leak * gas_lca("GWP100", mrate, lpen) - d_coal * config.COAL_CO2["GWP100"]
        e20 = leak * gas_lca("GWP20", mrate, lpen) - d_coal * config.COAL_CO2["GWP20"]
        rows.append(dict(Year=year, Displaced=round(disp, 1),
                         ESL_pct=round(esl, 1), ESL_raw=round(esl_raw, 1),
                         leak=round(leak, 1), MexDemandLoss=round(mex_loss, 1),
                         d_coal=round(d_coal, 1),
                         dE_GWP100=round(e100, 1), dE_GWP20=round(e20, 1),
                         # diagnostics: is the leakage channel saturated already?
                         coal_ref=round(dr["coal"], 1), coal_sov=round(ds["coal"], 1),
                         lng_ref=round(dr["us_lng"], 1), lng_sov=round(ds["us_lng"], 1)))
    return pd.DataFrame(rows)


def headline_esl(df, from_year=2035):
    """Mean ESL over the years where leakage matters (default >=2035)."""
    sub = df[df["Year"] >= from_year]
    return float(sub["ESL_pct"].mean()) if len(sub) else float("nan")

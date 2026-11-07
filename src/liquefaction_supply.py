# ==========================================================
# liquefaction_supply.py   (Tier 1e)
#
# Rising marginal-cost US LIQUEFACTION supply curve.
#
# Replaces the single endogenous USA->US_LNG link (which behaved as a
# hard on/off capacity wall: when its ceiling bound, lng_ref == lng_sov
# and leakage was suppressed to 0%; when it had spare, ~all freed gas
# leaked, giving an implausibly bimodal 0%/80% ESL between periods) with
# a STACK of parallel USA->US_LNG tranches at increasing cost. The model
# fills cheap (existing) liquefaction first and climbs into costlier
# new-build capacity only when the delivered LNG value justifies it, so
# the sovereignty case expands liquefaction *smoothly and partially* over
# the reference -- a stable, defensible partial leakage instead of a
# knife-edge.
#
# Cost units are model $/MMBtu-equivalent ADDED to the feed gas. The
# delivered US-LNG cost into Asia is:
#     US production tranche (~2.2-3.2)  +  liquefaction tranche (below)
#                                       +  shipping (~1.8, US_LNG->Asia)
# which must beat the coal-parity price (config.COAL_PARITY = 6.5) to
# displace coal. The top tranche (2.6) sits at that wall on purpose:
# 2.3 + 2.6 + 1.8 = 6.7 > 6.5, so frontier US LNG can no longer undercut
# Asian coal -- the economic ceiling on leakage.
#
# Tranche CAPACITIES ramp with the announced US build-out. 2025 is just
# existing capacity (~150 BCM) so the calibration baseline is realistic;
# later years add capacity at rising cost.
#
# Pipeline:  build_network -> apply_scenario -> add_liquefaction_curve
# (called in experiment_core.solve_case, like add_us_supply_curve).
# ==========================================================

# (cost, {year: tranche capacity BCM})
# Costs are REALISTIC US liquefaction tolling fees (model $/MMBtu-equiv),
# ~2.0-5.0, rising as cheaper brownfield capacity is exhausted and costlier
# greenfield terminals are built. This matters: the delivered US-LNG cost into
# Asia is feed(~2.3) + tolling(below) + shipping(~1.8). With tolling ~2.5 that
# is ~6.6, right at the coal-parity wall (6.5) -- so only the cheapest tranches
# undercut Asian coal and the export/leakage decision sits AT the margin
# (partial leakage). Earlier toy costs (0.2-2.6) put delivered US LNG far below
# coal parity, forcing ~100% of freed gas to leak.
# Each year exposes liquefaction capacity up to LIQ_TOTAL[year] along a single
# GLOBAL cost curve (LIQ_CMIN..LIQ_CMAX over 0..LIQ_XMAX BCM). Splitting into
# N_LIQ_STEPS fine steps approximates a smooth convex curve, so the US-LNG
# export response to the reliability premium is continuous -- removing the
# tranche-edge jumps that made ESL bimodal.
LIQ_TOTAL = {2025: 150, 2030: 320, 2035: 470, 2040: 580, 2045: 680}
LIQ_XMAX = 680.0                 # cumulative capacity at the top of the curve
LIQ_CMIN, LIQ_CMAX = 2.0, 5.0    # tolling at bottom / top of the curve
N_LIQ_STEPS = 14                 # fine steps approximating a smooth curve


def _liq_cost(cum_bcm):
    """Tolling ($/MMBtu) at a cumulative liquefaction position (BCM)."""
    frac = min(1.0, max(0.0, cum_bcm / LIQ_XMAX))
    return LIQ_CMIN + (LIQ_CMAX - LIQ_CMIN) * frac


def add_liquefaction_curve(n, year):
    """Replace the single USA->US_LNG link with a fine rising-cost curve."""
    if "USA_US_LNG" in n.links.index:
        n.remove("Link", "USA_US_LNG")

    total = float(LIQ_TOTAL.get(year, 0.0))
    if total <= 0:
        return n
    step = total / N_LIQ_STEPS
    for i in range(N_LIQ_STEPS):
        cost = _liq_cost((i + 0.5) * step)      # cost at the step midpoint
        n.add(
            "Link", f"USA_US_LNG_t{i}",
            bus0="USA", bus1="US_LNG", carrier="gas",
            p_nom=step, p_nom_extendable=False,
            marginal_cost=cost, efficiency=1,
        )
    return n


def liq_curve_is_active():
    from src.config import USE_LIQ_CURVE
    return bool(USE_LIQ_CURVE)


def us_liquefaction_flow(n):
    """Total USA->US_LNG liquefaction throughput (single link or tranches)."""
    tot = 0.0
    for l in n.links.index:
        if (n.links.loc[l, "bus0"] == "USA"
                and n.links.loc[l, "bus1"] == "US_LNG"
                and l in n.links_t.p0.columns):
            tot += float(n.links_t.p0[l].sum())
    return tot

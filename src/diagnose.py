# ==========================================================
# diagnose.py
#
# One-shot introspection of a single solved SOVEREIGNTY year, to
# find why the freed US gas is/ isn't re-exported (leakage channel).
# Prints the US liquefaction state, the US-LNG route flows, the US
# supply-tranche dispatch, and -- for the coal-switch regions -- the
# bus marginal price, coal-backstop output, and inbound link room.
#
# Run in Spyder (working dir = project root):
#     from src.diagnose import diagnose_year
#     diagnose_year(2040)
# ==========================================================

import pandas as pd

from src.experiment_core import solve_case

COAL_REGIONS = ["CHINA", "SOUTH_ASIA", "SOUTHEAST_ASIA", "NORTHEAST_ASIA", "EUROPE"]


def _f(n, link):
    return float(n.links_t.p0[link].sum()) if link in n.links.index else float("nan")


def diagnose_year(year=2040):
    n, _ = solve_case(year, "sovereignty", {}, {})
    print(f"\n================ DIAGNOSE sovereignty {year} ================")

    # --- US liquefaction link ---
    if "USA_US_LNG" in n.links.index:
        L = n.links.loc["USA_US_LNG"]
        print("\nUSA_US_LNG (liquefaction):")
        print(f"  extendable = {bool(L['p_nom_extendable'])}")
        print(f"  p_nom      = {float(L['p_nom']):.1f}")
        print(f"  p_nom_min  = {float(L.get('p_nom_min', 0)):.1f}")
        print(f"  p_nom_max  = {float(L.get('p_nom_max', 0)):.1f}")
        opt = L.get("p_nom_opt", None)
        print(f"  p_nom_opt  = {float(opt):.1f}" if opt is not None else "  p_nom_opt  = n/a")
        print(f"  FLOW       = {_f(n,'USA_US_LNG'):.1f}")

    # --- US LNG destination routes: flow vs capacity ---
    print("\nUS-LNG routes (flow / p_nom):")
    for l in n.links.index:
        if l.startswith("US_LNG_"):
            print(f"  {l:<26} {_f(n,l):7.1f} / {float(n.links.loc[l,'p_nom']):7.1f}")

    # --- US supply tranche dispatch ---
    gp = n.generators_t.p.sum()
    print("\nUS supply tranches (dispatch, cost):")
    for nm in gp.index:
        if n.generators.loc[nm].get("node_type") == "us_supply":
            print(f"  {nm:<16} {float(gp[nm]):7.1f}  @ {float(n.generators.loc[nm,'marginal_cost']):.2f}")

    # --- coal-switch regions: price, coal served, inbound room ---
    mp = n.buses_t.marginal_price.iloc[0] if len(n.buses_t.marginal_price) else pd.Series(dtype=float)
    print("\nCoal-switch regions:")
    print(f"  {'region':<16}{'price':>8}{'coal_out':>10}{'inbound_used/cap':>22}")
    for reg in COAL_REGIONS:
        price = float(mp.get(reg, float("nan")))
        coalg = f"{reg}_coal"
        coal_out = float(gp.get(coalg, 0.0))
        used = cap = 0.0
        for l in n.links.index:
            if n.links.loc[l, "bus1"] == reg:
                used += _f(n, l); cap += float(n.links.loc[l, "p_nom"])
        print(f"  {reg:<16}{price:8.2f}{coal_out:10.1f}   {used:8.1f}/{cap:8.1f}")

    print("\nRead-out guide:")
    print("  * If USA_US_LNG flow << p_nom_max but coal_out>0 and region price>6.5,")
    print("    the export is blocked by INBOUND ROUTE caps (used==cap).")
    print("  * If region price < 6.5 yet coal_out>0, the coal backstop is mis-wired.")
    print("  * If US tranche-2/3 are dispatched, cheap gas is exhausted (real limit).")
    return n


if __name__ == "__main__":
    diagnose_year(2040)

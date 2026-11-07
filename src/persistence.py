# ==========================================================
# persistence.py   (Tier 1c)
#
# Capacity persistence across years. Because each year is solved
# as an independent snapshot, endogenous capacity (US liquefaction)
# could otherwise "un-build" between years -- physically impossible.
# This helper threads built capacity forward: the optimal capacity
# from year y becomes the lower bound (p_nom_min) in year y+1.
#
# Usage (sequential runner):
#     built = {}
#     for year in YEARS:
#         n = build_network(year); n = apply_scenario(n, year, ...)
#         apply_capacity_floor(n, built)        # before solve
#         n = solve(n)
#         built = record_capacity(n, built)     # after solve
# ==========================================================

# extendable assets whose capacity must persist (grow-only)
PERSISTENT_LINKS = ["USA_US_LNG"]


def apply_capacity_floor(n, built):
    """Set p_nom_min for persistent extendable assets to last year's build."""
    for link in PERSISTENT_LINKS:
        if link in n.links.index and bool(n.links.loc[link, "p_nom_extendable"]):
            floor = float(built.get(link, 0.0))
            cur_min = float(n.links.loc[link, "p_nom_min"])
            n.links.loc[link, "p_nom_min"] = max(cur_min, floor)
            # keep the upper bound consistent
            if n.links.loc[link, "p_nom_max"] < n.links.loc[link, "p_nom_min"]:
                n.links.loc[link, "p_nom_max"] = n.links.loc[link, "p_nom_min"]
    return n


def record_capacity(n, built):
    """Store optimal capacity of persistent assets after a solve."""
    out = dict(built)
    for link in PERSISTENT_LINKS:
        if link in n.links.index:
            opt = n.links.loc[link].get("p_nom_opt", None)
            if opt is None:
                opt = n.links.loc[link, "p_nom"]
            out[link] = max(float(built.get(link, 0.0)), float(opt))
    return out

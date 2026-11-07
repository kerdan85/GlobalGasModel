# ==========================================================
# dual_prices.py   (Tier 2c)
#
# Extracts the LP shadow prices (bus marginal prices) from a
# solved network. These are produced for free by the optimiser
# and make two paper-relevant quantities explicit:
#
#   * the delivered gas price by region, and
#   * the SOVEREIGNTY PREMIUM = price(Mexico) - price(USA),
#     i.e. how much more Mexico pays to source domestic shale
#     instead of importing US gas -- the premise of the paper.
#
# It also reports where the leakage constraint binds (the US
# market price, which rises as US gas is pulled into exports).
# ==========================================================

import pandas as pd


def bus_prices(n):
    """Return a Series of marginal (shadow) prices by bus."""
    try:
        mp = n.buses_t.marginal_price
        if len(mp):
            return mp.iloc[0]
    except Exception:
        pass
    return pd.Series(dtype=float)


def price_summary(n, ref_us="USA", ref_mx="MEXICO"):
    """Return a dict of headline price diagnostics for one solved year."""
    p = bus_prices(n)
    out = {b: round(float(p.get(b, float("nan"))), 3) for b in p.index}
    us = float(p.get(ref_us, float("nan")))
    mx = float(p.get(ref_mx, float("nan")))
    out["_US_price"] = round(us, 3)
    out["_MX_price"] = round(mx, 3)
    out["_sovereignty_premium"] = round(mx - us, 3)
    return out


def collect_prices(results_by_year):
    """results_by_year: {year: solved network}. Returns a tidy DataFrame."""
    rows = []
    for year, n in results_by_year.items():
        s = price_summary(n)
        rows.append(dict(Year=year,
                         US_price=s["_US_price"],
                         MX_price=s["_MX_price"],
                         Sovereignty_premium=s["_sovereignty_premium"]))
    return pd.DataFrame(rows).sort_values("Year")

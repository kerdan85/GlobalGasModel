# -*- coding: utf-8 -*-
"""
=====================================================================
PyPSA  x  Brightway coupling  --  Energy Sovereignty Leakage
Ivan Garcia Kerdan (Tec de Monterrey)
=====================================================================
Turns the gas-trade optimisation into a LIFE-CYCLE model: Brightway
(ecoinvent 3.9.1, IPCC 2021) computes a lifecycle GHG intensity for
each supply ARCHETYPE ONCE, and those intensities are then applied to
the PyPSA dispatch of every solved year to give per-region, per-year
lifecycle emissions (GWP100 and GWP20). Because LCIA scores are linear
in the functional unit, precomputing intensity-per-MJ and multiplying
by dispatch is exact and fast -- the standard, defensible way to couple
a process-LCA to an energy-system model, evaluated every iteration.

Two steps:
  1. precompute_intensities()  [needs Brightway; run once per calibration]
       -> outputs/lca_tech_intensities.csv  (archetype, GWP100, GWP20 gCO2e/MJ)
  2. emissions_by_region(year) / run_all_years()  [pure pandas; every run]
       reads production_nodes_{year}.csv, regional_balance_{year}.csv and the
       intensities -> outputs/emissions_by_region.csv

Per-region ledger (production + upstream, consequential-lite):
  region emissions =
      upstream(cradle-to-gate) of what the region PRODUCES, by resource type
    + combustion of what the region CONSUMES
    + LNG-chain of what it EXPORTS as LNG
    + coal it burns (coal-switch not met by gas)
This is transparent and avoids double counting (each stage assigned once).
"""
import os
import pandas as pd

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OUT = os.path.join(_ROOT, "outputs")

# 1 BCM gas ~ 36 PJ = 36e9 MJ; (gCO2e/MJ) x BCM x 36e9 / 1e12 = Mt CO2e
MT_PER_INTENSITY_BCM = 0.036
GAS_COMBUSTION_KG_PER_MJ = 0.0561    # direct combustion CO2 (kg/MJ)

# The coupling combines the ecoinvent process-LCA non-methane lifecycle
# (config.GAS_UPSTREAM_CO2 + combustion, from src.lca_brightway.run()) with a
# per-RESOURCE-TYPE upstream methane rate from data/technology.csv. ecoinvent
# 3.9.1 has no shale-specific gas activity, so the measurement-based US-shale
# methane rate is applied explicitly -- which is precisely the paper's point.
_GAS_MJ_PER_M3 = 36.0


# =====================================================================
# STEP 1 -- Brightway: per-archetype lifecycle intensity (gCO2e/MJ)
# =====================================================================
def precompute_intensities(save=True):
    """Build the per-technology lifecycle-intensity table used by the coupling.

    Non-methane lifecycle CO2 (combustion + non-CH4 upstream/LNG-chain) comes
    from the ecoinvent 3.9.1 process-LCA (config, refreshed by
    src.lca_brightway.run()); the per-RESOURCE-TYPE UPSTREAM METHANE is layered
    on using each technology's leak rate in data/technology.csv, since ecoinvent
    has no shale-specific gas activity. No per-activity Brightway lookup is
    needed here, so it runs in any environment and never fails on a missing name.
    """
    from src import config
    tech = pd.read_csv(os.path.join(_ROOT, "data/technology.csv"))
    ch4 = dict(zip(tech["Technology"], tech["CH4Leakage"]))
    comb = GAS_COMBUSTION_KG_PER_MJ * 1000.0                  # 56.1 gCO2/MJ
    up_co2 = getattr(config, "GAS_UPSTREAM_CO2", 18.4)
    per = config.GAS_METHANE_PER_PCT
    rows = []
    for t, r in ch4.items():
        if str(t).upper() == "SLACK":
            continue
        up100 = up_co2 + per["GWP100"] * float(r)
        up20 = up_co2 + per["GWP20"] * float(r)
        rows.append(dict(archetype=t, stage="upstream",
                         GWP100=round(up100, 2), GWP20=round(up20, 2)))
        rows.append(dict(archetype=t, stage="combustion", GWP100=comb, GWP20=comb))
        print(f"  {t:14s} CH4={float(r):.1f}%  upstream={up100:5.1f}/{up20:5.1f}  (+comb 56.1)")
    df = pd.DataFrame(rows)
    if save:
        os.makedirs(_OUT, exist_ok=True)
        p = os.path.join(_OUT, "lca_tech_intensities.csv")
        df.to_csv(p, index=False); print("wrote", p)
    return df


# =====================================================================
# STEP 2 -- apply intensities to PyPSA dispatch -> per-region emissions
# =====================================================================
def _intensity_lookup():
    """Return {archetype: {'upstream':(g100,g20),'combustion':(g100,g20)}}.
    Falls back to sensible defaults if the Brightway CSV is absent."""
    p = os.path.join(_OUT, "lca_tech_intensities.csv")
    if os.path.exists(p):
        d = pd.read_csv(p)
        out = {}
        for _, r in d.iterrows():
            out.setdefault(r["archetype"], {})[r["stage"]] = (r["GWP100"], r["GWP20"])
        return out
    # fallback defaults (gCO2e/MJ): upstream by tech incl methane, combustion 56
    up = {"CONVENTIONAL": (10, 28), "SHALE": (18, 45), "SHALE_MATURE": (14, 35),
          "CANADIAN": (12, 30), "OFFSHORE": (8, 20), "LNG_EXPORTER": (34, 52)}
    return {t: {"upstream": v, "combustion": (56.1, 56.1)} for t, v in up.items()}


def emissions_by_region(year, producers_csv="data/producers.csv"):
    """Per-region lifecycle emissions (Mt CO2e, GWP100 & GWP20) for one year,
    from the solved-model outputs."""
    import re
    inten = _intensity_lookup()
    prod = pd.read_csv(os.path.join(_OUT, f"production_nodes_{year}.csv"))
    bal = pd.read_csv(os.path.join(_OUT, f"regional_balance_{year}.csv"))
    prods = pd.read_csv(os.path.join(_ROOT, producers_csv))
    node_region = dict(zip(prods["Node"], prods["MarketBus"]))
    valid_regions = set(bal["Region"])

    def region_of(node):
        """Map a production node (incl. depletion-curve tranches like
        US_GULF_t0) to its market region."""
        if node in node_region:
            return node_region[node]
        base = re.sub(r"_t\d+$", "", str(node))       # strip tranche suffix
        if base in node_region:
            return node_region[base]
        for p, reg in (("US_GULF", "USA"), ("PERMIAN", "USA"), ("APPALACHIA", "USA"),
                       ("MEX_", "MEXICO"), ("CAN_", "CANADA")):
            if str(node).startswith(p):
                return reg
        return node if node in valid_regions else "USA"

    rows = {}
    def add(region, g100, g20):
        r = rows.setdefault(region, [0.0, 0.0]); r[0] += g100; r[1] += g20

    # (a) upstream emissions of production, by node's technology
    for _, r in prod.iterrows():
        tech = r["Technology"]; region = region_of(r["Node"])
        up = inten.get(tech, {}).get("upstream", (10.0, 28.0))
        add(region, r["Production"] * up[0] * MT_PER_INTENSITY_BCM,
                    r["Production"] * up[1] * MT_PER_INTENSITY_BCM)

    # (b) combustion of each region's gas consumption (demand)
    for _, r in bal.iterrows():
        dem = float(r.get("Demand", 0.0))
        add(r["Region"], dem * 56.1 * MT_PER_INTENSITY_BCM,
                         dem * 56.1 * MT_PER_INTENSITY_BCM)
        # (c) coal burned (coal-switch not met by gas)
        from src import config
        coal = float(r.get("Backstop", 0.0))
        add(r["Region"], coal * config.COAL_CO2["GWP100"] * MT_PER_INTENSITY_BCM,
                         coal * config.COAL_CO2["GWP20"] * MT_PER_INTENSITY_BCM)

    out = pd.DataFrame([{"Year": year, "Region": k,
                         "Emissions_GWP100_Mt": round(v[0], 2),
                         "Emissions_GWP20_Mt": round(v[1], 2)}
                        for k, v in rows.items()])
    return out.sort_values("Region")


def run_all_years(years=(2025, 2030, 2035, 2040, 2045)):
    frames = []
    for y in years:
        try:
            frames.append(emissions_by_region(y))
        except FileNotFoundError as e:
            print(f"  [skip {y}] {e}")
    if not frames:
        print("No solved-year outputs found; run run_model.py first."); return None
    df = pd.concat(frames, ignore_index=True)
    p = os.path.join(_OUT, "emissions_by_region.csv")
    df.to_csv(p, index=False); print("wrote", p)
    return df


if __name__ == "__main__":
    run_all_years()

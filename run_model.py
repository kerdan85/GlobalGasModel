# ==========================================================
# run_model.py
# Global Gas Model
# ==========================================================

import os
import sys
import datetime

import pandas as pd

from src.config import YEARS, OUTPUT_DIR, SCENARIO
from src.build_network import build_network
from src.apply_scenario import apply_scenario
from src.solve import solve
from src.experiment_core import solve_case
from src.export_results import export_results
from src.plot_results import plot_results
from src.plot_north_america import plot_north_america
from src.plot_world_flows import plot_world_flows
from src.lng_terminals import lng_terminal_report
from src.reserves_depletion import reserves_depletion_report

# ==========================================================
# INPUT SANITY ECHO  -> console AND outputs/RUN_DIAGNOSTICS.txt
# If OFFSHORE cost is not 2.5 or APPALACHIA is not
# SHALE_MATURE, this copy is running OLD inputs.
# ==========================================================
os.makedirs(OUTPUT_DIR, exist_ok=True)
_DIAG = os.path.join(OUTPUT_DIR, "RUN_DIAGNOSTICS.txt")


def _diag(line, mode="a"):
    print(line)
    with open(_DIAG, mode) as fh:
        fh.write(line + "\n")


_diag("=" * 60, mode="w")
_diag(f"RUN_DIAGNOSTICS  {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
_diag(f"python      : {sys.executable}")
_diag(f"working dir : {os.path.abspath(os.getcwd())}")
_diag(f"run_model   : {os.path.abspath(__file__)}")
_diag(f"data dir    : {os.path.abspath('data')}")
_diag("-" * 60)
_diag("INPUT CHECK")
try:
    _t = pd.read_csv("data/technology.csv").set_index("Technology")
    _p = pd.read_csv("data/producers.csv").set_index("Node")
    _d = pd.read_csv("data/demand.csv").set_index("Node")
    _diag(f"  OFFSHORE marginal cost : {_t.loc['OFFSHORE','MarginalCost']}   (expected 2.5)")
    _diag(f"  APPALACHIA technology  : {_p.loc['APPALACHIA','Technology']}   (expected SHALE_MATURE)")
    _diag(f"  CAN_WEST technology    : {_p.loc['CAN_WEST','Technology']}   (expected CANADIAN)")
    _diag(f"  USA 2025 demand        : {_d.loc['USA','2025']}   (expected 985)")
    _ok = (float(_t.loc['OFFSHORE', 'MarginalCost']) == 2.5
           and _p.loc['APPALACHIA', 'Technology'] == 'SHALE_MATURE')
    _diag(f"  >>> INPUTS ARE {'CURRENT' if _ok else 'STALE - THIS COPY HAS OLD DATA'} <<<")
except Exception as _e:
    _diag(f"  ! Could not read inputs: {_e}")
_diag("=" * 60)

# ==========================================================
# REMOVE OLD MASTER FILES
# ==========================================================
master_files = [
    f"{OUTPUT_DIR}/trade_flows.csv",
    f"{OUTPUT_DIR}/mexico_supply_mix.csv",
    f"{OUTPUT_DIR}/technology_mix.csv",
    f"{OUTPUT_DIR}/consumption.csv",
    f"{OUTPUT_DIR}/regional_balance.csv",
    f"{OUTPUT_DIR}/production_nodes.csv",
]
for file in master_files:
    if os.path.exists(file):
        os.remove(file)

# ==========================================================
# RUN MODEL
# ==========================================================
results = {}

# Build/solve each year through the SAME pipeline used by
# run_experiments.py (src.experiment_core.solve_case). This wires in
# the Tier-1 features controlled by src/config.py:
#   * USE_DEPLETION_CURVE -> US production added as rising-cost tranches
#     (add_us_supply_curve). build_network SKIPS the flat US producers
#     when this is on, so without this step the US has no supply at all
#     and the whole country falls back to slack.
#   * ELASTIC_DEMAND      -> price-elastic demand curve per region.
#   * CAPACITY_PERSISTENCE-> endogenous capacity carried forward via `built`.
# Using solve_case guarantees run_model and run_experiments solve the
# IDENTICAL network for the configured scenario.
built = {}

for year in YEARS:

    print()
    print("=" * 60)
    print(f"Running Global Gas Model - {year}  (scenario: {SCENARIO})")
    print("=" * 60)

    n, built = solve_case(year, SCENARIO, {}, built)
    export_results(n, year)
    results[year] = n

    print(f"✓ Year {year} completed.")

# ==========================================================
# SUMMARY
# ==========================================================
print()
print("=" * 60)
print("GLOBAL GAS MODEL FINISHED SUCCESSFULLY")
print("=" * 60)
print()
print("Years simulated:", ", ".join(str(y) for y in YEARS))
print(f"Output directory: {OUTPUT_DIR}/")
print()

# ==========================================================
# FIGURES
# ==========================================================
print("Generating figures...")
plot_results()
os.makedirs(f"{OUTPUT_DIR}/figures", exist_ok=True)
plot_north_america()
plot_world_flows()

# LNG terminal buildout implied by the optimised flows
lng_terminal_report()

# Reserve depletion & regions under pressure (real reserves)
reserves_depletion_report()
print("✓ Figures created.")

# ==========================================================
# OUTPUT SANITY CHECK
# ==========================================================
_diag("=" * 60)
_diag(f"OUTPUT CHECK  (from {os.path.abspath(f'{OUTPUT_DIR}/regional_balance.csv')})")
try:
    rb = pd.read_csv(f"{OUTPUT_DIR}/regional_balance.csv")
    nor45 = rb.query("Year==2045 and Region=='EUROPE'")["Production"].iloc[0]
    usa25 = rb.query("Year==2025 and Region=='USA'")["Production"].iloc[0]
    max_resid = rb["Residual"].abs().max()
    tot_slack = rb["Slack"].sum()
    _diag(f"  EUROPE 2045 production (Norway) : {nor45:.0f}   (expected ~188, NOT 0)")
    _diag(f"  USA 2025 production             : {usa25:.0f}   (expected ~1075)")
    _diag(f"  Max |Residual|                  : {max_resid:.2e}   (expected ~0)")
    _diag(f"  Total slack                     : {tot_slack:.1f}   (expected ~0)")
    # A genuine pass requires: Norway alive, US actually producing (not on
    # slack), every regional balance closing, and slack negligible. The old
    # check only looked at Norway, so a US-on-slack run could still read
    # "CORRECT" -- that blind spot is what hid the missing US supply curve.
    _ok = (nor45 > 100 and usa25 > 800 and max_resid < 1.0 and tot_slack < 50.0)
    if _ok:
        _diag("  >>> OUTPUT IS CORRECT <<<")
    else:
        reasons = []
        if nor45 <= 100:   reasons.append("Norway collapsed")
        if usa25 <= 800:   reasons.append("US on slack / no supply curve")
        if max_resid >= 1.0: reasons.append("balance does not close")
        if tot_slack >= 50.0: reasons.append("excess slack")
        _diag(f"  >>> OUTPUT IS BROKEN: {', '.join(reasons)} <<<")
except Exception as _e:
    _diag(f"  ! Could not read regional_balance.csv: {_e}")
_diag("=" * 60)
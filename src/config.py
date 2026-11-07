# ==========================================================
# config.py
# ==========================================================

YEARS = [2025, 2030, 2035, 2040, 2045]

# Preferred solver, with an open fallback. If Gurobi isn't
# licensed/installed, solve.py automatically uses HiGHS
# (bundled with PyPSA via `highspy`, no licence required).
SOLVER = "gurobi"
FALLBACK_SOLVER = "highs"

OUTPUT_DIR = "outputs"

# ----------------------------------------------------------
# LNG terminal sizing (BCM/year of throughput per terminal).
# Used to convert required liquefaction/regasification
# capacity into a count of new terminals beyond the current
# (2025) fleet. Adjust to taste.
#   Liquefaction: a large export train ~5-6 Mtpa ~ 7-8 BCM/yr;
#     a multi-train terminal ~9-12 BCM/yr  -> default 9.
#   Regasification: onshore/FSRU import terminal ~5-9 BCM/yr
#     -> default 7.
# ----------------------------------------------------------
AVG_LIQ_BCM = 9.0       # avg liquefaction (export) terminal size
AVG_REGAS_BCM = 7.0     # avg regasification (import) terminal size

# ==========================================================
# ENERGY SOVEREIGNTY LEAKAGE (ESL) experiment settings
# ==========================================================
# Scenario:
#   "sovereignty" = Mexico builds domestic shale and phases out US imports
#                   (US_GULF_MEXICO -> 0, MexicoShaleCap ramps).
#   "reference"   = Mexico keeps importing US gas (no shale build-out).
# The ESL driver runs BOTH and compares.
SCENARIO = "sovereignty"

# US gas cost advantage (Henry Hub). US is the low-cost global swing
# supplier, so freed gas can compete in export markets.
US_GAS_COST = 2.5
US_PRODUCERS = ("US_GULF", "PERMIAN", "APPALACHIA")

# US shale production PLATEAU: if True, US production capacity is held
# ~flat (not grown by SupplyGrowth), making US supply-constrained — the
# condition under which sovereignty leakage emerges.
US_PLATEAU = True

# Demand-side coal-to-gas switching. Coal-heavy importers can take extra
# gas only if delivered gas undercuts a coal-parity backstop price.
# COAL_PARITY is the gas price (model units ~ $/MMBtu) at which gas = coal.
# Raised to 6.5 so delivered (post-liquefaction) US LNG can still
# undercut coal at the margin -- i.e. the leakage channel can fire
# rather than being priced out by the depletion-curve tranche cost.
COAL_PARITY = 6.5

# Coal-to-gas switching is modeled as a SPREAD of parity prices (a heterogeneous
# coal fleet: some plants switch to gas easily, others only at a high gas-cost
# disadvantage) rather than a single threshold. This makes switching -- and thus
# leakage -- respond GRADUALLY to the delivered gas price instead of flipping
# all-or-nothing. A FINE spread (13 sub-tranches over +/-2.0 $/MMBtu) makes the
# coal->gas response effectively continuous, so leakage varies smoothly and
# monotonically with the reliability premium rather than bimodally. Offsets are
# applied around COAL_PARITY; each region's switchable volume in coal_switch.csv
# is split evenly across these sub-tranches.
COAL_PARITY_SPREAD = [round(-2.0 + 4.0 * k / 12, 4) for k in range(13)]

# --- Logit coal-to-gas switching (reviewer robustness) ------------------
# When True, the coal-to-gas channel is resolved by an OUTER FIXED-POINT
# (src/logit_resolve.py, src/run_logit_experiment.py) that sets each region's
# gas-served (switched) volume from a smooth LOGIT share of the delivered gas
# price, instead of the least-cost merit order over COAL_PARITY_SPREAD tranches.
# This tests whether the leakage THRESHOLD survives a non-least-cost, smooth
# inter-supplier substitution rule in the FULL 19-region model. The baseline
# results in the paper use LOGIT_SWITCHING = False (least-cost).
LOGIT_SWITCHING = False   # global default; the runner sets it per-experiment
LOGIT_TAU       = 0.6     # logit temperature ($/MMBtu): fleet-response smoothness
LOGIT_MAX_ITER  = 30      # outer fixed-point iteration cap
LOGIT_TOL       = 1.0     # convergence tol on switched volume (BCM, max over regions)
LOGIT_DAMPING   = 0.5     # under-relaxation (0<d<=1); lower = more stable, slower

# --- Strict-convexity slope (Tier 1g) -----------------------------------
# A per-generator QUADRATIC cost term gives each supply source a gently rising
# marginal cost across its output range (within-region resource heterogeneity),
# making the objective STRICTLY CONVEX so the optimal dispatch is UNIQUE and
# varies SMOOTHLY with parameters. This is the cure for the system-wide LP
# degeneracy that left ESL bimodal / non-monotonic even after the US supply,
# liquefaction and coal curves were fine-grained (fine LINEAR tranches don't fix
# it because the degeneracy is in which of many suppliers serves each market).
# QUADRATIC_SLOPE is the $/MMBtu rise across a generator's full capacity; the
# quadratic coefficient is slope / p_nom. Set 0 to disable.
# REQUIRES PyPSA marginal_cost_quadratic support (>= 0.25) AND a QP solver
# (Gurobi, or HiGHS for convex QP).
QUADRATIC_SLOPE = 0.8

# US LNG liquefaction treated as an ENDOGENOUS investment (extendable
# link with an annualised capital cost) rather than a fixed/must-run cap.
US_LNG_ENDOGENOUS = True
US_LNG_CAPITAL = 0.5    # annualised capex per unit US-LNG capacity (model units)

# --- Reliability / security premium (Tier 1f) ---------------------------
# Importers pay a premium for RELIABLE supply (US / allied LNG) over
# geopolitically-exposed gas: Russia under sanction and pipeline cut-off,
# Iran and the Gulf/Middle East exposed to regional conflict and chokepoint
# (Hormuz) risk. This is a security-of-supply VALUE, not a pure cost -- the
# central reason a market would re-absorb US gas even when marginally pricier
# than coal or rival LNG. Modeled as an effective delivered-cost advantage
# (model $/MMBtu-equiv) on US LNG export routes. At 0 the model is pure
# least-cost and leakage is ~0; as it rises, freed US gas is re-exported to
# reliability-valuing markets and displaces coal -> leakage. KEY axis: ESL is
# reported as a function of this premium.
RELIABILITY_PREMIUM = 1.0

# US liquefaction as a RISING marginal-cost supply curve (src/liquefaction_
# supply.py) instead of a single hard-capped link. A hard cap makes leakage
# bimodal (0% when it binds, ~80% when spare); the cost curve lets the
# sovereignty case expand liquefaction smoothly and partially over the
# reference, giving a stable, defensible leakage fraction. When True it
# supersedes the US_LIQ_CAP ceiling in apply_scenario for the solve_case path.
USE_LIQ_CURVE = True

# ==========================================================
# Emissions accounting for the ESL climate ledger.
# Lifecycle intensities in gCO2e/MJ-equivalent units (same scale as
# technology.csv CO2Factor ~56 = gas combustion CO2). Reported at BOTH
# GWP100 and GWP20 (IPCC AR6). Sources: IEA Global Methane Tracker 2024,
# Howarth (2024) LNG GHG footprint, IPCC AR6.
# ==========================================================
# The lifecycle intensities below are CALIBRATED to the ecoinvent process-LCA
# (src/lca_brightway.py, IPCC 2021 GWP100/GWP20), which cross-checks and
# CORRECTS an earlier parametric ledger. Two fixes matter:
#   (1) upstream methane was overstated ~2.75x (it used combustion CO2, 56, as
#       the base instead of the CH4 THROUGHPUT, 56/2.75 ~ 20.4 g CH4/MJ);
#   (2) coal is dirtier than first assumed (ecoinvent adds coal-mine methane).
# Consequence: at central methane (2.5%) shale-LNG is ~AT or BELOW coal at both
# horizons; it exceeds coal only at high methane (>~3%, GWP20). The climate
# sign of leakage is therefore CONTINGENT on the methane rate and the horizon.

# Gas lifecycle intensity split into a methane-independent part (combustion +
# upstream CO2 + LNG chain) and a per-% upstream-methane term, so the intensity
# responds correctly to the swept methane rate:  I_gas = NONMETHANE + PER_PCT*r
# From the ecoinvent 3.9.1 process-LCA (src/lca_brightway.run()): the US LNG
# chain + combustion give a methane-INDEPENDENT intensity of ~74.5 gCO2e/MJ
# (combustion 56.1 + non-methane upstream/LNG-chain CO2 ~18.4), the SAME at both
# horizons because it is CO2; upstream methane is layered on with the swept rate.
GAS_NONMETHANE      = {"GWP100": 74.5, "GWP20": 74.5}    # combustion + non-CH4 chain CO2
GAS_UPSTREAM_CO2    = 18.4                               # non-CH4 upstream+LNG-chain CO2 (for per-tech coupling)
GAS_METHANE_PER_PCT = {"GWP100": 6.1,  "GWP20": 16.8}    # gCO2e/MJ per % upstream CH4 (CH4-throughput basis)
# -> at r=2.5%: I_gas = 89.8 (GWP100) / 116.5 (GWP20)

# US shale upstream methane leakage (% of throughput). Central 2.5%; the paper
# sweeps 1.5-3.7% (Alvarez 2018; IEA Methane Tracker; Permian upper: Howarth).
US_METHANE_RATE = 2.5

# CH4 mass<->combustion-CO2 conversion (molar mass ratio CO2/CH4 = 44/16).
CH4_CO2_MASS_RATIO = 2.75
GAS_COMBUSTION = 56.0       # gas combustion CO2 (gCO2/MJ), retained for reference
CH4_GWP = {"GWP100": 30.0, "GWP20": 82.5}   # IPCC AR6 fossil CH4 GWP (reference)
LNG_EMIS_PENALTY = 0.25     # (reference; now folded into GAS_NONMETHANE)

# Coal lifecycle CO2e (combustion + coal-mine methane), gCO2e/MJ, ecoinvent 3.9.1.
COAL_CO2 = {"GWP100": 108.0, "GWP20": 126.0}

# Approximate methane rates at which shale-LNG lifecycle = coal (break-even):
#   GWP20 crossover ~3.1% ; GWP100 crossover ~5.5% (see Discussion).

# ==========================================================
# TIER 1 / TIER 2 MODEL IMPROVEMENTS
# Master switches consumed by the new modules and by
# run_experiments.py. All default to the behaviour used in the
# ESL paper; the scenario runner overrides them per scenario.
# ==========================================================

# --- Tier 1a: endogenous US supply tightness (depletion curve) ---
# When True, US production is represented as a rising marginal-cost
# STEP SUPPLY CURVE (data/us_supply_curve.csv) instead of a flat
# block + binary plateau. Tightness (and hence leakage) then emerges
# from the resource base rather than being imposed.
USE_DEPLETION_CURVE = True
# Global multiplier on the *slope* of the US supply curve. 1.0 = as
# calibrated; >1 steepens (scarcer/costlier incremental gas, more
# leakage); a shallow curve with cheap tranches ~ "spare capacity".
US_SUPPLY_SLOPE = 1.0

# --- Tier 1b: price-elastic demand beyond coal switching ---
# When True, a multi-step demand curve (data/demand_elasticity.csv)
# lets a fraction of each region's gas demand drop out as delivered
# price rises (substitution / demand destruction). Tests whether the
# ~100% reabsorption survives realistic demand response.
ELASTIC_DEMAND = True
# Constant-elasticity default used to build steps when a region is
# not listed explicitly in demand_elasticity.csv.
DEMAND_ELASTICITY = -0.3      # price elasticity of gas demand
DEMAND_STEPS = 4              # linear steps approximating the demand curve
DEMAND_REF_PRICE = 6.0        # reference delivered gas price (model units)

# --- Tier 1c: capacity persistence across years ---
# When True, endogenous capacity (US liquefaction) built in an earlier
# year cannot be removed later: prev-year p_nom_opt becomes this year's
# p_nom_min. Enforced by the sequential runner, not the single solve.
CAPACITY_PERSISTENCE = True

# --- Tier 1d: out-of-sample validation ---
# Historical years to back-cast against observed trade (data/
# validation_history.csv). The model is NOT tuned to these years.
VALIDATION_YEARS = [2018, 2021, 2023]

# --- Tier 2a: scenario matrix axes ---
# Each axis is swept by run_experiments.py; the full grid is the
# Cartesian product. Keep small to bound run time.
SCENARIO_AXES = {
    # US spare export capacity: tight .. abundant (KEY axis; central=1.0).
    # NOTE: the extreme-tight 0.70 point was dropped. At that tightness the
    # displaced US->MX volume (the ESL denominator) collapses toward zero, so
    # the ratio becomes numerically unstable and prints ~63% -- breaking the
    # otherwise monotonic 0.85->1.3 response (15->20->69->95%). Keep the sweep
    # over the economically meaningful 0.85-1.3 range; report extreme tightness
    # separately if needed.
    "us_supply_scale":  [0.85, 1.0, 1.15, 1.3],
    "mex_shale_cost":   [2.8, 4.0, 5.5],         # Mexican shale cost (sovereignty premium)
    "coal_demand":      [0.7, 1.0, 1.3],         # multiplier on coal-switch volumes
    "methane_rate":     [1.5, 2.5, 3.7],         # US shale CH4 leakage (%) lo/central/hi
}

# --- Tier 2b: parameter uncertainty (Monte Carlo / tornado) ---
# (param_name, low, central, high) used by src/uncertainty.py.
UNCERTAINTY_PARAMS = [
    ("us_gas_cost",    2.0, 2.5, 3.2),
    ("coal_parity",    5.5, 6.5, 7.5),
    ("us_lng_capital", 0.3, 0.5, 0.8),
    ("methane_rate",   1.5, 2.5, 3.7),
    ("lng_penalty",    0.15, 0.25, 0.35),
    ("us_supply_scale",0.85, 1.0, 1.3),
]
N_MONTECARLO = 200             # samples for the Monte Carlo ESL distribution
                              # (TEMPORARY preview value; restore to 200 for the
                              #  final paper run to get a stable median/spread)

MARKETS = [
    "USA",
    "CANADA",
    "MEXICO",
    "EUROPE",
    "CHINA",
    "SOUTH_ASIA",
    "SOUTHEAST_ASIA",
    "NORTHEAST_ASIA",
    "LATIN_AMERICA",
    "RUSSIA",
    "IRAN",
    "GULF_STATES",
    "QATAR",
    "NORTH_AFRICA",
    "SUBSAHARAN_AFRICA",
    "CENTRAL_ASIA",
    "CASPIAN_REGION",
    "AUSTRALIA",
    "US_LNG",
]

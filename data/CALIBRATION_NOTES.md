# Calibration & Model-Fix Notes

All quantities are **BCM/year**. The 2025 base year is calibrated to the
latest available real figures (2024 actuals, the best proxy for 2025).

## Data sources (2024 actuals)
- **Production / consumption by country** — Energy Institute, *Statistical Review of World Energy 2025*; IEA *Global Energy Review 2025*.
- **US LNG exports (~120 BCM, 11.9 Bcf/d)** and **US→Mexico pipeline (~66 BCM, 6.4 Bcf/d)** — US EIA, *Today in Energy*.
- **Mexico production (~40 BCM, 3.77 Bcf/d)** — US EIA / NGI.
- **Norway (124 BCM)** — Gassco / Norwegian Petroleum.
- **Russia pipeline to Europe (~32 BCM)** — Gazprom data via AAWSAT/Reuters.
- **China (prod 246 / cons 428), India/South Asia, Indonesia+Malaysia (SE Asia)** — IEA, PPAC India, DOSM Malaysia, EIA country briefs.

## Structural fixes
1. **Topology** — `build_network` now auto-adds a producer→`MarketBus` delivery
   link when one is missing. Previously MIDDLE_EAST, TURKMENISTAN and AZERBAIJAN
   had no link to their home demand bus, so their domestic demand was met by the
   high-cost slack generator and the regional balance never closed.
2. **Domestic production for major importers** — added `CHINA_DOM`,
   `SOUTH_ASIA_DOM`, `SEA_DOM` so "imports" reflect real *net* imports
   (e.g. China now imports ~178 BCM, not its full 428 BCM demand).
3. **US LNG must-run** — `USA_US_LNG` runs at full contracted capacity
   (`p_min_pu = 1.0`); a pure least-cost dispatch otherwise ignores the
   (relatively expensive) US LNG and exports ~12 BCM instead of ~120.
4. **Accounting** — `export_results` now reports a `Slack` column and a
   `Residual`, so `Production + Imports + Slack − Exports − Demand = 0` holds
   for every region/year.
5. **Data-driven scenarios** — `apply_scenario` reads all levers from
   `scenarios.csv` (no hard-coded dicts). New `SupplyGrowth` column scales
   producer + trade-link capacity over time (2025 = 1.0) so the demand
   trajectory to 2045 stays feasible without artificial bottlenecks.
6. **Extendability** comes from `technology.csv` (`Extendable` column), not a
   hard-coded node list.
7. **Solver** — `solve.py` tries Gurobi, automatically falling back to the open
   HiGHS solver if Gurobi is unavailable.

## Verification
A standalone min-cost-flow shadow model (equivalent to the PyPSA LP because all
link efficiencies = 1 and costs are linear) confirms, for **every year
2025–2045**: demand fully served, **zero slack**, and the regional-balance
identity closes for all regions.

2025 modelled production vs real (BCM): USA 1072 (~1069), Russia 580 (~642),
Iran 300 (~279), China dom 250 (~246), Canada 199 (~199), Norway 125 (~124),
Australia 160 (~155), Mexico 43 (~40); US LNG to world 120 (~120); China net
imports 178 (~182).

**Note on US demand (985 BCM, 2025):** this represents total US domestic
*disposition* — end-use consumption (~893) plus lease, plant and pipeline fuel,
reinjection and flaring (~90). Using total disposition rather than end-use
reconciles modelled US production (~1075) with real **gross** production
(~1069); the ~100 BCM wedge between gross production and end-use consumption is
standard in national gas balances and is not inter-regional trade.

## Forward-year dynamics (merit-order refinements)
A second calibration pass corrected several rest-of-world artifacts that a pure
least-cost dispatch produced. All are merit-order/cost adjustments; the 2025
base year and the zero-slack / closed-balance verification are unaffected.

- **Technology split for shale.** `SHALE` (frontier: MEX_SHALE, ARG_SHALE) keeps
  the extendable + capital-cost buildout treatment. `SHALE_MATURE` (Appalachia /
  Marcellus) is a low-cost established basin (marginal cost 2.8) so it stays the
  US production backbone (430 -> 645 BCM) instead of being undercut to zero.
- **Canadian gas** has its own low marginal cost (2.5), reflecting
  takeaway-constrained AECO pricing, so Western Canada keeps exporting its
  surplus (~80–120 BCM) to the US rather than being displaced.
- **Norway** offshore marginal cost lowered (2.5) so it remains European baseload
  (~125–188 BCM) instead of being squeezed out by must-run US LNG.
- **US LNG destination split.** US_LNG_EUROPE / US_LNG_LATIN_AMERICA caps are
  limited so the must-run US LNG also reaches Asia (Asia share 45 -> 180 BCM by
  2045), matching the real ~Europe/Asia/LatAm distribution.
- **US -> Mexico consolidation.** The parallel `PERMIAN_MEXICO` route is folded
  into the scenario-controlled `US_GULF_MEXICO` lever, so the pipeline phase-out
  governs ALL US gas into Mexico and Mexican shale ramps as intended
  (0 -> 78 BCM as imports fall 50 -> 0).
- **Latin American import corridors** (North/Sub-Saharan Africa) held fixed
  against the supply-growth factor so rising LatAm demand pulls domestic
  Argentine shale (Vaca Muerta grows rather than being out-competed by LNG).

Known limitation: Middle East (ex-Qatar) LNG to Asia tapers to zero after ~2030
as Qatar's North Field expansion (cheaper LNG) scales up — a defensible market
outcome rather than a model error.

## Added trade routes & producer realism (third pass)
New flows/producers added to address gaps in the global LNG picture:

- **Canada LNG to Asia (NEW).** West-coast liquefaction (LNG Canada etc.):
  `CAN_WEST -> {NORTHEAST_ASIA, CHINA, SOUTHEAST_ASIA}` LNG, scheduled 6 -> 52 BCM
  (2025 -> 2045); short Pacific haul so low shipping cost. CAN_WEST capacity
  raised 170 -> 235 for export headroom.
- **Russia Asian pivot (NEW + expanded).** Power-of-Siberia pipeline to China
  scheduled 55 -> 100 BCM; Arctic/Sakhalin **LNG** `RUSSIA -> NORTHEAST_ASIA`
  (must-run, contracted) 20 -> 40 BCM; residual EU LNG `RUSSIA_EUROPE_LNG`
  declining 20 -> 0 (phase-out). RUSSIA capacity 700 -> 750.
- **Sub-Saharan Africa LNG to Asia (NEW).** Mozambique/Tanzania/Nigeria:
  `SUBSAHARAN_AFRICA -> {CHINA, SOUTH_ASIA, NORTHEAST_ASIA}` LNG, 10 -> 80 BCM;
  East-Africa->India is a short haul (low cost). SUBSAHARAN capacity 130 -> 200.
- **Australia -> South Asia (NEW)** route added (Australia also serves India).
- **Iran constrained (sanctions).** Export routes capped low and held flat
  (China 25, South Asia 20, SE Asia 0) instead of the previous unrealistic
  ~169 BCM. Reflects sanctioned, limited Iranian exports.
- **China pipeline imports made realistic.** `TURKMENISTAN_CHINA` capped to
  ~55-75 BCM (was an inflated ~130) so China imports growing volumes of **LNG**
  (43 -> 130 BCM), which absorbs global LNG supply and prevents cheaper exporters
  (Qatar, Australia) from being artificially crowded out.

## Reserves & depletion (data/reserves.csv + src/reserves_depletion.py)
Regional reserves split by resource type (Conventional / Unconventional) and
maturity (Proved / Potential), in BCM. Sources:
  - Proved reserves: Energy Institute Statistical Review 2024 (Russia 37.4 Tcm,
    Iran ~34, Qatar ~24.7, Turkmenistan ~13.6, USA ~12.6 Tcm, etc.).
  - Unconventional potential: EIA technically-recoverable shale resources
    (China 1,115 Tcf ~31.6 Tcm, Argentina 802 ~22.7, Mexico 681 ~19.3,
    Canada 573 ~16.2, Algeria 707 ~20, Australia ~437 Tcf, etc.; 1 Tcf = 28.3 BCM).
  - Conventional "potential" (undiscovered/probable) are order-of-magnitude
    estimates, flagged as such.

`reserves_depletion_report()` integrates cumulative extraction over 2025–2045
(trapezoidal over the 5-yearly snapshots) by region and resource type, then
reports % of proved consumed, % of proved+potential, remaining volumes, R/P
years, and a "pressure" flag (proved exhausted, or <25 yrs of proved+potential
cover at the 2045 rate). Writes outputs/reserves_depletion.csv and
outputs/figures/Reserves_Depletion.png. Headline: USA, Mexico and Argentina
(Latin America) extract well beyond their PROVED reserves, i.e. their growth
depends on converting unconventional *potential* (shale) into production — the
core resource-pressure story; the US and South Asia also have the shortest
proved+potential cover.

Known limitation (LNG oversupply): with US LNG must-run to 300 BCM plus the new
exporters, the global LNG market tightens in the 2040s, so the highest-cost /
lowest-priority exporters give way — notably Australia (declines toward ~66 BCM
by 2045) and Sub-Saharan exports to Europe (displaced by US LNG). This is the
expected consequence of contracted US must-run in an oversupplied market, not a
solver error; it can be softened by relaxing `US_LNG_UTIL` (<1.0) or by making
terminal capacity an endogenous investment.

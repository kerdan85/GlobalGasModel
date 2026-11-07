# Sanity check on the regenerated results (2026-06-22 run)

Checked against the freshly written `outputs/` (run_model 21:26, run_esl 21:30).

## TL;DR
The structural fixes worked — the model now solves cleanly with the US actually
producing. The ESL **differences** (the paper's core result) are internally
consistent and reproducible. **But the absolute 2025 trade volumes overshoot
observed reality by a wide margin**, which breaks the manuscript's calibration
claim and needs a fix before submission.

---

## 1. What is now SOLID ✓

**Solve integrity (run_model, central case).** `RUN_DIAGNOSTICS.txt`:
- Total slack = **0.0**, max |Residual| = **1.1e-13**, every region balances.
- US 2025 production = 1370 (was 0 on slack before the fix). Norway 2045 = 188.
- The new bus-based regional balance closes exactly, including the `Backstop`
  column (coal/demand-curve substitution), e.g. China 2025 Backstop = 214.9.

**ESL results reproducible and consistent.** `esl_results.csv` is now populated
(run_esl works) and matches `esl_results_improved.csv` exactly:

| Year | Displaced | ESL | leak | d_coal | dE_GWP100 | dE_GWP20 |
|---|---|---|---|---|---|---|
| 2030 | 2 | 100% | 2.0 | 2.0 | 24 | 131 |
| 2035 | 23 | 20% | 4.6 | 4.6 | 55 | 301 |
| 2040 | 46 | 19.6% | 9.0 | 9.0 | 108 | 590 |
| 2045 | 66 | 18.8% | 12.4 | 12.4 | 149 | 812 |

**Conditionality now clean & monotonic.** `esl_results_by_regime.csv` (mean
2035–45): tight (0.85) → **15.3%**, central (1.0) → **19.5%**, abundant (1.3) →
**95.4%**. This reproduces the scenario-sweep endpoints and supports the
abstract's "15% tight → 95% abundant, ~20% central" — monotonically, once the
0.70 outlier is excluded (now done in `config.SCENARIO_AXES`).

---

## 2. What is BROKEN — calibration overshoot ✗ (highest priority)

The 2025 baseline does **not** reproduce observed trade. Model vs observed
(observed = the benchmarks already in `data/validation_history.csv`, consistent
with EIA/IEA):

| Quantity (2025) | Model | Observed ~ | Error |
|---|---|---|---|
| **US LNG exports** (USA→US_LNG) | **415** | ~120 | **+245% (×3.5)** |
| US marketed production | 1370 | ~1050 | +30% |
| Europe imports | 440 | ~330 | +33% |
| China imports | 393 (+214 coal backstop) | ~165 | **+138% (×2.4)** |
| Global liquefaction throughput | 1001 | ~550 | +82% (×1.8) |
| US→Mexico pipeline | 50 | ~60 | −17% (ok) |
| Norway exports | 125 | ~115 | +9% (ok) |

The back-cast `validation_results.csv` independently confirms the same biases:
China imports modelled **+123% to +139%** above observed in 2018/2021/2023, and
US→Mexico **+48% to +78%** above observed.

**The manuscript currently claims (Opening, ~line 180):** *"it reproduces
observed 2025 trade — US marketed production and LNG exports, Norwegian and
Canadian flows, Chinese pipeline and LNG imports, and the US→Mexico pipeline —
within its regional resolution … a fidelity that is a precondition for trusting
the counterfactual."* With US LNG at 415 vs ~120 BCM and China at ×2.4, this
sentence is not defensible as written, and Fig. 1 (the 2025 "calibration
baseline") will visibly show implausibly thick US-LNG corridors.

### Root cause of the US-LNG overshoot
In `src/apply_scenario.py`, the **endogenous-LNG branch** does:
```python
if US_LNG_ENDOGENOUS:
    for nm in US_LNG_DEST[year]:
        n.links.loc[nm, "p_nom"] = 500      # every destination, every year
```
So all US-LNG export routes are opened to 500 BCM in **every** year (including
2025), and the liquefaction link `USA_US_LNG` is left extendable with **no
2025 capacity ceiling**. With cheap US tranche gas and a sanctioned Russia, the
optimiser builds ~415 BCM of US LNG in the base year — physically impossible
(actual US liquefaction in 2025 ≈ 140 BCM). The per-year ramp `US_LNG_DEST`
(60/40/30 … for 2025) that *would* constrain this is computed but **overridden**
and unused in the endogenous branch.

### Suggested fix (changes results — your call)
Cap US liquefaction to a realistic build-out, e.g. set `USA_US_LNG`
`p_nom_max` on a ramp ≈ {2025: 140, 2030: 200, 2035: 250, 2040: 290, 2045: 320}
BCM, and/or restore the per-year `US_LNG_DEST` caps instead of the flat 500.
Also review `data/coal_switch.csv` (China's switchable tranche ≈ 430 BCM looks
high and is what inflates China imports). This will lower absolute volumes and
will somewhat change the leak magnitudes, but should *strengthen* credibility;
the ESL ratios are differences and should stay qualitatively similar.

---

## 3. STALE outputs to regenerate

These predate the 21:26 fixes and were produced by the older pipeline:
`scenario_1d.csv` (19:46), `scenario_2d.csv` (19:49), `dual_prices.csv` (19:43),
`uncertainty_montecarlo.csv` (**02:44**), `uncertainty_tornado.csv`. The Monte
Carlo median "57%" and the tornado in the paper therefore are **not** from the
fixed model. After any calibration change, re-run the full set:
```
python run_experiments.py all      # scenarios + uncertainty + validation + dual prices
python run_esl.py                  # esl_results.csv + ESL/emissions figures
python run_model.py                # master CSVs + flow maps
```

---

## 4. Changes applied (calibration fix — option A)

**Model**
- `src/apply_scenario.py`: added `US_LIQ_CAP` and capped the endogenous
  `USA_US_LNG` liquefaction link to a realistic per-year ceiling
  {2025:150, 2030:220, 2035:270, 2040:300, 2045:320} BCM. The base year can no
  longer build ~415 BCM of US LNG. (Persistence is compatible — caps grow
  monotonically and always exceed the carried-forward floor.)
- `data/coal_switch.csv`: replaced the switchable coal-to-gas tranches, which
  previously *exceeded* base demand (China 430→760, i.e. >base), with realistic
  values at ~20–30 % of base demand (China 95→155, etc.). This curbs the China
  ×2.4 import overshoot at its source.
- `src/config.py`: dropped the unstable 0.70 point from the `us_supply_scale`
  1-D sweep so the regenerated Fig. 5 is monotonic.

**Manuscript**
- Trimmed the abstract (~280→~160 words); fixed the stale title in the header
  comment.

## 5. Re-run and verify (please run, then send me the new CSVs)
```
python run_experiments.py all     # scenarios + uncertainty + validation + dual prices
python run_esl.py                 # esl_results.csv + ESL/emissions figures
python run_model.py               # master CSVs + flow maps
```
Then check, from `outputs/`:
1. **`RUN_DIAGNOSTICS.txt`** — total slack still 0, max |Residual| ~0. (Capping
   US LNG could in principle push an importer onto slack; the check will catch it.)
2. **US LNG 2025** (`trade_flows.csv`, USA_US_LNG) — should now be ≤150 (was 415).
3. **China imports 2025** (`regional_balance.csv`) — should fall toward ~180–250
   (was 393); compare with observed ~165.
4. **ESL central** (`esl_results.csv`) — confirm it stays ~20% (2035–45). This is
   the key thing to watch: shrinking the coal-switch headroom *could* change
   leakage if the channel saturates. If ESL moves materially, tell me — that may
   be the more credible number, or we retune `coal_switch.csv`.
5. **`validation_results.csv`** — China/US-Mexico back-cast errors should shrink.

Once you send the regenerated CSVs I'll re-cross-check every manuscript number and
update the text + the calibration claim to match.

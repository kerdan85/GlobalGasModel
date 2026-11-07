# Manuscript review — `manuscript_nature_energy.tex`

Two parts: (1) every quantitative claim checked against the output CSVs, and
(2) an editorial/proofreading pass. Checked on 2026-06-22 against the files in
`outputs/`.

---

## 1. Numbers cross-check

### 1.1 Claims that MATCH the data ✓

Source unless noted: `outputs/esl_results_improved.csv`.

| Claim in text | Manuscript | Data | OK |
|---|---|---|---|
| Displaced US→MX volume by 2045 | "roughly 66 BCM/yr" | 66.0 | ✓ |
| ESL in 2030 | "≈100%" | 100.0 | ✓ |
| ESL 2035 / 2040 / 2045 | "20%, 20%, 19%" | 20.0 / 19.6 / 18.8 | ✓ |
| Central headline ESL | "~20%" | mean 2035–45 = 19.5 | ✓ |
| Leakage when US abundant | "~95%" | `scenario_1d` us_supply_scale=1.3 → 95.4 | ✓ |
| Monte Carlo median | "57%" | 56.8 (n=200) | ✓ |
| Monte Carlo spread | "entire 0–100% range" | min 0, max 100 | ✓ |
| Mexican demand priced out | "23–29 BCM/yr" | MexDemandLoss 23.0 / 29.0 / 23.4 | ✓ |
| Coal displaced abroad | "~2 → ~12 BCM" | 2.0 → 12.4 | ✓ |
| Coal tracks leak one-for-one | stated | leak = d_coal each year | ✓ |
| Net GWP100 by 2045 | "~5 Mt CO₂e" | 148.8 × 0.036 = 5.36 | ✓ |
| Net GWP20 by 2045 | "~29 Mt CO₂e" | 812.2 × 0.036 = 29.2 | ✓ |
| Abundant + high-methane GWP20 | ">130 Mt" | us_supply_scale=1.3 → 3727 × 0.036 = 134 | ✓ |
| Gas lifecycle intensity | "112 / 186 gCO₂e MJ⁻¹" | 56×2.0=112.0 ; 56×3.3125=185.5 | ✓ |
| Coal lifecycle intensity | "100 / 120" | config COAL_CO2 | ✓ |
| ESL invariant to Mexican shale cost | stated | `scenario_1d` mex_shale_cost: 19.5/19.5/19.5; `scenario_2d` flat | ✓ |
| Sensitivity dominated by liquefaction + coal-parity | stated | `tornado` swings: us_lng_capital 80.5, coal_parity 43.6 (largest) | ✓ |
| Sovereignty premium near-zero 2025 | stated | `dual_prices` 2025 = 0.2 | ✓ |

### 1.2 Issues to FIX before submission ✗

**(A) "Monotonic" is contradicted by the data — highest priority.**
Abstract and the *"Leakage is conditional on US export capacity"* section say the
response is *"monotonic and large"* and *"rises from ~15% when tight to ~95% when
abundant."* The actual sweep is **non-monotonic (U-shaped):**

```
us_supply_scale:  0.7    0.85   1.0    1.15   1.3
ESL (%):          62.8   15.3   19.5   68.8   95.4
```

The *tightest* point (0.7) gives **62.8%**, not ~15% — the ~15% minimum is at 0.85.
Figure `Scenario_1d.png` will visibly show this up-tick at the left end and
contradict the "monotonic / 15%→95%" wording. Likely cause: at extreme US
tightness the displaced volume (the ESL denominator) collapses, so the ratio
becomes unstable. Options:
  - Investigate / cap the 0.7 case (probable small-denominator artifact), or
  - Report the band over **0.85–1.3**, where it *is* monotonic (15→20→69→95%), or
  - Reword from "monotonic" to "threshold / non-monotonic" and explain the
    low-tightness spike.

**(B) Provenance & reproducibility mismatch — high priority.**
Methods says *"the ESL driver (`run_esl.py`)"* and *"figures are regenerated from
`outputs/esl_results.csv`."* But:
  - `outputs/esl_results.csv` is **empty**; the live numbers live in
    `esl_results_improved.csv` (produced by `run_experiments.py base`).
  - `run_esl.py` is currently **broken** under `USE_DEPLETION_CURVE=True`: its
    `_solve()` calls `build_network → apply_scenario → solve` but never
    `add_us_supply_curve`, so the US runs entirely on slack (the same bug just
    fixed in `run_model.py`). The cited driver therefore does **not** reproduce
    the paper's numbers.
  Fix: either repair `run_esl.py` (same one-line pipeline patch) and regenerate
  `esl_results.csv`, or change the manuscript to cite `run_experiments.py` /
  `esl_results_improved.csv`. Repairing `run_esl.py` gives the cleaner repro story.

**(C) Tornado disagrees with the "US export capacity" claim.**
`uncertainty_tornado.csv` shows **Swing = 0.0** for `us_supply_scale` (Low=High=100),
and also for `methane_rate` and `lng_penalty`. That contradicts the scenario sweep
(where us_supply_scale is the dominant axis) and the sentence that leakage is
governed "by US export capacity." The tornado baseline appears to sit at a point
where ESL is saturated at 100%, killing those swings. Either don't cite the tornado
for the capacity claim, or re-run it from a non-saturated central baseline.

**(D) Verify the "slack unused" Methods claim.**
Methods: the slack generator *"is verified to remain unused in all solved years."*
The `run_model.py` / `run_esl.py` master outputs currently violate this (US fully on
slack). The experiment pipeline probably satisfies it (`dual_prices` US_price = 4.0,
not the slack cost of 100), but re-verify explicitly after the fixes before letting
the sentence stand.

**(E) Minor — sovereignty premium magnitude.**
Text: premium reaches "several units … by the late 2030s." Data: 2035 = 5.75, but
2040–45 = 15.1. Fine for 2035; consider acknowledging the larger late-period value.

---

## 2. Editorial / proofreading pass

**Blockers for compilation/submission**
- **All `\citep` keys are placeholders** and there is no `references.bib`. The file
  will not compile a bibliography as-is. The "REFERENCES TO FIND" checklist lists 10
  keys (howarth2024, iea_methane_2024, carbonleakage, eia_mexico, sener, pypsa,
  ei_statreview, ipcc_ar6_gwp, Kemfert2022, GURSAN2021) — all must be supplied.
- **Placeholder URLs:** Data availability and Code availability contain
  "[REPOSITORY URL TO ADD]". Must be a real (or anonymized-for-review) link.
- Confirm **Supplementary Table S1** (the 19-region list) actually exists in an SI file.

**Structure / Nature Energy fit**
- **Abstract length:** the abstract is ~280 words in one block. Nature Energy
  abstracts are ~150 words and unreferenced — recommend trimming by roughly half.
- **Stale title in the header comment** (lines 4–5: "From sovereignty to carbon
  leakage…") differs from the actual `\title` ("Energy sovereignty leakage in global
  gas markets…"). Harmless (it's a comment) but tidy it to avoid confusion.
- Figure load (6 main figures) is within Nature Energy norms.

**Wording / clarity**
- Define "model \$/MMBtu-equivalent" once where first used (Fig. emissions / premium).
- A few very long sentences could be split for readability — e.g. the ~5-line
  sentence in "Leakage is conditional on US export capacity," and the methane
  sentence in the abstract.
- "19 regional market nodes": one of the 19 (`US_LNG`) is a virtual export hub with
  zero demand, not a consuming region. Consider "18 demand regions plus a US LNG
  export hub" for precision.
- Internal consistency of the headline figure is good ("~20%", "about one-fifth",
  "20%, 20%, 19%" all agree).
- The claim that US pipeline gas "now meets the majority of Mexican demand" is
  consistent with the model (66 of 90 BCM ≈ 73% in a corrected run).

---

## 3. Suggested next actions
1. Resolve issue (A): decide how to present the non-monotonic capacity sweep.
2. Repair `run_esl.py` (issue B) so the cited driver reproduces the numbers; then
   regenerate `esl_results.csv` and re-confirm the table above.
3. Re-run/re-frame the tornado (issue C) and re-verify "slack unused" (issue D).
4. Fill citations + repository URL; trim the abstract.

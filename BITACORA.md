# Bitácora — GlobalGasModel / Energy Sovereignty Leakage paper

Working logbook so the project can be resumed on any machine. Updated every
session (most recent entry first, below).

---

## Session log (most recent first)

### 2026-10-04 (cont.28) — PyPSA justification, Fig 3 Pacific routing, F5 fix
- Methods: added 2 sentences justifying PyPSA for gas (carrier-agnostic least-cost
  network flow; supplies quadratic costs + sized links + nodal dual prices =
  delivered gas price). Limitations: noted gas hydraulics / contracts / imperfect
  competition abstracted (least-cost = competitive equilibrium).
- Fig 3 (plot_north_america.py): route Asia-Pacific destinations WEST (lon-360) so
  US->Asia exits the Pacific/left, not east across Atlantic. NOTE: inert for the
  current base run (see below) but correct + future-proof.
- DATA CHECK (user Q): in the solved model US LNG exports ONLY to Europe + Latin
  America; US_LNG->Asia = 0 every year. Asia served by Qatar/Australia/Russia/ME/
  Turkmenistan + domestic. This IS the central ESL~0 result (US gas can't beat
  Asian coal OR incumbent suppliers at present prices).
- FIXED INCONSISTENCY: old F5_us_lng_destinations.png (June, orphan code, no longer
  in repo) + its SI caption claimed "shift toward China" -> CONTRADICTED the data.
  Wrote NEW src/plot_us_lng_destinations.py (pandas, reproducible); regenerated F5
  from trade_flows.csv (Europe+Latam only, honest footnote). Rewrote SI fig:lngdest
  caption + intro sentence to the honest "US LNG does not reach Asia under present
  prices; only above the threshold" framing (reinforces thesis).
- SI compiles 21 pp, no undefined refs.


### 2026-10-04 (cont.27) — New title + cover letter + DOI verification
- TITLE (user pick, citation-forward): "Energy sovereignty leakage: import
  substitution can relocate rather than reduce global gas use". Updated in
  manuscript \title, header comment, and SI title.
- Cover letter: retitled; added methane-contingency to finding 3 + a paragraph
  on the PyPSA x Brightway lifecycle-coupling method contribution; filled counts
  (~3000 words, 7 display items + 2 Extended Data). Repo URL + author list still
  user to fill.
- DOI VERIFICATION (web): spot-checked 9 of the from-memory refs. 9/9 DOIs
  CORRECT (Sherwin2024, Gordon2023, Gan2020, Qin2017, Rutherford2021, Omara2022,
  Kholod2020, GreenDenniss2018; RomanWhite2021 metadata confirmed, DOI not shown
  but plausible). Fixed ONE error: Qin2017 author list was wrong -> corrected to
  Qin/Wagner/Scovronick/Peng/Yang/Zhu/Smith/Mauzerall. High confidence in bib.
- Bundle rebuilt. STILL OPEN: repo URL placeholders (x2); user verify main
  compiles on Overleaf (tikz + Extended Data figurename); regenerate flat map
  (python -m src.plot_reserves_map); re-upload full latex/.

### 2026-07-18 (cont.26) — Fix SI figure floats (were landing in reference list)
- Root cause: SI figures/tables used [h] (a suggestion), so LaTeX deferred the
  ones that didn't fit and they piled up at the end, interleaved with the
  bibliography. Same class of bug fixed earlier in the main.
- Fix: forced all SI figures + small tables to [H] (float pkg already loaded):
  14x figure[h] + 1 figure[htbp] + 3 table[h] -> [H]. Now each figure/table
  renders exactly where its discussion is.
- Verified by rendering: pages 18-19 are a clean reference list, NO figures
  interspersed; figures sit with their text. SI compiles 20 pp, no errors/
  undefined refs. Bundle rebuilt.

### 2026-07-18 (cont.25) — Nature Energy compliance pass
- Per user choice: kept params in SI (no main table); moved flowchart + balance
  grid to a new EXTENDED DATA section (ED Fig 1 = flowchart, ED Fig 2 = balgrid;
  \setcounter{figure}{0}+\renewcommand{\figurename}). Main display items now
  7 figures + 2 Extended Data (<=8 limit). Updated in-text refs to "Extended
  Data Fig. 1/2" (hard-coded) + SI mentions.
- Abstract trimmed 231 -> 147 words (<=150).
- Main-text prose trimmed ~3546 -> ~3225 (crude count; real ~3000-3100) via
  compressions across intro, on-pure-economics, threshold, coal channel,
  sovereignty premium, methane, discussion. No results/insight lost.
- Refs 57 (~50 guideline; soft, left as-is).
- Verified: no unresolved refs; SI compiles (all figs/tables cited); bundle
  rebuilt. NOTE: cannot compile main here (sn-jnl only on Overleaf) -> USER must
  verify main compiles: (a) tikz in main preamble, (b) Extended Data \figurename
  renders "Extended Data Fig. 1/2".

### 2026-07-18 (cont.24) — SI citation audit + Nature Energy limits check
- SI: audited every fig/table. 3 were present but not \ref-cited: Fig S4
  (validation back-cast), Fig S7 (uncertainty tornado/MC), Table S4 (validation).
  Added citations + discussion. Now ALL SI figs (S1-S15) + tables (S1-S5) +
  Listing 1 cited and discussed. SI compiles 18 pp, no undefined refs.
- Nature Energy ARTICLE limits check (flagged to user, decisions pending):
  abstract 231 w (limit 150); main text 3847 w (limit 3000); display items
  9 figs (limit 8); refs 57 (~50 guideline). Needs a compliance trim pass +
  a decision on figures (e.g. flowchart -> Extended Data) and whether to add a
  key-parameters table to main.

### 2026-07-18 (cont.23) — Discuss figures as results; thread emissions modelling
- Fig 2 (WorldFlows): now discussed as a MODEL RESULT in the intro -- reproduces
  2025 exporter/importer structure AND projects evolution (Russia->China pivot,
  US/Qatar LNG to Asia, EU LNG up), tested out-of-sample (SI). Not just "baseline".
- Fig 3 (NAflows) + Fig 4 (balgrid): expanded into results in "On pure economics"
  -- US->Mexico pipeline ->0, US Gulf LNG grows but IDENTICAL ref vs sov (freed gas
  not re-routed = key result); balance shows US surplus, Mexico 1:1 substitution,
  Asian coal/import gaps = latent demand freed gas could serve.
- Emissions modelling threaded throughout: flagged in intro (lifecycle coupling),
  strengthened Fig 8 (regemis) paragraph -> relocation of gas = relocation of
  lifecycle emissions; Mexico's carbon counterpart to the sovereignty premium;
  US carries its methane as swing exporter; ties to flowchart (Fig 9). lifecycle
  mentioned 21x, coupling 8x.
- Full check: all 9 figures referenced + discussed; no unresolved refs; body
  ~3850 words. Bundle rebuilt.

### 2026-07-18 (cont.22) — Figure polish: legends + flat map
- Fig 4 (Region_balance_grid) & Fig 8 (Region_emissions_panels): legend moved
  OUT of the overlapping first panel into the BOTTOM-LEFT open space. Trick:
  shift the partial last row RIGHT by the #empty slots so the bottom-left slots
  free up, host the shared legend there (plot_region_panels.py, both grids).
  Regenerated here (pandas/mpl, no solver) -> clean, no overlap.
- Fig 1 (plot_reserves_map.py): switched Robinson (ESRI:54030, curvy) -> FLAT
  equirectangular (native EPSG:4326, identity proj); REMOVED the S.America->Asia
  price-gradient arrow; added soft ocean panel + light graticule for a cleaner
  cartographic look; kept the teal/terracotta/sage palette + hub-price callouts.
  NOTE: needs geopandas (not in sandbox) -> USER must run on their machine:
      python -m src.plot_reserves_map     (regenerates Fig_unconventional_gas_map)
  then re-run build_overleaf.py / re-upload the map PNG.
- All code py_compiles; bundle rebuilt (Fig 4/7/8 refreshed; Fig 1 pending user run).

### 2026-07-18 (cont.21) — regemis -> main; fixed decimal-year x-axis
- Moved Region_emissions_panels (was S16, fig:regemis) into the MAIN text, in the
  methane/climate section (cited; pairs with the coupling flowchart now in main).
  Removed from SI; SI ref -> "shown in the main text". Main figs 8 -> 9, SI 16 -> 15.
- Fixed decimal-year x-axis on ESL_improved_base (main Fig 7): panels showed
  2025.0/2027.5/... . Patched run_experiments.py _plot_base to set integer
  xticks (config.YEARS) + "Year" xlabel (+ save .pdf); regenerated the PNG from
  outputs/esl_results_improved.csv + dual_prices.csv (no solver needed).
- Verified: no dup labels / unresolved refs; SI compiles 18 pp; bundle rebuilt.
  Main figure order now 1 resourcemap, 2 flows, 3 naflows, 4 balgrid, 5 arbitrage,
  6 threshold, 7 ESL/premium, 8 regemis, 9 flowchart.

### 2026-07-18 (cont.20) — Promoted 4 SI figs to main; fixed missing SI figs
- Moved SI figures into the MAIN text (per request): WorldFlows (intro),
  NorthAmericaFlows + Region_balance_grid + Region_demand_panels ("On pure
  economics"). Main figures 4 -> 8; each cited in text. Removed the 4 from the SI
  and rewrote the SI "Regional supply, demand and trade" intro (now keeps
  US-LNG destinations, net-trade, reserves). SI figs 20 -> 16, no dupe labels,
  no dangling refs; SI compiles (19 pp).
- "Missing S8/S9/S10" (Sensitivity_global/toggle, Threshold_logit_vs_leastcost):
  NOT a code problem -- files exist and ARE in latex/outputs/figures/. They were
  missing on Overleaf because an OLDER bundle had been uploaded. FIX = re-upload
  the whole latex/ folder (incl. outputs/figures/, 26 pngs). Bundle rebuilt.

### 2026-07-18 (cont.19) — Full-model logit is UNSTABLE -> quarantined
- Ran tau sweep (0.3/0.6/1.0) of the full 19-region endogenous logit fixed
  point. Result: ESL swings with tau, goes NEGATIVE (tau=0.6 premium 2.0 mean
  ESL = -42%), dE_GWP20 ranges -429..+2377 Mt, up to 7/30 negative rows, and is
  NOT reproducible. Cause: ESL is a tiny difference between two independently-
  converged fixed points, swamped by re-dispatch noise near the parity wall.
  CONCLUSION: not usable; do NOT publish any number/figure from it.
- Actions (avoid future liability):
  * SI: REMOVED the code pointer (src/logit_resolve.py, run_logit_experiment.py)
    that had directed reviewers at the unstable script. Replaced with an honest
    code-free sentence: fully endogenising switching does not stabilise the
    above-threshold MAGNITUDE, consistent with the reported non-convergence ->
    reinforces "we report the threshold, not a percentage".
  * MAIN future-work sentence softened to match (full re-solve "does not yet
    stabilise the magnitude").
  * CODE: prominent "!!! EXPERIMENTAL -- NOT USED FOR ANY PUBLISHED RESULT !!!"
    warning added atop logit_resolve.py and run_logit_experiment.py.
- PUBLISHED robustness evidence = the DETERMINISTIC single-channel reduction
  src/logit_switching.py (SI fig:logit), unchanged. Bundle: 0 references to the
  full-model figure/code; SI 23 pp, no undefined refs.
- For repo release: safe to DELETE src/logit_resolve.py + src/run_logit_experiment.py
  + outputs/esl_logit*.csv + Threshold_fullmodel_logit_vs_leastcost.png if zero
  footprint preferred. build_network's logit branch is dormant (default off);
  revert its coalswitch_override block for a fully clean repo if desired.

### 2026-07-18 (cont.18b) — fix: Spyder --wdir broke data/ paths
- run_logit_experiment failed with FileNotFoundError 'data/coal_switch.csv'
  because Spyder `%runfile ... --wdir` sets cwd to src/, not repo root.
- Added _chdir_repo_root() in logit_resolve.py; called at the top of
  run_counterfactual_logit(), run_logit_experiment.run() and plot_compare().
  Now robust to launch location. Verified compile + plot_compare from src/ cwd.

### 2026-07-18 (cont.18) — FULL-model logit fixed point (code, ready to run)
- Implemented the full 19-region smooth-substitution variant the reviewer asked
  for, as an OUTER FIXED POINT around the existing solve (no LP rewrite):
  * config.py: LOGIT_SWITCHING/LOGIT_TAU(0.6)/LOGIT_MAX_ITER(30)/LOGIT_TOL(1.0)/
    LOGIT_DAMPING(0.5).
  * build_network.py: new backward-compatible arg `coalswitch_override`. When a
    dict {region: switched_BCM} is passed, the switched volume is committed to
    gas (fixed load on the region bus) and the unswitched remainder is isolated
    on its own coal bus -> coal-backstop generation still == unswitched, so
    diag()/ESL/emissions ledger are reused UNCHANGED. Default None = baseline
    least-cost (13 COAL_PARITY_SPREAD tranches). Existing runs unaffected.
  * experiment_core.solve_case: threads coalswitch_override to build_network.
  * NEW src/logit_resolve.py: logit_share, logit_update, fixed_point (injectable
    solve fn -> unit-testable), solve_case_logit (reads delivered price =
    n.buses_t.marginal_price), run_counterfactual_logit (mirrors baseline ESL).
    Self-test (mock price, no solver) CONVERGES: residual 4e-4 BCM. PASSED.
  * NEW src/run_logit_experiment.py: sweeps reliability_premium {0..2.5}, writes
    outputs/esl_logit_by_regime.csv + overlays logit vs least-cost
    (Threshold_fullmodel_logit_vs_leastcost.png). plot_compare() runs standalone.
- Verified here (no solver in sandbox): all modules py_compile OK; fixed-point
  self-test passes; comparison plot renders baseline (threshold ~1.5) with the
  logit curve slot pending the user's run.
- SI: reproducibility pointer added (code paths). No fabricated numbers.
- TO RUN ON YOUR MACHINE (Spyder/terminal, repo root, needs PyPSA+solver):
      python -m src.run_logit_experiment          # full sweep + figure
      python -m src.run_logit_experiment --quick   # premiums {0,1.5,2.5}
  then the overlay figure is ready to drop into the SI (fig slot already worded).
- Bundle rebuilt.

### 2026-07-18 (cont.17) — Threshold robustness under logit (reviewer's key ask)
- NEW `src/logit_switching.py` (pure numpy, no solver): isolates the coal-to-gas
  switching channel and re-expresses it as least-cost step vs smooth LOGIT share
  over the delivered-cost margin m = delivered US LNG - coal parity. Both switch
  on at m=0 (half-plateau crossings +0.32 vs 0.00 $/MMBtu) -> threshold is a
  property of the delivered-cost comparison, not the solver; logit removes the
  discrete jumps (the non-convergent magnitude) without moving the threshold.
  Outputs outputs/logit_threshold.csv + figures/Threshold_logit_vs_leastcost.png.
- SI si:robust: added "The threshold is not an artefact of least-cost tipping"
  paragraph + fig:logit. Framed honestly as a single-channel reduction; full
  19-region endogenous-logit re-solve flagged as remaining extension.
- MAIN: discussion robust/model-dependent para now cites the logit result;
  future-work sentence updated (single-channel confirms threshold; full re-solve
  pending). No fabricated numbers - figure is real (arithmetic).
- Verified: SI compiles (bibtex, 23 pp), fig:logit resolves, no undefined refs.
  Bundle rebuilt.

### 2026-07-18 (cont.16) — Reviewer-#2 hardening (no new data)
- Addressed the skeptical-referee weaknesses by surfacing EXISTING model runs
  and reframing overclaims; no fabricated numbers.
- NEW SI §"Global sensitivity, structural robustness and break-even levers"
  (si:robust): presents sensitivity_global.csv (us_supply_scale |β|0.46, us_gas_cost
  0.22, coal_parity 0.09, lng_penalty 0.06, methane 0.03, us_lng_capital 0.01),
  sensitivity_toggle.csv (elastic-demand off -> ESL 14%; flat supply 4%; pure LP 0),
  and sensitivity_breakeven.csv (premium 2.05 $/MMBtu, supply 0.82x for 25%).
  Two figs (Sensitivity_global/toggle) + Table tab:breakeven.
- MAIN honesty edits: threshold para now cites global SA + breakeven and states
  crossing-location is robust while magnitude is not; carbon price reframed as
  acting via the wall (cleaner levers = premium + supply); elastic-demand
  dependence stated (1% vs 14%); methane result flagged as a transparent
  parametric sensitivity (ecoinvent non-methane + explicit swept CH4);
  one-for-one coal displacement -> delivered-energy basis + efficiency caveat;
  66 BCM = bounding full-phase-out, threshold invariant to substitution depth;
  ESL-vs-carbon-leakage operational distinction added; validation scoped
  (North Atlantic reproduced, Asian volumes stylised -> rely on direction/threshold);
  dropped "pinned by observable prices/any market representation", "genuine
  substitution not artefact", softened critical-minerals to open question.
- Verified: SI compiles (bibtex, 22 pp), no undefined refs/dupe labels; main 57
  cites intact, 4 figures. Bundle rebuilt.
- STILL NEEDS A USER RUN (real reviewer ask, needs solver): one alternative
  substitution rule (e.g. logit shares) to show the THRESHOLD survives a
  non-least-cost representation. Everything else is answered from existing runs.

### 2026-07-18 (cont.15) — Nature Energy editorial pass (concept-forward)
- Reframed the paper around ESL as the contribution, not the PyPSA model.
- **Title:** "Energy sovereignty leakage reshapes global gas use".
- **Abstract:** concept-first rewrite, Mexico demoted to one clause, threshold
  = robust vs magnitude = model-dependent made explicit; ~30% shorter.
- **Intro:** 6 paras -> 4; ESL defined prominently; Mexico moved out of the
  opening to a single test-case paragraph; removed repeated delivered-cost
  statements. Generalised mechanism to "any import-substitution policy".
- **Results:** trimmed repetition (threshold/coal/methane each stated once);
  DELETED the "one of the first ... coupled to a full process-LCA" oversell;
  compressed 'On pure economics' and coal-channel sections.
- **Figures: main cut 10 -> 4** (resourcemap, arbitrage, threshold, emissions).
  Moved to SI: WorldFlows, NorthAmericaFlows, US-LNG destinations, net-trade
  dumbbell, balance grid, reserves (-> si:regions_detail), regional emissions
  (-> si:coupling). Rewired all refs; SI figs 10 -> 17.
- **Discussion:** rewritten to NOT re-narrate results -> why ESL matters, how it
  bridges security + climate literatures, robust vs model-dependent, policy
  (completeness of carbon pricing), future work (smooth substitution, methane
  tracking, ESL for critical minerals/fuels/ammonia). Ends on "a way of seeing".
- Main body ~3800 -> ~2960 words (~22% cut). All 57 main cites preserved
  (relocated, not deleted); NO orphan bib entries; SI compiles (bibtex, 21 pp),
  zero undefined refs/cites. Bundle rebuilt.

### 2026-07-18 (cont.14) — Main text to 56+ references
- Target: main text should carry ~56 high-quality references. Added 21 NEW bib
  entries (bib now 77) + newly cited 2 already-present (Howarth2014,
  worldbank_carbon2023) → **main now cites 57 distinct references** (was 33).
- Grouped citations at shared claims (Nature style): methane budget/erosion
  (Newell2014, Saunois2020, Jackson2020, Howarth2014); carbon-leakage lit
  (FischerFox2012, Bohringer2012, Jakob2021); measurement campaigns
  (Karion2013, Miller2013, Peischl2015, Omara2022); GWP/near-term metric
  (Allen2018, Shindell2012); carbon price (worldbank_carbon2023, Nordhaus2015);
  coal-exit co-benefits vs LNG critique (Rauner2020, Grubert2020,
  GilbertSovacool2017); green-paradox/supply-side (Jensen2015, Harstad2012,
  Asheim2019); modelling reviews (Chang2021, Ringkjob2018, DeCarolis2017).
- Added a few short clauses so grouped cites read naturally, not as dumps.
- Verified: all 57 main cite keys resolve; NO duplicate bib keys; bibtex
  \nocite{*} over all 77 entries compiles with ZERO errors/warnings. Bundle rebuilt.
- Metadata best-effort as before — VERIFY DOIs on Overleaf before submission.

### 2026-07-18 (cont.13) — +30 references (10 main, 20 SI)
- **Added 30 real, high-impact refs** to sn-bibliography.bib (now 56 entries),
  each cited at a relevant point. Metadata best-effort — VERIFY DOIs on Overleaf.
- **Main (10):** Tong2019 (committed emissions/lock-in, intro); McGladeEkins2015
  + Erickson2018 (unextracted resource, economics); Cui2019 (coal fleet lifetimes,
  channel); Gordon2023 (gas-vs-coal at varying methane); Sherwin2024 + Rutherford2021
  (measurement-based US methane); FowlieReguant2018 (carbon-leakage measurement,
  discussion); HorschPyPSAEur2018 + Pfenninger2014 (methods).
- **SI (20):** Wernet2016 (ecoinvent), Mutel2017 + Steubing2020 (Brightway),
  DeCarolis2017 (modelling best practice), Labandeira2017 (demand elasticity),
  GonzalezSalazar2018 + Qin2017 (coal-to-gas), Welsby2021 + GreenDenniss2018
  (supply-side/unextracted), RomanWhite2021 + Skone2019 + Gan2020 (LNG-chain LCA),
  Alvarez2012 + Brandt2014 + Schwietzke2016 + Zhang2020 + Lauvaux2022 (methane
  measurement), Kholod2020 (coal-mine methane), Hoesly2018 + iea_weo2024
  (validation data), + newly cited ipcc_ar6_wg1 (GWP).
- Also added two short SI paragraphs (price-elastic demand; supply-side note).
- **Verified:** all 33 main + 25 SI cite keys resolve to bib entries; SI compiles
  via bibtex to 15 pp, 25 bibitems, ZERO undefined citations. Bundle rebuilt.
- (Pre-existing uncited: Howarth2014, worldbank_carbon2023 — harmless, plainnat
  simply omits them.)

### 2026-07-18 (cont.12) — GGR 2025 benchmark: new figures, citations, SI expansion
- **Read the IGU/Snam/Rystad Global Gas Report 2025** (76 pp). Numbers cross-check
  our assumptions well: HH <$2 (2024) / 3.5–4.5 (2025), TTF ~11, NE Asia ~12–15
  (our $2.5/$10/$12 callouts OK); ~270 Bcm liquefaction to 2030; Mexico = 4th
  importer at 68 Bcm; China largest importer 175 Bcm; coal-to-gas switching in
  2024 US power sector; methane historically under-reported (MMRV/OGMP/MARS).
- **NEW module `src/plot_ggr_style.py`** → 4 Nature-grade panels from OUR data
  (palette matches Fig 1): G1 delivered-to-Asia arbitrage merit-order vs
  coal-parity wall (MAIN, fig:arbitrage), G2 regional demand 2025–45 (SI S1),
  G3 net-trade ranking w/ Mexico+China highlighted (SI), G4 US wellhead supply
  curve + us_supply_scale headroom (SI). Files outputs/figures/GGR_G{1..4}.
- **Main text:** added ggr2025 to bib; G1 figure in the arbitrage section;
  citations at Mexico-68-Bcm (intro), ~270 Bcm + Asian spot band (arbitrage),
  coal-to-gas empirics, methane under-reporting; cross-refs to SI S4 and
  Tables S1/S2. Model-structure now points to Tables S1 & S2.
- **SI restructured into Part I (model details) / Part II (data, validation,
  results)** with dividers. NEW Table S2 = regional composition (countries per
  region, from region_colors _LISTS). NEW §S4 "Market context benchmarked
  against GGR" with G2/G3/G4. NEW §S3 coupling-framework overview (forward-ref).
- **SI preamble fixes (latent bugs):** added `float` (for [H]) and
  `natbib` (\citep was undefined); dropped unused `siunitx`; bib style →
  plainnat. Verified: SI compiles to 13 pp, ALL \citep + cross-refs resolve
  (only the pre-existing TikZ flowchart warns on the sandbox's 2021 PGF —
  fine on Overleaf). Fixed stale coal intensity in Table S3 (100/120→108/126).
- Bundle rebuilt (20 figs incl. 4 new). Upload latex/ contents to Overleaf.

### 2026-07-17 (cont.11) — Final read-through: consistency fixes
- **Full editorial read-through** of manuscript + SI. Fixes applied:
  - SI: removed leftover "Fig.~2-style regional panel" placeholder → now
    "shown in the main-text regional emissions panel".
  - Main: dropped the three "parametric cross-check / cross-checked against a
    transparent parametric inventory" mentions (climate section, Methods ledger,
    limitations) per the standing rule *Brightway is the emissions engine, no
    parametric comparison*. Now framed as ecoinvent/Brightway (IPCC 2021) only;
    the parametric lca.py survives internally as a stage decomposition, cited in
    the SI, not as a validation.
  - Main Methods: "least-cost linear program" → "least-cost optimisation … a
    convex quadratic program" so it agrees with the Supply-curves subsection.
  - src/lca.py: stale docstring totals (112/186, 100/120) → 90/116, 108/126.
- **Still open for the user (not code — manuscript metadata):** two
  `[REPOSITORY URL TO ADD]` placeholders (main §Data/Code, SI end); DOI check on
  the .bib. Numbers verified consistent: gas 89–90/116–117, coal 108/126.
- Bundle rebuilt (latex/). Ready to upload.

### 2026-07-02 (cont.10) — Figure order fixed + methodology flowchart + coupling pseudocode
- **Figure order fixed:** figures were out of sequence (fig 5/6 cited before 3/4)
  because [H] pins to source order but blocks weren't in citation order. Moved
  each figure block to right after its FIRST citation: nettrade+balgrid up to the
  reabsorption paragraph; reserves to the coal-channel section; emissions to the
  sovereignty-premium section; regemis stays last. Verified appearance order ==
  citation order 1..10 exactly.
- **SI: methodology flowchart (TikZ, fig:flowchart)** at the top of the coupling
  section — inputs -> PyPSA build/scenario/solve -> Brightway intensities ->
  couple -> outputs (ESL, per-region emissions, methane-contingent result).
- **SI: PyPSA x Brightway pseudocode (lstlisting, lst:coupling)** — the novel
  coupling as ~20 lines: precompute intensities once, then per-year dispatch ->
  per-region emissions. Added tikz + listings + xcolor to SI preamble; SI title
  synced to new title.
- Bundle rebuilt. Main 10 figs (all [H], in order); SI 7 img + flowchart + code.

### 2026-07-02 (cont.9) — Multi-region figures to MAIN + SI expansion (Nature-grade)
- **Main gained 3 multi-region figures** (all full-width figure*): Region_balance_grid
  (fig:balgrid, economics section), Region_emissions_panels (fig:regemis, climate
  section, showcases the PyPSA x Brightway coupling), and the reserves figure
  upgraded from aggregate Reserves_Depletion -> per-region Region_reserves_panels
  (fig:reserves). Main now 10 figures, ~5.9k words. All cited in text.
- **Added a coupling paragraph to the Main climate section** framing PyPSA x
  Brightway as "one of the first energy-system trade models coupled to a full
  process-LCA at every iteration".
- **SI expanded + deduplicated:** removed main/SI duplicate figures (balance,
  reserves, emissions now only in main; SI keeps demand panels). Rewrote the
  coupling subsection into a DETAILED framework (why linearity makes it exact;
  inventory + the ecoinvent-no-shale-activity point; I_gas=a+b*r eqn with
  per-tech methane; the per-region ledger equation; scope/limitations).
  Filled the validation table with real back-cast numbers (US prod 3-11%, Norway
  4-14%, US LNG exact; US->Mexico + China over-predicted, framed honestly).
- **Numbers synced** in SI emissions intro to 90/117, 108/126.
- Checked: no duplicate labels, no dangling refs, all 10 main figs exist.
- NOTE for user: Figure 1 IS the new map (teal + price arbitrage) on disk; the
  "old map" is Overleaf showing a pre-upload copy -> re-upload latex/. (Robinson
  reprojection didn't take; cosmetic, left as equirectangular.)
- Bundle rebuilt (16 figs across main+SI).

### 2026-07-02 (cont.8) — Clean ecoinvent numbers + coupling redesign (no missing activities)
- **buscar() revealed** ecoinvent 3.9.1 has NO per-tech gas production with
  "natural gas, high pressure" product and NO shale gas activity (gas is a
  co-product of "petroleum and gas production, offshore", ref product=petroleum).
  So per-tech ecoinvent lookups are infeasible -> the paper's resource-type
  methane MUST be an explicit parameter (technology.csv), which is the point.
- **Coupling redesigned:** `lca_link.precompute_intensities()` now builds the
  per-tech intensity table from config (ecoinvent-derived non-methane, from
  lca_brightway.run()) + per-tech CH4 rate from data/technology.csv. NO Brightway
  per-activity lookup -> runs in any env, never crashes on a missing name. US
  shale upstream 33.6/60.4, offshore 20.8/25.1 etc. Tested; emissions_by_region
  + Region_emissions_panels regenerate.
- **Clean ecoinvent numbers adopted** (from lca_brightway.run() with the correct
  US-LNG chain): gas 89/116, coal 108/126 gCO2e/MJ at 2.5% methane (was 103/151,
  122/161 from a stale run). Break-even 3.1% (GWP20) / 5.5% (GWP100). Story
  UNCHANGED (gas<coal at 2.5%, crosses ~3% GWP20).
- **Updated everywhere:** config (GAS_NONMETHANE={74.5,74.5}, GAS_UPSTREAM_CO2=18.4,
  GAS_METHANE_PER_PCT={6.1,16.8}, COAL_CO2={108,126}); gas_lca unchanged formula;
  lca.py stage split (gas 89/116, coal 108/126); manuscript emissions Results +
  Methods ledger (a={74.5,74.5}, I_gas={90,117}, I_coal={108,126}, break-even
  5.5%); SI numbers. Figures regenerated. Bundle 17 figs.

### 2026-07-02 (cont.7) — PyPSA x Brightway coupling + per-region emissions/reserves
- **`src/lca_link.py` (NEW): live PyPSA x Brightway coupling.** Brightway
  (ecoinvent 3.9.1, IPCC 2021) computes a lifecycle intensity per MJ per supply
  archetype ONCE; applied to PyPSA dispatch every solved year -> per-region,
  per-year emissions (GWP100+GWP20). `precompute_intensities()` (Brightway, on
  machine) -> outputs/lca_tech_intensities.csv; `emissions_by_region()/run_all_years()`
  (pandas, has fallback intensities) -> outputs/emissions_by_region.csv. Region
  ledger = upstream(production by tech) + combustion(consumption) + LNG-chain
  (exports) + coal burned; robust node->region map (folds US tranches into USA).
  Tested vs existing outputs.
- **Per-region graphs (`plot_region_panels.py`): +`emissions_grid()`
  (Region_emissions_panels, GWP20 gold / GWP100 teal, from the coupling) and
  +`reserves_grid()` (Region_reserves_panels, % resource consumed, pressure
  flagged). Both tested/rendered.
- **Manuscript reframed to Brightway-as-engine (per user):** dropped the
  parametric-vs-ecoinvent comparison (fig:lcacompare removed from SI); SI now has
  a "PyPSA x Brightway coupling" subsection + per-region emissions figure
  (fig:regemis) and per-region reserves figure (fig:regreserves); Methods gained
  a "PyPSA--Brightway coupling" subsection. Parametric lca.py kept only as an
  internal transparency/stage-decomposition tool.
- TODO on machine: run `precompute_intensities()` (confirm ecoinvent activity
  names for shale/offshore/on-shore gas with buscar()), then run_model.py +
  `src/lca_link.run_all_years()` + `plot_region_panels.run_all()`; rebuild bundle.
- Bundle now 17 figures.

### 2026-07-02 (cont.6) — MAJOR: LCA correction flips the climate result
- **ecoinvent process-LCA ran** (gas_leakage_lca project, ecoinvent 3.9.1,
  IPCC 2021 GWP100/GWP20). It CAUGHT a real bug in the emissions ledger:
  upstream methane was overstated ~2.75x (formula used combustion CO2, 56, as
  the base instead of CH4 THROUGHPUT, 56/2.75~20.4). Also coal was too low
  (ecoinvent adds coal-mine methane).
- **Corrected lifecycle intensities (gCO2e/MJ):** gas 103/151, coal 122/161
  (GWP100/GWP20) at 2.5% methane. So at central methane shale-LNG is BELOW coal
  at BOTH horizons -> coal->gas leakage LOWERS emissions. Break-even: 3.1%
  methane (GWP20), 5.7% (GWP100). Leakage RAISES emissions only at high methane
  (>3%) + GWP20 (the Howarth/measurement-based case).
- **Code fixed:** config.py (GAS_NONMETHANE={88,109}, GAS_METHANE_PER_PCT={6.0,16.8},
  COAL_CO2={122,161}); experiment_core.gas_lca() and esl_metric._gas_lca()
  rewritten to I_gas = a + b*rate; src/lca.py stage values recalibrated (gas
  103/151, coal 122/161). LCA figures regenerated.
- **Manuscript reframed throughout** to a METHANE-CONTINGENT climate result:
  - Title -> "Energy sovereignty leakage relocates gas use, with a
    methane-contingent climate cost".
  - Abstract, opening tension line, emissions Results section (now "The climate
    effect of leakage is contingent on methane"), fig:emissions caption,
    Discussion (green paradox now conditional on methane; asymmetric-pricing
    point sharpened), Methods emissions ledger (new I_gas=a+b*r eqn, ecoinvent-
    grounded), limitations (methane is THE decisive uncertainty), SI emissions
    section (corrected numbers + explicit note on the earlier methane basis).
- Core results UNCHANGED: ESL threshold/conditionality, sovereignty premium on
  Mexico. Only the climate SIGN became contingent (honest + stronger).
- TODO on machine: rerun run_esl/run_carbonsweep so ESL emissions CSVs/figures
  reflect corrected ledger; rerun lca_brightway (clean stage attribution after
  kernel restart) + lca.figure_compare(); rebuild bundle.

### 2026-07-02 (cont.5) — Parametric-vs-ecoinvent LCA comparison figure
- Added `figure_compare()` to `src/lca.py`: reads `outputs/lca_intensities.csv`
  (parametric) and `outputs/lca_brightway_intensities.csv` (ecoinvent) and plots
  the lifecycle totals side by side (gas/coal x GWP100/GWP20) as a robustness
  check. Gracefully plots parametric-only + warns if the ecoinvent CSV is absent.
  → `LCA_parametric_vs_ecoinvent.png`. Wired into SI (`fig:lcacompare`) after the
  decomposition figure. `run()` now also produces it.
- After running `src/lca_brightway.py` on the machine, re-run `src/lca.py` (or
  `figure_compare()`) so the comparison shows both bars, then rebuild the bundle.

### 2026-07-02 (cont.4) — Brightway LCA (matched to materials project) + map redesign
- **`src/lca_brightway.py` rewritten** to mirror the user's materials-project
  Brightway code (`brightway_acv_completo.py`, uploaded): same conventions --
  `resolver_metodos()` (keyword method resolution, now GWP100+GWP20 IPCC 2021),
  deterministic `_find()`, `buscar()`, `CONFIG`/`EI_MAP`, `construir_foreground()`.
  Builds one foreground activity per (fuel, stage) with ecoinvent background +
  explicit CO2/CH4 biosphere flows; outputs stage intensities in the same CSV
  schema as `src/lca.py` (parametric vs ecoinvent = robustness). Optional Monte
  Carlo. RUN ON MACHINE (needs Brightway+ecoinvent). Verify EI_MAP activity names
  and per-MJ amounts (shipping/regas TODO=0) with buscar() before final.
- **Figure 1 redesign** (`plot_reserves_map.py`): (a) Robinson projection
  (ESRI:54030) replacing stretched equirectangular -- annotation coords now
  transformed via `proj()`; (b) distinct teal/terracotta/sage palette +
  purple accent (deliberately unlike the referenced WEC blue/purple original);
  price callouts recolored to match. Needs geopandas -> re-render on machine,
  then rebuild bundle.

### 2026-07-02 (cont.3) — LCA module, Figure 1 arbitrage, float placement
- **LCA (`src/lca.py`, NEW).** Stage-resolved lifecycle GHG intensity of US
  shale-LNG-to-Asia vs Asian coal (extraction, upstream methane, liquefaction,
  shipping, regas, combustion | mining+CMM, transport, combustion). Reproduces
  the ledger EXACTLY (gas 112/186, coal 100/120). → `outputs/lca_intensities.csv`
  + `LCA_stage_decomposition.png`. Wired into SI emissions section (`fig:lca`).
  Decision: NOT full Brightway/ecoinvent (scope/licence); stage dict has a
  `map_to_brightway()` stub for a future full process-LCA.
- **Figure 1 improved.** Added regional hub-price callouts (Henry Hub ~$2.5,
  TTF ~$10, JKM ~$12) + a west-to-east gradient arrow to `plot_reserves_map.py`
  — shows the price arbitrage that drives re-export (ties Fig 1 to the thesis).
  Subtitle updated. (Needs geopandas → re-render on your machine.)
- **Figure placement.** Main-text floats `[t]` → `[htbp]` so figures sit near
  their text (Overleaf). More figures will move to SI as the set grows.
- Rebuilt Overleaf bundle. NOTE: LCA fig + improved Fig 1 need to be
  regenerated on the machine (geopandas) and the bundle re-run to include them.

### 2026-07-02 (cont.2) — Detailed per-region balance figures
- **`src/plot_region_panels.py` extended.** Added `region_balance_grid()`
  (combined figure: per-region stacked supply = production + imports +
  coal/backstop, with demand line; surplus above line = exports) and
  `region_balance_single()` (one standalone chart per region -> outputs/figures/
  regions/balance_{REGION}.png). Tested against existing regional_balance data.
- Wired the combined grid into the SI (replaces the simpler production-vs-demand
  panel, `fig:sdpanels`). Main-text dumbbell (`fig:nettrade`) unchanged.
- Rebuilt Overleaf bundle. Reminder: regenerate all region figures with the
  Week-1 N_MONTECARLO=200 locked run before final.

### 2026-07-02 (cont.) — New studies, comparative figures, Overleaf bundle
- **Policy counterfactual (`src/policy_counterfactual.py`, NEW).** Lifecycle-
  complete carbon price test: sweeps carbon price under asymmetric (coal only)
  vs complete (also charges gas's full lifecycle CO2e) pricing → shows a complete
  price closes the leak. Needed a `gas_carbon_charge` hook in
  `experiment_core.solve_case`. → `outputs/policy_complete_pricing.csv`,
  `Policy_complete_pricing.png`. (Main-figure candidate.)
- **Sensitivity (`src/sensitivity.py`, NEW).** (1) structural feature-toggle
  matrix (depletion/elastic/persistence/quadratic off) → threshold robust;
  (2) tipping-point/break-even table (critical carbon price, reliability premium,
  US capacity); (3) global sensitivity via standardized regression coefficients
  from the existing Monte-Carlo CSV. → Sensitivity_toggle/global figures + CSVs.
- **Comparative region figures (`src/plot_region_panels.py`, NEW).** Reads
  `outputs/regional_balance_{year}.csv`; three small-multiples: demand-by-region
  grid, production-vs-demand grid, and a net-trade dumbbell (2025 vs 2045). Tested
  against existing outputs — all render. Strong SI (dumbbell = main candidate).
- **Overleaf bundle (`build_overleaf.py` + `latex/`, NEW).** Assembles
  `latex/` with the two .tex, the .bib, and every referenced figure (mirrors the
  `outputs/figures/` subpath). Re-run `python build_overleaf.py` after changes,
  upload `latex/` contents. Still need `sn-jnl.cls` + `sn-*.bst` in Overleaf once.
- `run_experiments.py` gained `policy` and `sensitivity` subcommands.
- **STANDING RULE (agreed):** at the end of each session, update BITACORA and
  rebuild the `latex/` bundle.
- Corresponding-author fix: `\author*[1]` (asterisk) so it renders "Corresponding
  author" not "Contributing authors".

### 2026-07-02 — References, narrative, Supplementary + cover letter
- **References (`sn-bibliography.bib`, NEW).** Real reference library (~26 entries)
  from major journals: McJeon 2014 (Nature), Alvarez 2018 (Science), Howarth 2011
  (Nature)/2014/2024, Kemfert 2022 (Nature Energy), Gürsan 2021, Sinn 2008 + van
  der Ploeg 2012 (green paradox), Felder–Rutherford 1993 + Aichele 2015 + Branger
  2014 (carbon leakage), Bordoff 2022, Balcombe 2017, Ocko 2021, PyPSA, IPCC AR6,
  EI Statistical Review 2024, EIA/ARI 2013, Alpízar 2016 + EIA Mexico + SENER.
  Keys match the `\citep` already in the .tex (carbonleakage→Felder,
  greenparadox→Sinn). **Verify DOIs/volumes in Overleaf before submission.**
- **Main narrative.** Added a dedicated Mexico paragraph in the opening (import
  dependence as strategic vulnerability; shale sovereignty; Eagle Ford/Burgos
  continuation; the premium framing) and wove citations through intro/discussion/
  methods (McJeon on "gas abundance ≠ climate benefit"; methane; security; green
  paradox; border-carbon completeness; GWP).
- **Supplementary Information (`supplementary_information.tex`, NEW).** Standalone:
  S1 region table (the Table S1 the Main cites), S2 supply curves + convexity +
  parameter table, S3 validation back-cast, S4 threshold figures, S5 scenario
  response surface, S6 uncertainty (tornado + Monte Carlo), S7 emissions, S8
  data/code. Figure paths → outputs/figures; some table cells are `__` to fill
  from the final locked run.
- **Cover letter (`cover_letter.md`, NEW).** Draft to Nature Energy.
- **Finish-by-end-July plan (4-week):** Wk1 lock numbers (N_MONTECARLO=200, rerun
  all, freeze figures, numbers-consistency pass); Wk2 verify bib + fill SI tables;
  Wk3 polish + package; Wk4 co-author review + submit.
- TODO: run N_MONTECARLO=200 & fill SI/validation cells; verify bib DOIs; fill
  repo URL; confirm author list (Sara Giarola?); align the cover letter/SI titles
  with the current Main title ("Carbon pricing turns energy sovereignty into a
  hidden climate cost"); final read-through.

### 2026-06-28 (latest+3) — title -> "energy sovereignty"; term unified
- Title changed to: **"Carbon pricing turns energy sovereignty into a hidden
  climate cost"** (was "...energy independence..."). Reason: precision +
  consistency with the paper's named concept (energy sovereignty leakage) and
  the running head; "energy independence" was slightly broad for a gas-only study.
- Aligned the two body mentions of "energy independence" -> "energy sovereignty"
  (sovereignty-premium section + fig:emissions caption). Term now uniform;
  gas scope carried by abstract + Methods.

### 2026-06-28 (latest+2) — Main leads; plain-language summary removed
- Removed the plain-language summary entirely (per user). Paper now opens
  straight into the MAIN (headingless introduction, Nature Energy style) — the
  powerful, tone-setting lead.
- Strengthened the Main's opening paragraph: new hook ("Few commodities sit at
  the centre of as many competing imperatives as natural gas...") fusing the
  security + climate framings, closing on a thesis line ("a policy chosen for
  security can... quietly become a policy that warms the planet").
- Verified: 0 plain-language sections; figures 7/7 and equations 5/5 balanced.

### 2026-06-28 (latest+1) — title set, abstract tightened, Discussion hardened
- **Title set to: "Carbon pricing turns energy independence into a hidden
  climate cost."** (\title and header comment both updated; running head
  unchanged.)
- Tightened the abstract (~230 -> ~180 words; states the paradox explicitly).
- **Discussion hardened** against the obvious reviewer pushback: added a
  paragraph framing the result as a SECOND-BEST / ASYMMETRIC-PRICING effect in
  the lineage of the GREEN PARADOX (Sinn). Key line: the leak comes from carbon
  being priced on coal combustion while the competing gas's lifecycle (methane +
  LNG) is unpriced; a lifecycle-complete carbon price would close it. So the
  take-home is about the COMPLETENESS of carbon pricing, not "carbon pricing is
  bad." New citation key `greenparadox` added to the REFERENCES TO FIND list.
- Reviewer-defense notes (for final polish): lean on the dual-GWP hedge for the
  contested Howarth methane/LNG intensities; concede US-LNG-vs-coal parity is
  stylised (contribution is the threshold structure, not today's spot economics).

### 2026-06-28 (latest) — MERGE DONE: manuscript re-written to paper A
- Re-applied the threshold/carbon-price rewrite ("paper A") onto
  `manuscript_nature_energy.tex` via a full-file rewrite, KEEPING the new Fig 1
  resource map (`fig:resourcemap`) and the title. The earlier Framing-B text is
  gone. Verified: 7/7 figure envs + 5/5 equations balanced; every figure
  referenced; ZERO old-framing leftovers ("spare export capacity",
  "supply-tightness", "plateau regime", "median of 57" = 0 hits);
  "carbon price"/"reliability premium" appear 17x.
- What changed vs the Framing-B file: new abstract + plain-language summary;
  intro para reframed to the delivered-cost/threshold mechanism; calibration
  overclaim softened; Results sections = "On pure economics, the freed gas is
  not re-exported" / "Leakage switches on past a reliability or carbon-price
  threshold" / coal-switch channel / sovereignty premium / emissions+paradox;
  fig:conditional(Scenario_1d) -> fig:threshold(ESL_thresholds.png); Methods
  gained "Supply curves and convexity" + "Reliability premium and carbon-price
  axes" (replacing "US supply-tightness regimes"); Limitations now states the
  LP-discreteness (magnitude = range, not point).
- The manuscript now tells ONE story (paper A). Divergence resolved.
- STILL PENDING (unchanged): bibliography (references.bib — hard blocker);
  regenerate figures from locked model incl. ESL_thresholds.png; fill repo URL
  + confirm Supplementary Table S1; restore N_MONTECARLO=200; final read-through.

### 2026-06-28 (later) — DIVERGENCE FOUND: .tex on disk is the OLD framing
- **Read the synced `manuscript_nature_energy.tex`. It is the OLD "Framing B"
  manuscript** (leakage conditional on US export capacity; ~15%→95%; central
  ~20%; Monte-Carlo median 57%; Methods "US supply-tightness regimes /
  plateau"). The earlier threshold/carbon-price rewrite ("paper A") is GONE from
  the file — the OneDrive sync from the other machine overwrote it. Only two
  newer things survived on top: the new TITLE ("…carbon-priced world") and the
  new Fig 1 resource map (`fig:resourcemap`, Fig_unconventional_gas_map.png).
- **Two problems in the current file:** (1) the title promises a carbon-priced
  world but the body never mentions carbon pricing or the reliability premium —
  internal contradiction; (2) Framing B's numbers (~20%, 15–95%, 57%) are the
  pre-calibration-fix ARTIFACTS (broken baseline, US LNG 415 vs ~120 real), and
  the Methods still has the calibration overclaim + obsolete plateau mechanism.
- **Agreed narrative = paper A (threshold).** Grounded in the LOCKED-model runs
  actually seen this session: today ESL≈0–2% (delivered US LNG ~6.6 just above
  coal ~6.5 → freed gas unproduced); switches on past a reliability premium
  (~>1.5 $/MMBtu; ~15% at 2.0) OR a carbon price (~>$20/tCO2; ~40% at $26);
  above threshold large but a RANGE (~10–45%); methane-LNG worse than coal at
  GWP20 → emissions ~6 Mt/yr today, ~120 Mt/yr carbon-priced; paradox = the
  carbon price unlocks the leak; sovereignty premium on Mexico robust.
- **PENDING (next action):** re-apply the paper-A rewrite onto the current file
  (abstract, plain-language summary, results, discussion, methods, captions),
  KEEPING the new Fig 1 and the title; fix Methods calibration claim; replace
  "US supply-tightness regimes" with the reliability-premium + carbon-price axes.
  Claude has the paper-A text and can redo the merge on request.
- Process note: update THIS bitácora every chat (user request).

### 2026-06-28 — Figure 1 (resource map) + conditional-range manuscript pass
- **New Figure 1.** Created `src/plot_reserves_map.py` →
  `outputs/figures/Fig_unconventional_gas_map.{png,pdf}`: publication world map
  of shale-gas TRR + development status, US/Mexico accented. Output path now
  resolves to the project root (cwd-proof; previously dumped into `src/outputs`).
  Inserted into `manuscript_nature_energy.tex` as Figure 1 (`fig:resourcemap`),
  cited in the opening; downstream figures auto-renumber.
- **Manuscript text.** Rewrote the abstract, added a **Plain-language summary**
  section, and updated all Results sections (+ new "sovereignty premium falls on
  Mexico" section) to a **conditional-range** framing: ESL ~15 % (tight US export
  capacity) → ~95 % (abundant); central ~20 %; MexDemandLoss 23–29 BCM; emissions
  positive, sharp at GWP₂₀. Removed the old flat "~100–114 %" claim.
- **Code (earlier in session).** Built Tier-1/Tier-2 modules: `depletion_supply`,
  `elastic_demand`, `persistence`, `validation`, `scenario_matrix`, `dual_prices`,
  `uncertainty`, `experiment_core`, and the `run_experiments.py` orchestrator;
  added the `us_supply_scale` capacity axis (central 1.0).
- **⚠ RECONCILE before submission.** This session frames conditionality on **US
  export capacity** (`us_supply_scale`, 15–95 %). The locked thesis in §2 frames
  it on a **carbon-price / reliability-premium threshold** (10–45 %). These are
  almost certainly the same mechanism (delivered US LNG vs Asian coal price)
  expressed through different levers — pick the headline lever and align the
  abstract, Results and §2 so the paper tells ONE story.
- Still TODO: Discussion + Methods rewrite to the chosen framing; bibliography;
  regenerate figures from the locked model; fill placeholders; `N_MONTECARLO=200`.

**Current repo snapshot (for sync to the other machine):**
- `src/` modules present: apply_scenario, build_network, config, depletion_supply,
  diagnose, dual_prices, elastic_demand, esl_metric, experiment_core,
  export_results, liquefaction_supply, lng_terminals, persistence,
  plot_north_america, plot_reserves_map, plot_results, plot_thresholds,
  plot_world_flows, region_colors, reserves_depletion, scenario_matrix, solve,
  uncertainty, validation.
- Drivers (root): run_model, run_esl, run_carbonsweep, run_highleak,
  run_experiments, plot_thresholds.
- Data added this track: `data/us_supply_curve.csv`, `data/demand_elasticity.csv`,
  `data/validation_history.csv`, `data/demand_history.csv`
  (coal_switch.csv hand-tuned down: China 250→480 over 2025–45).
- `config.py` state (both framings live together): COAL_PARITY=6.5,
  COAL_PARITY_SPREAD 13 steps ±2.0, QUADRATIC_SLOPE=0.8, RELIABILITY_PREMIUM=1.0,
  USE_LIQ_CURVE=True, USE_DEPLETION_CURVE=True, ELASTIC_DEMAND=True,
  CAPACITY_PERSISTENCE=True, SCENARIO_AXES key axis `us_supply_scale`
  [0.7,0.85,1.0,1.15,1.3], **N_MONTECARLO=20 (preview — restore 200)**.
- Manuscript figures wired & captioned: Fig 1 resource map (`fig:resourcemap`),
  WorldFlows, NorthAmericaFlows, F5 LNG destinations, conditional-range
  (`Scenario_1d.png`), central+premium (`ESL_improved_base.png`), Reserves.
- Headline numbers (central run): ESL 100 %→20 %→20 %→19 % (2030–45); conditional
  range 15 %(tight)→95 %(abundant); Monte-Carlo median 57 % (0–100 %);
  emissions +~5 Mt (GWP100) / ~29 Mt (GWP20) per yr by 2045.

**Resume here on the other computer:** sign into the same OneDrive, recreate the
env (§3), restart kernel, run §5 to regenerate outputs, then either (a) reconcile
the two conditionality framings, or (b) do the Discussion + Methods rewrite.

---

## 0. Where to work
- Folder: this one, `…/OneDrive-…/ENERGY_MODELS/PyPSA/Nature_energy/GlobalGasModel`.
- It is OneDrive-synced, so it appears on any machine signed into the same
  OneDrive account. Work in it directly; do not keep a separate copy (avoids
  divergence). Let it finish syncing before and after each session.
- Everything below is run from the repo **root** (this folder).

## 1. One-paragraph status
Paper title: **"Energy sovereignty leakage exposes the hidden climate cost of
import substitution in a carbon-priced world."** The model is **locked** and the
manuscript (`manuscript_nature_energy.tex`) is fully rewritten around the final
thesis. What remains is mechanical: fill the bibliography, regenerate figures
from the locked model, and fill two placeholders (repo URL, Supplementary
Table S1). See §6.

## 2. The thesis (what the paper now argues)
Energy Sovereignty Leakage (ESL) = the share of a sovereignty-driven import cut
that reappears as gas consumption elsewhere. Findings:
1. On pure economics, ESL ≈ 0–2 % — Mexico's substitution genuinely lowers
   global gas use (the freed gas is left unproduced).
2. Leakage is a **threshold**: it switches on only when delivered US LNG is
   pushed below the Asian coal-parity price, by either a **reliability premium**
   importers pay for secure US supply (≳1.5 $/MMBtu) or a **carbon price** on
   coal (≳20 $/tCO₂).
3. Above the threshold, leakage is large but conditional (~10–45 % across runs);
   methane-intensive shale-LNG makes it a net emitter under GWP₂₀. Report this
   as a RANGE, not a point estimate.
4. Central paradox: a carbon price, meant to cut emissions, is what unlocks the
   leak.
5. The sovereignty premium (costlier domestic shale) falls on Mexico — robust.

Honest limitation, stated in the paper: this single-period least-cost LP gives a
robust *threshold* but cannot pin the above-threshold *magnitude* (discrete,
market-by-market switching). A smooth-substitution (logit) model would be needed
for a point estimate — a future extension, not attempted.

## 3. Environment setup (on the house laptop)
Recreate the conda env (named `gas_model` on the other machine):

```
conda create -n gas_model python=3.11
conda activate gas_model
pip install pypsa pandas numpy matplotlib highspy
# maps need geospatial libs (conda is most reliable for these):
conda install -c conda-forge geopandas cartopy
# solver: Gurobi if licensed (preferred), else HiGHS (highspy, already installed)
```

`src/config.py` has `SOLVER = "gurobi"` with automatic fallback to HiGHS, so it
runs without a Gurobi licence (just slower). Quadratic costs (see §4) need a
QP-capable solver — both Gurobi and HiGHS handle convex QP.

Quick check it all imports:
```
python -c "import pypsa, geopandas, cartopy, highspy; print('ok')"
```

## 4. The LOCKED model — do not retune these
After ~14 calibration/structural iterations, these are settled. Changing them
reopens the instability we spent the session resolving.

In `src/config.py`:
- `QUADRATIC_SLOPE = 0.8`  ← strict-convexity; 2.0 broke the baseline, 0 is bimodal. Keep 0.8.
- `USE_LIQ_CURVE = True`   ← rising-cost US liquefaction curve (src/liquefaction_supply.py)
- `RELIABILITY_PREMIUM = 1.0`  ← central security premium ($/MMBtu); key axis
- `COAL_PARITY = 6.5`, `COAL_PARITY_SPREAD` = 13 steps over ±2.0
- `USE_DEPLETION_CURVE = True`, `ELASTIC_DEMAND = True`, `CAPACITY_PERSISTENCE = True`
- `SCENARIO = "sovereignty"`
- `N_MONTECARLO` — currently **20** (a fast PREVIEW value). **Restore to 200**
  before the final paper run so the Monte Carlo is stable.

Realistic 2025 baseline this produces: US production ~1,120 BCM, US LNG ~150,
Europe imports ~380, China imports ~275, US→Mexico ~66, slack 0, residuals ~0.

## 5. How to reproduce everything (run order)
```
python run_model.py          # core solve: master CSVs, flow maps, RUN_DIAGNOSTICS
python run_esl.py            # esl_results.csv + reliability-premium sweep (esl_results_by_regime.csv)
python run_carbonsweep.py    # carbon_sweep.csv (ESL vs carbon price)
python run_highleak.py       # highleak_scenarios.csv (named high-leak scenarios)
python src/plot_thresholds.py   # outputs/figures/ESL_thresholds.png (the new headline figure)
python run_experiments.py all   # scenarios + uncertainty (SLOW; set N_MONTECARLO=200 first)
```
Sanity check after `run_model.py`: open `outputs/RUN_DIAGNOSTICS.txt` — total
slack must be 0, max|residual| ~0, US 2025 production ~1,100.

## 6. TO DO (what's left before submission)
1. **Bibliography (hard blocker).** Every `\citep` in the .tex is a placeholder
   and there is no `references.bib`, so LaTeX won't compile a reference list. The
   10 keys to find are listed in the "REFERENCES TO FIND" comment block at the
   bottom of the .tex (howarth2024, iea_methane_2024, carbonleakage, eia_mexico,
   sener, pypsa, ei_statreview, ipcc_ar6_gwp, Kemfert2022, GURSAN2021).
   (Claude offered to also strengthen the intro/lit-review prose with real refs —
   user chose to source references personally.)
2. **Regenerate figures from the locked model** (run §5). The manuscript
   references: ESL_thresholds.png (new), WorldFlows_AllPeriods, NorthAmericaFlows_AllPeriods,
   F5_us_lng_destinations, ESL_improved_base, Reserves_Depletion, plus the
   resource map. Captions already match the new threshold framing.
3. **Fill placeholders:** repository URL ("[REPOSITORY URL TO ADD]" in Data/Code
   availability) and confirm Supplementary Table S1 (19-region list) exists.
4. **Restore `N_MONTECARLO = 200`** before the final uncertainty run.
5. Final read-through once figures are in.

## 7. File map (key files)
- `manuscript_nature_energy.tex` — the paper (rewritten).
- `src/config.py` — all switches (see §4).
- `src/build_network.py` — network; US producers skipped under depletion curve; coal-switch spread.
- `src/apply_scenario.py` — per-year policy levers; US_LIQ_CAP (superseded by liq curve).
- `src/depletion_supply.py` — US production cost curve.
- `src/liquefaction_supply.py` — US liquefaction rising-cost curve (replaces single link).
- `src/elastic_demand.py` — price-elastic demand + coal-switch handling.
- `src/experiment_core.py` — `solve_case` (the canonical build), `run_counterfactual`; applies reliability premium + quadratic convexity. **Single source of truth** used by run_model/run_esl/run_experiments.
- `src/export_results.py` — writes outputs; bus-based regional balance (closes exactly).
- `src/plot_thresholds.py` — new threshold figure (location-independent).
- Drivers: `run_model.py`, `run_esl.py`, `run_carbonsweep.py`, `run_highleak.py`, `run_experiments.py`.
- Working docs: `manuscript_review_notes.md`, `sanity_check_findings.md`,
  `ESL_investigation_summary.md` (the full 14-iteration story).

## 8. Gotchas learned this session
- `run_model.py` and `run_esl.py` MUST build via `experiment_core.solve_case`,
  not bare build_network→apply_scenario→solve, or the US runs on slack (the
  original bug). Already fixed; don't revert.
- coal_switch.csv is read WITHOUT `comment=` → keep it comment-free.
- Don't chase a smooth ESL magnitude by tuning — it's structural. The threshold
  is the result.
- The original draft's clean "~20%" leakage was an artifact of an unrealistic
  baseline (US LNG 415 vs ~120 real). Gone now.

---
Next obvious step on the laptop: run §5 to regenerate outputs/figures from the
locked model, then work the bibliography.

---
## cont.29 — Contracted US LNG floor to NE Asia (realism fix)
Reviewer-realism gap caught by IGK: base case showed US->Asia LNG = 0, but the
US is the world's largest LNG exporter and sent ~26% (2023) / 33% (2024) of its
LNG to Asia; Japan & S. Korea were the 4th/5th-largest destinations (~0.8 Bcf/d
each). Zero-Asia was a single-shot least-cost artifact (US loses the Asian spot
race to Qatar/Australia, so all US cargoes went to Europe+LatAm) — it omits the
long-term destination-flexible SPAs that in reality place US LNG in Japan/Korea.
Fix (`src/apply_scenario.py`): `US_LNG_NEASIA_CONTRACT = {2025:17 ... 2045:45}`
imposed as a must-run FLOOR on `US_LNG_NORTHEAST_ASIA` via p_min_pu computed
from the route's p_nom (floor only; more can flow if economic). Mirrors the
existing RUSSIA_NORTHEAST_ASIA contracted-Sakhalin treatment. NE Asia chosen
deliberately: Japan/Korea are real US contract buyers with little coal-switch
headroom, so the floor restores baseline realism WITHOUT mechanically triggering
leakage — central ESL≈0 expected to hold. Direction of residual bias is now
honest/conservative: real US LNG in Asian coal markets would, if anything, make
leakage switch on more easily, so the model still does not under-claim risk.
TODO after laptop re-run: regenerate trade_flows.csv + F5; confirm central ESL
unchanged; update fig:lngdest caption + SI intro (US LNG now reaches Europe,
LatAm AND contracted NE Asia, but still not the Chinese coal-switch market under
present prices — that is the ESL point).

### cont.29 — RESULT (re-run 2026-10-04, laptop)
Re-ran run_model.py + run_esl.py with the NE Asia contracted floor. Confirmed:
- US LNG by dest now: Europe 41/30/0/0/0, LatAm 92/105/117/126/92,
  NE Asia 17/25/32/40/45 (exactly the contracted floor -> US LNG still not
  competitive in Asia beyond contract). China still 0. Mass-balance clean
  (max|resid| 4.6e-08, slack 0).
- Central ESL (reliability premium = 1.0) unchanged: 1.5% mean 2035-2045;
  per-year ESL_pct 1.5/1.4/1.7 (was 1.4/1.5). d_coal still ~0 in central case.
  Threshold structure intact (premium 0 -> 11.4%, crossings at 1.5/2.0).
=> Baseline realism fixed, headline untouched. Updated fig:lngdest caption +
SI intro sentence + plot_us_lng_destinations.py docstring/footnote to the new
narrative (US LNG serves Europe/LatAm/contracted NE Asia, but not the Chinese
coal-switch market under present prices = the ESL point). Main text unaffected
(no US-LNG-not-Asia claim there). DONE.

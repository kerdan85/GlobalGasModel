# ESL investigation — full summary and honest assessment

After fixing the model so it solves correctly (US producing, slack 0, balances
closing), we tried to recover a robust, realistic estimate of Energy Sovereignty
Leakage. Eight calibration/structural iterations follow, with the central ESL
each produced.

## What we changed and what ESL did

| # | Configuration | US LNG 2025 | Central ESL (2035–45) | Verdict |
|---|---|---|---|---|
| 0 | Original draft (cheap liquefaction, uncapped US LNG, coal-switch > base demand) | **415** (3.5× real) | ~20%, smooth | baseline unreal |
| 1 | Realistic US-LNG cap + realistic coal-switch | 150 | **0** | leak vanished |
| 2 | Intermediate coal-switch (hard cap) | 150 | 0 (cap binds) | bimodal off |
| 3 | Raised hard cap | 150 | 0/0/0/84/64 | bimodal |
| 4 | Liquefaction cost-curve, cheap tolling | 150 | 0/0/60/100/100 | tolling too low |
| 5 | Liquefaction cost-curve, **realistic** tolling | 150 | **0** | leak vanished |
| 6 | + reliability premium = 1.0 | 150 | 0/0/0/84/64 | leak returns, erratic |
| 7 | + coal-parity **spread** (smoothing) | 150 | 0/0/0/84/64 | unchanged |

Reliability-premium sweep (iteration 7, by year): premium 0 → 0; 0.5 → 0;
**1.0 → leakage (64–84% in 2040–45)**; **1.5 → 0 again**.

## The two robust findings

1. **Under pure economics, leakage is ~0.** With a realistic 2025 baseline
   (US LNG ≈150 BCM, China imports ≈274, slack 0) and realistic liquefaction
   tolling, delivered US LNG to Asia (≈6.6) sits just *above* the coal-parity
   wall (6.5). Freed Mexican gas cannot profitably displace Asian coal, so it is
   simply not produced. **Mexican import substitution genuinely reduces global
   gas use — no hidden climate cost — on pure economics.**

2. **A reliability premium switches leakage on.** Your mechanism is correct and
   important: if importers pay a security premium for US supply over
   geopolitically-exposed gas (Russia, Iran, Gulf), delivered US LNG drops below
   coal parity and freed gas is re-exported, displacing coal. At a premium of
   ~1.0 $/MMBtu this produces large leakage (64–84%) and real emissions
   (GWP20 ≈ 91–99 Mt CO2e/yr by 2040–45).

## The problem: the magnitude is not robust

The model does **not** yield a stable, smooth, monotonic leakage number. Across
every lever (liquefaction cost, coal-switch size, US-LNG cap, reliability
premium, coal-parity spread) ESL is **bimodal** — essentially 0 or large — and
even **non-monotonic** in the premium (1.0 leaks, 1.5 does not). Diagnosis:

- A **single-period least-cost LP** switches at the margin discretely. Whether
  the freed ~40–66 BCM is exported depends on exactly where the US-LNG tranche
  boundary falls relative to reference demand. When the reference case sits just
  below a tranche edge, freed gas tips it over → large leak; when it sits at the
  edge in both cases (lng_ref == lng_sov) → zero. This is an artifact of
  discrete LP equilibria, not a robust economic signal.
- The non-monotonicity at premium 1.5 (US LNG saturates identically in both
  reference and sovereignty, so the marginal difference disappears) is the same
  degeneracy. It is a red flag that the *magnitude* is not trustworthy.

Neither the liquefaction supply curve nor the coal-parity spread removed this —
because the discreteness is in the LP merit order itself, not in any one input.

## Bottom line
- The **direction** is robust and defensible: leakage is ~0 on pure economics and
  turns on once a reliability premium pushes delivered US LNG below coal parity.
  This is a genuine, novel, policy-relevant **threshold** result, and it matches
  the real-world intuition that countries pay for reliable suppliers.
- A **precise central ESL %** is **not** robustly estimable in this single-period
  LP. The original draft's clean "~20%" was a coincidence of one (unrealistic)
  configuration; it does not survive realistic calibration.

## Options (more parameter tuning is NOT one of them)

A. **Reframe the paper around the threshold + reliability premium.** Headline:
   under pure economics sovereignty substitution does not leak; it leaks only
   when importers' reliability premium for US gas exceeds a threshold, at which
   point a large share is re-exported with a real (short-horizon) climate
   penalty. Report leakage as a *regime* (near-0 vs large) governed by the
   premium, with explicit caveats on the discrete switching. Honest and
   publishable; minimal new modeling.

B. **Change the model structure** to get robust magnitudes: replace the hard LP
   merit order with smooth substitution (e.g. logit/market-share or a convex
   multi-step delivered-cost-vs-coal curve at fine granularity), and/or a
   multi-period investment formulation. This is the rigorous route to a stable
   central ESL but is real work beyond input tweaks.

C. **Reconsider the operational definition of ESL** in this framework — whether a
   single-snapshot trade LP can identify a leakage fraction at all, or whether
   the contribution should be the threshold mechanism rather than a number.

My recommendation: **A** now (it's honest and the reliability-premium framing is
strong), with **B** as a clearly-scoped follow-up if a precise number is
required by reviewers.

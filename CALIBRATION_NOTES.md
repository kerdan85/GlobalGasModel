# Calibration notes

Calibration sources and assumptions for the Energy Sovereignty Leakage (ESL)
global gas-trade model. The model is calibrated to **2025** observations; forward
trajectories (2030–2045) rebase published supply outlooks onto that baseline.
All quantities are in billion cubic metres per year (BCM yr⁻¹) unless noted.

## Baseline trade structure (calibration targets, 2025)

| Quantity | Target | Source |
|----------|--------|--------|
| US marketed gas production | ~1,100 BCM | EIA; Energy Institute Statistical Review |
| US LNG exports (existing capacity) | ~150 BCM | EIA |
| US → Mexico pipeline | ~66 BCM | EIA; Global Gas Report |
| Mexico total gas imports (2024) | ~68 BCM | EIA Mexico; Global Gas Report |
| Norwegian exports | ~110–125 BCM | Energy Institute Statistical Review |

These are reproduced to within roughly 10–25%. At the 19-region resolution some
importing-region totals (notably Chinese imports) are matched only approximately
and are treated as **stylised** in the paper; results rely on the direction and
threshold of the Asian response rather than its calibrated magnitude. An
out-of-sample back-cast against 2018/2021/2023 trade is reported in the
Supplementary Information (`src/validation.py`, `data/validation_history.csv`).

## Key economic parameters (`src/config.py`)

| Parameter | Value | Meaning |
|-----------|-------|---------|
| `US_GAS_COST` | 2.5 | Henry-Hub-class feed cost (model $/MMBtu-equivalent) |
| `COAL_PARITY` | 6.5 | Gas price at which gas displaces coal in Asia |
| `COAL_PARITY_SPREAD` | −2.0 … +2.0 (13 tranches) | Heterogeneous coal fleet around parity |
| US liquefaction tolling | ~2.0–5.0 | Rising-cost tranches (brownfield → expansion) |
| Trans-Pacific shipping | ~1.8 | Added to delivered US LNG into Asia |

Delivered US LNG into Asia ≈ feed (2.3–2.5) + liquefaction (~2.5) + shipping
(~1.8) ≈ 6.6, just above the 6.5 coal-parity wall — which is why leakage is a
threshold phenomenon.

### Contracted LNG floors

Long-term, destination-flexible contracts are imposed as must-run floors so the
baseline reproduces observed trade that a single-shot least-cost solve omits:

- **US → NE Asia** (Japan + Korea long-term SPAs): 17 → 45 BCM over 2025–2045.
  Japan and Korea were the 4th/5th-largest US LNG destinations in 2023 (EIA).
- **Russia → NE Asia** (Sakhalin/Arctic) and **Russia → China** (Power of
  Siberia) are likewise pinned to contracted levels.

## Emissions / life-cycle parameters

Lifecycle intensities are built on a licensed **ecoinvent 3.9.1** background in
Brightway with **IPCC 2021** GWP₁₀₀/GWP₂₀ characterisation, functional unit
1 MJ delivered. The gas intensity is split into a methane-independent part and a
per-percent upstream-methane term so it responds to the swept methane rate:

- Methane-independent intensity `a` ≈ 74.5 gCO₂e MJ⁻¹ (combustion ~56.1 +
  non-methane upstream/LNG-chain CO₂ ~18.4), the same at both horizons.
- Per-percent upstream-methane term `b` = 6.1 (GWP₁₀₀) / 16.8 (GWP₂₀).
- At the central `US_METHANE_RATE = 2.5%`: I_gas = 89.8 (GWP₁₀₀) / 116.5 (GWP₂₀).
- Displaced coal: I_coal = 108 (GWP₁₀₀) / 126 (GWP₂₀), incl. coal-mine methane.
- Shale-LNG and coal break even at ~5.5% methane (GWP₁₀₀) and ~3.1% (GWP₂₀).

US shale upstream methane leakage is swept over **1.5–3.7%** (central 2.5%),
spanning database averages through measurement/satellite-based estimates. This
is the single parameter that determines the climate sign of leakage.

Unit conversion: 1 BCM ≈ 36 PJ, so 1 (gCO₂e MJ⁻¹ × BCM) = 0.036 Mt CO₂e.

## Data sources

- Energy Institute, *Statistical Review of World Energy* (2024).
- US Energy Information Administration (production, LNG exports, Mexico imports).
- International Energy Agency, incl. *Global Methane Tracker* and *WEO 2024*.
- EIA/ARI, *World Shale Gas and Shale Oil Resource Assessment*.
- ecoinvent 3.9.1 (licensed) for life-cycle backgrounds.

Historical emissions cross-checks use standardised inventories (CEDS/Hoesly
et al. 2018). Full input files are in `data/`.

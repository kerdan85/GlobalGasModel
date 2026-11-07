# Energy Sovereignty Leakage (ESL): a global gas-trade model

Code and data for the paper **"Energy sovereignty leakage: gas import
substitution could relocate global emissions to mid-century."**

This repository contains a 19-region, least-cost global gas-trade optimisation
(2025–2045, five-year steps) built on [PyPSA](https://pypsa.org), coupled to a
process life-cycle assessment (ecoinvent 3.9.1 via Brightway). It quantifies
**Energy Sovereignty Leakage** — the fraction of a sovereignty-driven cut in gas
imports that reappears as gas consumption elsewhere — using Mexico's substitution
of US pipeline imports with domestic shale as the test case.

## What the model shows

- Leakage is a **threshold phenomenon**: freed gas stays unproduced while
  delivered US LNG sits above the Asian coal-parity price, and switches on once a
  reliability premium (~1.5 $/MMBtu) or a carbon price (~25 $/tCO₂) pushes it
  below.
- Under present-day economics the central leakage is negligible (~1.7% by 2045).
- The climate sign of any leakage is contingent on the upstream methane rate.

## Requirements

Python 3.10+. Install dependencies with:

```bash
pip install -r requirements.txt
```

The optimisation uses the open **HiGHS** solver by default (no licence needed);
**Gurobi** is used automatically if licensed and installed. The life-cycle
intensities derived from the licensed **ecoinvent 3.9.1** database are cached in
`outputs/`, so the model and every figure reproduce without an ecoinvent licence.

## Reproducing the results

Run from the repository root (paths to `data/` and `outputs/` are relative):

```bash
python run_model.py          # base calibration + trade-flow maps
python run_esl.py            # sovereignty counterfactual -> esl_results.csv
python run_carbonsweep.py    # carbon-price axis -> carbon_sweep.csv
python run_experiments.py    # regime sweep, sensitivity, central-case figure
```

Then regenerate the remaining figures:

```bash
python src/lca_link.py              # per-region lifecycle emissions
python src/plot_region_panels.py    # regional balance + emissions panels
python src/plot_thresholds.py       # threshold figure
python src/plot_us_lng_destinations.py
python src/plot_reserves_map.py     # Fig. 1 (needs geopandas)
python src/plot_north_america.py    # Fig. 3 (needs geopandas + cartopy)
```

> **Spyder users:** set the working directory to the repository root first, then
> run with `runfile("run_model.py", wdir=os.getcwd())`. Do **not** use the green
> Run button — it sets its own working directory and breaks the relative
> `data/` and `outputs/` paths.

## Layout

| Path | Contents |
|------|----------|
| `run_*.py` | Top-level drivers (base run, ESL, carbon sweep, experiments). |
| `src/` | Model build (`build_network`, `apply_scenario`), solve core (`experiment_core`, `solve`), LCA coupling (`lca_brightway`, `lca_link`), sensitivity/uncertainty, and all plotting. |
| `data/` | Calibration inputs (nodes, links, producers, demand, reserves, coal-switching, technology/methane rates, scenarios, validation history). |
| `outputs/` | Solved results (`esl_results.csv`, `carbon_sweep.csv`, …) and figures. |
| `CALIBRATION_NOTES.md` | Calibration sources and assumptions. |

## Data sources

Energy Institute *Statistical Review of World Energy*; US EIA; IEA (incl. Global
Methane Tracker); EIA/ARI world shale assessment. Life-cycle backgrounds from
ecoinvent 3.9.1 with IPCC 2021 GWP₁₀₀/GWP₂₀ characterisation. See
`CALIBRATION_NOTES.md`.

## Citation

If you use this code or data, please cite the paper (citation to be added on
acceptance) and this repository.

## License

Released under the MIT License (see `LICENSE`).

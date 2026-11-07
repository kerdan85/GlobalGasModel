# ==========================================================
# run_esl.py
# Energy Sovereignty Leakage (ESL) experiment — canonical driver.
#
#   python run_esl.py
#
# Runs the reference-vs-sovereignty counterfactual and writes
# outputs/esl_results.csv plus the ESL/emissions figures.
#
# IMPORTANT: this delegates to src.experiment_core.run_counterfactual,
# the SAME routine used by run_experiments.py and (via solve_case) by
# run_model.py. That routine wires in the Tier-1 features set in
# src/config.py — the US depletion-curve supply (add_us_supply_curve),
# price-elastic demand, and capacity persistence. An earlier version of
# this script built the network with build_network -> apply_scenario ->
# solve directly and never called add_us_supply_curve, so under
# USE_DEPLETION_CURVE=True the US had no supply and ran on slack. Using
# run_counterfactual guarantees the numbers here MATCH the rest of the
# pipeline and the manuscript.
#
# Conditionality (leakage depends on how much spare, cost-competitive
# export capacity the displaced supplier has) is shown by re-running the
# counterfactual across US supply-tightness regimes via the
# `us_supply_scale` axis (tight 0.85 .. abundant 1.3), which is the
# mechanism the depletion curve actually exposes — the old binary
# us_plateau flag no longer bites once US supply is a tranche curve.
#
# Outputs (outputs/):
#   esl_results.csv               central case, per year
#   esl_results_by_regime.csv     tight / central / abundant, per year
#   figures/ESL_leakage_contrast.png
#   figures/ESL_emissions.png
# ==========================================================

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.config import YEARS
from src.experiment_core import run_counterfactual

# model-unit emissions (gCO2e/MJ x BCM) -> Mt CO2e   (1 BCM ~ 36 PJ)
_MT = 0.036

# Reliability-premium regimes for the conditionality contrast: how much
# importers value reliable US supply over geopolitically-exposed gas. This is
# the KEY axis -- at premium 0 the model is pure least-cost (leakage ~0); as it
# rises, freed US gas is re-absorbed abroad and leakage emerges.
REGIMES = {"premium 0.0 (pure cost)": 0.0, "premium 0.5": 0.5,
           "premium 1.0": 1.0, "premium 1.5": 1.5,
           "premium 2.0": 2.0, "premium 2.5": 2.5}


def run_esl():
    os.makedirs("outputs/figures", exist_ok=True)

    # ---- central case -> esl_results.csv (the manuscript's source) ----
    print("=" * 60)
    print("ENERGY SOVEREIGNTY LEAKAGE — reference vs sovereignty (central)")
    print("=" * 60)
    central = run_counterfactual({})
    central.to_csv("outputs/esl_results.csv", index=False)
    print(central.to_string(index=False))

    # ---- conditionality: sweep US supply tightness ----
    by_regime = {}
    rows = []
    for label, prem in REGIMES.items():
        df = run_counterfactual({"reliability_premium": prem})
        by_regime[label] = df
        tmp = df.copy()
        tmp.insert(0, "Regime", label)
        tmp.insert(1, "reliability_premium", prem)
        rows.append(tmp)
    pd.concat(rows, ignore_index=True).to_csv(
        "outputs/esl_results_by_regime.csv", index=False)

    # ---- Figure 1: leakage conditional on US supply tightness ----
    fig, ax = plt.subplots(figsize=(8, 5))
    styles = {"premium 0.0 (pure cost)": ("o-", "#1f6fb2"),
              "premium 0.5": ("s--", "#5aae61"),
              "premium 1.0": ("^-.", "#e0a030"),
              "premium 1.5": ("D-", "#d1734a"),
              "premium 2.0": ("v-", "#b2182b"),
              "premium 2.5": ("P-", "#762a83")}
    for label, df in by_regime.items():
        mk, col = styles.get(label, ("o-", "#444444"))
        ax.plot(df["Year"], df["ESL_pct"], mk, color=col, lw=2.1, ms=7, label=label)
    ax.axhline(100, ls=":", color="grey")
    ax.set_ylim(-5, 120)
    ax.set_ylabel("Energy Sovereignty Leakage (%)")
    ax.set_title("Sovereignty leakage is conditional on the US reliability premium")
    ax.legend(title="reliability premium ($/MMBtu)"); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("outputs/figures/ESL_leakage_contrast.png", dpi=300)
    plt.close(fig)

    # ---- Figure 2: emissions ledger (central), dual GWP, in Mt CO2e ----
    fig, ax = plt.subplots(figsize=(8.5, 5))
    ys = list(central["Year"]); w = 1.3
    ax.bar([y - w for y in ys], central["d_coal"], w,
           label="Coal displaced abroad (BCM)", color="#777777")
    ax.bar(ys, central["dE_GWP100"] * _MT, w,
           label=r"Net CO$_2$e, GWP$_{100}$ (Mt)", color="#e0a030")
    ax.bar([y + w for y in ys], central["dE_GWP20"] * _MT, w,
           label=r"Net CO$_2$e, GWP$_{20}$ (Mt)", color="#d1495b")
    ax.axhline(0, color="black", lw=0.6)
    ax.set_ylabel(r"BCM  /  Mt CO$_2$e")
    ax.set_title("Climate consequence of leakage: methane-intensive shale-LNG vs coal")
    ax.legend(fontsize=9); ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig("outputs/figures/ESL_emissions.png", dpi=300)
    plt.close(fig)

    # ---- console summary ----
    print("\nLeakage by regime (mean over 2035-2045):")
    for label, df in by_regime.items():
        sub = df[df["Year"] >= 2035]
        print(f"  {label:>16}: ESL = {sub['ESL_pct'].mean():5.1f}%")
    print("\nESL results written to outputs/esl_results.csv")
    return central


if __name__ == "__main__":
    run_esl()

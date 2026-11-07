#!/usr/bin/env python3
# ==========================================================
# run_experiments.py
#
# One entry point that runs the Tier-1 / Tier-2 experiments and
# writes all CSVs + figures. Run from the model root:
#
#     python run_experiments.py            # everything
#     python run_experiments.py base       # baseline ESL (+ persistence, dual prices)
#     python run_experiments.py validate   # out-of-sample back-cast
#     python run_experiments.py scenarios  # scenario matrix (1d + 2d)
#     python run_experiments.py uncertainty# tornado + Monte Carlo
#
# Notes
#   * Requires PyPSA + a solver (Gurobi or HiGHS); run on your machine.
#   * Feature switches live in src/config.py (USE_DEPLETION_CURVE,
#     ELASTIC_DEMAND, CAPACITY_PERSISTENCE, ...). Defaults reproduce
#     the improved (Tier-1) baseline.
# ==========================================================

import os
import sys
import pandas as pd

from src import config


def run_base():
    """Baseline reference-vs-sovereignty ESL with all Tier-1 features,
    plus capacity-persistence diagnostics and dual (shadow) prices."""
    from src.experiment_core import run_counterfactual, solve_case
    from src.dual_prices import collect_prices

    print("\n=== BASELINE ESL (depletion curve + elastic demand + persistence) ===")
    df = run_counterfactual({})
    df.to_csv("outputs/esl_results_improved.csv", index=False)
    print(df.to_string(index=False))

    # dual prices + sovereignty premium from the sovereignty case
    nets, built = {}, {}
    for year in config.YEARS:
        n, built = solve_case(year, "sovereignty", {}, built)
        nets[year] = n
    prices = collect_prices(nets)
    prices.to_csv("outputs/dual_prices.csv", index=False)
    print("\nSovereignty premium (MX price - US price), by year:")
    print(prices.to_string(index=False))

    _plot_base(df, prices)
    return df


def _plot_base(df, prices):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    years = [int(y) for y in config.YEARS]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
    ax[0].plot(df["Year"], df["ESL_pct"], "o-", color="#b2182b", lw=2)
    ax[0].axhline(100, ls=":", color="grey")
    ax[0].set_title("a  ESL with endogenous supply + elastic demand")
    ax[0].set_ylabel("ESL (%)"); ax[0].set_xlabel("Year"); ax[0].grid(alpha=0.3)
    ax[0].set_xticks(years)
    ax[1].plot(prices["Year"], prices["Sovereignty_premium"], "s-", color="#1f6fb2", lw=2)
    ax[1].axhline(0, color="black", lw=0.6)
    ax[1].set_title("b  Sovereignty premium (MX - US shadow price)")
    ax[1].set_ylabel("price difference (model units)"); ax[1].set_xlabel("Year")
    ax[1].grid(alpha=0.3); ax[1].set_xticks(years)
    plt.tight_layout()
    plt.savefig("outputs/figures/ESL_improved_base.png", dpi=300)
    plt.savefig("outputs/figures/ESL_improved_base.pdf")
    plt.close(fig)


def main():
    os.makedirs("outputs/figures", exist_ok=True)
    what = sys.argv[1] if len(sys.argv) > 1 else "all"

    if what in ("all", "base"):
        run_base()
    if what in ("all", "validate"):
        from src.validation import validate
        print("\n=== OUT-OF-SAMPLE VALIDATION ===")
        validate()
    if what in ("all", "scenarios"):
        from src.scenario_matrix import sweep_1d, sweep_2d
        print("\n=== SCENARIO MATRIX (1D) ===")
        sweep_1d()
        print("\n=== SCENARIO MATRIX (2D heatmap) ===")
        sweep_2d()
    if what in ("all", "uncertainty"):
        from src.uncertainty import tornado, montecarlo
        print("\n=== UNCERTAINTY: TORNADO ===")
        tornado()
        print("\n=== UNCERTAINTY: MONTE CARLO ===")
        montecarlo()
    if what in ("all", "sensitivity"):
        from src.sensitivity import run_all as sensitivity_all
        print("\n=== SENSITIVITY: toggle matrix + tipping points + global ===")
        sensitivity_all()
    if what in ("all", "policy"):
        from src.policy_counterfactual import run as policy_run
        print("\n=== POLICY: lifecycle-complete carbon price ===")
        policy_run()

    print("\nDone. CSVs in outputs/, figures in outputs/figures/.")


if __name__ == "__main__":
    main()

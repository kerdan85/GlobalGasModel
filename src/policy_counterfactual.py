# ==========================================================
# policy_counterfactual.py
#
# The paper's central policy test: does a LIFECYCLE-COMPLETE carbon
# price close the leak?
#
# The leak is driven by ASYMMETRIC pricing -- a carbon price charges
# coal combustion but leaves the upstream methane + LNG-chain emissions
# of the competing gas unpriced, so gas beats coal and is re-exported.
# Here we run, across a carbon-price sweep, two regimes:
#
#   asymmetric : carbon price on coal only (raises the coal-parity wall)
#   complete   : carbon price ALSO applied to the gas's full lifecycle
#                CO2e (methane + LNG + combustion), symmetric across fuels
#
# If the mechanism in the Discussion is correct, ESL rises with the
# carbon price under asymmetric pricing but stays near zero under
# complete pricing -- operationalising the paper's key recommendation.
#
# Outputs: outputs/policy_complete_pricing.csv
#          outputs/figures/Policy_complete_pricing.png
# ==========================================================

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src import config
from src.experiment_core import run_counterfactual, headline_esl, gas_lca

# coal combustion carbon intensity used to convert a carbon price ($/tCO2)
# into a $/MMBtu lift of the coal-parity wall (matches run_carbonsweep).
COAL_TCO2_PER_MMBTU = 0.095
MJ_PER_MMBTU = 1055.0


def _gas_charge_per_dollar(gwp_key="GWP100"):
    """$/MMBtu carbon charge on the leaked gas per $1/tCO2, at its full
    lifecycle intensity (gCO2e/MJ -> tCO2e/MMBtu)."""
    intensity = gas_lca(gwp_key, config.US_METHANE_RATE, config.LNG_EMIS_PENALTY)
    return intensity * MJ_PER_MMBTU / 1.0e6


def run(taus=None, gwp_key="GWP100"):
    os.makedirs("outputs/figures", exist_ok=True)
    taus = taus or [0, 10, 20, 30, 40, 50, 60]
    gc = _gas_charge_per_dollar(gwp_key)      # $/MMBtu per $/tCO2 on gas
    rows = []
    for tau in taus:
        coal_wall = config.COAL_PARITY + COAL_TCO2_PER_MMBTU * tau
        p_asym = dict(coal_parity=coal_wall)
        p_comp = dict(coal_parity=coal_wall, gas_carbon_charge=gc * tau)
        esl_a = headline_esl(run_counterfactual(p_asym))
        esl_c = headline_esl(run_counterfactual(p_comp))
        rows.append(dict(carbon_price=tau,
                         ESL_asymmetric=round(esl_a, 1),
                         ESL_complete=round(esl_c, 1),
                         gas_charge=round(gc * tau, 2)))
        print(f"  tau=${tau}/tCO2: ESL asym={esl_a:.0f}%  complete={esl_c:.0f}%")
    df = pd.DataFrame(rows)
    df.to_csv("outputs/policy_complete_pricing.csv", index=False)
    _plot(df, gwp_key)
    return df


def _plot(df, gwp_key):
    fig, ax = plt.subplots(figsize=(7, 4.6))
    ax.plot(df.carbon_price, df.ESL_asymmetric, "o-", color="#b2182b", lw=2.2,
            ms=7, label="Carbon price on coal only (asymmetric)")
    ax.plot(df.carbon_price, df.ESL_complete, "s--", color="#1f6fb2", lw=2.2,
            ms=7, label="Lifecycle-complete carbon price")
    ax.axhline(0, color="black", lw=0.6)
    ax.set_xlabel(r"Carbon price (\$/tCO$_2$)")
    ax.set_ylabel("Energy Sovereignty Leakage (%)")
    ax.set_title(f"A lifecycle-complete carbon price closes the leak ({gwp_key})")
    ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("outputs/figures/Policy_complete_pricing.png", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    run()

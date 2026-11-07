# ==========================================================
# esl_metric.py
#
# Energy Sovereignty Leakage (ESL) driver with a calibrated,
# dual-GWP lifecycle-emissions ledger.
#
# Runs the reference vs sovereignty counterfactual, AND the
# US-plateau on/off contrast, to show that leakage is
# CONDITIONAL on US supply being constrained.
#
# Per year it reports:
#   * displaced bilateral volume   = US->Mexico(ref) - US->Mexico(sov)
#   * ESL ratio (plateau on & off) = (global gas_sov - gas_ref)/displaced
#   * coal displaced abroad
#   * net lifecycle CO2e change (sov - ref) at GWP100 AND GWP20,
#     counting gas combustion + methane leakage + LNG penalty vs coal.
#
# Outputs (outputs/):
#   esl_results.csv
#   figures/ESL_leakage_contrast.png
#   figures/ESL_emissions.png
# ==========================================================

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.config import (YEARS, US_PRODUCERS, US_METHANE_RATE,
                        GAS_NONMETHANE, GAS_METHANE_PER_PCT, COAL_CO2)
from src.build_network import build_network
from src.apply_scenario import apply_scenario
from src.solve import solve

_LINKS = pd.read_csv("data/links.csv")
_LNG_LINKS = set(_LINKS.loc[_LINKS["Type"].str.upper() == "LNG", "Name"])


def _solve(year, scenario, us_plateau):
    n = build_network(year)
    n = apply_scenario(n, year, scenario=scenario, us_plateau=us_plateau)
    n = solve(n)
    return n


# Lifecycle intensity of the LEAKED molecule (US shale gas exported as LNG),
# gCO2e/MJ, ecoinvent-calibrated: methane-independent part (combustion +
# upstream CO2 + LNG chain) + a per-% upstream-methane term.
def _gas_lca(gwp_key):
    return GAS_NONMETHANE[gwp_key] + GAS_METHANE_PER_PCT[gwp_key] * US_METHANE_RATE


def _diag(n):
    # Classify by node_type so the new generator kinds (us_supply
    # tranches, demand_curve backstops) are accounted for correctly:
    #   gas  = real production (producer + us_supply tranches)
    #   coal = coal-switch backstop served (displaced coal abroad)
    # Slack and demand_curve generators are excluded from "gas".
    gp = n.generators_t.p.sum()
    nt = n.generators["node_type"] if "node_type" in n.generators else None
    gas = coal = 0.0
    for nm in gp.index:
        t = (nt.get(nm) if nt is not None else None)
        if t in ("producer", "us_supply"):
            gas += float(gp[nm])
        elif t == "coal_backstop":
            coal += float(gp[nm])
        elif t == "demand_curve":
            continue
        elif not (nm.endswith("_slack") or nm.endswith("_coal")):
            gas += float(gp[nm])      # fallback for any untagged producer
    us_mex = 0.0
    for l in ("US_GULF_MEXICO", "PERMIAN_MEXICO"):
        if l in n.links.index:
            us_mex += float(n.links_t.p0[l].sum())
    return dict(gas=gas, coal=coal, us_mex=us_mex)


def run_esl():
    os.makedirs("outputs/figures", exist_ok=True)
    rows = []
    esl_by_plateau = {True: {}, False: {}}

    for plateau in (True, False):
        tag = "plateau" if plateau else "noplateau"
        print(f"--- US_PLATEAU = {plateau} ---")
        for year in YEARS:
            ref = _diag(_solve(year, "reference", plateau))
            sov = _diag(_solve(year, "sovereignty", plateau))
            disp = ref["us_mex"] - sov["us_mex"]
            d_gas = sov["gas"] - ref["gas"]
            d_coal = ref["coal"] - sov["coal"]      # coal displaced abroad
            esl = (d_gas / disp * 100.0) if disp > 1e-6 else 0.0
            esl_by_plateau[plateau][year] = esl
            # Emissions attributed to the leakage: extra gas (US shale-LNG)
            # burned, net of coal displaced. Avoids LP re-dispatch noise.
            d_emis100 = d_gas * _gas_lca("GWP100") - d_coal * COAL_CO2["GWP100"]
            d_emis20  = d_gas * _gas_lca("GWP20")  - d_coal * COAL_CO2["GWP20"]
            row = dict(
                Year=year, Plateau=plateau,
                Displaced=round(disp, 1), ESL_pct=round(esl, 1),
                d_global_gas=round(d_gas, 1),
                d_coal_displaced=round(d_coal, 1),
                d_emis_GWP100=round(d_emis100, 1),
                d_emis_GWP20=round(d_emis20, 1),
            )
            rows.append(row)
            print(f"  {year}: displaced={disp:.0f}  ESL={esl:.0f}%  "
                  f"coal_disp={ref['coal']-sov['coal']:.0f}  "
                  f"dCO2e(100/20)={row['d_emis_GWP100']:.0f}/{row['d_emis_GWP20']:.0f}")
    df = pd.DataFrame(rows)
    df.to_csv("outputs/esl_results.csv", index=False)

    # ---- Figure 1: leakage, plateau on vs off ----
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(YEARS, [esl_by_plateau[True][y] for y in YEARS], "o-",
            color="#b22222", lw=2.2, ms=8, label="US at plateau (supply-constrained)")
    ax.plot(YEARS, [esl_by_plateau[False][y] for y in YEARS], "s--",
            color="#1f6fb2", lw=2, ms=7, label="US with spare capacity")
    ax.axhline(100, ls=":", color="grey"); ax.set_ylim(-5, 120)
    ax.set_ylabel("Energy Sovereignty Leakage (%)"); ax.set_xlabel("")
    ax.set_title("Sovereignty leakage is conditional on US supply tightness")
    ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig("outputs/figures/ESL_leakage_contrast.png", dpi=300)
    plt.close(fig)

    # ---- Figure 2: emissions ledger (plateau case), dual GWP ----
    main = df[df.Plateau].set_index("Year")
    fig, ax = plt.subplots(figsize=(8.5, 5))
    ys = list(YEARS); w = 1.3
    ax.bar([y - w for y in ys], main.loc[ys, "d_coal_displaced"], w,
           label="Coal displaced abroad (BCM)", color="#777777")
    ax.bar(ys, main.loc[ys, "d_emis_GWP100"] / 100, w,
           label="Net CO2e change, GWP100 (/100)", color="#e0a030")
    ax.bar([y + w for y in ys], main.loc[ys, "d_emis_GWP20"] / 100, w,
           label="Net CO2e change, GWP20 (/100)", color="#d1495b")
    ax.axhline(0, color="black", lw=0.6)
    ax.set_ylabel("BCM  /  CO2e (x100, model units)")
    ax.set_title("Climate consequence of leakage: methane-intensive shale-LNG vs coal")
    ax.legend(fontsize=8); ax.grid(axis="y", alpha=0.3)
    plt.tight_layout(); plt.savefig("outputs/figures/ESL_emissions.png", dpi=300)
    plt.close(fig)

    print(f"ESL results written. Plateau-on mean leakage = "
          f"{pd.Series(esl_by_plateau[True]).mean():.0f}%, "
          f"plateau-off = {pd.Series(esl_by_plateau[False]).mean():.0f}%.")
    return df


if __name__ == "__main__":
    run_esl()

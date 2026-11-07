# ==========================================================
# run_carbonsweep.py
# Energy Sovereignty Leakage as a function of a CARBON PRICE on coal.
#
#   python run_carbonsweep.py
#
# A carbon price raises the cost of coal, lifting the gas-vs-coal parity
# price. That moves delivered US LNG decisively BELOW coal (off the
# knife-edge at today's prices), so freed US gas robustly displaces coal
# and leakage becomes large AND stable. This sweep traces ESL vs the
# carbon price -- the headline conditionality of the paper.
#
# Coal carbon intensity ~0.095 tCO2 / MMBtu, so a carbon price of $X/tCO2
# raises the coal-parity gas price by ~0.095*X. Reliability premium is
# held at the central 1.0 $/MMBtu.
#
# Output: outputs/carbon_sweep.csv
# ==========================================================

import pandas as pd
from src.experiment_core import run_counterfactual

CO2_PER_MMBTU = 0.095     # tCO2 per MMBtu of coal (approx)
BASE_PARITY = 6.5         # gas-coal parity at zero carbon price
PREMIUM = 1.0             # central reliability premium
PARITIES = [6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5]
_MT = 0.036               # model-unit emissions -> Mt CO2e


def main():
    rows = []
    for cp in PARITIES:
        carbon = round((cp - BASE_PARITY) / CO2_PER_MMBTU)
        print(f"--- coal parity {cp}  (~${carbon}/tCO2) ---")
        df = run_counterfactual({"reliability_premium": PREMIUM, "coal_parity": cp})
        late = df[df["Year"] >= 2035]

        def yr(col, y):
            return float(df.loc[df["Year"] == y, col].iloc[0])

        rows.append(dict(
            coal_parity=cp,
            carbon_price_USD_tCO2=carbon,
            mean_ESL_2035_45=round(late["ESL_pct"].mean(), 1),
            mean_leak_BCM=round(late["leak"].mean(), 1),
            ESL_2035=round(yr("ESL_pct", 2035), 1),
            ESL_2040=round(yr("ESL_pct", 2040), 1),
            ESL_2045=round(yr("ESL_pct", 2045), 1),
            dE_GWP20_2045_Mt=round(yr("dE_GWP20", 2045) * _MT, 1),
        ))

    out = pd.DataFrame(rows)
    out.to_csv("outputs/carbon_sweep.csv", index=False)
    print()
    print(out.to_string(index=False))
    print("\nWritten to outputs/carbon_sweep.csv")
    return out


if __name__ == "__main__":
    main()

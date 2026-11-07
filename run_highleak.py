# ==========================================================
# run_highleak.py
# Scenarios under which Energy Sovereignty Leakage is LARGER.
#
#   python run_highleak.py
#
# Leakage grows when delivered US LNG more easily undercuts Asian coal:
#   * higher reliability premium (geopolitical fragmentation),
#   * higher coal-parity price (a carbon price on coal),
#   * abundant/cheap US gas (more spare export capacity),
#   * a larger switchable Asian coal fleet.
# Each scenario is a parameter set passed to run_counterfactual; the last
# combines all four levers (a fragmented, decarbonising, gas-abundant world).
#
# Output: outputs/highleak_scenarios.csv
# ==========================================================

import pandas as pd
from src.experiment_core import run_counterfactual

# (reliability premium $/MMBtu, coal parity, US supply scale, coal-fleet mult)
SCENARIOS = {
    "baseline (today's prices)":     dict(reliability_premium=1.0),
    "high reliability premium":      dict(reliability_premium=2.0),
    "carbon-priced coal":            dict(reliability_premium=1.0, coal_parity=9.0),
    "abundant US LNG":               dict(reliability_premium=1.0, us_supply_scale=1.3),
    "large Asian coal fleet":        dict(reliability_premium=1.0, coal_demand=1.3),
    "fragmented + decarbonising":    dict(reliability_premium=2.0, coal_parity=9.0,
                                          us_supply_scale=1.3, coal_demand=1.3),
}

_MT = 0.036   # model-unit emissions -> Mt CO2e


def main():
    rows = []
    for name, p in SCENARIOS.items():
        print(f"--- {name}: {p} ---")
        df = run_counterfactual(p)
        late = df[df["Year"] >= 2035]

        def yr(col, y):
            return float(df.loc[df["Year"] == y, col].iloc[0])

        rows.append(dict(
            Scenario=name,
            mean_ESL_2035_45=round(late["ESL_pct"].mean(), 1),
            mean_leak_BCM=round(late["leak"].mean(), 1),
            ESL_2030=round(yr("ESL_pct", 2030), 1),
            ESL_2035=round(yr("ESL_pct", 2035), 1),
            ESL_2040=round(yr("ESL_pct", 2040), 1),
            ESL_2045=round(yr("ESL_pct", 2045), 1),
            dE_GWP20_2045_Mt=round(yr("dE_GWP20", 2045) * _MT, 1),
        ))

    out = pd.DataFrame(rows)
    out.to_csv("outputs/highleak_scenarios.csv", index=False)
    print()
    print(out.to_string(index=False))
    print("\nWritten to outputs/highleak_scenarios.csv")
    return out


if __name__ == "__main__":
    main()

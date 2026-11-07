# ==========================================================
# sensitivity.py
#
# Three referee-facing analyses for the Supplementary Information:
#
#   1. feature_toggle_matrix() -- STRUCTURAL robustness. Re-runs the
#      headline ESL with each modelling choice switched off in turn
#      (depletion curve, elastic demand, capacity persistence, quadratic
#      convexity). Shows the THRESHOLD result survives the modelling
#      decisions (and flags honestly which choice moves the magnitude).
#
#   2. breakeven_table() -- TIPPING POINTS. For each policy lever, the
#      value at which leakage crosses a target level (bisection).
#
#   3. global_sensitivity() -- GLOBAL sensitivity via standardized
#      regression coefficients computed from the existing Monte Carlo
#      sample (outputs/uncertainty_montecarlo.csv). No extra model runs;
#      ranks parameters by their standardized influence on ESL.
#
# Outputs: outputs/sensitivity_toggle.csv / _breakeven.csv / _global.csv
#          outputs/figures/Sensitivity_toggle.png
#          outputs/figures/Sensitivity_global.png
# ==========================================================

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src import config
from src import build_network as _bn
from src.experiment_core import run_counterfactual, headline_esl


# ----------------------------------------------------------
# 1. Structural robustness: toggle each modelling feature off
# ----------------------------------------------------------
def _set_flag(name, value):
    """Set a config flag AND mirror it where a module bound the name at
    import time (build_network binds USE_DEPLETION_CURVE)."""
    old = getattr(config, name, None)
    setattr(config, name, value)
    if name == "USE_DEPLETION_CURVE" and hasattr(_bn, "USE_DEPLETION_CURVE"):
        _bn.USE_DEPLETION_CURVE = value
    return old


def feature_toggle_matrix():
    os.makedirs("outputs/figures", exist_ok=True)
    base = headline_esl(run_counterfactual({}))
    rows = [dict(Configuration="Full model (baseline)", ESL=round(base, 1))]

    toggles = [
        ("USE_DEPLETION_CURVE", False, "No depletion curve (flat US supply)"),
        ("ELASTIC_DEMAND",      False, "No elastic demand"),
        ("CAPACITY_PERSISTENCE", False, "No capacity persistence"),
        ("QUADRATIC_SLOPE",     0.0,   "No quadratic convexity (pure LP)"),
    ]
    for name, off_val, label in toggles:
        old = _set_flag(name, off_val)
        try:
            esl = headline_esl(run_counterfactual({}))
            rows.append(dict(Configuration=label, ESL=round(esl, 1)))
            print(f"  [toggle] {label}: ESL={esl:.0f}%")
        finally:
            _set_flag(name, old)

    df = pd.DataFrame(rows)
    df.to_csv("outputs/sensitivity_toggle.csv", index=False)

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    y = range(len(df))
    ax.barh(list(y), df.ESL, color=["#1f3b57"] + ["#8aa9c2"] * (len(df) - 1))
    ax.axvline(base, ls="--", color="#b2222a", label=f"baseline {base:.0f}%")
    ax.set_yticks(list(y)); ax.set_yticklabels(df.Configuration)
    ax.invert_yaxis(); ax.set_xlabel("Headline ESL (%)")
    ax.set_title("Structural robustness: headline leakage under each modelling choice")
    ax.legend(); ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig("outputs/figures/Sensitivity_toggle.png", dpi=300)
    plt.close(fig)
    return df


# ----------------------------------------------------------
# 2. Tipping points: value of each lever at which ESL crosses a target
# ----------------------------------------------------------
def _esl_at(lever, value):
    """Headline ESL when `lever` is set to `value` (others central)."""
    if lever == "carbon_price":
        p = dict(coal_parity=config.COAL_PARITY + 0.095 * value)
    else:
        p = {lever: value}
    return headline_esl(run_counterfactual(p))


def _bisect(lever, lo, hi, target, tol=1.0, itmax=18):
    """Find the lever value where ESL crosses `target` (assumes increasing)."""
    flo, fhi = _esl_at(lever, lo) - target, _esl_at(lever, hi) - target
    if flo * fhi > 0:
        return None  # no crossing in range
    for _ in range(itmax):
        mid = 0.5 * (lo + hi)
        fmid = _esl_at(lever, mid) - target
        if abs(fmid) < tol:
            return mid
        if flo * fmid <= 0:
            hi = mid
        else:
            lo, flo = mid, fmid
    return 0.5 * (lo + hi)


def breakeven_table(target=25.0):
    levers = [
        ("carbon_price",        0.0, 80.0,  "$/tCO2"),
        ("reliability_premium", 0.0, 2.5,   "$/MMBtu"),
        ("us_supply_scale",     0.7, 1.5,   "x capacity"),
    ]
    rows = []
    for lever, lo, hi, unit in levers:
        crit = _bisect(lever, lo, hi, target)
        rows.append(dict(Lever=lever, Unit=unit,
                         Critical_value=(round(crit, 2) if crit is not None else "no crossing"),
                         Target_ESL_pct=target))
        print(f"  [breakeven] {lever}: crosses {target:.0f}% at "
              f"{crit if crit is None else round(crit,2)} {unit}")
    df = pd.DataFrame(rows)
    df.to_csv("outputs/sensitivity_breakeven.csv", index=False)
    return df


# ----------------------------------------------------------
# 3. Global sensitivity from the existing Monte Carlo sample
#    (standardized regression coefficients; |beta| ranks influence)
# ----------------------------------------------------------
def global_sensitivity(mc_csv="outputs/uncertainty_montecarlo.csv"):
    if not os.path.exists(mc_csv):
        print(f"  [global] {mc_csv} not found -- run uncertainty.montecarlo() first.")
        return None
    d = pd.read_csv(mc_csv)
    params = [c for c in d.columns if c not in ("sample", "ESL")]
    X = d[params].values.astype(float)
    y = d["ESL"].values.astype(float)
    # standardize
    Xs = (X - X.mean(0)) / (X.std(0) + 1e-12)
    ys = (y - y.mean()) / (y.std() + 1e-12)
    # least-squares standardized betas
    beta, *_ = np.linalg.lstsq(Xs, ys, rcond=None)
    r2 = 1.0 - np.sum((ys - Xs @ beta) ** 2) / np.sum(ys ** 2)
    out = (pd.DataFrame({"Param": params, "Std_beta": np.round(beta, 3),
                         "Abs_beta": np.round(np.abs(beta), 3)})
           .sort_values("Abs_beta", ascending=True))
    out.to_csv("outputs/sensitivity_global.csv", index=False)
    print(f"  [global] standardized-regression R^2 = {r2:.2f}")

    fig, ax = plt.subplots(figsize=(7, 4.2))
    colors = ["#b2182b" if b > 0 else "#1f6fb2" for b in out.Std_beta]
    ax.barh(range(len(out)), out.Std_beta, color=colors)
    ax.set_yticks(range(len(out))); ax.set_yticklabels(out.Param)
    ax.axvline(0, color="black", lw=0.6)
    ax.set_xlabel("Standardized regression coefficient (influence on ESL)")
    ax.set_title(f"Global sensitivity of leakage (SRC, R$^2$={r2:.2f})")
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig("outputs/figures/Sensitivity_global.png", dpi=300)
    plt.close(fig)
    return out


def run_all():
    print("--- structural toggle matrix ---");  feature_toggle_matrix()
    print("--- tipping points ---");             breakeven_table()
    print("--- global sensitivity ---");         global_sensitivity()


if __name__ == "__main__":
    run_all()

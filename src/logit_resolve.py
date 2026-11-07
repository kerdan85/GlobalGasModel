# -*- coding: utf-8 -*-
"""
=====================================================================
logit_resolve.py  --  FULL-model coal-to-gas switching by a logit
                      fixed point (smooth inter-supplier substitution)
Ivan Garcia Kerdan (Tec de Monterrey)
=====================================================================
!!! EXPERIMENTAL -- NOT USED FOR ANY PUBLISHED RESULT !!!
The full 19-region endogenous logit fixed point below is NUMERICALLY
UNSTABLE: ESL is a small difference between two independently-converged
fixed points and is swamped by re-dispatch noise (across a tau sweep it
swings sign and is not reproducible). It is retained only as exploratory
code and MUST NOT be used to make any quantitative claim. The published
threshold-robustness check is the deterministic, single-channel reduction
in src/logit_switching.py (Supplementary Fig. "logit"). The pure
fixed-point logic here (logit_share/logit_update/fixed_point) is sound and
unit-tested; the instability is in differencing the full model, not the loop.
=====================================================================
Reviewer robustness (full 19-region version of src/logit_switching.py).

The baseline model resolves the coal-to-gas channel by a least-cost merit
order (build_network's COAL_PARITY_SPREAD tranches: the LP decides which
coal sub-fleets switch). Here we replace that with SMOOTH substitution: each
region's gas-served (switched) volume is set by a LOGIT SHARE of the
delivered gas price, and we iterate to a fixed point:

    switch^(0)                              (initial guess)
    repeat:
        solve the full network with switch^(i) committed to gas
        read delivered gas price p_reg at each coal-switch region (LP dual)
        share_reg   = sigmoid((parity_eff - p_reg) / tau)
        switch^(i+1)= (1-d)*switch^(i) + d * market_reg * share_reg
    until  max_reg |switch^(i+1) - switch^(i)| < tol

Because the switched volume is committed to gas as a fixed load and the
unswitched remainder is isolated on its own coal bus (see build_network),
coal-backstop generation still equals the unswitched volume; diag() and the
ESL / emissions ledger in experiment_core are therefore reused unchanged.

The heavy path (solve_case_logit, run_counterfactual_logit) needs PyPSA + a
solver and is meant to be run in the model environment. The pure fixed-point
logic (fixed_point, logit_share, logit_update) is solver-free and unit-tested
in __main__ with a mock price response.
"""
import os
import numpy as np
import pandas as pd

from src import config


def _chdir_repo_root():
    """Model data/outputs paths are relative to the project root. Spyder's
    `%runfile ... --wdir` sets cwd to src/, which breaks them; force cwd to the
    repo root (the folder containing data/) so the run works from anywhere."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.isdir(os.path.join(root, "data")):
        os.chdir(root)
    return root


# =====================================================================
# Pure logit logic (no solver) -- unit-testable
# =====================================================================
def logit_share(price, parity_eff, tau):
    """Smooth coal->gas switched share at a region: sigmoid((parity - price)/tau).
    price below parity (gas cheap) -> share -> 1; above -> share -> 0."""
    z = (parity_eff - np.asarray(price, dtype=float)) / max(tau, 1e-6)
    return 1.0 / (1.0 + np.exp(-z))


def logit_update(switched, prices, market, parity_eff, tau, damping):
    """One under-relaxed fixed-point step. All args are {region: value} dicts
    (market, switched) or {region: price}; returns the new {region: switched}."""
    new = {}
    for reg, mkt in market.items():
        share = float(logit_share(prices.get(reg, np.inf), parity_eff, tau))
        target = mkt * share
        new[reg] = (1.0 - damping) * switched.get(reg, 0.0) + damping * target
    return new


def fixed_point(solve_and_price, market, parity_eff,
                tau=None, max_iter=None, tol=None, damping=None,
                switched0=None, verbose=True):
    """Iterate the logit switched volumes to a fixed point.

    solve_and_price : callable(switched_dict) -> (objective, prices_dict)
        Solves the system with the given committed switched volumes and returns
        an objective/label and the delivered gas price per region. Injected so
        this loop is testable without a solver.
    market      : {region: switchable_volume_BCM}
    parity_eff  : effective coal-parity price ($/MMBtu); a carbon price raises it.
    Returns (switched_dict, history_list).
    """
    tau = config.LOGIT_TAU if tau is None else tau
    max_iter = config.LOGIT_MAX_ITER if max_iter is None else max_iter
    tol = config.LOGIT_TOL if tol is None else tol
    damping = config.LOGIT_DAMPING if damping is None else damping

    switched = dict(switched0) if switched0 else {r: 0.5 * m for r, m in market.items()}
    history = []
    for it in range(1, max_iter + 1):
        _, prices = solve_and_price(switched)
        new = logit_update(switched, prices, market, parity_eff, tau, damping)
        delta = max((abs(new[r] - switched[r]) for r in market), default=0.0)
        history.append(dict(iter=it, max_delta=round(delta, 3),
                            total_switched=round(sum(new.values()), 1)))
        if verbose:
            print(f"  [logit it{it:02d}] max|Delta switch|={delta:8.3f} BCM  "
                  f"total switched={sum(new.values()):7.1f} BCM")
        switched = new
        if delta < tol:
            break
    return switched, history


# =====================================================================
# PyPSA path (needs solver) -- run in the model environment
# =====================================================================
def _delivered_price(n, reg):
    """Delivered gas price at a region = LP dual of its nodal balance."""
    try:
        return float(n.buses_t.marginal_price[reg].iloc[0])
    except Exception:
        return float("nan")


def _parity_eff(p):
    """Effective coal-parity price: a carbon price is applied in the baseline
    by raising coal parity, so honour p['coal_parity'] if present."""
    return float(p.get("coal_parity", config.COAL_PARITY))


def solve_case_logit(year, scenario, p, built, market, verbose=True):
    """Full-model logit fixed point for one (year, scenario). Returns
    (solved_network, switched_dict, built)."""
    from src.experiment_core import solve_case          # local import: needs PyPSA
    parity_eff = _parity_eff(p)
    last = {}

    def solve_and_price(switched):
        # solve from a *copy* of the persistence state so inner iterations of
        # the same year do not accumulate capacity records
        n, _built = solve_case(year, scenario, p, dict(built),
                               coalswitch_override=switched)
        last["n"], last["built"] = n, _built
        prices = {reg: _delivered_price(n, reg) for reg in market}
        return scenario, prices

    switched, _hist = fixed_point(solve_and_price, market, parity_eff,
                                  verbose=verbose)
    return last.get("n"), switched, last.get("built", built)


def _coal_market(year):
    coal = pd.read_csv("data/coal_switch.csv")
    yc = str(year)
    if yc not in coal.columns:
        return {}
    return {row["Region"]: float(row[yc]) for _, row in coal.iterrows()
            if float(row[yc]) > 0}


def run_counterfactual_logit(p=None, years=None, verbose=True):
    """Reference vs sovereignty under the LOGIT switching rule, over all years.
    Mirrors experiment_core.run_counterfactual (same ESL & emissions ledger),
    but resolves coal-to-gas by the fixed point above."""
    from src.experiment_core import diag, gas_lca        # local import: needs PyPSA
    _chdir_repo_root()                                    # make data/ paths work
    p = dict(p or {})
    years = years or config.YEARS
    mrate = p.get("methane_rate", config.US_METHANE_RATE)
    lpen = p.get("lng_penalty", config.LNG_EMIS_PENALTY)

    built_ref, built_sov = {}, {}
    rows = []
    for year in years:
        market = _coal_market(year)
        if verbose:
            print(f"\n=== {year}: logit fixed point (reference) ===")
        ref, sw_ref, built_ref = solve_case_logit(year, "reference", p, built_ref,
                                                  market, verbose)
        if verbose:
            print(f"=== {year}: logit fixed point (sovereignty) ===")
        sov, sw_sov, built_sov = solve_case_logit(year, "sovereignty", p, built_sov,
                                                  market, verbose)
        dr, ds = diag(ref), diag(sov)
        disp = dr["us_mex"] - ds["us_mex"]
        d_gas_raw = ds["gas"] - dr["gas"]
        mex_loss = ds["mex_sub"] - dr["mex_sub"]
        leak = d_gas_raw + mex_loss
        d_coal = dr["coal"] - ds["coal"]
        esl = (leak / disp * 100.0) if disp > 1e-6 else 0.0
        e100 = leak * gas_lca("GWP100", mrate, lpen) - d_coal * config.COAL_CO2["GWP100"]
        e20 = leak * gas_lca("GWP20", mrate, lpen) - d_coal * config.COAL_CO2["GWP20"]
        rows.append(dict(Year=year, Displaced=round(disp, 1),
                         ESL_pct=round(esl, 1), leak=round(leak, 1),
                         d_coal=round(d_coal, 1),
                         switched_sov=round(sum(sw_sov.values()), 1),
                         switched_ref=round(sum(sw_ref.values()), 1),
                         dE_GWP100=round(e100, 1), dE_GWP20=round(e20, 1)))
    return pd.DataFrame(rows)


# =====================================================================
# Self-test of the fixed point (no solver): a mock in which the delivered
# price RISES with the committed switched volume (more gas demand -> higher
# price -> lower share), which has a unique stable fixed point.
# =====================================================================
def _selftest():
    market = {"CHINA": 480.0, "SOUTH_ASIA": 225.0, "SOUTHEAST_ASIA": 110.0}
    parity_eff = 6.5

    def mock_solve(switched, base=5.6, slope=0.004):
        # price increases with how much has switched (congestion/supply cost)
        prices = {r: base + slope * switched.get(r, 0.0) for r in market}
        return "mock", prices

    sw, hist = fixed_point(mock_solve, market, parity_eff,
                           tau=0.6, max_iter=40, tol=1e-3, damping=0.5,
                           verbose=True)
    print("\nConverged switched volumes (BCM):",
          {k: round(v, 1) for k, v in sw.items()})
    # verify it is a genuine fixed point: recompute shares at the solution
    _, prices = mock_solve(sw)
    resid = max(abs(sw[r] - market[r] * float(logit_share(prices[r], parity_eff, 0.6)))
                for r in market)
    print(f"fixed-point residual (max over regions): {resid:.4f} BCM")
    assert resid < 0.1, "logit fixed point did not converge"
    print("SELF-TEST PASSED")


if __name__ == "__main__":
    _selftest()

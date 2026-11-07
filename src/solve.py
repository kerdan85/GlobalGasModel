# ==========================================================
# solve.py
# ==========================================================

from src.config import SOLVER, FALLBACK_SOLVER


def solve(n):

    print("\nChecking network...")
    n.determine_network_topology()
    n.consistency_check()

    print("Network OK")
    print(f"Buses: {len(n.buses)}")
    print(f"Generators: {len(n.generators)}")
    print(f"Loads: {len(n.loads)}")
    print(f"Links: {len(n.links)}")

    print(f"\nStarting optimization (solver: {SOLVER})...\n")

    try:
        n.optimize(solver_name=SOLVER)
    except Exception as exc:
        print(f"\n! Solver '{SOLVER}' failed ({type(exc).__name__}: {exc}).")
        print(f"! Falling back to open solver '{FALLBACK_SOLVER}'.\n")
        n.optimize(solver_name=FALLBACK_SOLVER)

    return n

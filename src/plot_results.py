# ==========================================================
# plot_results.py
# Global Gas Model
# ==========================================================
#
# NOTE: All plotting code now lives INSIDE plot_results().
# Previously the figure code sat at module level, so it ran
# on import (crashing if outputs/*.csv did not yet exist) and
# plot_results() itself did nothing.
# ==========================================================

import os

import pandas as pd
import matplotlib

# Use a non-interactive backend so figures render without a display
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUTPUT_DIR = "outputs"


def plot_results():
    """Generate summary figures from the master CSV outputs."""

    # ------------------------------------------------------
    # Load master outputs
    # ------------------------------------------------------

    mexico_path = os.path.join(OUTPUT_DIR, "mexico_supply_mix.csv")
    technology_path = os.path.join(OUTPUT_DIR, "technology_mix.csv")
    trade_path = os.path.join(OUTPUT_DIR, "trade_flows.csv")

    # ======================================================
    # FIGURE 1 - MEXICO SUPPLY MIX
    # ======================================================

    if os.path.exists(mexico_path):

        mexico = pd.read_csv(mexico_path)

        cols = [
            c for c in ["Imports", "Conventional", "Shale"]
            if c in mexico.columns
        ]

        if "Year" in mexico.columns and cols:

            mexico = mexico.groupby("Year", as_index=True)[cols].sum()

            fig, ax = plt.subplots(figsize=(8, 5))

            mexico[cols].plot(
                kind="bar",
                stacked=True,
                ax=ax
            )

            ax.set_ylabel("BCM")
            ax.set_xlabel("")
            ax.set_title("Mexico Natural Gas Supply Mix")

            plt.tight_layout()
            plt.savefig(
                os.path.join(OUTPUT_DIR, "Figure1_MexicoSupply.png"),
                dpi=600
            )
            plt.close(fig)
        else:
            print("  ! Skipping Figure 1: expected columns not found.")
    else:
        print(f"  ! Skipping Figure 1: {mexico_path} not found.")

    # ======================================================
    # FIGURE 2 - TECHNOLOGY MIX
    # ======================================================

    if os.path.exists(technology_path):

        technology = pd.read_csv(technology_path)

        needed = {"Year", "Technology", "Production"}

        if needed.issubset(technology.columns):

            pivot = technology.pivot_table(
                index="Year",
                columns="Technology",
                values="Production",
                aggfunc="sum",
                fill_value=0
            )

            fig, ax = plt.subplots(figsize=(8, 5))

            pivot.plot(
                kind="area",
                stacked=True,
                ax=ax
            )

            ax.set_ylabel("BCM")
            ax.set_xlabel("")
            ax.set_title("Global Gas Production by Technology")

            plt.tight_layout()
            plt.savefig(
                os.path.join(OUTPUT_DIR, "Figure2_TechnologyMix.png"),
                dpi=600
            )
            plt.close(fig)
        else:
            print("  ! Skipping Figure 2: expected columns not found.")
    else:
        print(f"  ! Skipping Figure 2: {technology_path} not found.")

    # ======================================================
    # FIGURE 3 - TOP TRADE ROUTES
    # ======================================================

    if os.path.exists(trade_path):

        trade = pd.read_csv(trade_path)

        needed = {"Year", "Route", "Flow"}

        if needed.issubset(trade.columns):

            # Largest routes by total flow across all years
            top_routes = (
                trade.groupby("Route")["Flow"].sum()
                .sort_values(ascending=False)
                .head(10)
                .index
            )

            pivot = trade[trade["Route"].isin(top_routes)].pivot_table(
                index="Year",
                columns="Route",
                values="Flow",
                aggfunc="sum",
                fill_value=0
            )

            fig, ax = plt.subplots(figsize=(9, 5))

            pivot.plot(ax=ax, marker="o")

            ax.set_ylabel("BCM")
            ax.set_xlabel("")
            ax.set_title("Top 10 Trade Routes by Flow")
            ax.legend(
                loc="center left",
                bbox_to_anchor=(1.0, 0.5),
                fontsize=8
            )

            plt.tight_layout()
            plt.savefig(
                os.path.join(OUTPUT_DIR, "Figure3_TradeRoutes.png"),
                dpi=600
            )
            plt.close(fig)
        else:
            print("  ! Skipping Figure 3: expected columns not found.")
    else:
        print(f"  ! Skipping Figure 3: {trade_path} not found.")


if __name__ == "__main__":
    plot_results()
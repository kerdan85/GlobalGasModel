# ==========================================================
# lca.py
#
# Stage-resolved lifecycle assessment (LCA) of the two fuels that
# compete at the leakage margin: US shale gas delivered to Asia as
# LNG, versus the Asian coal it would displace. It decomposes the
# cradle-to-combustion greenhouse-gas intensity into transparent life
# stages and reproduces the aggregate intensities used in the model's
# emissions ledger (I_gas = 90 / 116, I_coal = 108 / 126
# gCO2e/MJ at GWP100 / GWP20; ecoinvent 3.9.1, IPCC 2021).
#
# This is a parametric, process-transparent LCA. It is deliberately
# NOT a full Brightway/ecoinvent process-LCA: for a gas-trade study the
# stage-resolved form is more transparent and needs no proprietary
# background database. The STAGES dict is structured so each stage could
# later be mapped to a Brightway activity + ecoinvent background if a
# full process-LCA is ever wanted (see map_to_brightway() stub).
#
# Sources for stage split: IPCC AR6 (GWP); IEA Global Methane Tracker;
# Howarth (2014, 2024) LNG chain; Alvarez et al. (2018) US methane.
# Values are illustrative-but-calibrated -- verify against the cited
# literature before submission.
#
# Outputs: outputs/lca_intensities.csv
#          outputs/figures/LCA_stage_decomposition.png
# ==========================================================

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIG = os.path.join(_ROOT, "outputs", "figures")
_OUT = os.path.join(_ROOT, "outputs")

# ----------------------------------------------------------
# Stage-resolved intensities, gCO2e per MJ of delivered energy (LHV).
# Each entry: (GWP100, GWP20). Methane stages differ across horizons.
# Totals reconcile to the model's ledger: gas 112/186, coal 100/120.
# ----------------------------------------------------------
# Stage split calibrated to the ecoinvent 3.9.1 process-LCA (src/lca_brightway.py,
# IPCC 2021). Upstream methane uses the CORRECT CH4-throughput basis (~15/42 at
# 2.5%), not the earlier overstated combustion-CO2 basis (42/115.5).
GAS_STAGES = {
    "Upstream \\& LNG-chain (CO$_2$)":   (18.0, 18.0),   # non-methane, ecoinvent US LNG chain
    "Upstream methane leakage":           (15.0, 42.0),   # 2.5% leak, CH4-throughput basis
    "Combustion (CO$_2$)":               (56.0, 56.0),
}   # total ~90 / 116 gCO2e/MJ (ecoinvent 3.9.1)
COAL_STAGES = {
    "Mining \\& coal-mine methane":      (12.0, 30.0),
    "Transport":                          (1.0, 1.0),
    "Combustion (CO$_2$)":               (95.0, 95.0),
}   # total ~108 / 126 gCO2e/MJ (ecoinvent 3.9.1)

STAGE_COLORS = {
    "Upstream \\& LNG-chain (CO$_2$)":   "#c7c7c7",
    "Upstream methane leakage":           "#b2182b",
    "Liquefaction":                       "#e0a030",
    "Shipping \\& boil-off":              "#4a90c2",
    "Regasification":                     "#9ecae1",
    "Combustion (CO$_2$)":               "#5a5a5a",
    "Mining \\& coal-mine methane":      "#b2182b",
    "Transport":                          "#c7c7c7",
}


def totals():
    """Aggregate intensities (gCO2e/MJ) for gas and coal, both horizons."""
    def tot(st, i): return round(sum(v[i] for v in st.values()), 1)
    return {
        "gas":  {"GWP100": tot(GAS_STAGES, 0),  "GWP20": tot(GAS_STAGES, 1)},
        "coal": {"GWP100": tot(COAL_STAGES, 0), "GWP20": tot(COAL_STAGES, 1)},
    }


def write_table():
    os.makedirs(_OUT, exist_ok=True)
    import csv
    path = os.path.join(_OUT, "lca_intensities.csv")
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Fuel", "Stage", "GWP100_gCO2e_per_MJ", "GWP20_gCO2e_per_MJ"])
        for stage, (a, b) in GAS_STAGES.items():
            w.writerow(["Gas (US shale-LNG)", stage.replace("\\&", "&"), a, b])
        for stage, (a, b) in COAL_STAGES.items():
            w.writerow(["Coal (Asian)", stage.replace("\\&", "&"), a, b])
        t = totals()
        w.writerow(["Gas (US shale-LNG)", "TOTAL", t["gas"]["GWP100"], t["gas"]["GWP20"]])
        w.writerow(["Coal (Asian)", "TOTAL", t["coal"]["GWP100"], t["coal"]["GWP20"]])
    return path


def figure():
    os.makedirs(_FIG, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(9, 5), sharey=True)
    for ax, (h, idx) in zip(axes, [("GWP100 (100-year)", 0), ("GWP20 (20-year)", 1)]):
        for col, (fuel, stages) in enumerate([("Shale-LNG\n(US$\\to$Asia)", GAS_STAGES),
                                              ("Coal\n(Asian)", COAL_STAGES)]):
            bottom = 0.0
            for stage, vals in stages.items():
                v = vals[idx]
                if v <= 0:
                    continue
                ax.bar(col, v, 0.62, bottom=bottom, color=STAGE_COLORS[stage],
                       edgecolor="white", linewidth=0.5,
                       label=stage if col == 0 or "Mining" in stage or "Transport" in stage else None)
                bottom += v
            ax.text(col, bottom + 3, f"{bottom:.0f}", ha="center", fontsize=10,
                    fontweight="bold")
        ax.set_xticks([0, 1]); ax.set_xticklabels(["Shale-LNG\n(US$\\to$Asia)", "Coal\n(Asian)"])
        ax.set_title(h, fontsize=11, fontweight="bold")
        ax.set_ylim(0, 205)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].set_ylabel("Lifecycle intensity (gCO$_2$e MJ$^{-1}$)")
    # combined legend (dedup)
    handles, labels = [], []
    for ax in axes:
        for h_, l_ in zip(*ax.get_legend_handles_labels()):
            if l_ not in labels:
                handles.append(h_); labels.append(l_)
    fig.legend(handles, labels, loc="upper center", ncol=4, fontsize=7.5,
               frameon=False, bbox_to_anchor=(0.5, 0.02))
    fig.suptitle("Lifecycle greenhouse-gas intensity by stage: shale-LNG versus coal",
                 fontsize=13, fontweight="bold", x=0.02, ha="left")
    plt.tight_layout(rect=[0, 0.06, 1, 0.94])
    out = os.path.join(_FIG, "LCA_stage_decomposition.png")
    plt.savefig(out, dpi=300); plt.savefig(out.replace(".png", ".pdf"))
    plt.close(fig)
    return out


def _read_totals(csv_path):
    """Read TOTAL rows from an lca intensities CSV -> {(fuel_key): (g100,g20)}."""
    import csv as _csv
    out = {}
    if not os.path.exists(csv_path):
        return out
    with open(csv_path) as fh:
        for row in _csv.DictReader(fh):
            if row["Stage"].strip().upper() == "TOTAL":
                key = "gas" if row["Fuel"].lower().startswith("gas") else "coal"
                out[key] = (float(row["GWP100_gCO2e_per_MJ"]),
                            float(row["GWP20_gCO2e_per_MJ"]))
    return out


def figure_compare():
    """Side-by-side: parametric (src/lca.py) vs ecoinvent-backed
    (src/lca_brightway.py) lifecycle totals. Shows the two independent
    methods agree -- a robustness check for the emissions ledger.
    Needs outputs/lca_brightway_intensities.csv (run lca_brightway on your
    machine first); otherwise it plots the parametric totals only and warns."""
    os.makedirs(_FIG, exist_ok=True)
    para = {"gas": (totals()["gas"]["GWP100"], totals()["gas"]["GWP20"]),
            "coal": (totals()["coal"]["GWP100"], totals()["coal"]["GWP20"])}
    eco = _read_totals(os.path.join(_OUT, "lca_brightway_intensities.csv"))
    if not eco:
        print("  [compare] ecoinvent CSV not found -- run src/lca_brightway.py "
              "first; plotting parametric only.")

    cats = [("Gas GWP100", "gas", 0), ("Gas GWP20", "gas", 1),
            ("Coal GWP100", "coal", 0), ("Coal GWP20", "coal", 1)]
    labels = [c[0] for c in cats]
    pvals = [para[f][i] for _, f, i in cats]
    evals = [eco[f][i] if f in eco else 0.0 for _, f, i in cats]

    import numpy as np
    x = np.arange(len(cats)); w = 0.38
    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    ax.bar(x - w / 2, pvals, w, label="Parametric (this study)", color="#5a5a5a")
    ax.bar(x + w / 2, evals, w, label="ecoinvent (Brightway)", color="#1b6f6b")
    for xi, (p, e) in enumerate(zip(pvals, evals)):
        ax.text(xi - w / 2, p + 2, f"{p:.0f}", ha="center", fontsize=8)
        if e:
            ax.text(xi + w / 2, e + 2, f"{e:.0f}", ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel("Lifecycle intensity (gCO$_2$e MJ$^{-1}$)")
    ax.set_title("Emissions accounting robustness: parametric vs ecoinvent-backed LCA",
                 fontsize=12, fontweight="bold")
    ax.legend(frameon=False); ax.grid(axis="y", alpha=0.3)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    plt.tight_layout()
    out = os.path.join(_FIG, "LCA_parametric_vs_ecoinvent.png")
    plt.savefig(out, dpi=300); plt.savefig(out.replace(".png", ".pdf"))
    plt.close(fig)
    print(f"  compare figure -> {out}")
    return out


def map_to_brightway():
    """STUB. To upgrade to a full process-LCA, map each stage key to a
    Brightway activity keyed on ecoinvent background processes, e.g.
        {"Liquefaction": ("ecoinvent", "natural gas, liquefied"), ...}
    then build an LCA(fu, method) with method = IPCC AR6 GWP100/GWP20.
    Not implemented here (requires Brightway2/25 + an ecoinvent licence)."""
    raise NotImplementedError("Optional full process-LCA via Brightway/ecoinvent.")


def run():
    p = write_table(); f = figure(); figure_compare()
    t = totals()
    print(f"LCA totals (gCO2e/MJ): gas {t['gas']}, coal {t['coal']}")
    print(f"  table -> {p}\n  figure -> {f}")


if __name__ == "__main__":
    run()

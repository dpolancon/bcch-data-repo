"""
Stage:    09 -- Analyze the interregional trade network
Purpose:  Measure the observable part of Chile's interregional trade network --
          the weighted degree sequence and what follows from it -- and state
          precisely which part is not observable from the BCCh API.
Task:     CRSM dataset construction (SHT spatial rent vs resource rent)
Inputs:   data/raw/regional-spatial-macro-dataset/raw_monthly.csv
Outputs:  bcch-data-repo-vault/report1_REG_ECON_DEV/assets/table4_trade_network.csv
          bcch-data-repo-vault/report1_REG_ECON_DEV/assets/fig4_1_trade_openness.png/pdf
          bcch-data-repo-vault/report1_REG_ECON_DEV/assets/fig4_2_trade_balance.png/pdf
          bcch-data-repo-vault/report1_REG_ECON_DEV/assets/fig4_3_trade_vs_rents.png/pdf
Created:  2026-08-22
Updated:  2026-08-22
Owner:    dpolancon
Run:      python scripts/09_analyze_trade_network.py [--year YYYY]

Scope note
----------
BCCh publishes interregional trade only as per-region margins: how much each
region sells to the rest of the country, and how much it buys from it. It does
not publish the origin-destination matrix. For 16 regions that is 32 observed
numbers per period against 240 unobserved bilateral flows.

So this stage measures the network's degree sequence -- which is real -- and
does not report centrality, clustering or community structure, which cannot be
computed from margins without inventing the topology first. See
lib/trade.py::independence_baseline for why maximum entropy does not rescue it.
"""

import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from lib.codes import SECTOR_MINING, SECTOR_REAL_ESTATE
from lib.paths import REPORT1_ASSETS_DIR, ensure_dir
from lib.reporting import export_table_to_csv
from lib.sectors import compute_sector_shares
from lib.trade import IDENTITY_TOL, check_identities, compute_indicators, load_trade_margins

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

ASSETS_DIR = str(ensure_dir(REPORT1_ASSETS_DIR))


def save_fig(name: str) -> None:
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, f"{name}.png"), dpi=300)
    plt.savefig(os.path.join(ASSETS_DIR, f"{name}.pdf"), format="pdf")
    plt.close()
    logger.info("Saved figure: %s", name)


def plot_openness(ind: pd.DataFrame, year: int) -> None:
    d = ind.sort_values("openness", ascending=False)
    plt.figure(figsize=(11, 6))
    colors = ["#d9534f" if v < 40 else "#337ab7" for v in d["openness"]]
    plt.bar(d["region_name"], d["openness"], color=colors, edgecolor="black", linewidth=0.6)
    plt.axhline(50, color="grey", linestyle="--", linewidth=1, label="50%")
    plt.ylabel("Ventas fuera de la región (% del total regional)", fontweight="bold")
    plt.xlabel("Región", fontweight="bold")
    plt.title(
        f"Apertura comercial interregional, {year}\n"
        "Fracción de las ventas de cada región dirigida al resto del país",
        fontsize=13, fontweight="bold",
    )
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    save_fig("fig4_1_trade_openness")


def plot_balance(ind: pd.DataFrame, year: int) -> None:
    d = ind.sort_values("net_balance_pct")
    plt.figure(figsize=(11, 6))
    colors = ["#d9534f" if v < 0 else "#5cb85c" for v in d["net_balance_pct"]]
    plt.barh(d["region_name"], d["net_balance_pct"], color=colors, edgecolor="black", linewidth=0.6)
    plt.axvline(0, color="black", linewidth=1)
    plt.xlabel(
        "Balance interregional neto (% del intercambio bruto)\n"
        "positivo = vende más al resto del país de lo que le compra",
        fontweight="bold",
    )
    plt.title(f"Balance comercial interregional neto, {year}", fontsize=13, fontweight="bold")
    plt.grid(axis="x", linestyle="--", alpha=0.4)
    save_fig("fig4_2_trade_balance")


def plot_trade_vs_rents(ind: pd.DataFrame, year: int) -> None:
    """Trade position against the two SHT rent axes."""
    shares = compute_sector_shares(valuation="N")
    shares = shares[shares["year"] == year]
    if shares.empty:
        logger.warning("No sectoral shares for %d; skipping fig4_3.", year)
        return

    piv = shares.pivot_table(index="region_code", columns="sector_id", values="share") * 100
    d = ind.set_index("region_code").join(
        piv[[SECTOR_MINING, SECTOR_REAL_ESTATE]].rename(
            columns={SECTOR_MINING: "mining", SECTOR_REAL_ESTATE: "real_estate"}
        )
    ).dropna(subset=["mining", "real_estate"])

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax, (axis_col, label) in zip(
        axes,
        [("mining", "Minería (% del PIB regional)"),
         ("real_estate", "Servicios de vivienda e inmobiliarios (% del PIB regional)")],
    ):
        ax.scatter(d[axis_col], d["openness"], s=90, color="#337ab7",
                   edgecolor="black", alpha=0.8, zorder=3)
        for _, row in d.iterrows():
            ax.annotate(row["region_name"], (row[axis_col], row["openness"]),
                        fontsize=7, xytext=(4, 4), textcoords="offset points")
        r = d[axis_col].corr(d["openness"])
        ax.set_xlabel(label, fontweight="bold", fontsize=9)
        ax.set_ylabel("Apertura interregional (%)", fontweight="bold", fontsize=9)
        ax.set_title(f"r = {r:+.2f}", fontsize=11)
        ax.grid(linestyle="--", alpha=0.4)

    fig.suptitle(
        f"Apertura comercial frente a los dos ejes de renta, {year}",
        fontsize=13, fontweight="bold",
    )
    save_fig("fig4_3_trade_vs_rents")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyse the interregional trade network.")
    parser.add_argument("--year", type=int, default=None, help="year to analyse (default: latest complete)")
    args = parser.parse_args()

    logger.info("Loading interregional trade margins...")
    margins = load_trade_margins()

    # The published identities are the only guarantee that these margins belong
    # to one closed matrix. If they ever stop holding, every indicator below
    # becomes meaningless, so fail loudly rather than reporting anyway.
    deviations = check_identities(margins)
    logger.info("Identity checks (max relative deviation): %s", deviations.to_dict())
    breached = deviations[deviations > IDENTITY_TOL]
    if not breached.empty:
        raise ValueError(
            f"Published trade identities no longer hold: {breached.to_dict()}. "
            "Interregional totals must equal inter + intra, and aggregate "
            "interregional sales must equal aggregate interregional purchases."
        )

    year = args.year or int(margins["year"].max())
    ind = compute_indicators(margins, year=year)

    export_table_to_csv(
        ind[[
            "region_code", "region_name", "openness", "self_containment",
            "out_strength", "in_strength", "net_balance", "net_balance_pct", "turnover",
        ]],
        "table4_trade_network.csv",
    )

    plot_openness(ind, year)
    plot_balance(ind, year)
    plot_trade_vs_rents(ind, year)

    # --- summary -----------------------------------------------------------
    print("\n" + "=" * 78)
    print(f"INTERREGIONAL TRADE NETWORK — {year}")
    print("=" * 78)
    print(f"\nUnits: 10^9 CLP. Regions: {len(ind)}. Span available: "
          f"{int(margins['year'].min())}-{int(margins['year'].max())}.")

    print("\nObservable: the weighted degree sequence.")
    print(ind[["region_name", "openness", "self_containment", "net_balance", "net_balance_pct"]]
          .to_string(index=False, float_format=lambda v: f"{v:,.1f}"))

    residual = abs(float(ind["net_balance"].sum()))
    print(f"\nNet balances sum to {residual:.2e} — the system closes, as a network must.")

    most_open = ind.loc[ind["openness"].idxmax()]
    most_closed = ind.loc[ind["openness"].idxmin()]
    print(f"\nMost open:   {most_open['region_name']} ({most_open['openness']:.1f}% of sales leave)")
    print(f"Most closed: {most_closed['region_name']} ({most_closed['openness']:.1f}%)")

    print("\n" + "-" * 78)
    print("NOT OBSERVABLE: the origin-destination matrix.")
    n = len(ind)
    print(f"  observed per period : {2 * n} margins")
    print(f"  unobserved          : {n * (n - 1)} bilateral flows")
    print("  BCCh publishes no origin-destination series, so who-trades-with-whom")
    print("  cannot be recovered. Centrality, clustering and community structure")
    print("  are therefore NOT reported: computed from margins alone they would")
    print("  restate the degree sequence and describe an assumed topology, not")
    print("  a measured one. See lib/trade.py::independence_baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
Stage:    09 -- Build themed panels for the publication programme
Purpose:  Compile the per-report analytical panels declared in lib.families,
          starting with the two-axis panel (spatial rent vs resource rent) that
          Report 3 publishes. Panels are the single input the site reads, so
          every number on a page is traceable to a CSV in data/.
Task:     Publication programme -- BCCh regional data
Inputs:   data/raw/regional-spatial-macro-dataset/raw_annual.csv (via lib.sectors)
          data/panel_regional_pib_annual.csv
Outputs:  data/panel_two_axes_annual.csv
          data/panel_two_axes_summary.csv
Created:  2026-08-26
Updated:  2026-08-26
Owner:    dpolancon
Run:      python scripts/09_build_theme_panels.py [--family two_axes]
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd

from lib import families as families_lib
from lib.codes import SECTOR_CONSTRUCTION, SECTOR_MINING, SECTOR_REAL_ESTATE
from lib.paths import DATA_DIR
from lib.regions import REGIONS
from lib.sectors import compute_sector_shares
from lib.stats import compute_weighted_gini

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s"
)
logger = logging.getLogger(__name__)

# The three axes travel together: two rents plus the investment leg that links
# them. Named here rather than inlined so a reader of the CSV can find them.
AXIS_SECTORS = {
    SECTOR_REAL_ESTATE: "spatial_rent",
    SECTOR_MINING: "resource_rent",
    SECTOR_CONSTRUCTION: "construction",
}


def build_two_axes() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Region x year shares for the two rent axes, plus a per-year summary.

    Shares are nominal-over-nominal (`valuation="N"`): chained volumes are not
    additive across sectors, so a share built from them would not sum to the
    regional total. compute_sector_shares() already defaults this way; the
    argument is passed explicitly because the choice is load-bearing.
    """
    shares = compute_sector_shares(valuation="N")

    axes = shares[shares["sector_id"].isin(AXIS_SECTORS)].copy()
    if axes.empty:
        raise SystemExit(
            "No rows for sectors 03/06/10 -- has raw_annual.csv been fetched?"
        )
    axes["axis"] = axes["sector_id"].map(AXIS_SECTORS)

    # The sector panel carries ASCII slugs ("Arica_y_Parinacota"), which are the
    # right join key and the wrong thing to print. Carry both: `region_name`
    # stays the stable key, `region_display` is what a reader sees.
    display = {r.name_ascii: r.name_es for r in REGIONS}
    unmapped = set(axes["region_name"]) - set(display)
    if unmapped:
        raise SystemExit(f"Region names with no display form: {sorted(unmapped)}")
    axes["region_display"] = axes["region_name"].map(display)

    panel = (
        axes[
            [
                "year",
                "region_code",
                "region_name",
                "region_display",
                "sector_id",
                "sector_name",
                "axis",
                "value",
                "region_total",
                "share",
            ]
        ]
        .sort_values(["year", "region_code", "sector_id"])
        .reset_index(drop=True)
    )

    # The ratio is the point of the whole framework: how much of a region's
    # output is spatial rent per unit of resource rent. Undefined where mining
    # is absent, and left as NaN rather than zero-filled -- a region with no
    # mining has no ratio, not a ratio of zero.
    wide = panel.pivot_table(
        index=["year", "region_code", "region_name", "region_display"],
        columns="axis",
        values="share",
    ).reset_index()
    for col in ("spatial_rent", "resource_rent", "construction"):
        if col not in wide.columns:
            wide[col] = pd.NA
    wide["rent_ratio"] = wide["spatial_rent"] / wide["resource_rent"]

    # Cross-regional dispersion of each axis, year by year. Unweighted here:
    # this measures how unevenly the axis is distributed across regions as
    # units, not welfare, so no population weight belongs in it.
    rows = []
    for year, grp in wide.groupby("year"):
        ones = pd.Series([1.0] * len(grp), index=grp.index)
        rec = {"year": int(year), "n_regions": int(len(grp))}
        for axis in ("spatial_rent", "resource_rent", "construction"):
            vals = grp[axis].astype(float)
            rec[f"{axis}_mean"] = float(vals.mean())
            rec[f"{axis}_max"] = float(vals.max())
            rec[f"{axis}_argmax"] = grp.loc[vals.idxmax(), "region_display"]
            rec[f"{axis}_gini"] = float(compute_weighted_gini(vals, ones))
        rows.append(rec)
    summary = pd.DataFrame(rows).sort_values("year").reset_index(drop=True)

    return panel, summary


BUILDERS = {"two_axes": build_two_axes}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build themed analytical panels for the publication programme."
    )
    parser.add_argument(
        "--family",
        default="two_axes",
        choices=sorted(BUILDERS),
        help="which report's panel to build",
    )
    args = parser.parse_args()

    fam = families_lib.get(args.family)
    logger.info(
        "Building panel for %s (report %d, tier %s)", fam.name, fam.report, fam.tier
    )

    panel, summary = BUILDERS[args.family]()

    panel_path = DATA_DIR / f"panel_{args.family}_annual.csv"
    summary_path = DATA_DIR / f"panel_{args.family}_summary.csv"
    panel.to_csv(panel_path, index=False, encoding="utf-8")
    summary.to_csv(summary_path, index=False, encoding="utf-8")

    logger.info(
        "Panel: %d rows | %d regions | %d-%d",
        len(panel),
        panel["region_code"].nunique(),
        int(panel["year"].min()),
        int(panel["year"].max()),
    )
    logger.info("Wrote %s", panel_path.name)
    logger.info("Wrote %s", summary_path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

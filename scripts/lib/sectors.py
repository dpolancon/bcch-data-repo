"""
Purpose:  Load REAL regional sectoral GDP from the raw CRSM layer, replacing the
          fabricated sector panel the analysis stages used to generate.
Task:     Regional economic development analysis (SHT spatial vs resource rent)
Inputs:   data/raw/regional-spatial-macro-dataset/raw_annual.csv
Outputs:  n/a (returns DataFrames)
Created:  2026-08-21
Updated:  2026-08-21
Owner:    dpolancon

Background
----------
04_analyze_regional.py used to build its 12-sector breakdown by multiplying
each region's total GDP by hand-written shares (REGION_SECTOR_PROFILES) plus
seeded Gaussian noise, while the reports described the result as "the official
12-sector regional GDP classification compiled by the Central Bank of Chile".
08_audit_outputs.py then "verified" those numbers by re-running the same
generator with the same seed.

BCCh publishes the real thing: annual sectoral GDP per region, current and
chained prices, all 16 regions. This module reads it.

Taxonomy note: the sector list is lib.codes.SECTOR_MAP, which is BCCh's own.
The superseded SECTORS_12 lists split Comercio from Restaurantes y hoteles and
lumped Servicios sociales y personales together -- neither matches BCCh, which
has 07 = "Comercio, restaurantes y hoteles" and splits 11 Servicios personales
from 12 Administracion publica.
"""

import logging
from typing import Optional

import pandas as pd

from lib.codes import (
    SECTOR_CONSTRUCTION,
    SECTOR_MAP,
    SECTOR_MINING,
    SECTOR_REAL_ESTATE,
    f035_pattern,
)
from lib.paths import CRSM_RAW_DIR
from lib.regions import BY_ID

logger = logging.getLogger(__name__)

RAW_ANNUAL = CRSM_RAW_DIR / "raw_annual.csv"

# The activity codes forming a mutually exclusive breakdown of regional GDP in
# the 2018 reference base, verified against the fetched data (each has 208
# series covering all 16 regions).
#
# Note there is no '07' here. Older reference bases carry a combined
# "07 Comercio, restaurantes y hoteles"; from 2018 BCCh splits it into COM and
# RH. Assuming '07' silently loses ~13% of every region's output. PB, RB, SERV
# and CONT are aggregates that would double-count, and 13 ("menos: imputaciones
# bancarias") is an adjustment rather than a sector; all are excluded.
SECTOR_BREAKDOWN_IDS = [
    "01", "02", "03", "04", "05", "06", "COM", "RH",
    "08", "09", "10", "11", "12",
]

# The two SHT rent axes, plus construction as the investment leg.
SHT_SECTORS = {
    "spatial_rent": SECTOR_REAL_ESTATE,
    "resource_rent": SECTOR_MINING,
    "construction": SECTOR_CONSTRUCTION,
}


def _require_raw_annual() -> pd.DataFrame:
    if not RAW_ANNUAL.exists():
        raise FileNotFoundError(
            f"{RAW_ANNUAL} not found. Run scripts/01_fetch_crsm_raw.py first. "
            "This module reads fetched sectoral GDP and will not synthesise it."
        )
    return pd.read_csv(
        RAW_ANNUAL,
        parse_dates=["date"],
        dtype={"region_id": str, "sector_id": str},
        low_memory=False,
    )


def load_sector_panel(
    valuation: str = "N",
    ref_year: str = "2018",
    sector_ids: Optional[list] = None,
) -> pd.DataFrame:
    """Return real annual sectoral GDP as region x year x sector.

    valuation: 'N' for current prices (the right basis for rent *shares*),
               'R' for chained volume (the right basis for growth).

    Columns: year, region_code, region_name, sector_id, sector_name, value.
    """
    df = _require_raw_annual()
    sector_ids = sector_ids or SECTOR_BREAKDOWN_IDS

    frames = []
    for sector_id in sector_ids:
        # f035_pattern wildcards the sub-activity slot. Hardcoding 'Z' there
        # drops mining and construction for the regions that use '21' --
        # silently, with no error and no empty cell.
        pattern = f035_pattern(valuation=valuation, ref_year=ref_year, sector=sector_id)
        subset = df[df["series_code"].str.match(pattern, na=False)]
        if subset.empty:
            logger.warning("No series matched for sector %s", sector_id)
            continue
        frames.append(subset.assign(sector_id=sector_id))

    if not frames:
        raise RuntimeError("No sectoral GDP series matched; cannot build a sector panel.")

    panel = pd.concat(frames, ignore_index=True)
    panel["year"] = panel["date"].dt.year
    panel["sector_name"] = panel["sector_id"].map(SECTOR_MAP)
    panel["region_code"] = panel["region_id"]
    panel["region_name"] = panel["region_code"].map(
        {r.id: r.name_ascii for r in BY_ID.values()}
    )

    out = (
        panel.groupby(
            ["year", "region_code", "region_name", "sector_id", "sector_name"],
            as_index=False,
        )["value"]
        .sum()
        .sort_values(["region_code", "year", "sector_id"])
        .reset_index(drop=True)
    )

    logger.info(
        "Sector panel: %d rows | %d regions | %d sectors | %d-%d",
        len(out), out.region_code.nunique(), out.sector_id.nunique(),
        out.year.min(), out.year.max(),
    )
    return out


def load_regional_totals(valuation: str = "N", ref_year: str = "2018") -> pd.DataFrame:
    """Return real annual TOTAL regional GDP (the `Z` sector token)."""
    df = _require_raw_annual()
    pattern = f035_pattern(valuation=valuation, ref_year=ref_year)  # sector defaults to Z
    subset = df[df["series_code"].str.match(pattern, na=False)].copy()
    if subset.empty:
        raise RuntimeError("No regional total GDP series matched.")

    subset["year"] = subset["date"].dt.year
    subset["region_code"] = subset["region_id"]
    subset["region_name"] = subset["region_code"].map(
        {r.id: r.name_ascii for r in BY_ID.values()}
    )
    return (
        subset.groupby(["year", "region_code", "region_name"], as_index=False)["value"]
        .sum()
        .sort_values(["region_code", "year"])
        .reset_index(drop=True)
    )


def compute_sector_shares(valuation: str = "N", ref_year: str = "2018") -> pd.DataFrame:
    """Sector share of each region's GDP, as a fraction.

    Shares are computed on current prices by default: a rent share is a
    nominal-over-nominal ratio, and chained volumes are not additive across
    sectors, so summing them would not reproduce the regional total.
    """
    sectors = load_sector_panel(valuation=valuation, ref_year=ref_year)
    totals = load_regional_totals(valuation=valuation, ref_year=ref_year).rename(
        columns={"value": "region_total"}
    )
    merged = sectors.merge(totals, on=["year", "region_code", "region_name"], how="left")
    merged["share"] = merged["value"] / merged["region_total"]
    return merged


def compute_location_quotients(year: Optional[int] = None, valuation: str = "N") -> pd.DataFrame:
    """Location quotient by region and sector for one year.

    LQ = (sector share of the region) / (sector share of the national total).
    A value above 1 means the region is more specialised in that sector than
    the country as a whole.
    """
    shares = compute_sector_shares(valuation=valuation)
    year = year or int(shares["year"].max())
    slice_ = shares[shares["year"] == year]
    if slice_.empty:
        raise ValueError(
            f"No sectoral data for {year}. Available: "
            f"{int(shares['year'].min())}-{int(shares['year'].max())}"
        )

    national = slice_.groupby("sector_id")["value"].sum()
    national_share = national / national.sum()

    out = slice_.copy()
    out["national_share"] = out["sector_id"].map(national_share)
    out["lq"] = out["share"] / out["national_share"]
    return out[
        ["year", "region_code", "region_name", "sector_id", "sector_name", "share", "national_share", "lq"]
    ].reset_index(drop=True)

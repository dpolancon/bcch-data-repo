"""
Purpose:  Interregional trade from the BCCh compraventas series -- the observable
          part of the interregional trade network, plus the diagnostics that
          establish exactly which part is NOT observable.
Task:     CRSM dataset construction (SHT spatial rent vs resource rent)
Inputs:   data/raw/regional-spatial-macro-dataset/raw_monthly.csv
Outputs:  n/a (returns DataFrames)
Created:  2026-08-22
Updated:  2026-08-22
Owner:    dpolancon

What BCCh publishes, and what it does not
-----------------------------------------
The `F035.CVR*` families give, per region and month:

    CVRV     total sales by the region        CVRC     total purchases
    CVRVITE  of which, to other regions       CVRCITE  of which, from other regions
    CVRVITA  of which, within the region      CVRCITA  of which, within the region

Both decompositions are exact in the data (total = inter + intra to 1e-14).

Every series carries exactly ONE region slot. There is no counterpart region
anywhere in the code, and no origin-destination series exists in the catalog.
So for a 16-region system each period gives:

    observed    32 numbers  (16 out-margins + 16 in-margins)
    unobserved  240 numbers (the off-diagonal cells of the O-D matrix)

The margins nonetheless cross-check exactly -- total interregional sales equals
total interregional purchases in every month -- which shows they are the row and
column margins of a single closed matrix that BCCh computes internally and
publishes only in aggregated form. The cuadro title says as much:
"Compraventas regionales SEGUN REGION DE VENTA Y DE COMPRA".

Consequence for network analysis
--------------------------------
What is observable is the network's *strength sequence*: each region's weighted
out-degree and in-degree. Openness, self-containment and net balance are all
functions of that, and all are real measurements.

The network's *topology* -- who trades with whom -- is not observable and cannot
be recovered from margins alone. See `independence_baseline` for why filling the
gap by maximum entropy does not help.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

from lib.paths import CRSM_RAW_DIR
from lib.regions import BY_ID

logger = logging.getLogger(__name__)

RAW_MONTHLY = CRSM_RAW_DIR / "raw_monthly.csv"

# BCCh family stem -> column name in the tidy frame.
TRADE_FAMILIES = {
    "CVRV": "sales_total",
    "CVRVITE": "sales_inter",
    "CVRVITA": "sales_intra",
    "CVRC": "buys_total",
    "CVRCITE": "buys_inter",
    "CVRCITA": "buys_intra",
}

# Values are "monto en miles de millones de pesos" (10^9 CLP), per the cuadro.
TRADE_UNIT = "Miles_de_millones_pesos"

# Tolerance for the internal identities. The data satisfies them at ~1e-14, so
# anything above this signals a real change in what BCCh publishes.
IDENTITY_TOL = 1e-6


def _require_raw_monthly() -> pd.DataFrame:
    if not RAW_MONTHLY.exists():
        raise FileNotFoundError(
            f"{RAW_MONTHLY} not found. Run scripts/01_fetch_crsm_raw.py first. "
            "This module reads fetched trade series and will not synthesise them."
        )
    return pd.read_csv(
        RAW_MONTHLY, parse_dates=["date"], dtype={"region_id": str}, low_memory=False
    )


def load_trade_margins(complete_years_only: bool = True) -> pd.DataFrame:
    """Return monthly interregional trade margins, one row per region-month.

    Columns: date, year, region_code, region_name, plus the six TRADE_FAMILIES.

    complete_years_only drops the trailing partial year. The series currently
    run to mid-year, and annual sums over a partial year are not comparable to
    full ones -- a silent way to make the latest year look like a collapse.
    """
    df = _require_raw_monthly()
    trade = df[df["series_code"].str.contains("CVR", na=False)].copy()
    if trade.empty:
        raise RuntimeError("No CVR* trade series found in the raw monthly layer.")

    trade["family"] = trade["series_code"].str.split(".").str[1]
    trade = trade[trade["family"].isin(TRADE_FAMILIES)]

    wide = (
        trade.pivot_table(
            index=["date", "region_id"], columns="family", values="value", aggfunc="sum"
        )
        .rename(columns=TRADE_FAMILIES)
        .reset_index()
        .rename(columns={"region_id": "region_code"})
    )
    wide["region_name"] = wide["region_code"].map({r.id: r.name_es for r in BY_ID.values()})
    wide["year"] = wide["date"].dt.year

    if complete_years_only:
        months = wide.groupby("year")["date"].nunique()
        complete = months[months == 12].index
        dropped = sorted(set(wide["year"]) - set(complete))
        if dropped:
            logger.info("Dropping incomplete years: %s", dropped)
        wide = wide[wide["year"].isin(complete)]

    ordered = ["date", "year", "region_code", "region_name"] + list(TRADE_FAMILIES.values())
    return wide[ordered].sort_values(["date", "region_code"]).reset_index(drop=True)


def check_identities(margins: pd.DataFrame) -> pd.Series:
    """Verify the published data's internal consistency. Returns max deviations.

    Three checks:
      total = inter + intra, on both the sales and the purchase side;
      and the adding-up condition, that across regions total interregional
      sales equal total interregional purchases -- which is what shows the two
      margin vectors belong to one closed matrix.
    """
    out = {}
    for side in ("sales", "buys"):
        gap = (
            margins[f"{side}_total"] - (margins[f"{side}_inter"] + margins[f"{side}_intra"])
        ).abs()
        denom = margins[f"{side}_total"].abs().replace(0, np.nan)
        out[f"{side}_total_vs_parts"] = float((gap / denom).max())

    by_date = margins.groupby("date")[["sales_inter", "buys_inter"]].sum()
    out["adding_up"] = float(
        ((by_date["sales_inter"] - by_date["buys_inter"]).abs() / by_date["sales_inter"]).max()
    )
    return pd.Series(out)


def compute_indicators(margins: pd.DataFrame, year: Optional[int] = None) -> pd.DataFrame:
    """Per-region trade-network indicators for one year.

    These are the observable network quantities -- the weighted degree sequence
    and what follows from it:

      openness         share of the region's sales that leave the region
      self_containment share that stays inside (1 - openness)
      out_strength     interregional sales   (weighted out-degree)
      in_strength      interregional purchases (weighted in-degree)
      net_balance      out_strength - in_strength, in 10^9 CLP
      net_balance_pct  net balance over gross interregional turnover
      turnover         out_strength + in_strength
    """
    year = year or int(margins["year"].max())
    slice_ = margins[margins["year"] == year]
    if slice_.empty:
        raise ValueError(
            f"No trade data for {year}. Available: "
            f"{int(margins['year'].min())}-{int(margins['year'].max())}"
        )

    agg = slice_.groupby(["region_code", "region_name"], as_index=False)[
        list(TRADE_FAMILIES.values())
    ].sum()

    agg["openness"] = agg["sales_inter"] / agg["sales_total"] * 100
    agg["self_containment"] = agg["sales_intra"] / agg["sales_total"] * 100
    agg["out_strength"] = agg["sales_inter"]
    agg["in_strength"] = agg["buys_inter"]
    agg["net_balance"] = agg["out_strength"] - agg["in_strength"]
    agg["turnover"] = agg["out_strength"] + agg["in_strength"]
    agg["net_balance_pct"] = agg["net_balance"] / agg["turnover"] * 100
    agg["year"] = year

    return agg.sort_values("net_balance_pct", ascending=False).reset_index(drop=True)


def independence_baseline(margins: pd.DataFrame, year: Optional[int] = None) -> pd.DataFrame:
    """The maximum-entropy O-D matrix consistent with the observed margins.

    **This is a null model, not an estimate of actual trade flows.** It exists to
    make the identification problem explicit rather than to fill it in.

    Given only row margins r and column margins c, the maximum-entropy (and
    equivalently the IPF / RAS fixed-point) solution is the independence model

        T_ij = r_i * c_j / T

    which is a complete weighted graph whose every cell is a deterministic
    function of the margins. Any network statistic computed on it -- centrality,
    clustering, community structure, assortativity -- is therefore a restatement
    of the degree sequence and carries no information about who actually trades
    with whom. Reporting such statistics as findings about the Chilean
    interregional trade network would be reporting an artifact.

    Recovering real topology needs information the BCCh API does not carry:
    bilateral flows, or an external structure (distance, input-output linkages)
    plus the modelling assumptions that come with it. Either way the result is a
    model and must be labelled as one.

    Returned frame carries `is_model=True` on every row so it cannot be confused
    with observed data downstream.
    """
    ind = compute_indicators(margins, year=year)
    r = ind.set_index("region_code")["out_strength"]
    c = ind.set_index("region_code")["in_strength"]
    total = r.sum()

    rows = []
    for origin, r_i in r.items():
        for dest, c_j in c.items():
            if origin == dest:
                continue  # interregional margins exclude own-region trade
            rows.append(
                {
                    "year": int(ind["year"].iloc[0]),
                    "origin": origin,
                    "destination": dest,
                    "flow_modelled": r_i * c_j / total,
                    "is_model": True,
                }
            )
    return pd.DataFrame(rows)

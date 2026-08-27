"""
Purpose:  Tests for the interregional trade module -- the published identities
          that make the margins usable, and the identification limit that stops
          them from becoming a network.
Task:     CRSM dataset construction (SHT spatial rent vs resource rent)
Inputs:   data/raw/regional-spatial-macro-dataset/raw_monthly.csv
Outputs:  n/a
Created:  2026-08-22
Updated:  2026-08-22
Owner:    dpolancon
"""

import numpy as np
import pytest

from lib.trade import (
    IDENTITY_TOL,
    RAW_MONTHLY,
    TRADE_FAMILIES,
    check_identities,
    compute_indicators,
    independence_baseline,
    load_trade_margins,
)

pytestmark = pytest.mark.skipif(
    not RAW_MONTHLY.exists(),
    reason="raw monthly data not fetched; run scripts/01_fetch_crsm_raw.py",
)


@pytest.fixture(scope="module")
def margins():
    return load_trade_margins()


class TestCoverage:
    def test_all_sixteen_regions(self, margins):
        assert margins["region_code"].nunique() == 16

    def test_every_family_is_present(self, margins):
        for column in TRADE_FAMILIES.values():
            assert column in margins.columns
            assert margins[column].notna().any()

    def test_partial_years_are_dropped(self, margins):
        """A partial year summed against full ones looks like a collapse."""
        months = margins.groupby("year")["date"].nunique()
        assert (months == 12).all(), f"incomplete years retained: {months[months != 12].to_dict()}"


class TestPublishedIdentities:
    def test_total_equals_inter_plus_intra(self, margins):
        dev = check_identities(margins)
        assert dev["sales_total_vs_parts"] < IDENTITY_TOL
        assert dev["buys_total_vs_parts"] < IDENTITY_TOL

    def test_adding_up_holds(self, margins):
        """Aggregate interregional sales must equal aggregate purchases.

        This is what shows the two margin vectors are the rows and columns of a
        single closed matrix, rather than two unrelated aggregates.
        """
        assert check_identities(margins)["adding_up"] < IDENTITY_TOL


class TestIndicators:
    def test_openness_and_self_containment_are_complementary(self, margins):
        ind = compute_indicators(margins)
        total = ind["openness"] + ind["self_containment"]
        assert np.allclose(total, 100.0, atol=1e-9)

    def test_net_balances_sum_to_zero(self, margins):
        """In a closed network one region's surplus is another's deficit."""
        ind = compute_indicators(margins)
        turnover = ind["turnover"].sum()
        assert abs(ind["net_balance"].sum()) / turnover < 1e-12

    def test_shares_are_within_bounds(self, margins):
        ind = compute_indicators(margins)
        assert ind["openness"].between(0, 100).all()
        assert ind["net_balance_pct"].between(-100, 100).all()

    def test_unknown_year_raises_with_available_range(self, margins):
        with pytest.raises(ValueError, match="Available"):
            compute_indicators(margins, year=1990)


class TestIdentificationLimit:
    """The margins do not determine the network, and the baseline proves it."""

    def test_baseline_is_flagged_as_a_model(self, margins):
        base = independence_baseline(margins)
        assert base["is_model"].all()
        assert "flow_modelled" in base.columns
        assert "flow" not in base.columns, "a modelled flow must not be named like an observation"

    def test_baseline_has_no_self_loops(self, margins):
        base = independence_baseline(margins)
        assert (base["origin"] != base["destination"]).all()

    def test_baseline_is_a_complete_graph(self, margins):
        """Maximum entropy puts a positive flow on every pair.

        That is the point: it invents 240 edges from 32 numbers, so its topology
        is an assumption, not a measurement.
        """
        base = independence_baseline(margins)
        n = margins["region_code"].nunique()
        assert len(base) == n * (n - 1)
        assert (base["flow_modelled"] > 0).all()

    def test_baseline_carries_no_information_beyond_the_margins(self, margins):
        """Every cell is exactly r_i * c_j / T.

        Because the matrix factorises, any statistic computed on it is a
        function of the degree sequence alone. Reporting centrality or
        clustering from it would restate the margins, not describe the network.
        """
        ind = compute_indicators(margins)
        base = independence_baseline(margins)
        r = ind.set_index("region_code")["out_strength"]
        c = ind.set_index("region_code")["in_strength"]
        total = r.sum()

        expected = base.apply(
            lambda row: r[row["origin"]] * c[row["destination"]] / total, axis=1
        )
        assert np.allclose(base["flow_modelled"], expected, rtol=1e-12)

    def test_margins_are_far_fewer_than_the_unknowns(self, margins):
        """16 regions: 32 observations against 240 unknown bilateral flows."""
        n = margins["region_code"].nunique()
        observed = 2 * n
        unknown = n * (n - 1)
        assert observed < unknown / 5

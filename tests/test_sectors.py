"""
Purpose:  Tests for the real sectoral GDP loader -- the module that replaced the
          fabricated sector panel.
Task:     Regional economic development analysis (SHT spatial vs resource rent)
Inputs:   data/raw/regional-spatial-macro-dataset/raw_annual.csv
Outputs:  n/a
Created:  2026-08-21
Updated:  2026-08-21
Owner:    dpolancon
"""

import pytest

from lib.codes import SECTOR_CONSTRUCTION, SECTOR_MINING, SECTOR_REAL_ESTATE
from lib.sectors import (
    RAW_ANNUAL,
    SECTOR_BREAKDOWN_IDS,
    SHT_SECTORS,
    compute_location_quotients,
    compute_sector_shares,
    load_regional_totals,
    load_sector_panel,
)

pytestmark = pytest.mark.skipif(
    not RAW_ANNUAL.exists(),
    reason="raw annual data not fetched; run scripts/01_fetch_crsm_raw.py",
)


class TestBreakdownDefinition:
    def test_excludes_aggregates_that_would_double_count(self):
        for aggregate in ("PB", "RB", "SERV", "CONT", "Z", "13"):
            assert aggregate not in SECTOR_BREAKDOWN_IDS

    def test_uses_the_2018_commerce_split_not_the_combined_07(self):
        """Ref-2018 splits commerce into COM and RH; '07' does not exist there.

        Assuming '07' silently drops ~13% of every region's output.
        """
        assert "07" not in SECTOR_BREAKDOWN_IDS
        assert "COM" in SECTOR_BREAKDOWN_IDS
        assert "RH" in SECTOR_BREAKDOWN_IDS

    def test_covers_both_sht_rent_axes(self):
        assert SHT_SECTORS["resource_rent"] == SECTOR_MINING
        assert SHT_SECTORS["spatial_rent"] == SECTOR_REAL_ESTATE
        for sector_id in SHT_SECTORS.values():
            assert sector_id in SECTOR_BREAKDOWN_IDS


class TestSectorPanel:
    @pytest.fixture(scope="class")
    def panel(self):
        return load_sector_panel()

    def test_covers_all_sixteen_regions(self, panel):
        assert panel["region_code"].nunique() == 16

    def test_every_breakdown_sector_is_present(self, panel):
        assert set(panel["sector_id"]) == set(SECTOR_BREAKDOWN_IDS)

    def test_every_sector_has_a_name(self, panel):
        assert panel["sector_name"].notna().all()

    def test_mining_is_present_for_tarapaca(self, panel):
        """Tarapaca encodes mining with '21' in the sub-activity slot.

        A selector hardcoding 'Z' there drops it silently, which is exactly how
        a 39% mining share once vanished from an analysis without any error.
        """
        rows = panel[(panel.region_code == "01") & (panel.sector_id == SECTOR_MINING)]
        assert not rows.empty
        assert (rows["value"] > 0).any()


class TestShares:
    @pytest.fixture(scope="class")
    def shares(self):
        return compute_sector_shares()

    def test_shares_sum_to_one_per_region_year(self, shares):
        """The breakdown must be exhaustive; a gap means a missing sector."""
        totals = shares.groupby(["year", "region_code"])["share"].sum()
        assert totals.min() == pytest.approx(1.0, abs=1e-6)
        assert totals.max() == pytest.approx(1.0, abs=1e-6)

    def test_shares_are_fractions(self, shares):
        assert shares["share"].between(0, 1).all()

    def test_antofagasta_is_mining_dominated(self, shares):
        """A sanity anchor against real-world knowledge, not a tautology."""
        latest = shares[shares.year == shares.year.max()]
        row = latest[(latest.region_code == "02") & (latest.sector_id == SECTOR_MINING)]
        assert row["share"].iloc[0] > 0.4

    def test_construction_is_distinct_from_real_estate(self, shares):
        """A superseded inventory labelled sector 10 as 'Construccion'."""
        latest = shares[shares.year == shares.year.max()]
        constr = latest[latest.sector_id == SECTOR_CONSTRUCTION]["value"].sum()
        realest = latest[latest.sector_id == SECTOR_REAL_ESTATE]["value"].sum()
        assert constr != realest


class TestLocationQuotients:
    def test_national_shares_sum_to_one(self):
        """One national share per sector, and together they exhaust the economy."""
        lq = compute_location_quotients()
        per_sector = lq.drop_duplicates("sector_id")["national_share"]
        assert per_sector.sum() == pytest.approx(1.0, abs=1e-9)

    def test_lq_above_one_means_more_specialised_than_the_country(self):
        lq = compute_location_quotients()
        assert (lq["lq"] >= 0).all()
        # Antofagasta's mining share far exceeds the national one.
        row = lq[(lq.region_code == "02") & (lq.sector_id == SECTOR_MINING)].iloc[0]
        assert row["share"] > row["national_share"]
        assert row["lq"] > 1

    def test_unknown_year_raises_with_available_range(self):
        with pytest.raises(ValueError, match="Available"):
            compute_location_quotients(year=1900)

    def test_totals_match_sum_of_sectors(self):
        sectors = load_sector_panel()
        totals = load_regional_totals()
        merged = (
            sectors.groupby(["year", "region_code"])["value"].sum().rename("summed")
            .to_frame()
            .join(totals.set_index(["year", "region_code"])["value"].rename("total"))
            .dropna()
        )
        assert (merged["summed"] - merged["total"]).abs().max() < 1e-6

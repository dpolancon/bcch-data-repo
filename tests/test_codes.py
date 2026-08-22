"""
Purpose:  Tests for frequency and sector parsing, including a full-catalog
          assertion that frequency resolves for every series code, and guards
          on the three sectors the SHT framework depends on.
Task:     CRSM dataset construction (SHT spatial rent vs resource rent)
Inputs:   data/catalogo_series.xlsx (for the full-catalog coverage test)
Outputs:  n/a
Created:  2026-08-21
Updated:  2026-08-21
Owner:    dpolancon
"""

import pandas as pd
import pytest

from lib.codes import (
    FREQ_LABEL,
    FREQ_SLUG,
    FREQ_STORAGE,
    SECTOR_CONSTRUCTION,
    SECTOR_MINING,
    SECTOR_REAL_ESTATE,
    VALID_FREQUENCIES,
    is_sectoral_total,
    parse_frequency,
    parse_sector,
)
from lib.paths import CATALOG_XLSX


class TestParseFrequency:
    @pytest.mark.parametrize(
        "code,expected",
        [
            ("F035.PIB.FLU.R.CLP.2018.Z.Z.Z.13.0.T", "T"),
            ("F035.PIB.FLU.N.CLP.2018.10.Z.Z.02.0.A", "A"),
            ("F034.SAHAP.FLU.INE.Z.0.M", "M"),
            ("F034.BESOAP.IND.BCCH.2020.0.D", "D"),
        ],
    )
    def test_reads_last_dot_token(self, code, expected):
        assert parse_frequency(code) == expected

    @pytest.mark.parametrize("value", ["", None, "NODOTS", 42])
    def test_returns_none_for_malformed(self, value):
        assert parse_frequency(value) is None

    def test_every_frequency_has_all_label_mappings(self):
        for letter in VALID_FREQUENCIES:
            assert letter in FREQ_LABEL
            assert letter in FREQ_SLUG
            assert letter in FREQ_STORAGE


class TestParseSector:
    def test_mining_is_03(self):
        assert parse_sector("F035.PIB.FLU.N.CLP.2018.03.Z.Z.13.0.A") == (
            SECTOR_MINING,
            "Minería",
        )

    def test_construction_is_06(self):
        assert parse_sector("F035.PIB.FLU.N.CLP.2018.06.Z.Z.13.0.A") == (
            SECTOR_CONSTRUCTION,
            "Construcción",
        )

    def test_real_estate_is_10(self):
        """Guards the mislabel in the superseded coverage inventory, which
        tagged sector 10 as 'Construcción' and sector 03 as 'UNKNOWN'."""
        assert parse_sector("F035.PIB.FLU.N.CLP.2018.10.Z.Z.13.0.A") == (
            SECTOR_REAL_ESTATE,
            "Servicios de vivienda e inmobiliarios",
        )

    def test_aggregate_token_has_no_sector(self):
        assert parse_sector("F035.PIB.FLU.R.CLP.2018.Z.Z.Z.13.0.T") == (None, None)

    def test_non_f035_has_no_sector(self):
        assert parse_sector("F034.SAHAP.FLU.INE.Z.0.M") == (None, None)


class TestIsSectoralTotal:
    def test_true_for_aggregate(self):
        assert is_sectoral_total("F035.PIB.FLU.R.CLP.2018.Z.Z.Z.13.0.T")

    def test_false_for_sectoral(self):
        assert not is_sectoral_total("F035.PIB.FLU.N.CLP.2018.10.Z.Z.13.0.A")


@pytest.mark.skipif(not CATALOG_XLSX.exists(), reason="catalog not available")
class TestFullCatalogCoverage:
    """The frequency suffix is the pipeline's only frequency source, so it must
    resolve for every row -- not merely for the codes we happened to sample."""

    @pytest.fixture(scope="class")
    def catalog(self):
        df = pd.read_excel(CATALOG_XLSX)
        df.columns = [c.strip() for c in df.columns]
        return df

    def test_frequency_resolves_for_every_row(self, catalog):
        unresolved = catalog["CÓDIGO"].map(parse_frequency).isna()
        assert unresolved.sum() == 0, (
            f"{unresolved.sum()} codes have no parseable frequency, e.g. "
            f"{catalog.loc[unresolved, 'CÓDIGO'].head().tolist()}"
        )

    def test_all_four_frequencies_are_present(self, catalog):
        found = set(catalog["CÓDIGO"].map(parse_frequency).dropna())
        assert found == set(VALID_FREQUENCIES)

    def test_sht_sectors_have_regional_series(self, catalog):
        """Each rent axis must actually be measurable, not merely mapped."""
        from lib.regions import parse_region

        codes = catalog["CÓDIGO"].drop_duplicates()
        counts = {SECTOR_MINING: 0, SECTOR_CONSTRUCTION: 0, SECTOR_REAL_ESTATE: 0}
        for code in codes:
            sector_id, _ = parse_sector(code)
            if sector_id in counts:
                match = parse_region(str(code))
                if match is not None and match.region is not None:
                    counts[sector_id] += 1

        for sector_id, n in counts.items():
            assert n > 0, f"sector {sector_id} has no regional series"


class TestF035Selectors:
    """The sub-activity slot (token 7) must be wildcarded.

    Mining and construction use '21' there for some regions. A selector that
    hardcodes 'Z' drops them silently -- Tarapaca's 34% mining share simply
    stops existing, with no error to notice.
    """

    def test_matches_both_subactivity_variants(self):
        import re

        from lib.codes import f035_pattern

        pat = re.compile(f035_pattern(sector="03"))
        assert pat.match("F035.PIB.FLU.N.CLP.2018.03.Z.Z.02.0.A")   # most regions
        assert pat.match("F035.PIB.FLU.N.CLP.2018.03.21.Z.01.0.A")  # Tarapaca

    def test_respects_sector_and_frequency(self):
        import re

        from lib.codes import f035_pattern

        pat = re.compile(f035_pattern(sector="10", frequency="A"))
        assert pat.match("F035.PIB.FLU.N.CLP.2018.10.Z.Z.13.0.A")
        assert not pat.match("F035.PIB.FLU.N.CLP.2018.03.Z.Z.13.0.A")  # wrong sector
        assert not pat.match("F035.PIB.FLU.N.CLP.2018.10.Z.Z.13.0.T")  # wrong frequency

    def test_total_pattern_excludes_sectoral(self):
        import re

        from lib.codes import f035_pattern

        pat = re.compile(f035_pattern())  # sector defaults to the total token Z
        assert pat.match("F035.PIB.FLU.N.CLP.2018.Z.Z.Z.13.0.A")
        assert not pat.match("F035.PIB.FLU.N.CLP.2018.10.Z.Z.13.0.A")

"""
Purpose:  Tests for the four region encodings, with explicit guards against the
          false positives a naive suffix parser produces.
Task:     CRSM dataset construction (SHT spatial rent vs resource rent)
Inputs:   n/a
Outputs:  n/a
Created:  2026-08-21
Updated:  2026-08-21
Owner:    dpolancon
"""

import pytest

from lib.regions import (
    BY_ID,
    PARSE_CUADRO,
    PARSE_GLUED,
    PARSE_POSITIONAL,
    PARSE_ROMAN,
    REGIONS,
    parse_region,
    strip_accents,
)


class TestRegionTable:
    def test_sixteen_regions_with_unique_keys(self):
        assert len(REGIONS) == 16
        for attr in ("id", "mnemonic", "roman", "ine_code"):
            values = [getattr(r, attr) for r in REGIONS]
            assert len(set(values)) == 16, f"duplicate {attr}"

    def test_ids_are_zero_padded_one_to_sixteen(self):
        assert {r.id for r in REGIONS} == {f"{i:02d}" for i in range(1, 17)}


class TestPositionalEncoding:
    """F035 12-part codes carry the region at index 9."""

    @pytest.mark.parametrize(
        "code,expected_id",
        [
            ("F035.PIB.FLU.R.CLP.2018.Z.Z.Z.13.0.T", "13"),
            ("F035.PIB.FLU.R.CLP.2018.Z.Z.Z.15.0.T", "15"),
            ("F035.PIB.FLU.N.CLP.2018.10.Z.Z.02.0.A", "02"),
            ("F035.PIB.FLU.N.CLP.2018.03.Z.Z.01.0.A", "01"),
        ],
    )
    def test_resolves_region(self, code, expected_id):
        match = parse_region(code)
        assert match is not None
        assert match.region.id == expected_id
        assert match.method == PARSE_POSITIONAL

    @pytest.mark.parametrize("token", ["Z", "99", "98"])
    def test_aggregate_tokens_are_national(self, token):
        match = parse_region(f"F035.PIB.FLU.R.CLP.2018.Z.Z.Z.{token}.0.A")
        assert match is not None
        assert match.is_national
        assert match.region is None


class TestGluedMnemonicEncoding:
    """F034/F022 weld a 2-letter mnemonic onto the concept token."""

    @pytest.mark.parametrize(
        "code,expected_id",
        [
            ("F034.SAHAP.FLU.INE.Z.0.M", "15"),   # Arica y Parinacota
            ("F034.SANHTA.FLU.INE.Z.0.M", "01"),  # Tarapaca
            ("F034.NVARM.FLU.INE.Z.0.M", "13"),   # Metropolitana
            ("F034.CEYSBI.FLU.MEFT.Z.0.M", "08"), # Biobio
            ("F022.DV90AN.TAS.Z.Z.Z.M", "02"),    # Antofagasta
            ("F034.BESOMA.IND.BCCH.2020.0.D", "12"),  # Magallanes
        ],
    )
    def test_resolves_region(self, code, expected_id):
        match = parse_region(code)
        assert match is not None
        assert match.region.id == expected_id
        assert match.method == PARSE_GLUED

    @pytest.mark.parametrize(
        "code,why",
        [
            ("F022.CTOBI.STO.Z.Z.CLP.M", "BI here is 'balances individuales', not Biobio"),
            ("F022.CAP.TIN.D089.NO.Z.M", "AP here is 'captaciones', not Arica y Parinacota"),
        ],
    )
    def test_rejects_concept_tokens_that_merely_end_in_a_mnemonic(self, code, why):
        """The family-stem whitelist is what prevents these false positives."""
        match = parse_region(code)
        assert match is None or match.region is None, why


class TestRomanEncoding:
    @pytest.mark.parametrize(
        "code,expected_id",
        [
            ("F034.SEVC.POR.BCCH.Z.RM.A", "13"),
            ("F034.TEMP.STO.BCCH.Z.RXV.A", "15"),
            ("F034.TEAMV.STO.BCCH.Z.RII.A", "02"),
            ("F034.ICNE.POR.BCCH.Z.RVIII.A", "08"),
        ],
    )
    def test_resolves_region(self, code, expected_id):
        match = parse_region(code)
        assert match is not None
        assert match.region.id == expected_id
        assert match.method == PARSE_ROMAN

    @pytest.mark.parametrize("token", ["RVIIIRXVI", "RXRXIV", "RXIRXII", "RXVRI"])
    def test_rejects_merged_region_compounds(self, token):
        """Merged groups are not a single region; assigning one would be wrong."""
        match = parse_region(f"F068.G1.STO.Z.IED.Z.Z.Z.Z.CL.IED.6.{token}.A")
        assert match is None or match.region is None


class TestCuadroFallback:
    """F049 labour codes use INE internal numbers; region is only in the text."""

    @pytest.mark.parametrize(
        "table_name,expected_id",
        [
            ("Fuerza de trabajo, Región de Tarapacá", "01"),
            ("Tasa de desocupación, Región Metropolitana de Santiago", "13"),
            ("Ocupados, Región del Biobío", "08"),
            ("Ocupados, Región de Ñuble", "16"),
            ("Ocupados, Región de Los Ríos", "14"),
            ("Ocupados, Región de Aysén", "11"),
        ],
    )
    def test_resolves_from_table_name(self, table_name, expected_id):
        match = parse_region("F049.DES.TAS.INE9.11.M", "", table_name)
        assert match is not None
        assert match.region.id == expected_id
        assert match.method == PARSE_CUADRO

    @pytest.mark.parametrize(
        "spelling", ["Región de O'Higgins", "Region de OHiggins", "Región del Libertador"]
    )
    def test_tolerates_ohiggins_spelling_variants(self, spelling):
        """The catalog spells O'Higgins at least three different ways."""
        match = parse_region("F049.OCU.PMT.INE9.16.M", "", spelling)
        assert match is not None
        assert match.region.id == "06"


class TestStripAccents:
    @pytest.mark.parametrize(
        "raw,expected",
        [("Biobío", "biobio"), ("Ñuble", "nuble"), ("O'Higgins", "ohiggins"), ("Aysén", "aysen")],
    )
    def test_folds_accents_and_apostrophes(self, raw, expected):
        assert strip_accents(raw) == expected


class TestMalformedInput:
    @pytest.mark.parametrize("value", ["", "   ", None, 12345, "NOTACODE"])
    def test_returns_none_without_raising(self, value):
        assert parse_region(value) is None

"""
Purpose:  Enforce the publication programme's absorption rules mechanically.
          A cadence that depends on everyone remembering the convention is not
          a cadence; these tests are what make "self-paced" a property of the
          repository rather than an intention.
Task:     Publication programme -- BCCh regional data
Inputs:   scripts/lib/families.py, the vault, data/
Outputs:  n/a (pytest)
Created:  2026-08-26
Updated:  2026-08-26
Owner:    dpolancon
"""

import os
import re

import pandas as pd

from lib import unidades as unidades_lib
import sys

import pytest

SCRIPTS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"
)
sys.path.insert(0, SCRIPTS)

from lib import families as families_lib  # noqa: E402
from lib.paths import BRIEFINGS_DIR, CRSM_RAW_DIR, REPO_ROOT  # noqa: E402


class TestFamilyRegistry:
    """The registry is the contract every stage reads; keep it well-formed."""

    def test_report_numbers_are_unique(self):
        reports = [f.report for f in families_lib.FAMILIES.values()]
        assert len(reports) == len(set(reports)), f"Duplicate report numbers: {reports}"

    def test_reports_are_contiguous_from_three(self):
        # Reports 1 and 2 predate the programme and are hand-built.
        reports = sorted(f.report for f in families_lib.FAMILIES.values())
        assert reports == list(range(3, 3 + len(reports))), (
            f"Report numbers must be contiguous from 3: {reports}"
        )

    def test_dict_key_matches_family_name(self):
        for key, fam in families_lib.FAMILIES.items():
            assert key == fam.name, f"Key {key!r} does not match name {fam.name!r}"

    def test_every_family_declares_a_scale(self):
        for fam in families_lib.FAMILIES.values():
            assert fam.escala in families_lib.ESCALAS, (
                f"{fam.name} declara escala {fam.escala!r}"
            )

    def test_every_scale_has_a_label(self):
        """El distintivo del sitio se construye desde aquí; sin etiqueta, revienta."""
        for escala in families_lib.ESCALAS:
            assert escala in families_lib.ESCALA_LABEL, f"{escala} sin etiqueta"

    def test_every_family_declares_valid_frequencies(self):
        for fam in families_lib.FAMILIES.values():
            assert fam.frequencies, f"{fam.name} declares no frequency"
            for freq in fam.frequencies:
                assert freq in {"D", "M", "T", "A"}, (
                    f"{fam.name} declares unknown frequency {freq!r}"
                )

    def test_patterns_compile(self):
        for fam in families_lib.FAMILIES.values():
            re.compile(fam.pattern())

    def test_non_regional_scales_expect_zero_regions(self):
        """Nacional y macro-zona no se desagregan; afirmar lo contrario engaña."""
        for fam in families_lib.FAMILIES.values():
            if not fam.es_regional:
                assert fam.expected_regions == 0, (
                    f"{fam.name} es escala {fam.escala} pero espera "
                    f"{fam.expected_regions} regiones"
                )

    def test_regional_scales_expect_all_sixteen_regions(self):
        for fam in families_lib.FAMILIES.values():
            if fam.es_regional:
                assert fam.expected_regions == 16, (
                    f"{fam.name} es escala {fam.escala} pero espera "
                    f"{fam.expected_regions} regiones"
                )

    def test_every_family_carries_notes_in_spanish(self):
        """Las trampas son el punto, y el sitio es en español.

        `notes` quedó como memoria técnica interna; lo que se publica es
        `notas_es`. Una familia sin notas en español publica inglés o no
        publica nada, y ambas cosas ya ocurrieron.
        """
        for fam in families_lib.FAMILIES.values():
            assert fam.notas_es.strip(), f"{fam.name} no tiene notas_es"

    def test_every_family_declares_its_objective(self):
        """A qué objetivo de la formulación responde. Sin esto no se sabe qué citar."""
        for fam in families_lib.FAMILIES.values():
            assert fam.objetivo.strip(), f"{fam.name} no declara objetivo"

    def test_ordered_is_by_report(self):
        got = [f.report for f in families_lib.ordered()]
        assert got == sorted(got)


class TestZoneVocabulary:
    """Tier A geography must stay unambiguous."""

    def test_known_zone_codes_resolve(self):
        cases = {
            "F034.VALV.FLU.BCCH.Z.ZN.A": "Zona Norte",
            "F034.VALT.FLU.BCCH.Z.CAS.A": "Nacional -- casas",
            "F034.IPVZ42C.FLU.BCCH.2008.0.T": "RM Oriente -- casas",
            # The transposed mnemonic is BCCh's, not ours -- it must still match.
            "F034.IVPZ1.FLU.BCCH.2008.0.T": "Zona Norte",
        }
        for code, expected in cases.items():
            assert families_lib.parse_zone(code) == expected, code

    def test_regional_codes_do_not_resolve_to_a_zone(self):
        """A regional series must never be mistaken for zone-level data."""
        assert families_lib.parse_zone("F035.PIB.FLU.R.CLP.2018.03.Z.Z.02.0.A") is None

    def test_zone_subsets_are_a_subset_of_known_zones(self):
        known = set(families_lib.ZONE_MAP.values()) | set(
            families_lib.IPV_ZONE_MAP.values()
        )
        assert families_lib.ZONE_SUBSETS <= known


class TestAbsorptionGate:
    """The gate: a family may not be ingested before its briefing note exists.

    This is the mechanism that makes the cadence self-paced. It is deliberately
    skipped when nothing has been fetched yet, so a fresh clone is not blocked.
    """

    @pytest.mark.parametrize(
        "fam", families_lib.ordered(), ids=lambda f: f.name
    )
    def test_fetched_family_has_a_briefing_note(self, fam):
        # The manifest -- not the universe -- is the evidence of ingestion.
        # A --dry-run resolves a universe without calling the API, and
        # resolving what a family *would* fetch teaches nobody anything.
        manifest = CRSM_RAW_DIR / f"manifest_{fam.name}.csv"
        if not manifest.exists():
            pytest.skip(f"{fam.name} not yet fetched -- gate does not apply")
        note = BRIEFINGS_DIR / fam.briefing_note
        assert note.exists(), (
            f"Family {fam.name!r} has been fetched (manifest_{fam.name}.csv exists) "
            f"but its briefing note is missing: {note.relative_to(REPO_ROOT)}. "
            "Write the note before the next report's fetch."
        )

    def test_briefing_notes_are_non_trivial(self):
        """A stub file satisfies the letter of the gate and none of its point."""
        if not BRIEFINGS_DIR.exists():
            pytest.skip("no briefings yet")
        for note in BRIEFINGS_DIR.glob("*.md"):
            text = note.read_text(encoding="utf-8")
            assert len(text.split()) >= 120, (
                f"{note.name} is too short to brief anyone ({len(text.split())} words)"
            )

class TestCapaCruda:
    """Invariantes de la capa cruda que un merge parcial ya rompió dos veces.

    Las dos fallas fueron silenciosas: nada explotó al escribir, y el error
    apareció mucho después, en un consumidor que usaba .dt sobre una columna
    de texto o que cruzaba por un region_id sin relleno.
    """

    def _archivos(self):
        raw = REPO_ROOT / "data" / "raw" / "regional-spatial-macro-dataset"
        return sorted(raw.glob("raw_*.csv"))

    def test_fecha_uniforme(self):
        """Una sola representación de fecha por archivo, YYYY-MM-DD."""
        for archivo in self._archivos():
            fechas = pd.read_csv(archivo, dtype=str, low_memory=False)["date"]
            largos = set(fechas.dropna().str.len())
            assert largos == {10}, (
                f"{archivo.name} mezcla formatos de fecha {sorted(largos)}. "
                "Un merge parcial dejó filas nuevas con hora y preservadas sin."
            )

    def test_region_id_con_relleno(self):
        """region_id es texto de dos caracteres: '01', no '1'."""
        for archivo in self._archivos():
            ids = pd.read_csv(archivo, dtype=str, low_memory=False)["region_id"]
            malos = sorted({v for v in ids.dropna().unique() if len(v) != 2})
            assert not malos, (
                f"{archivo.name} tiene region_id sin relleno: {malos[:5]}. "
                "Leerlo como entero convierte '01' en 1 y rompe todo cruce."
            )

class TestUnidades:
    """Un panel debe declarar qué operaciones admite sobre sus valores.

    Los tres errores que este módulo existe para impedir ya se cometieron:
    sumar los doce meses de un stock, etiquetar igual un saldo en pesos y otro
    en millones de pesos, y sumar entre regiones un saldo que es un promedio.
    """

    def _paneles(self):
        data = REPO_ROOT / "data"
        return [
            p for p in sorted(data.glob("panel_*.csv"))
            if "unidad" in pd.read_csv(p, nrows=1).columns
        ]

    def test_una_unidad_por_dimension(self):
        """Dos series de la misma dimensión no pueden venir en unidades distintas."""
        for panel in self._paneles():
            d = pd.read_csv(panel)
            for dim, grupo in d.groupby("dimension"):
                unidades = set(grupo["unidad"].unique())
                assert len(unidades) == 1, (
                    f"{panel.name}: la dimensión {dim} trae {sorted(unidades)}. "
                    "Dos unidades en una dimensión no son comparables ni sumables."
                )

    def test_unidad_es_la_canonica(self):
        for panel in self._paneles():
            d = pd.read_csv(panel)
            for dim, grupo in d.groupby("dimension"):
                esperada = unidades_lib.CANONICA[dim]
                got = grupo["unidad"].iloc[0]
                assert got == esperada, (
                    f"{panel.name}: {dim} está en {got!r} y la canónica es {esperada!r}"
                )

    def test_agregacion_declarada(self):
        """Sin este campo no se sabe si un valor se puede sumar entre regiones."""
        for panel in self._paneles():
            d = pd.read_csv(panel)
            malos = set(d["agregacion"].unique()) - {
                unidades_lib.TOTAL, unidades_lib.PROMEDIO
            }
            assert not malos, f"{panel.name}: agregación desconocida {malos}"

    def test_toda_unidad_de_origen_esta_declarada(self):
        for panel in self._paneles():
            d = pd.read_csv(panel)
            for u in d["unidad_original"].dropna().unique():
                unidades_lib.resolver(u)

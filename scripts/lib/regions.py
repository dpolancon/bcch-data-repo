"""
Purpose:  Canonical table of Chile's 16 regions plus a parser that recovers the
          region from a BCCh series code. The catalog uses FOUR mutually
          incompatible region encodings; this module is the single place that
          knows about all of them.
Task:     CRSM dataset construction (SHT spatial rent vs resource rent)
Inputs:   BCCh series codes and catalog text (series name, cuadro name)
Outputs:  n/a (pure functions)
Created:  2026-08-21
Updated:  2026-08-21
Owner:    dpolancon

The four encodings
-----------------
1. F035 positional  -- 12-part code, region at index 9: 'F035.PIB....13.0.T'
2. Glued mnemonic   -- 2 letters welded onto token 1: 'F034.SAH[AP]....M'
3. Roman numeral    -- region as a later whole token:  'F034.SEVC.POR.BCCH.Z.[RM].A'
4. Cuadro fallback  -- region only in the table name:  F049 labour series

Encoding 2 is the dangerous one. 'BI' and 'AP' occur inside ordinary concept
tokens ('CTOBI' = balances individuales, 'CAP' = captaciones), so a naive
"does token 1 end in a region mnemonic" test yields hundreds of false
positives. We therefore require the *stripped stem* to appear in
GLUED_FAMILY_STEMS -- membership in a known regional family, not suffix shape,
is what licenses the match.
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Optional

# Sentinel values that appear in the F035 region slot to mean "not a region".
NATIONAL_REGION_TOKENS = frozenset({"Z", "99", "98", "00", "T"})


@dataclass(frozen=True)
class Region:
    """One Chilean region and every alias the BCCh catalog uses for it."""

    id: str  # zero-padded '01'..'16' -- the canonical key
    name_es: str  # accented Spanish name, for reports
    name_ascii: str  # ASCII/underscore name, for filenames and joins
    mnemonic: str  # 2-letter code glued onto F034/F022 concept tokens
    roman: str  # roman-numeral token used by TEMP/TEAMV/SEVC/ICNE
    ine_code: Optional[str]  # INE internal code used by the F049 labour family


# Ordered north to south, which is also how BCCh tables present them.
REGIONS: List[Region] = [
    Region("15", "Arica y Parinacota", "Arica_y_Parinacota", "AP", "RXV", "25"),
    Region("01", "Tarapacá", "Tarapaca", "TA", "RI", "11"),
    Region("02", "Antofagasta", "Antofagasta", "AN", "RII", "12"),
    Region("03", "Atacama", "Atacama", "AT", "RIII", "13"),
    Region("04", "Coquimbo", "Coquimbo", "CO", "RIV", "14"),
    Region("05", "Valparaíso", "Valparaiso", "VA", "RV", "15"),
    Region("13", "Metropolitana de Santiago", "Metropolitana", "RM", "RM", "23"),
    Region("06", "O'Higgins", "OHiggins", "LI", "RVI", "16"),
    Region("07", "Maule", "Maule", "ML", "RVII", "17"),
    Region("16", "Ñuble", "Nuble", "NB", "RXVI", "26"),
    Region("08", "Biobío", "Biobio", "BI", "RVIII", "18N"),
    Region("09", "La Araucanía", "Araucania", "AR", "RIX", "19"),
    Region("14", "Los Ríos", "Los_Rios", "LR", "RXIV", "24"),
    Region("10", "Los Lagos", "Los_Lagos", "LL", "RX", "20"),
    Region("11", "Aysén", "Aysen", "AI", "RXI", "21"),
    Region("12", "Magallanes", "Magallanes", "MA", "RXII", "22"),
]

BY_ID: Dict[str, Region] = {r.id: r for r in REGIONS}
BY_MNEMONIC: Dict[str, Region] = {r.mnemonic: r for r in REGIONS}
BY_ROMAN: Dict[str, Region] = {r.roman: r for r in REGIONS}
BY_INE: Dict[str, Region] = {r.ine_code: r for r in REGIONS if r.ine_code}

# Concept stems that genuinely carry a glued region mnemonic. A code only
# qualifies for encoding 2 if stripping the mnemonic leaves one of these.
GLUED_FAMILY_STEMS = frozenset(
    {
        # Land use / construction permits (INE)
        "SAH", "SANH", "NVA",
        # ISUP -- superficie / numero de establecimientos, retail sales
        "ISUPSE", "ISUPNE", "ISUPPC", "ISUP",
        # Regional economic indicator composites
        "CEYS",
        # Electronic invoices, incl. gas stations
        "BES", "BESO",
        # Debt delinquency (90+ days): vivienda / consumo / comercial
        "DV90", "DCS90", "DCM90",
        # Deposits and placements
        "CCPN", "CCPE", "SCCPN", "SCCPE", "SDV",
        # Mining production index (4 northern regions only)
        "PMI", "INDPM",
        # Energy generation / distribution
        "GEE", "DEE",
        # Tourism (EMAT): ADR, occupancy, RevPAR, arrivals
        "ETADR", "ETOP", "ETTOH", "ETP", "ETL", "ETEM",
        # Population
        "POB",
        # Misc regional families
        "CTAP", "DART", "DIND", "MCP", "MCPN", "MCPE", "PV",
    }
)

# Roman-numeral compounds denoting MERGED regions (e.g. F068 FDI groups).
# These are not atomic regions and must be rejected rather than mis-assigned.
MERGED_ROMAN_TOKENS = frozenset(
    {"RXVRI", "RVIIIRXVI", "RXRXIV", "RXIRXII", "RIRII", "RIIIRIV"}
)

PARSE_POSITIONAL = "f035_positional"
PARSE_GLUED = "glued_mnemonic"
PARSE_ROMAN = "roman_numeral"
PARSE_CUADRO = "cuadro_name"
PARSE_NATIONAL = "national"


@dataclass(frozen=True)
class RegionMatch:
    """Result of a region lookup, carrying the method that produced it.

    `method` is retained downstream so a run can be audited by encoding --
    an unexpected method/chapter combination is how false positives surface.
    """

    region: Optional[Region]
    method: str

    @property
    def is_national(self) -> bool:
        return self.region is None and self.method == PARSE_NATIONAL

    @property
    def id(self) -> Optional[str]:
        return self.region.id if self.region else None

    @property
    def name_es(self) -> Optional[str]:
        return self.region.name_es if self.region else None


def strip_accents(text: str) -> str:
    """Fold accents and normalize apostrophes so name matching is spelling-proof.

    The catalog is internally inconsistent -- O'Higgins appears as O'higgins,
    OHiggins and O'Higgins; Ñuble as Nuble and Ñuble.
    """
    if not isinstance(text, str):
        return ""
    folded = unicodedata.normalize("NFKD", text)
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    return folded.replace("'", "").replace("`", "").replace("’", "").lower()


# Longest names first so "Los Rios" cannot be shadowed by a shorter prefix.
_NAME_LOOKUP = sorted(
    ((strip_accents(r.name_es), r) for r in REGIONS),
    key=lambda pair: len(pair[0]),
    reverse=True,
)
# A few table-name spellings that differ from the canonical name.
_NAME_ALIASES = {
    "metropolitana": BY_ID["13"],
    "region metropolitana": BY_ID["13"],
    "santiago": BY_ID["13"],
    "araucania": BY_ID["09"],
    "libertador": BY_ID["06"],
    "libertador general bernardo ohiggins": BY_ID["06"],
    "bio bio": BY_ID["08"],
    "aisen": BY_ID["11"],
    "magallanes y la antartica chilena": BY_ID["12"],
}

_REGION_PHRASE = re.compile(r"regi[oó]n(?:\s+de[l]?|\s+del)?\s+(.+)", re.IGNORECASE)


def _parse_positional(code: str) -> Optional[RegionMatch]:
    """Encoding 1: F035 12-part codes carry the region at index 9."""
    parts = code.split(".")
    if len(parts) != 12 or parts[0] != "F035":
        return None
    token = parts[9].strip().upper()
    if token in BY_ID:
        return RegionMatch(BY_ID[token], PARSE_POSITIONAL)
    if token in NATIONAL_REGION_TOKENS:
        return RegionMatch(None, PARSE_NATIONAL)
    return None


def _parse_glued(code: str) -> Optional[RegionMatch]:
    """Encoding 2: mnemonic welded onto token 1, gated by a family whitelist.

    The whitelist is what separates 'F034.SAH|AP' (Arica) from 'F022.C|AP'
    (captaciones) -- both end in the letters AP, only one is regional.
    """
    parts = code.split(".")
    if len(parts) < 2:
        return None
    token = parts[1].strip().upper()
    for mnemonic, region in BY_MNEMONIC.items():
        if not token.endswith(mnemonic):
            continue
        stem = token[: -len(mnemonic)]
        if stem in GLUED_FAMILY_STEMS:
            return RegionMatch(region, PARSE_GLUED)
    # A whitelisted stem with no mnemonic is that family's national aggregate.
    if token in GLUED_FAMILY_STEMS:
        return RegionMatch(None, PARSE_NATIONAL)
    return None


def _parse_roman(code: str) -> Optional[RegionMatch]:
    """Encoding 3: region as a standalone roman-numeral token.

    Merged compounds (RVIIIRXVI = Biobio+Nuble) are rejected: they are not a
    single region and assigning them to either member would be wrong.
    """
    for raw in code.split(".")[1:]:
        token = raw.strip().upper()
        if token in MERGED_ROMAN_TOKENS:
            return None
        if token in BY_ROMAN:
            return RegionMatch(BY_ROMAN[token], PARSE_ROMAN)
    return None


def _parse_cuadro(*texts: str) -> Optional[RegionMatch]:
    """Encoding 4: region recoverable only from free text.

    Required for the F049 labour family, whose codes use INE internal numbers
    that collide with nothing parseable -- the region appears solely in the
    cuadro name ("... , Región de Tarapacá").
    """
    for text in texts:
        folded = strip_accents(text)
        if not folded:
            continue
        phrase = _REGION_PHRASE.search(folded)
        haystack = phrase.group(1) if phrase else None
        if haystack is None:
            continue
        for alias, region in _NAME_ALIASES.items():
            if haystack.startswith(alias):
                return RegionMatch(region, PARSE_CUADRO)
        for name, region in _NAME_LOOKUP:
            if name in haystack:
                return RegionMatch(region, PARSE_CUADRO)
    return None


def parse_region(
    code: str,
    series_name: str = "",
    table_name: str = "",
) -> Optional[RegionMatch]:
    """Resolve the region for a BCCh series code.

    Returns None when no encoding applies (the series is not regional and not a
    recognised national aggregate). A RegionMatch with `is_national` True means
    the series was positively identified as a national/aggregate series.

    Encodings are tried most-specific first: a positional match is unambiguous,
    whereas the cuadro-name fallback is the loosest and runs last.
    """
    if not isinstance(code, str) or not code.strip():
        return None
    code = code.strip()

    for parser in (_parse_positional, _parse_glued, _parse_roman):
        match = parser(code)
        if match is not None:
            return match

    return _parse_cuadro(table_name, series_name)

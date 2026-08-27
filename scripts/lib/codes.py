"""
Purpose:  Parse frequency and economic sector out of BCCh series codes, and
          translate between the three frequency vocabularies used across this
          repo and the BCCh API.
Task:     CRSM dataset construction (SHT spatial rent vs resource rent)
Inputs:   BCCh series codes
Outputs:  n/a (pure functions)
Created:  2026-08-21
Updated:  2026-08-21
Owner:    dpolancon

Sector mapping
--------------
The three sectors this dataset turns on are 03 (Mineria, the resource-rent
axis), 06 (Construccion) and 10 (Servicios de vivienda e inmobiliarios, the
spatial-rent axis). The previously committed coverage inventory had a shifted
mapping that labelled 10 as "Construccion" and 03 as "UNKNOWN"; the table below
was re-derived from the catalog and supersedes it.
"""

from typing import Optional, Tuple

# --- Frequency ---------------------------------------------------------------
# The last dot-token of every code is its frequency. Verified: this resolves
# for 100% of the 30,873 catalog rows, with no fifth value and no blanks.

FREQ_DAILY = "D"
FREQ_MONTHLY = "M"
FREQ_QUARTERLY = "T"  # 'T' for trimestral, BCCh's own letter
FREQ_ANNUAL = "A"

VALID_FREQUENCIES = (FREQ_DAILY, FREQ_MONTHLY, FREQ_QUARTERLY, FREQ_ANNUAL)

# Canonical letter -> the English label used in panel outputs.
FREQ_LABEL = {
    FREQ_DAILY: "Daily",
    FREQ_MONTHLY: "Monthly",
    FREQ_QUARTERLY: "Quarterly",
    FREQ_ANNUAL: "Annual",
}

# Canonical letter -> the uppercase vocabulary storage.py uses for staleness.
FREQ_STORAGE = {
    FREQ_DAILY: "DAILY",
    FREQ_MONTHLY: "MONTHLY",
    FREQ_QUARTERLY: "QUARTERLY",
    FREQ_ANNUAL: "ANNUAL",
}

# Canonical letter -> lowercase slug used in raw output filenames.
FREQ_SLUG = {
    FREQ_DAILY: "daily",
    FREQ_MONTHLY: "monthly",
    FREQ_QUARTERLY: "quarterly",
    FREQ_ANNUAL: "annual",
}

# Rough observation counts per year, for coverage diagnostics.
FREQ_PERIODS_PER_YEAR = {
    FREQ_DAILY: 365,
    FREQ_MONTHLY: 12,
    FREQ_QUARTERLY: 4,
    FREQ_ANNUAL: 1,
}


def parse_frequency(code: str) -> Optional[str]:
    """Return the canonical frequency letter for a series code, or None."""
    if not isinstance(code, str) or "." not in code:
        return None
    token = code.strip().rsplit(".", 1)[-1].upper()
    return token if token in VALID_FREQUENCIES else None


# --- Sector ------------------------------------------------------------------
# F035 codes carry the economic activity at token index 6.

SECTOR_MAP = {
    "01": "Agropecuario-silvícola",
    "02": "Pesca",
    "03": "Minería",
    "04": "Industria",
    "05": "Electricidad, gas, agua y gestión de desechos",
    "06": "Construcción",
    "07": "Comercio, restaurantes y hoteles",
    "08": "Transporte, información y comunicaciones",
    "09": "Servicios financieros y empresariales",
    "10": "Servicios de vivienda e inmobiliarios",
    "11": "Servicios personales",
    "12": "Administración pública",
    "13": "Menos: imputaciones bancarias",
    "102": "Agropecuario-silvícola-pesca",
    "COM": "Comercio",
    "RH": "Restaurantes y hoteles",
    "PB": "Producción de bienes",
    "RB": "Resto de bienes",
    "SERV": "Servicios",
    "CONT": "PIB (contribución)",
    "XBI": "Exportaciones de bienes",
    "XBS": "Exportaciones de servicios",
    "XBSSR": "Exportaciones de bienes y servicios",
}

# Short column labels for report tables. Keyed by the *name* rather than the
# sector id, because table frames carry sector names as column headers. Report
# table headers must be derived from these -- a hand-written header row drifts
# out of alignment with the data the moment the sector set changes, which is
# exactly how Table 2 came to print Antofagasta's mining LQ under "Trade".
SECTOR_SHORT_LABELS_EN = {
    "Agropecuario-silvícola": "Agro",
    "Pesca": "Fish",
    "Minería": "Mining",
    "Industria": "Manuf",
    "Electricidad, gas, agua y gestión de desechos": "EGA",
    "Construcción": "Const",
    "Comercio": "Trade",
    "Restaurantes y hoteles": "Hotels",
    "Transporte, información y comunicaciones": "Transp",
    "Servicios financieros y empresariales": "Finance",
    "Servicios de vivienda e inmobiliarios": "RealEst",
    "Servicios personales": "Personal",
    "Administración pública": "PubAdm",
}

SECTOR_SHORT_LABELS_ES = {
    "Agropecuario-silvícola": "Agro",
    "Pesca": "Pesca",
    "Minería": "Minería",
    "Industria": "Manuf",
    "Electricidad, gas, agua y gestión de desechos": "EGA",
    "Construcción": "Const",
    "Comercio": "Comercio",
    "Restaurantes y hoteles": "Hoteles",
    "Transporte, información y comunicaciones": "Transp",
    "Servicios financieros y empresariales": "Finan",
    "Servicios de vivienda e inmobiliarios": "Inmob",
    "Servicios personales": "Personales",
    "Administración pública": "AdmPub",
}


def short_labels(names, lang="en"):
    """Map sector names to short table headers, preserving the given order.

    Raises KeyError on an unmapped sector so a new sector surfaces as a build
    failure rather than a silently mislabelled column.
    """
    table = SECTOR_SHORT_LABELS_ES if lang == "es" else SECTOR_SHORT_LABELS_EN
    missing = [n for n in names if n not in table]
    if missing:
        raise KeyError(f"No short label for sector(s): {missing}")
    return [table[n] for n in names]


# The SHT framework's two rent axes, plus construction as the investment leg.
SECTOR_MINING = "03"
SECTOR_CONSTRUCTION = "06"
SECTOR_REAL_ESTATE = "10"

# Token meaning "no sector breakdown" -- i.e. the regional total.
SECTOR_TOTAL_TOKEN = "Z"


def parse_sector(code: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (sector_id, sector_name) for an F035 code.

    Returns (None, None) for non-F035 codes and for the aggregate token 'Z',
    which denotes a total rather than a sector.
    """
    if not isinstance(code, str):
        return None, None
    parts = code.strip().split(".")
    if len(parts) != 12 or parts[0] != "F035":
        return None, None
    token = parts[6].strip().upper()
    if token == SECTOR_TOTAL_TOKEN:
        return None, None
    return (token, SECTOR_MAP[token]) if token in SECTOR_MAP else (token, None)


def is_sectoral_total(code: str) -> bool:
    """True when the code is an F035 regional total (no sector breakdown)."""
    parts = code.strip().split(".") if isinstance(code, str) else []
    return len(parts) == 12 and parts[0] == "F035" and parts[6].upper() == SECTOR_TOTAL_TOKEN


# --- Selectors ---------------------------------------------------------------
# Token 7 of an F035 code is a SUB-activity slot. It is 'Z' for most
# region/sector pairs, but not all: mining (03) and construction (06) use '21'
# for some regions, notably Tarapaca. A selector written as the obvious
# `...03\.Z\.Z\.` therefore silently drops those regions -- Tarapaca's 34% mining
# share vanishes from the panel with no error and no empty cell, just a missing
# row. Always build F035 selectors through this function.

F035_SUBACTIVITY_ANY = r"[^.]+"


def f035_pattern(
    measure: str = "PIB",
    flow: str = "FLU",
    valuation: str = "N",
    ref_year: str = "2018",
    sector: str = SECTOR_TOTAL_TOKEN,
    frequency: str = FREQ_ANNUAL,
    region: str = r"\d\d",
) -> str:
    """Build a regex matching one family of F035 regional series.

    The sub-activity slot (token 7) is wildcarded by default, which is the
    whole point -- see the note above.
    """
    return (
        rf"^F035\.{measure}\.{flow}\.{valuation}\.CLP\.{ref_year}\."
        rf"{sector}\.{F035_SUBACTIVITY_ANY}\.Z\.{region}\.0\.{frequency}$"
    )

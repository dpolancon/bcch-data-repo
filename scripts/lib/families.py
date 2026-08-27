"""
Purpose:  Declarative registry of the series families that each publication in
          the programme ingests. One family per report, so that a report's data
          dependency is a named, testable object rather than a regex buried in
          a stage script.
Task:     Publication programme -- BCCh regional data
Inputs:   n/a (pure declarations; consumers pass in a resolved universe)
Outputs:  n/a
Created:  2026-08-26
Updated:  2026-08-26
Owner:    dpolancon
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

# Tier of the two-tier design. Tier A is measured nationally or by the seven
# IPV zones and cannot be disaggregated to the 16 regions; Tier B is genuinely
# regional. Mixing them in one chart without saying so is the single easiest
# way to mislead a reader, so the tier travels with the family.
TIER_NATIONAL = "A"
TIER_REGIONAL = "B"

# Regions that BCCh does not publish for a given family are *absent*, not
# failed. Quarterly mining GDP for the southern regions is the standing
# example: six regions have no series at all because there is no mining to
# report. Data notes must render this differently from a fetch error.
KNOWN_ABSENT_QUARTERLY_MINING = (
    "07",  # Maule
    "08",  # Biobío
    "09",  # La Araucanía
    "10",  # Los Lagos
    "14",  # Los Ríos
    "16",  # Ñuble
)


# --------------------------------------------------------------------------
# Tier A geography. BCCh publishes the housing stock and the price index for a
# handful of coarse zones, NOT for the 16 regions. These labels are the whole
# geographic vocabulary available on the rent axis, and the mapping to regions
# is one-to-many in every case except RM -- which is why no crosswalk to the
# regional panel is offered here. Aggregating Tier B up to these zones is the
# only honest join direction.
# --------------------------------------------------------------------------

ZONE_MAP = {
    "NAC": "Nacional",
    "CAS": "Nacional -- casas",
    "DEP": "Nacional -- departamentos",
    "ZN": "Zona Norte",
    "ZC": "Zona Centro",
    "ZS": "Zona Sur",
    "RM": "Región Metropolitana",
}

# The IPV index carries its zone in the mnemonic rather than in a positional
# token. Note IVPZ1: the transposition is upstream, in BCCh's own catalog, and
# correcting it here would simply fail to match.
IPV_ZONE_MAP = {
    "IVPZ1": "Zona Norte",
    "IPVZ1": "Zona Norte",
    "IPVZ2": "Zona Centro",
    "IPVZ3": "Zona Sur",
    "IPVZ4": "Región Metropolitana",
    "IPVZ41": "RM Centro",
    "IPVZ42": "RM Oriente",
    "IPVZ42C": "RM Oriente -- casas",
    "IPVZ42D": "RM Oriente -- departamentos",
    "IPVZ43": "RM Poniente",
    "IPVZ44": "RM Sur",
}

# Zones that are strict subsets of another zone in the same family. Summing
# across every zone would double-count these, so charts and totals must pick
# one level.
ZONE_SUBSETS = {
    "RM Centro", "RM Oriente", "RM Poniente", "RM Sur",
    "RM Oriente -- casas", "RM Oriente -- departamentos",
    "Nacional -- casas", "Nacional -- departamentos",
}


def parse_zone(code: str) -> str | None:
    """Resolve the Tier A geography label for a series code, or None.

    Checks the IPV mnemonic first (it is more specific), then the positional
    zone token used by the housing-stock family.
    """
    if not isinstance(code, str):
        return None
    parts = code.strip().split(".")
    if len(parts) < 2:
        return None

    mnemonic = parts[1].upper()
    if mnemonic in IPV_ZONE_MAP:
        return IPV_ZONE_MAP[mnemonic]

    for token in parts[2:]:
        upper = token.upper()
        if upper in ZONE_MAP:
            return ZONE_MAP[upper]
    return None


@dataclass(frozen=True)
class SeriesFamily:
    """One publication's data dependency.

    `tokens` are matched against the series code as alternates of a regex, the
    same mechanism the original --sht-only flag used. `expected_regions` is the
    count a complete fetch should yield; a shortfall is a warning, not a crash,
    because BCCh genuinely omits some region/sector pairs -- see `absent`.
    """

    name: str
    report: int
    tier: str
    title_es: str
    tokens: tuple[str, ...]
    frequencies: tuple[str, ...]
    expected_regions: int
    briefing_note: str
    notes: str = ""
    absent: tuple[str, ...] = field(default_factory=tuple)

    def pattern(self) -> str:
        """Regex alternation matching any code in this family.

        Kept for logging and diagnostics. Prefer `matches()` for selection:
        this pattern is unanchored and will hit a token that merely appears
        inside another mnemonic.
        """
        return "|".join(self.tokens)

    def matches(self, code: str) -> bool:
        """True when `code` belongs to this family.

        Anchored on the mnemonic -- the second dot-token -- rather than on the
        code as a whole. An unanchored search matches a token wherever it
        appears, and the mnemonics collide: `F022.CCPNVA` (current accounts,
        Valparaiso) contains "NVA" and was being pulled into the building
        permits family, which owns `F034.NVA{RR}`. The mnemonic carries an
        optional two-letter region suffix, so the test is a prefix test, not
        equality. `SANH` and `SAH` stay distinct under it: "SANHAP" does not
        start with "SAH".
        """
        if not isinstance(code, str):
            return False
        parts = code.strip().split(".")
        if len(parts) < 2:
            return False
        mnemonic = parts[1].upper()
        return any(mnemonic.startswith(t.upper()) for t in self.tokens)


# --------------------------------------------------------------------------
# The programme. Ordered by ingestion cost: each entry introduces exactly one
# new data structure, so the team never meets two unfamiliar encodings at once.
# --------------------------------------------------------------------------

FAMILIES: dict[str, SeriesFamily] = {
    "two_axes": SeriesFamily(
        name="two_axes",
        report=3,
        tier=TIER_REGIONAL,
        title_es="Los dos ejes: renta espacial y renta de recursos",
        # Sector 10 (spatial rent) and 03 (resource rent) ride inside the F035
        # PIB codes already on disk. No new fetch: this family exists to prove
        # the chain, not to add data.
        tokens=("PIB",),
        frequencies=("A", "T"),
        expected_regions=16,
        briefing_note="briefing_two_axes.md",
        notes=(
            "No API calls required -- sector 10 and 03 are already present in "
            "raw_annual.csv. Sector 10 is largely IMPUTED rent from national "
            "accounts; every report leaning on it must say so."
        ),
        absent=KNOWN_ABSENT_QUARTERLY_MINING,
    ),
    "permits": SeriesFamily(
        name="permits",
        report=4,
        tier=TIER_REGIONAL,
        title_es="El ciclo regional de la construcción",
        tokens=("SAH", "SANH", "NVA", "CEYS"),
        frequencies=("M",),
        expected_regions=16,
        briefing_note="briefing_permits.md",
        notes=(
            "First encounter with the two-letter region suffix vocabulary "
            "(AP, TA, AN, ...). Monthly regional data; pairs against sector-06 "
            "construction GDP already on disk."
        ),
    ),
    "housing_wealth": SeriesFamily(
        name="housing_wealth",
        report=5,
        tier=TIER_NATIONAL,
        title_es="El inmueble como reserva de valor",
        # VALT vs VALC is the land-versus-structure split -- the most direct
        # measure of spatial rent the catalog offers, and it is national only.
        tokens=("VALV", "VALT", "VALC", "NUMP", "MCT", "MCC", "IPV", "IVPZ", "DEUBH"),
        frequencies=("A", "T"),
        expected_regions=0,  # seven zones, not regions -- see notes
        briefing_note="briefing_housing_wealth.md",
        notes=(
            "TIER A. Geography is 7 IPV zones (Norte/Centro/Sur + 4 RM "
            "sub-zones), which do NOT map onto the 16 regions. Any Tier A x "
            "Tier B comparison must state the aggregation loss or restrict "
            "itself to Norte/Centro/Sur/RM throughout. Note the upstream "
            "typo: zone 1 is IVPZ1, not IPVZ1."
        ),
    ),
    "financial_depth": SeriesFamily(
        name="financial_depth",
        report=6,
        tier=TIER_REGIONAL,
        title_es="Profundidad financiera y morosidad por región",
        tokens=("DV90", "DCS90", "DCM90", "CCPN", "SCCPN", "SDV"),
        frequencies=("M",),
        expected_regions=16,
        briefing_note="briefing_financial_depth.md",
        notes=(
            "F022 uses the glued-mnemonic encoding. F022.CTOBI is NOT Biobio "
            "and F022.CAP is NOT Arica y Parinacota -- lib.regions' "
            "GLUED_FAMILY_STEMS whitelist exists for exactly this family. "
            "Measures distress and deposit depth, never credit volume: "
            "mortgage volumes are national only."
        ),
    ),
    "interregional_trade": SeriesFamily(
        name="interregional_trade",
        report=7,
        tier=TIER_REGIONAL,
        title_es="Estancamiento del sector dinámico",
        tokens=("CVRV", "CVRC", "NFRV", "NFRC", "XSE"),
        frequencies=("M", "T", "A"),
        expected_regions=16,
        briefing_note="briefing_interregional_trade.md",
        notes=(
            "Compraventas use a NUMERIC region token (15 = Arica y "
            "Parinacota) -- a fifth encoding lib.regions does not yet handle. "
            "Add the parser there, never as a standalone parser elsewhere. "
            "No TFP series exists in the catalog, so 'stagnation' rests on "
            "output shares and shift-share, not productivity."
        ),
    ),
}

# The original --sht-only flag fetched the union of the regional families.
# Kept as an alias so existing invocations and docs stay correct.
SHT_ALIAS = "sht"


def get(name: str) -> SeriesFamily:
    """Look up a family by name, raising with the valid set on a typo."""
    try:
        return FAMILIES[name]
    except KeyError:
        raise KeyError(
            f"Unknown family {name!r}. Known families: {sorted(FAMILIES)}"
        ) from None


def tokens_for(names: Sequence[str]) -> tuple[str, ...]:
    """Union of the code tokens for the named families, order-stable."""
    seen: list[str] = []
    for n in names:
        for tok in get(n).tokens:
            if tok not in seen:
                seen.append(tok)
    return tuple(seen)


def by_report(report: int) -> SeriesFamily:
    """The family a given report number depends on."""
    for fam in FAMILIES.values():
        if fam.report == report:
            return fam
    raise KeyError(f"No family declared for report {report}")


def ordered() -> list[SeriesFamily]:
    """Families in publication order -- which is also ingestion-cost order."""
    return sorted(FAMILIES.values(), key=lambda f: f.report)

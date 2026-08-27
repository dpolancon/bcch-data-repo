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

# Escala de observación. El catálogo del Banco Central publica en cuatro
# escalas, y no son intercambiables: difieren en volumen, en frecuencia
# disponible y en estatus estadístico. El tier binario anterior colapsaba
# nacional con zonal y regional con sectorial-regional, y esa simplificación
# escondía justamente lo que la revisión tiene que mostrar.
#
# La asimetría entre ellas no es un accidente del catálogo. La BDE mide las
# escalas que al Banco Central le interesa gobernar: el grueso es nacional
# porque el mandato es la política monetaria nacional, la región aparece por
# vía de Cuentas Nacionales, la macro-zona aparece como estadística
# experimental, y el área metropolitana no aparece en absoluto.
ESCALA_NACIONAL = "nacional"
ESCALA_ZONAL = "macro-zona"
ESCALA_REGIONAL = "regional"
ESCALA_SECTORIAL_REGIONAL = "sectorial-regional"

ESCALAS = (
    ESCALA_NACIONAL,
    ESCALA_ZONAL,
    ESCALA_REGIONAL,
    ESCALA_SECTORIAL_REGIONAL,
)

# Etiqueta legible y unidad de observación de cada escala, para los
# distintivos del sitio y el encabezado de cada página.
ESCALA_LABEL = {
    ESCALA_NACIONAL: ("NACIONAL", "una economía"),
    ESCALA_ZONAL: ("MACRO-ZONA", "7 zonas"),
    ESCALA_REGIONAL: ("REGIONAL", "16 regiones"),
    ESCALA_SECTORIAL_REGIONAL: ("SECTORIAL-REGIONAL", "16 regiones × 13 sectores"),
}

# Escalas que NO se desagregan a la región. Cruzarlas con una escala regional
# exige declarar la pérdida por agregación, y la única dirección honesta es
# subir el dato regional hasta la zona, nunca bajar el zonal hasta la región.
ESCALAS_NO_REGIONALES = frozenset({ESCALA_NACIONAL, ESCALA_ZONAL})

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


# NAC, CAS y DEP no son macro-zonas: son el total nacional y sus dos
# desagregaciones por tipo de vivienda. Tratarlos como zona infla la escala
# zonal y confunde una tipología con una geografía. Sólo ZN, ZC, ZS y RM son
# macro-zonas, más las cuatro subzonas de la RM en el vocabulario del IPV.
ZONE_TOKENS_GEOGRAFICOS = frozenset({"ZN", "ZC", "ZS", "RM"})
ZONE_TOKENS_NACIONALES = frozenset({"NAC", "CAS", "DEP"})

# Etiquetas que corresponden a una macro-zona y no a un agregado nacional.
ZONAS_GEOGRAFICAS = frozenset(
    {
        "Zona Norte", "Zona Centro", "Zona Sur", "Región Metropolitana",
        "RM Centro", "RM Oriente", "RM Poniente", "RM Sur",
        "RM Oriente -- casas", "RM Oriente -- departamentos",
    }
)

# El token RM sirve a DOS esquemas incompatibles: el zonal
# (NAC/CAS/DEP/ZN/ZC/ZS/RM del stock habitacional) y el de las 16 regiones,
# donde la RM es una región más. Un código con RM aislado es ambiguo, y en el
# catálogo hay 14 series así. Lo que desambigua es la compañía: un mnemónico
# del esquema zonal aparece también con ZN, ZC o ZS; uno regional nunca. NAC
# no sirve para distinguirlos porque ambos esquemas publican total nacional.
def mnemonicos_del_esquema_zonal(codigos) -> frozenset[str]:
    """Mnemónicos que en algún código usan una macro-zona geográfica distinta de RM."""
    # El vocabulario del IPV codifica la zona DENTRO del mnemónico (IPVZ2 es
    # Zona Centro), no en un token posicional, así que entra por declaración y
    # no por detección. Sin esto, IPVZ4 se confunde con la región 13.
    zonales = {m.upper() for m in IPV_ZONE_MAP}
    for code in codigos:
        if not isinstance(code, str):
            continue
        partes = code.strip().split(".")
        if len(partes) < 3:
            continue
        marcas = {t.upper() for t in partes[2:]} & (ZONE_TOKENS_GEOGRAFICOS - {"RM"})
        if marcas:
            zonales.add(partes[1].upper())
    return frozenset(zonales)


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
    escala: str
    title_es: str
    tokens: tuple[str, ...]
    frequencies: tuple[str, ...]
    expected_regions: int
    briefing_note: str
    # A qué objetivo específico y a qué hipótesis de la formulación
    # responde la familia. Vacío mientras no sirva a ninguno.
    objetivo: str = ""
    notes: str = ""
    # Las trampas en español, que es el idioma del sitio. `notes` queda
    # como memoria técnica interna y no se publica.
    notas_es: str = ""
    absent: tuple[str, ...] = field(default_factory=tuple)

    @property
    def es_regional(self) -> bool:
        """True cuando la familia se desagrega a las 16 regiones."""
        return self.escala not in ESCALAS_NO_REGIONALES

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
        escala=ESCALA_SECTORIAL_REGIONAL,
        title_es="Los dos ejes: renta espacial y renta de recursos",
        # Sector 10 (spatial rent) and 03 (resource rent) ride inside the F035
        # PIB codes already on disk. No new fetch: this family exists to prove
        # the chain, not to add data.
        tokens=("PIB",),
        frequencies=("A", "T"),
        expected_regions=16,
        briefing_note="briefing_two_axes.md",
        objetivo=(
            "Contexto de selección de casos. No responde a un objetivo específico: sostiene el marco muestral, al medir cuán extractivas son las economías regionales cuyas capitales el proyecto estudia."
        ),
        notas_es=(
            "Los dos ejes del marco de crecimiento desbalanceado tienen contraparte directa en las cuentas regionales: sector 10 (Servicios de vivienda e inmobiliarios) es renta espacial, sector 03 (Minería) es renta de recursos, sector 06 (Construcción) es la pata de inversión. Ninguna requiere descarga: ya están en raw_annual.csv. El sector 10 es mayoritariamente ALQUILER IMPUTADO de las cuentas nacionales, no arriendo efectivamente pagado; es el supuesto que sostiene todo el eje espacial y se declara en cada reporte que se apoya en él. La familia abarca dos escalas: 2.037 series sectorial-regionales y 209 totales regionales (sector Z). La escala declarada es la principal, no la única."
        ),
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
        escala=ESCALA_REGIONAL,
        title_es="El ciclo regional de la construcción",
        tokens=("SAH", "SANH", "NVA", "CEYS"),
        frequencies=("M",),
        expected_regions=16,
        briefing_note="briefing_permits.md",
        objetivo=(
            "Objetivo 2 — demanda física de suelo. Es el insumo con que la formulación propone reconstruir el Consumo de Suelo Urbano del MINVU a partir de permisos de edificación desde 2010 (Proxy 2)."
        ),
        notas_es=(
            "Primer encuentro con el sufijo de región de dos letras pegado al mnemónico (AP, TA, AN...). Son permisos: intención de construir, no construcción ejecutada. Fuerte estacionalidad, así que toda lectura mes contra mes es ruido; usar variación doce meses. CEYS es constitución de empresas de todo tipo y entra como control de dinamismo empresarial, no como parte del eje espacial: no sumarlo a los otros tres."
        ),
        notes=(
            "First encounter with the two-letter region suffix vocabulary "
            "(AP, TA, AN, ...). Monthly regional data; pairs against sector-06 "
            "construction GDP already on disk."
        ),
    ),
    "housing_wealth": SeriesFamily(
        name="housing_wealth",
        report=5,
        escala=ESCALA_ZONAL,
        title_es="El inmueble como reserva de valor",
        # VALT vs VALC is the land-versus-structure split -- the most direct
        # measure of spatial rent the catalog offers, and it is national only.
        tokens=("VALV", "VALT", "VALC", "NUMP", "MCT", "MCC", "IPV", "IVPZ", "DEUBH"),
        frequencies=("A", "T"),
        expected_regions=0,  # seven zones, not regions -- see notes
        briefing_note="briefing_housing_wealth.md",
        objetivo=(
            "Reproduce y extiende la Figura 4 de la formulación (valor del stock de suelo residencial, agregado y unitario). VALT frente a VALC es la descomposición terreno/construcción de Knoll et al., premisa empírica de la propuesta, medida para Chile."
        ),
        notas_es=(
            "La geografía son zonas, no regiones: Norte, Centro, Sur y cuatro subzonas de la Región Metropolitana. La correspondencia con las 16 regiones es de uno a muchos salvo en la RM, de modo que la única dirección de agregación honesta es subir el dato regional hasta la zona. Ojo con la transposición de origen: la zona 1 es IVPZ1 y no IPVZ1, y corregirla acá sencillamente no encontraría la serie. La familia abarca dos escalas: 56 series zonales y 21 nacionales. VALT y VALC --la descomposición entre valorización del terreno y de la construcción-- sólo existen para NAC, CAS y DEP, de modo que la premisa empírica de Knoll et al. es medible en Chile únicamente a escala nacional y nunca por zona."
        ),
        notes=(
            "TIER A. Geography is 7 IPV zones (Norte/Centro/Sur + 4 RM "
            "sub-zones), which do NOT map onto the 16 regions. Any Tier A x "
            "Tier B comparison must state the aggregation loss or restrict "
            "itself to Norte/Centro/Sur/RM throughout. Note the upstream "
            "typo: zone 1 is IVPZ1, not IPVZ1."
        ),
    ),
    "tasas": SeriesFamily(
        name="tasas",
        report=8,
        escala=ESCALA_NACIONAL,
        title_es="El precio del dinero: tasas y apalancamiento",
        # La Tabla 1 de la formulación completa. Es enteramente de la BDE y es
        # el conjunto de regresores de H1: la tasa de descuento con que se
        # valoriza un activo que no se deprecia.
        tokens=(
            "TPM",      # tasa de política monetaria y operaciones BCCh
            "ECB",      # expectativa de TPM, encuesta
            "TIP",      # captación y colocación a distintos plazos
            "BCU",      # bonos BCCh en UF
            "VIV",      # tasa de créditos hipotecarios
            "IPSA",     # IPSA e índices bursátiles externos
            "DEUBH",    # deuda hipotecaria bancaria de hogares
        ),
        frequencies=("D", "M", "T", "A"),
        expected_regions=0,  # nacional: no se desagrega y no lo necesita
        briefing_note="briefing_tasas.md",
        objetivo=(
            "Objetivo 4 e hipótesis H1 — el efecto del descenso de las tasas "
            "sobre la variación del precio del suelo. Es el único conjunto de "
            "regresores de H1 que la BDE publica completo."
        ),
        notas_es=(
            "Escala nacional, y no le falta desagregación: la tasa de "
            "descuento que discute H1 es un precio único de la economía. La "
            "cobertura es desigual entre series (captación y colocación desde "
            "1983; TPM desde 1995; hipotecarias y bonos UF desde 2002), de "
            "modo que cualquier ventana común es más corta que la más larga. "
            "DEUBH mide apalancamiento de hogares como porcentaje del PIB y "
            "del ingreso disponible, y es la contraparte financiera del stock "
            "de vivienda que mide housing_wealth."
        ),
    ),
    "financial_depth": SeriesFamily(
        name="financial_depth",
        report=6,
        escala=ESCALA_REGIONAL,
        title_es="Profundidad financiera y morosidad por región",
        tokens=("DV90", "DCS90", "DCM90", "CCPN", "SCCPN", "SDV"),
        frequencies=("M",),
        expected_regions=16,
        briefing_note="briefing_financial_depth.md",
        objetivo=(
            "Objetivo 4 — huella regional del ciclo financiero. Mide angustia y profundidad de depósitos, nunca volumen de crédito: los volúmenes hipotecarios son nacionales."
        ),
        notas_es=(
            "F022 usa la codificación de mnemónico pegado. F022.CTOBI NO es Biobío y F022.CAP NO es Arica y Parinacota: la lista blanca de raíces en lib.regions existe exactamente para esta familia. La selección por familia se ancla al mnemónico por la misma razón, después de que NVA hiciera match dentro de CCPNVA."
        ),
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
        escala=ESCALA_REGIONAL,
        title_es="Estancamiento del sector dinámico",
        tokens=("CVRV", "CVRC", "NFRV", "NFRC", "XSE"),
        frequencies=("M", "T", "A"),
        expected_regions=16,
        briefing_note="briefing_interregional_trade.md",
        objetivo=(
            "Objetivo 1 — dinamismo del sector productivo. El estancamiento se argumenta con participaciones de producto y descomposición shift-share, nunca como caída de productividad medida: el catálogo no contiene ninguna serie de PTF."
        ),
        notas_es=(
            "Las compraventas usan un token de región NUMÉRICO (15 = Arica y Parinacota), una quinta codificación que lib.regions todavía no resuelve. El parser va ahí, nunca como parser suelto en otro lado."
        ),
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

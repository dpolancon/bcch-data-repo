"""
Stage:    09 -- Build themed panels for the publication programme
Purpose:  Compile the per-report analytical panels declared in lib.families,
          starting with the two-axis panel (spatial rent vs resource rent) that
          Report 3 publishes. Panels are the single input the site reads, so
          every number on a page is traceable to a CSV in data/.
Task:     Publication programme -- BCCh regional data
Inputs:   data/raw/regional-spatial-macro-dataset/raw_annual.csv (via lib.sectors)
          data/panel_regional_pib_annual.csv
Outputs:  data/panel_two_axes_annual.csv
          data/panel_two_axes_summary.csv
          data/panel_permits_{monthly,annual,summary}.csv
Created:  2026-08-26
Updated:  2026-08-26
Owner:    dpolancon
Run:      python scripts/09_build_theme_panels.py [--family two_axes]
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd

from lib import families as families_lib
from lib.codes import SECTOR_CONSTRUCTION, SECTOR_MINING, SECTOR_REAL_ESTATE
from lib.paths import CRSM_RAW_DIR, DATA_DIR
from lib.regions import REGIONS
from lib.sectors import compute_sector_shares
from lib.stats import compute_weighted_gini

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s"
)
logger = logging.getLogger(__name__)

# The three axes travel together: two rents plus the investment leg that links
# them. Named here rather than inlined so a reader of the CSV can find them.
AXIS_SECTORS = {
    SECTOR_REAL_ESTATE: "spatial_rent",
    SECTOR_MINING: "resource_rent",
    SECTOR_CONSTRUCTION: "construction",
}


def build_two_axes() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Region x year shares for the two rent axes, plus a per-year summary.

    Shares are nominal-over-nominal (`valuation="N"`): chained volumes are not
    additive across sectors, so a share built from them would not sum to the
    regional total. compute_sector_shares() already defaults this way; the
    argument is passed explicitly because the choice is load-bearing.
    """
    shares = compute_sector_shares(valuation="N")

    axes = shares[shares["sector_id"].isin(AXIS_SECTORS)].copy()
    if axes.empty:
        raise SystemExit(
            "No rows for sectors 03/06/10 -- has raw_annual.csv been fetched?"
        )
    axes["axis"] = axes["sector_id"].map(AXIS_SECTORS)

    # The sector panel carries ASCII slugs ("Arica_y_Parinacota"), which are the
    # right join key and the wrong thing to print. Carry both: `region_name`
    # stays the stable key, `region_display` is what a reader sees.
    display = {r.name_ascii: r.name_es for r in REGIONS}
    unmapped = set(axes["region_name"]) - set(display)
    if unmapped:
        raise SystemExit(f"Region names with no display form: {sorted(unmapped)}")
    axes["region_display"] = axes["region_name"].map(display)

    panel = (
        axes[
            [
                "year",
                "region_code",
                "region_name",
                "region_display",
                "sector_id",
                "sector_name",
                "axis",
                "value",
                "region_total",
                "share",
            ]
        ]
        .sort_values(["year", "region_code", "sector_id"])
        .reset_index(drop=True)
    )

    # The ratio is the point of the whole framework: how much of a region's
    # output is spatial rent per unit of resource rent. Undefined where mining
    # is absent, and left as NaN rather than zero-filled -- a region with no
    # mining has no ratio, not a ratio of zero.
    wide = panel.pivot_table(
        index=["year", "region_code", "region_name", "region_display"],
        columns="axis",
        values="share",
    ).reset_index()
    for col in ("spatial_rent", "resource_rent", "construction"):
        if col not in wide.columns:
            wide[col] = pd.NA
    wide["rent_ratio"] = wide["spatial_rent"] / wide["resource_rent"]

    # Cross-regional dispersion of each axis, year by year. Unweighted here:
    # this measures how unevenly the axis is distributed across regions as
    # units, not welfare, so no population weight belongs in it.
    rows = []
    for year, grp in wide.groupby("year"):
        ones = pd.Series([1.0] * len(grp), index=grp.index)
        rec = {"year": int(year), "n_regions": int(len(grp))}
        for axis in ("spatial_rent", "resource_rent", "construction"):
            vals = grp[axis].astype(float)
            rec[f"{axis}_mean"] = float(vals.mean())
            rec[f"{axis}_max"] = float(vals.max())
            rec[f"{axis}_argmax"] = grp.loc[vals.idxmax(), "region_display"]
            rec[f"{axis}_gini"] = float(compute_weighted_gini(vals, ones))
        rows.append(rec)
    summary = pd.DataFrame(rows).sort_values("year").reset_index(drop=True)

    return panel, summary


# Mnemónicos de la familia de permisos, con lo que mide cada uno. SAH y NVA
# son cantidad pura --metros y unidades-- sin precio de por medio; ahí está su
# valor para el programa. CEYS entra como control de dinamismo empresarial y
# NO forma parte del eje espacial: no se suma a los otros tres.
PERMISOS = {
    "SAH": ("superficie_habitacional", "m2", True),
    "SANH": ("superficie_no_habitacional", "m2", True),
    "NVA": ("viviendas_autorizadas", "unidades", True),
    "CEYS": ("empresas_constituidas", "unidades", False),
}

SUFIJOS_REGION = (
    "AP", "TA", "AN", "AT", "CO", "VA", "RM", "LI",
    "ML", "NB", "BI", "AR", "LR", "LL", "AI", "MA",
)


def _mnemonico(code: str) -> str:
    """Mnemónico sin el sufijo de región pegado."""
    mn = code.split(".")[1].upper()
    for suf in SUFIJOS_REGION:
        if mn.endswith(suf) and len(mn) > len(suf):
            return mn[: -len(suf)]
    return mn


def build_permits() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Permisos de edificación por región, mensual y anual.

    Son flujos mensuales con estacionalidad fuerte --los permisos caen en
    invierno austral y en enero--, de modo que el panel mensual carga la suma
    móvil de doce meses y ninguna lectura mes contra mes tiene sentido. El
    panel anual se limita a años calendario COMPLETOS: las series del INE
    terminan en mayo de 2026, y graficar un año parcial junto a años completos
    inventa una caída que no ocurrió.
    """
    ruta = CRSM_RAW_DIR / "raw_monthly.csv"
    if not ruta.exists():
        raise SystemExit(f"Falta {ruta}. Corra la etapa 01 con --family permits.")

    # dtype=str preserva el relleno de ceros de region_id y sector_id, pero
    # anula parse_dates: la conversión va explícita y con formato ISO, que es
    # como lib.client normaliza las fechas al escribir la capa cruda.
    crudo = pd.read_csv(ruta, dtype=str, low_memory=False)
    crudo["date"] = pd.to_datetime(crudo["date"], format="ISO8601")
    crudo["mnemonico"] = crudo["series_code"].map(_mnemonico)
    sub = crudo[crudo["mnemonico"].isin(PERMISOS)].copy()
    if sub.empty:
        raise SystemExit(
            "No hay filas de permisos en raw_monthly.csv -- ¿se descargó la familia?"
        )

    sub["valor"] = pd.to_numeric(sub["value"], errors="coerce")
    sub["indicador"] = sub["mnemonico"].map(lambda m: PERMISOS[m][0])
    sub["unidad"] = sub["mnemonico"].map(lambda m: PERMISOS[m][1])
    sub["eje_espacial"] = sub["mnemonico"].map(lambda m: PERMISOS[m][2])

    display = {r.name_ascii: r.name_es for r in REGIONS}
    por_id = {r.id: r.name_es for r in REGIONS}
    sub["region_display"] = sub["region_id"].map(por_id)
    faltan = sub[sub["region_display"].isna()]["region_id"].unique()
    if len(faltan):
        raise SystemExit(f"Regiones sin nombre: {sorted(faltan)}")

    mensual = (
        sub[[
            "date", "region_id", "region_display", "mnemonico", "indicador",
            "unidad", "eje_espacial", "valor",
        ]]
        .sort_values(["indicador", "region_id", "date"])
        .reset_index(drop=True)
    )
    # Suma móvil de doce meses: es la única lectura defendible de un flujo
    # mensual con esta estacionalidad, y evita que alguien grafique enero.
    mensual["suma_12m"] = mensual.groupby(
        ["indicador", "region_id"], sort=False
    )["valor"].transform(lambda x: x.rolling(12, min_periods=12).sum())

    # Panel anual, sólo años completos y comunes a los cuatro indicadores.
    mensual["anio"] = mensual["date"].dt.year
    conteo = (
        mensual.groupby(["indicador", "region_id", "anio"])["valor"]
        .size()
        .reset_index(name="meses")
    )
    completos = conteo[conteo["meses"] == 12]
    anios_por_ind = completos.groupby("indicador")["anio"].apply(set)
    comunes = set.intersection(*anios_por_ind) if len(anios_por_ind) else set()
    logger.info(
        "Años completos comunes a los %d indicadores: %d-%d",
        len(anios_por_ind), min(comunes), max(comunes),
    )

    anual = (
        mensual[mensual["anio"].isin(comunes)]
        .groupby(
            ["anio", "region_id", "region_display", "indicador", "unidad",
             "eje_espacial"],
            as_index=False,
        )["valor"]
        .sum()
    )
    # La Región Metropolitana domina en niveles por población, y el Banco
    # Central no publica población regional como serie propia: sólo aparece
    # como denominador dentro de las tablas per cápita. Comparar regiones
    # exige entonces un índice, no un per cápita que no se puede construir.
    base = min(comunes)
    ref = (
        anual[anual["anio"] == base]
        .set_index(["region_id", "indicador"])["valor"]
        .rename("base")
    )
    anual = anual.join(ref, on=["region_id", "indicador"])
    anual["indice_base100"] = 100 * anual["valor"] / anual["base"]
    anual = anual.drop(columns=["base"]).sort_values(
        ["indicador", "region_id", "anio"]
    ).reset_index(drop=True)

    # Resumen nacional por indicador y año, con variación anual.
    resumen = (
        anual.groupby(["anio", "indicador", "unidad"], as_index=False)["valor"]
        .sum()
        .sort_values(["indicador", "anio"])
    )
    resumen["var_anual_pct"] = 100 * resumen.groupby("indicador")["valor"].pct_change()
    resumen = resumen.reset_index(drop=True)

    return mensual.drop(columns=["anio"]), anual, resumen


BUILDERS = {"two_axes": build_two_axes, "permits": build_permits}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build themed analytical panels for the publication programme."
    )
    parser.add_argument(
        "--family",
        default="two_axes",
        choices=sorted(BUILDERS),
        help="which report's panel to build",
    )
    args = parser.parse_args()

    fam = families_lib.get(args.family)
    logger.info(
        "Construyendo panel de %s (reporte %d, escala %s)",
        fam.name, fam.report, fam.escala,
    )

    marcos = BUILDERS[args.family]()

    # Cada familia decide cuántos marcos publica. two_axes emite panel anual y
    # resumen; permits emite mensual, anual y resumen, porque un flujo mensual
    # no se deja resumir sin perder la estacionalidad que lo define.
    if len(marcos) == 2:
        nombres = ["annual", "summary"]
    elif len(marcos) == 3:
        nombres = ["monthly", "annual", "summary"]
    else:
        raise SystemExit(f"{args.family} devolvió {len(marcos)} marcos")

    for sufijo, marco in zip(nombres, marcos):
        ruta = DATA_DIR / f"panel_{args.family}_{sufijo}.csv"
        marco.to_csv(ruta, index=False, encoding="utf-8")
        col_region = "region_code" if "region_code" in marco.columns else "region_id"
        detalle = ""
        if col_region in marco.columns:
            detalle = f" | {marco[col_region].nunique()} regiones"
        logger.info(
            "Escribió %-34s %6d filas%s", ruta.name, len(marco), detalle
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

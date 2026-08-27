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
          data/panel_financial_depth_{monthly,annual,summary}.csv
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
from lib import trade as trade_lib
from lib.codes import SECTOR_CONSTRUCTION, SECTOR_MINING, SECTOR_REAL_ESTATE
from lib.paths import CRSM_RAW_DIR, DATA_DIR
from lib.regions import REGIONS
from lib.sectors import compute_sector_shares
from lib.stats import compute_weighted_gini
from lib import unidades as unidades_lib

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

    mensual = unidades_lib.normalizar(mensual.drop(columns=["anio"]))
    anual = unidades_lib.normalizar(anual)
    resumen = unidades_lib.normalizar(resumen)
    return mensual, anual, resumen


# Los seis indicadores de la familia, con su tipo de medida. La distinción
# tasa/stock es la que impide el error más fácil de cometer acá: ninguno de los
# seis es un flujo, así que sumar meses no significa nada. Un stock se promedia,
# una tasa se promedia, y nada se acumula.
FINANCIERO = {
    "DV90": ("mora_vivienda", "tasa", "% de la cartera de vivienda"),
    "DCS90": ("mora_consumo", "tasa", "% de la cartera de consumo"),
    "DCM90": ("mora_comercial", "tasa", "% de la cartera comercial"),
    # Las unidades salen del nombre que publica el Banco Central, no de un
    # supuesto: CCPN cuenta cuentas de personas naturales, SCCPN es un saldo
    # promedio en pesos y SDV un saldo total en MILLONES de pesos. Confundir
    # las dos últimas escalas por tres órdenes de magnitud.
    "CCPN": ("cuentas_corrientes", "stock", "número de cuentas de personas naturales"),
    "SCCPN": ("saldo_medio_cuenta", "stock", "pesos nominales por cuenta"),
    "SDV": ("depositos_vista", "stock", "millones de pesos nominales"),
}


def build_financial_depth() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Morosidad y profundidad de depósitos por región.

    Mide angustia del deudor y profundidad de depósitos, **nunca volumen de
    crédito**: los montos hipotecarios, las tasas y el LTV son nacionales. Es
    decir, dice cómo le va al deudor en cada región, no cuánto crédito entró en
    cada región; la segunda pregunta no se responde con la BDE.

    Ninguno de los seis indicadores es un flujo. Las tres tasas de mora son
    porcentajes de carteras distintas --con denominadores distintos, de modo que
    su suma no significa nada-- y los tres saldos son stocks. Todo se promedia;
    nada se acumula.
    """
    ruta = CRSM_RAW_DIR / "raw_monthly.csv"
    if not ruta.exists():
        raise SystemExit(f"Falta {ruta}. Corra la etapa 01 con --family financial_depth.")

    crudo = pd.read_csv(ruta, dtype=str, low_memory=False)
    crudo["date"] = pd.to_datetime(crudo["date"], format="ISO8601")
    crudo["mnemonico"] = crudo["series_code"].map(_mnemonico)
    sub = crudo[crudo["mnemonico"].isin(FINANCIERO)].copy()
    if sub.empty:
        raise SystemExit(
            "No hay filas de la familia en raw_monthly.csv -- ¿se descargó?"
        )

    sub["valor"] = pd.to_numeric(sub["value"], errors="coerce")
    sub["indicador"] = sub["mnemonico"].map(lambda m: FINANCIERO[m][0])
    sub["medida"] = sub["mnemonico"].map(lambda m: FINANCIERO[m][1])
    sub["unidad"] = sub["mnemonico"].map(lambda m: FINANCIERO[m][2])

    por_id = {r.id: r.name_es for r in REGIONS}
    sub["region_display"] = sub["region_id"].map(por_id)
    faltan = sub[sub["region_display"].isna()]["region_id"].unique()
    if len(faltan):
        raise SystemExit(f"Regiones sin nombre: {sorted(faltan)}")

    mensual = (
        sub[[
            "date", "region_id", "region_display", "mnemonico", "indicador",
            "medida", "unidad", "valor",
        ]]
        .sort_values(["indicador", "region_id", "date"])
        .reset_index(drop=True)
    )
    # Promedio móvil de doce meses. Para una tasa suaviza; para un stock quita
    # la estacionalidad de fin de año. En ningún caso es una acumulación.
    mensual["promedio_12m"] = mensual.groupby(
        ["indicador", "region_id"], sort=False
    )["valor"].transform(lambda x: x.rolling(12, min_periods=12).mean())

    mensual["anio"] = mensual["date"].dt.year
    conteo = (
        mensual.groupby(["indicador", "region_id", "anio"])["valor"]
        .size()
        .reset_index(name="meses")
    )
    completos = conteo[conteo["meses"] == 12]
    anios = completos.groupby("indicador")["anio"].apply(set)
    comunes = set.intersection(*anios) if len(anios) else set()
    logger.info(
        "Años completos comunes a los %d indicadores: %d-%d",
        len(anios), min(comunes), max(comunes),
    )

    # Promedio de los doce meses, para tasas y para stocks por igual.
    anual = (
        mensual[mensual["anio"].isin(comunes)]
        .groupby(
            ["anio", "region_id", "region_display", "indicador", "medida", "unidad"],
            as_index=False,
        )["valor"]
        .mean()
        .sort_values(["indicador", "region_id", "anio"])
        .reset_index(drop=True)
    )

    # Resumen nacional. Una tasa se promedia entre regiones --no se pondera,
    # porque el tamaño de cada cartera regional no está en esta familia-- y un
    # stock se suma, porque contar cuentas de todas las regiones sí tiene
    # sentido. Por eso el resumen distingue las dos operaciones.
    # La operación la decide la unidad, no el tipo de medida. `medida`
    # distingue tasa de stock, pero eso no basta: SCCPN es un stock y es un
    # saldo PROMEDIO por cuenta, así que sumarlo entre regiones no da nada
    # interpretable. lib.unidades declara la agregación de cada unidad y acá
    # se respeta: se suma lo sumable y se promedia el resto.
    claves = ["anio", "indicador", "medida", "unidad"]
    agregable = anual["unidad"].map(
        lambda u: unidades_lib.resolver(u)[2] == unidades_lib.TOTAL
    )
    sumables = (
        anual[agregable].groupby(claves, as_index=False)["valor"].sum()
    )
    promediables = (
        anual[~agregable].groupby(claves, as_index=False)["valor"].mean()
    )
    resumen = pd.concat([sumables, promediables], ignore_index=True)

    # Concentración metropolitana de las cuentas: la única de las seis series
    # donde la participación de una región dice algo por sí sola.
    cuentas = anual[anual["indicador"] == "cuentas_corrientes"]
    total = cuentas.groupby("anio")["valor"].sum()
    rm = cuentas[cuentas["region_id"] == "13"].set_index("anio")["valor"]
    conc = (100 * rm / total).rename("valor").reset_index()
    conc["indicador"] = "concentracion_rm_cuentas"
    conc["medida"] = "tasa"
    conc["unidad"] = "% de las cuentas del país"
    resumen = pd.concat([resumen, conc], ignore_index=True).sort_values(
        ["indicador", "anio"]
    ).reset_index(drop=True)

    # Todo a la unidad canónica de su dimensión: los saldos quedan en pesos y
    # no unos en pesos y otros en millones. El marco además declara si el
    # valor se suma entre regiones o no.
    mensual = unidades_lib.normalizar(mensual.drop(columns=["anio"]))
    anual = unidades_lib.normalizar(anual)
    resumen = unidades_lib.normalizar(resumen)
    return mensual, anual, resumen



# Las seis series de compraventas, en monto y en facturas. Todas son FLUJOS
# mensuales, asi que sumar meses si tiene sentido -- al reves que la familia
# financiera, donde ninguno de los seis indicadores era acumulable.
COMPRAVENTAS = {
    "CVRVITE": ("venta_interregional", "miles de millones de pesos"),
    "CVRVITA": ("venta_intrarregional", "miles de millones de pesos"),
    "CVRCITE": ("compra_interregional", "miles de millones de pesos"),
    "CVRCITA": ("compra_intrarregional", "miles de millones de pesos"),
    "NFRVITE": ("facturas_venta_interregional", "miles de unidades"),
    "NFRCITE": ("facturas_compra_interregional", "miles de unidades"),
}


def build_interregional_trade() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Panel de comercio interregional: mensual, anual y resumen.

    Lo que el Banco Central publica son MARGENES, no la matriz origen-destino:
    cuanto vende cada region al resto del pais y cuanto le compra. Para 16
    regiones eso son 32 numeros por mes contra 240 flujos bilaterales que no se
    publican. Los margenes cuadran exactamente entre si --las ventas
    interregionales agregadas igualan a las compras--, lo que muestra que son
    las filas y columnas de una misma matriz cerrada que el Banco calcula y no
    difunde.

    Por eso este panel publica la secuencia de grados de la red (apertura,
    autocontencion, balance neto), que es lo medible, y no centralidad ni
    comunidades, que exigirian inventar primero la topologia. Ver
    lib.trade.independence_baseline.
    """
    margenes = trade_lib.load_trade_margins()

    # Los margenes solo sirven si las identidades publicadas se sostienen.
    desvios = trade_lib.check_identities(margenes)
    excedidas = desvios[desvios > trade_lib.IDENTITY_TOL]
    if not excedidas.empty:
        raise SystemExit(
            f"Las identidades de compraventas dejaron de cumplirse: {excedidas.to_dict()}"
        )

    crudo = trade_lib._require_raw_monthly()
    crudo = crudo[crudo["series_code"].str.contains("CVR|NFR", na=False)].copy()
    crudo["familia"] = crudo["series_code"].str.split(".").str[1]
    crudo = crudo[crudo["familia"].isin(COMPRAVENTAS)]

    crudo["indicador"] = crudo["familia"].map(lambda f: COMPRAVENTAS[f][0])
    crudo["unidad"] = crudo["familia"].map(lambda f: COMPRAVENTAS[f][1])
    crudo["anio"] = crudo["date"].dt.year

    mensual = crudo.rename(columns={"region_id": "region_code", "value": "valor"})[
        ["date", "anio", "region_code", "region_name", "indicador", "unidad", "valor"]
    ].sort_values(["date", "region_code", "indicador"])

    # Solo anios completos: un anio a medias sumado contra anios enteros parece
    # un derrumbe.
    meses = mensual.groupby("anio")["date"].nunique()
    mensual = mensual[mensual["anio"].isin(meses[meses == 12].index)]

    anual = (
        mensual.groupby(["anio", "region_code", "region_name", "indicador", "unidad"],
                        as_index=False)["valor"].sum()
    )

    # Resumen: la secuencia de grados de la red, en el ultimo anio completo.
    ultimo = int(anual["anio"].max())
    ind = trade_lib.compute_indicators(margenes, year=ultimo)
    resumen = ind.melt(
        id_vars=["region_code", "region_name"],
        value_vars=["openness", "self_containment", "net_balance_pct"],
        var_name="indicador", value_name="valor",
    )
    resumen["indicador"] = resumen["indicador"].map({
        "openness": "apertura",
        "self_containment": "autocontencion",
        "net_balance_pct": "balance_neto",
    })
    # Apertura y balance no comparten denominador; la unidad lo dice.
    resumen["unidad"] = resumen["indicador"].map({
        "apertura": "% de las ventas de la región",
        "autocontencion": "% de las ventas de la región",
        "balance_neto": "% del intercambio interregional bruto",
    })
    resumen["anio"] = ultimo

    mensual = unidades_lib.normalizar(mensual.drop(columns=["anio"]))
    anual = unidades_lib.normalizar(anual)
    resumen = unidades_lib.normalizar(resumen)
    return mensual, anual, resumen


BUILDERS = {
    "two_axes": build_two_axes,
    "permits": build_permits,
    "financial_depth": build_financial_depth,
    "interregional_trade": build_interregional_trade,
}


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

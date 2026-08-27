"""
Stage:    13 -- Censo de la BDE del Banco Central por escala de observación
Purpose:  Clasificar cada serie del catálogo en una de las cuatro escalas que
          publica el Banco Central --nacional, macro-zona, regional y
          sectorial-regional-- y contar cuántas hay en cada una, por capítulo y
          frecuencia. Es el insumo de toda la revisión: la asimetría entre
          escalas es su hallazgo central.
Task:     Revisión multiescalar de la BDE -- proyecto de precio del suelo
Inputs:   data/catalogo_series.xlsx
Outputs:  data/censo_bde_series.csv
          data/censo_bde_resumen.csv
Created:  2026-08-27
Updated:  2026-08-27
Owner:    dpolancon
Run:      python scripts/13_census_bde.py
"""

from __future__ import annotations

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd

from lib import codes as codes_lib
from lib import families as families_lib
from lib.paths import CATALOG_XLSX, DATA_DIR
from lib.regions import parse_region

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s"
)
logger = logging.getLogger(__name__)

# El catálogo trae cuatro columnas y ninguna es fecha. La frecuencia se deriva
# del último token del código; la cobertura temporal SOLO se conoce
# descargando. Por eso este censo es exhaustivo en existencia y nunca en span:
# afirmar un rango de fechas acá sería inventarlo.
COL_CHAPTER = "CAPÍTULO"
COL_TABLE = "NOMBRE CUADRO"
COL_CODE = "CÓDIGO"
COL_NAME = "NOMBRE DE LA SERIE"


def clasificar(
    code: str, name: str, table: str, mnemonicos_zonales: frozenset[str]
) -> tuple[str, str | None, str | None, str | None]:
    """Escala de observación de una serie, con la geografía y el sector que la fijan.

    El orden de las pruebas importa, y la primera resuelve una ambigüedad real:
    el token RM pertenece tanto al esquema de macro-zonas del stock
    habitacional como al de las 16 regiones. Una serie con RM cuyo mnemónico
    aparece también con ZN, ZC o ZS es zonal; si no, la RM es una región más.
    Después: región con sector es sectorial-regional, región sola es regional,
    y el resto es nacional por descarte, que es lo correcto porque la BDE
    publica la mayor parte de su catálogo sin geografía alguna.
    """
    zona = families_lib.parse_zone(code)
    es_geografica = zona in families_lib.ZONAS_GEOGRAFICAS
    mnemonico = code.split(".")[1].upper() if "." in code else ""
    if es_geografica and mnemonico in mnemonicos_zonales:
        return families_lib.ESCALA_ZONAL, None, zona, None

    match = parse_region(code, name, table)
    region = match.region.id if (match and match.region) else None
    sector_id, _ = codes_lib.parse_sector(code)
    tiene_sector = sector_id is not None and sector_id != codes_lib.SECTOR_TOTAL_TOKEN

    if region and tiene_sector:
        return families_lib.ESCALA_SECTORIAL_REGIONAL, region, None, sector_id
    if region:
        return families_lib.ESCALA_REGIONAL, region, None, None
    if es_geografica:
        return families_lib.ESCALA_ZONAL, None, zona, None
    # NAC, CAS y DEP resuelven "zona" pero son agregados nacionales.
    return families_lib.ESCALA_NACIONAL, None, None, None


def main() -> int:
    logger.info("Leyendo el catálogo...")
    df = pd.read_excel(CATALOG_XLSX, dtype=str)
    df.columns = [c.strip() for c in df.columns]

    filas_catalogo = len(df)
    # El catálogo repite un mismo código bajo varios nombres de cuadro: contar
    # filas cuenta entradas de cuadro, no series. Se deduplica antes de contar
    # nada, conservando el primer cuadro como referencia.
    df = df.drop_duplicates(subset=[COL_CODE]).reset_index(drop=True)
    logger.info(
        "Catálogo: %d filas -> %d códigos únicos (%d repeticiones)",
        filas_catalogo, len(df), filas_catalogo - len(df),
    )

    # Precómputo para desambiguar el token RM entre los dos esquemas.
    mnemonicos_zonales = families_lib.mnemonicos_del_esquema_zonal(df[COL_CODE])
    logger.info(
        "Mnemónicos del esquema zonal: %d (%s)",
        len(mnemonicos_zonales), ", ".join(sorted(mnemonicos_zonales)),
    )

    registros = []
    sin_frecuencia = 0
    for code, name, table, chapter in zip(
        df[COL_CODE], df[COL_NAME], df[COL_TABLE], df[COL_CHAPTER]
    ):
        code = str(code).strip()
        name, table, chapter = str(name).strip(), str(table).strip(), str(chapter).strip()

        escala, region, zona, sector = clasificar(
            code, name, table, mnemonicos_zonales
        )
        frecuencia = codes_lib.parse_frequency(code)
        if frecuencia is None:
            sin_frecuencia += 1

        registros.append(
            {
                "codigo": code,
                "nombre": name,
                "capitulo": chapter,
                "cuadro": table,
                "escala": escala,
                "frecuencia": frecuencia,
                "region_id": region,
                "zona": zona,
                "sector_id": sector,
            }
        )

    censo = pd.DataFrame(registros)
    if sin_frecuencia:
        logger.warning("%d códigos sin frecuencia resoluble", sin_frecuencia)

    resumen = (
        censo.groupby(["escala", "capitulo", "frecuencia"], dropna=False)
        .size()
        .reset_index(name="series")
        .sort_values(["escala", "series"], ascending=[True, False])
        .reset_index(drop=True)
    )

    ruta_censo = DATA_DIR / "censo_bde_series.csv"
    ruta_resumen = DATA_DIR / "censo_bde_resumen.csv"
    censo.to_csv(ruta_censo, index=False, encoding="utf-8")
    resumen.to_csv(ruta_resumen, index=False, encoding="utf-8")

    total = len(censo)
    logger.info("--- Censo por escala ---")
    for escala in families_lib.ESCALAS:
        sub = censo[censo["escala"] == escala]
        if sub.empty:
            continue
        cap = sub["capitulo"].value_counts()
        logger.info(
            "%-20s %6d series (%4.1f%%) | %d capítulos | frecuencias: %s",
            escala, len(sub), 100 * len(sub) / total,
            sub["capitulo"].nunique(),
            "".join(sorted(sub["frecuencia"].dropna().unique())),
        )
        logger.info("%22s mayor: %s (%d)", "", cap.index[0][:42], cap.iloc[0])

    logger.info("Escribió %s (%d filas)", ruta_censo.name, len(censo))
    logger.info("Escribió %s (%d filas)", ruta_resumen.name, len(resumen))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

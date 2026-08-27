"""
Purpose:  Genera las páginas de escala del sitio -- nacional, macro-zona,
          regional y sectorial-regional -- desde el censo de la etapa 13. Cada
          página sigue el mismo patrón: censo primero, profundidad después, y
          al final lo que esa escala no puede sostener.
Task:     Revisión multiescalar de la BDE -- proyecto de precio del suelo
Inputs:   data/censo_bde_series.csv (vía el llamador)
Outputs:  texto .qmd (el llamador escribe)
Created:  2026-08-27
Updated:  2026-08-27
Owner:    dpolancon
"""

from __future__ import annotations

import pandas as pd

from lib import families as families_lib
from lib import site as site_lib

CENSO_CSV = "censo_bde_series.csv"

# Orden de presentación: de la unidad más agregada a la más fina. No es
# alfabético ni por tamaño, sino el recorrido que hace inteligible la
# asimetría: se empieza donde la BDE es abundante y se termina donde el
# proyecto necesita el dato.
ORDEN = (
    families_lib.ESCALA_NACIONAL,
    families_lib.ESCALA_ZONAL,
    families_lib.ESCALA_REGIONAL,
    families_lib.ESCALA_SECTORIAL_REGIONAL,
)

SLUG = {
    families_lib.ESCALA_NACIONAL: "nacional",
    families_lib.ESCALA_ZONAL: "macro-zona",
    families_lib.ESCALA_REGIONAL: "regional",
    families_lib.ESCALA_SECTORIAL_REGIONAL: "sectorial-regional",
}

FREQ_NOMBRE = {"A": "anual", "T": "trimestral", "M": "mensual", "D": "diaria"}

# Qué sostiene y qué no sostiene cada escala para el diseño de investigación.
# Es el juicio que el PI pidió: objetivo por objetivo, dónde la BDE alcanza y
# dónde hay que ir a otra fuente.
DIAGNOSTICO = {
    families_lib.ESCALA_NACIONAL: {
        "que_es": (
            "Es la escala donde la BDE es abundante y larga, y no por casualidad: "
            "el mandato del Banco Central es la política monetaria nacional, de "
            "modo que mide con detalle aquello que gobierna."
        ),
        "sostiene": (
            "El conjunto completo de regresores financieros de H1 --tasa de "
            "política monetaria, captación y colocación, hipotecarias, bonos en "
            "UF-- y el apalancamiento hipotecario de los hogares. También la "
            "descomposición entre valorización del terreno y de la construcción, "
            "que en Chile sólo existe a este nivel."
        ),
        "no_sostiene": (
            "Nada que requiera geografía. Una tasa nacional no distingue entre el "
            "mercado de suelo de Santiago y el de Puerto Montt, y el proyecto "
            "necesita justamente esa distinción para su variable dependiente."
        ),
    },
    families_lib.ESCALA_ZONAL: {
        "que_es": (
            "La escala más próxima a la unidad metropolitana que el proyecto mide, "
            "y la que la BDE casi no publica. Son siete zonas --Norte, Centro, Sur "
            "y cuatro subzonas de la Región Metropolitana--, y la mayor parte vive "
            "en Estadísticas Experimentales, no en estadística oficial."
        ),
        "sostiene": (
            "El índice de precios de vivienda por zona y el valor del stock "
            "habitacional. Es lo más cerca que la BDE llega de un precio "
            "inmobiliario con desagregación territorial."
        ),
        "no_sostiene": (
            "El precio del suelo, que no es el precio de la vivienda. Y ninguna "
            "comparación directa con las 16 regiones: la correspondencia es de uno "
            "a muchos salvo en la RM, de modo que la única dirección de agregación "
            "honesta es subir el dato regional hasta la zona, nunca bajar el zonal "
            "hasta la región."
        ),
    },
    families_lib.ESCALA_REGIONAL: {
        "que_es": (
            "Dieciséis regiones administrativas, repartidas en varios capítulos "
            "del catálogo. Conviene recordar que una región administrativa es una "
            "construcción del Estado y no una economía: la Región de Los Lagos no "
            "es el área metropolitana de Puerto Montt--Puerto Varas."
        ),
        "sostiene": (
            "La demanda física de suelo por la vía de los permisos de edificación, "
            "que es el insumo con que la formulación propone reconstruir el "
            "Consumo de Suelo Urbano del MINVU. También la morosidad hipotecaria y "
            "la profundidad de depósitos, como huella regional del ciclo "
            "financiero."
        ),
        "no_sostiene": (
            "Volumen de crédito, que es nacional. Población regional, que no existe "
            "como serie propia y aparece sólo como denominador dentro de las tablas "
            "per cápita. Y la unidad metropolitana, que no está en ninguna escala."
        ),
    },
    families_lib.ESCALA_SECTORIAL_REGIONAL: {
        "que_es": (
            "Región por sector, enteramente dentro de Cuentas Nacionales y casi "
            "enteramente anual. Es la escala más fina que publica la BDE y la que "
            "permite caracterizar la estructura productiva de cada territorio."
        ),
        "sostiene": (
            "La medición de cuán extractiva es cada economía regional, que sostiene "
            "el marco muestral del proyecto: las dos conurbaciones menores entran a "
            "la muestra por ser centros urbanos de economías extractivas, y esta "
            "escala lo mide en vez de asumirlo."
        ),
        "no_sostiene": (
            "Productividad: el catálogo no contiene ninguna serie de PTF, de modo "
            "que el estancamiento se argumenta con participaciones de producto y "
            "descomposición shift-share, nunca como caída de productividad medida."
        ),
    },
}


def _tabla_capitulos(sub: pd.DataFrame, tope: int = 8) -> str:
    """Capítulos de una escala, con su reparto de frecuencias."""
    filas = ["| Capítulo | Series | Frecuencias |", "|---|---:|---|"]
    conteo = sub["capitulo"].value_counts()
    for cap in conteo.index[:tope]:
        cap_sub = sub[sub["capitulo"] == cap]
        frec = ", ".join(
            f"{FREQ_NOMBRE.get(f, f)} {n}"
            for f, n in cap_sub["frecuencia"].value_counts().items()
        )
        filas.append(f"| {cap} | {conteo[cap]:,} | {frec} |".replace(",", "."))
    if len(conteo) > tope:
        resto = int(conteo.iloc[tope:].sum())
        filas.append(f"| *otros {len(conteo) - tope} capítulos* | {resto:,} | |".replace(",", "."))
    return "\n".join(filas)


def build_pagina_escala(escala: str, censo: pd.DataFrame) -> str:
    """Una página de escala: censo, profundidad, y lo que no sostiene."""
    sub = censo[censo["escala"] == escala]
    total = len(censo)
    n = len(sub)
    pct = 100 * n / total
    nombre, unidad = families_lib.ESCALA_LABEL[escala]
    diag = DIAGNOSTICO[escala]

    familias = [f for f in families_lib.ordered() if f.escala == escala]

    partes = [
        "---",
        f'title: "{nombre.capitalize()}"',
        "---",
        "",
        site_lib.escala_badge(escala),
        "",
        f"*{diag['que_es']}*",
        "",
        "---",
        "",
        "## El censo",
        "",
        f"La BDE publica **{n:,} series** en esta escala, {site_lib.es(pct, 1)}% "
        f"de los {total:,} códigos únicos del catálogo. La unidad de observación "
        f"es {unidad}.".replace(",", "."),
        "",
        _tabla_capitulos(sub),
        "",
        site_lib.fuente(CENSO_CSV),
        "",
        f"[Explorar el censo filtrado por esta escala](../explorar.qmd"
        f"#escala={escala})",
        "",
    ]

    if familias:
        partes += ["## Qué usa el proyecto", ""]
        for fam in familias:
            partes += [
                f"### {fam.title_es}",
                "",
                f"**Objetivo.** {fam.objetivo}",
                "",
                fam.notas_es,
                "",
            ]

    partes += [
        "## Lo que esta escala sostiene",
        "",
        diag["sostiene"],
        "",
        "## Lo que no sostiene",
        "",
        diag["no_sostiene"],
        "",
    ]
    return "\n".join(partes)

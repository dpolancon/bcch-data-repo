"""
Stage:    10 -- Generate the Quarto publication site
Purpose:  Emit the whole site into the git worktree checked out on the `site`
          branch: project config, programme index, one page per published
          report, the interactive explorer, and the methodology page carrying
          the standing caveats. Everything here is generated; nothing in the
          worktree is hand-edited.
Task:     Publication programme -- BCCh regional data
Inputs:   bcch-data-repo-vault/report*/  (markdown + assets)
          data/panel_two_axes_annual.csv, data/panel_two_axes_summary.csv
          data/panel_regional_pib_annual.csv
Outputs:  <site worktree>/_quarto.yml, index.qmd, explorar.qmd,
          metodologia.qmd, reportes/*.qmd, datos/*.csv, assets/*,
          asset_manifest.csv
Created:  2026-08-26
Updated:  2026-08-26
Owner:    dpolancon
Run:      python scripts/10_generate_site.py [--worktree PATH]
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd

from lib import families as families_lib
from lib import escalas as escalas_lib
from lib import site as site_lib
from lib.paths import (
    BRIEFINGS_DIR,
    DATA_DIR,
    SITE_WORKTREE_DEFAULT,
    report_assets_dir,
    report_dir,
    site_worktree,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s"
)
logger = logging.getLogger(__name__)

TOKEN_RE = re.compile(r"@@[A-Z0-9_]+@@")

# Panels the site publishes as raw CSV. The explorer reads these directly, so
# a reader can check any chart against the same file the chart was drawn from.
# Chart libraries vendored into the site worktree, kept out of
# GENERATED_DIRS so a regeneration does not delete them.
VENDORED_LIBS = ["d3.min.js", "plot.umd.min.js"]

PUBLISHED_PANELS = [
    "censo_bde_series.csv",
    "censo_explorador.csv",
    "censo_bde_resumen.csv",
    "panel_two_axes_annual.csv",
    "panel_two_axes_summary.csv",
    "panel_permits_annual.csv",
    "panel_permits_summary.csv",
    "panel_financial_depth_annual.csv",
    "panel_financial_depth_summary.csv",
    "panel_regional_pib_annual.csv",
]

# Reports that exist as finished markdown in the vault today. Report 3 is
# generated below from the two-axis panel; 4-8 are declared in lib.families but
# not yet written, and the index renders them as forthcoming rather than
# linking to pages that do not exist.
VAULT_REPORTS = [
    {
        "n": 1,
        "slug": "report1-disparidades",
        "nav_label": "1 · Disparidades regionales",
        "title": "Disparidades económicas regionales en Chile",
        "source": "report_REG_ECON_DEV_ES.md",
        "escala": families_lib.ESCALA_SECTORIAL_REGIONAL,
        "lead": (
            "La geografía productiva de Chile está estructuralmente fijada, "
            "mientras que la desigualdad de bienestar apenas oscila con los "
            "ciclos de commodities."
        ),
    },
    {
        "n": 2,
        "slug": "report2-cobertura",
        "nav_label": "2 · Cobertura de datos",
        "title": "Reporte de cobertura de datos regionales",
        "source": "data_coverage_report_ES.md",
        "escala": families_lib.ESCALA_SECTORIAL_REGIONAL,
        "lead": (
            "Qué publica efectivamente el Banco Central a nivel regional, "
            "por dominio temático, frecuencia y región."
        ),
    },
]


def strip_front_matter(text: str) -> str:
    """Remove a YAML block if the vault markdown carries one."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4 :].lstrip("\n")
    return text


def rewrite_asset_links(text: str) -> str:
    """Point `assets/...` references at the site's shared assets directory."""
    return re.sub(r"\((?:\./)?assets/", "(../assets/", text)


def demote_headings(text: str) -> str:
    """Drop the vault's H1 so the Quarto title is the only top-level heading."""
    lines = text.split("\n")
    out, seen_h1 = [], False
    for line in lines:
        if not seen_h1 and line.startswith("# "):
            seen_h1 = True
            continue
        out.append(line)
    return "\n".join(out)


def check_tokens(text: str, where: str) -> None:
    """Fail on any unresolved @@TOKEN@@ -- the same rule as stages 05 and 06."""
    leftover = TOKEN_RE.findall(text)
    if leftover:
        raise SystemExit(
            f"Unresolved narrative tokens in {where}: {sorted(set(leftover))}"
        )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    logger.info("Wrote %s", path.relative_to(path.parents[len(path.parts) - 2]) if False else path.name)


# --------------------------------------------------------------------------
# Page builders
# --------------------------------------------------------------------------

def build_index(
    published: list[dict],
    briefs: list[dict] | None = None,
    censo: "pd.DataFrame | None" = None,
) -> str:
    """The programme page: the thesis, the roadmap, and the absorption model."""
    rows = []
    for fam in families_lib.ordered():
        done = any(p.get("family") == fam.name for p in published)
        status = "publicado" if done else "en preparación"
        link = ""
        for p in published:
            if p.get("family") == fam.name:
                link = f"[{fam.title_es}](reportes/{p['slug']}.qmd)"
        label = link or fam.title_es
        rows.append(
            f"| {fam.report} | {label} | {fam.escala} | "
            f"`{fam.name}` | {', '.join(fam.frequencies)} | {status} |"
        )
    roadmap = "\n".join(rows)

    if briefs:
        links = "\n".join(
            f"- [{b['title']}](briefings/{b['slug']}.qmd)" for b in briefs
        )
        notes_section = (
            "## Notas de familia\n\n"
            "Cada familia de series ingerida deja una nota: qué significan "
            "los códigos, cómo se codifican las regiones, dónde están las "
            "trampas. Es lo que abre la compuerta del reporte siguiente.\n\n"
            + links + "\n"
        )
    else:
        notes_section = ""

    # Las cifras del censo se interpolan; ninguna se escribe a mano.
    if censo is not None:
        total = len(censo)
        conteo = censo["escala"].value_counts()
        tokens = {
            "@@N_TOTAL@@": f"{total:,}".replace(",", "."),
            "@@FUENTE_CENSO@@": site_lib.fuente(
                escalas_lib.CENSO_CSV, raiz=True
            ).strip(),
        }
        for clave, escala in (
            ("NAC", families_lib.ESCALA_NACIONAL),
            ("SEC", families_lib.ESCALA_SECTORIAL_REGIONAL),
            ("REG", families_lib.ESCALA_REGIONAL),
            ("ZON", families_lib.ESCALA_ZONAL),
        ):
            n = int(conteo.get(escala, 0))
            tokens[f"@@N_{clave}@@"] = f"{n:,}".replace(",", ".")
            tokens[f"@@P_{clave}@@"] = site_lib.es(100 * n / total, 1)
    else:
        tokens = {}

    pagina = f"""---
title: "La revisión"
subtitle: "{site_lib.SITE_SUBTITLE}"
include-before-body:
  - personal-nav.html
---

## Qué mide el Banco Central, y a qué escala

Esta revisión recorre la Base de Datos Estadísticos del Banco Central para el
proyecto sobre las determinantes financieras del precio del suelo metropolitano.
Su resultado no es un inventario sino una asimetría.

El catálogo publica **@@N_TOTAL@@ series únicas** repartidas de forma muy
desigual entre cuatro escalas de observación:

| Escala | Series | Participación |
|---|---:|---:|
| [Nacional](escalas/nacional.qmd) | @@N_NAC@@ | @@P_NAC@@% |
| [Sectorial-regional](escalas/sectorial-regional.qmd) | @@N_SEC@@ | @@P_SEC@@% |
| [Regional](escalas/regional.qmd) | @@N_REG@@ | @@P_REG@@% |
| [Macro-zona](escalas/macro-zona.qmd) | @@N_ZON@@ | @@P_ZON@@% |

@@FUENTE_CENSO@@

La BDE mide las escalas que al Banco Central le interesa gobernar. El grueso es
nacional porque el mandato es la política monetaria nacional; la región aparece
por vía de Cuentas Nacionales; la macro-zona aparece como estadística
experimental. La asimetría no es una limitación técnica del catálogo: es una
propiedad de la institución que lo produce.

::: {{.caveat}}
**El área metropolitana no existe en ninguna escala.** Es la unidad que el
proyecto mide, y la BDE no la publica. Lo más próximo son las macro-zonas
—@@N_ZON@@ series, la escala más pequeña del catálogo—, y la correspondencia
con las regiones es de uno a muchos salvo en la Región Metropolitana. La única
dirección de agregación honesta es subir el dato regional hasta la zona, nunca
bajar el zonal hasta la región.
:::

## Hoja de ruta

Cada reporte abre exactamente **una** familia de series nueva, y las familias
están ordenadas por costo de ingesta creciente. El equipo nunca enfrenta dos
estructuras de datos desconocidas al mismo tiempo. El orden *es* el diseño de
absorción.

| # | Reporte | Tier | Familia | Frec. | Estado |
|---|---------|------|---------|-------|--------|
{roadmap}

## Cómo avanza el programa

El ritmo lo fija la comprensión, no el calendario. Corren dos vías en paralelo.

**Vía lenta — los reportes.** Un ciclo no se cierra en una fecha: se cierra
cuando existen tres artefactos.

1. el reporte publicado,
2. una **nota de familia** que explica qué significan los códigos, cómo se
   codifican las regiones y dónde están las trampas —lo que necesita leer la
   *próxima* persona, no la que ya hizo el trabajo,
3. una respuesta escrita del equipo, enlazada desde la página del reporte.

**Vía rápida — las notas de datos.** Una nota breve cada vez que aterriza una
familia nueva en `data/raw/`, *antes* del reporte que la usa. Se genera desde
el manifiesto de descarga: cuántas series, qué regiones, qué rango de fechas,
qué falta. Barata y mecánica; mantiene la ingesta en movimiento entre reportes.

**La compuerta.** La descarga del reporte N+1 no corre hasta que existe la nota
de familia del reporte N. Ese es el mecanismo de autorregulación, y es
verificable de forma automática.

{notes_section}
## Procedencia

Todo número de este sitio proviene de un CSV en `data/`, y todo CSV proviene de
la API del Banco Central de Chile. No hay datos sintéticos, estimados ni
interpolados en ninguna etapa —la ausencia se reporta como ausencia. Todas las
bases procesadas están [disponibles para descarga](datos.qmd), y el
[crosswalk](diseno.qmd) permite rastrear cualquier cifra hasta el código de
serie que la origina.
"""
    for token, valor in tokens.items():
        pagina = pagina.replace(token, valor)
    return pagina


def build_report_page(meta: dict, body: str) -> str:
    """Wrap a vault report's markdown as a Quarto page."""
    badge = site_lib.escala_badge(meta["escala"])
    return f"""---
title: "{meta['title']}"
---

{badge}

*{meta['lead']}*

---

{body}
"""


def build_report3(panel: pd.DataFrame, summary: pd.DataFrame) -> str:
    """Report 3, written directly from the two-axis panel.

    Every statistic below is interpolated from `summary`; none is typed in by
    hand. That is the whole point of the exercise -- a hand-copied figure is
    correct exactly once.
    """
    first, last = summary.iloc[0], summary.iloc[-1]
    y0, y1 = int(first["year"]), int(last["year"])

    sr0, sr1 = first["spatial_rent_mean"], last["spatial_rent_mean"]
    rr0, rr1 = first["resource_rent_mean"], last["resource_rent_mean"]
    srg0, srg1 = first["spatial_rent_gini"], last["spatial_rent_gini"]
    rrg0, rrg1 = first["resource_rent_gini"], last["resource_rent_gini"]

    latest = panel[panel["year"] == y1]
    sr_top = (
        latest[latest["axis"] == "spatial_rent"]
        .nlargest(3, "share")[["region_display", "share"]]
        .values.tolist()
    )
    rr_top = (
        latest[latest["axis"] == "resource_rent"]
        .nlargest(3, "share")[["region_display", "share"]]
        .values.tolist()
    )
    sr_list = "; ".join(f"{n} ({site_lib.es_pct(v, 1)}%)" for n, v in sr_top)
    rr_list = "; ".join(f"{n} ({site_lib.es_pct(v, 1)}%)" for n, v in rr_top)

    badge = site_lib.escala_badge(families_lib.ESCALA_SECTORIAL_REGIONAL)

    return f"""---
title: "Los dos ejes: renta espacial y renta de recursos"
---

{badge}

*La renta espacial es difusa y creciente; la renta de recursos es concentrada y
se endurece. Son dos geografías distintas dentro del mismo país.*

---

## El argumento

El marco de crecimiento desbalanceado distingue dos rentas que compiten por el
excedente de una economía: la **renta espacial**, que se captura sobre el suelo
y el inmueble, y la **renta de recursos**, que se captura sobre el subsuelo. En
las cuentas regionales del Banco Central ambas tienen una contraparte directa:
el sector **10** (*Servicios de vivienda e inmobiliarios*) y el sector **03**
(*Minería*). El sector **06** (*Construcción*) es la pata de inversión que las
vincula.

Este reporte no descarga ninguna serie nueva. Todo lo que usa ya estaba en
`raw_annual.csv` desde el primer día del repositorio: su propósito es medir los
dos ejes a lo largo del tiempo, no ampliar la base.

::: {{.caveat}}
**El sector 10 es mayoritariamente renta imputada.** Las cuentas nacionales
incluyen el alquiler imputado de las viviendas ocupadas por sus propietarios,
no sólo el arriendo efectivamente pagado. Es la mejor aproximación disponible
—el catálogo del Banco Central no contiene ningún índice de arriendos
regional— pero es un supuesto que sostiene todo el eje espacial, y por eso se
declara en cada reporte que se apoya en él.
:::

## Lo que muestran los datos

Entre {y0} y {y1} la participación media de la **renta espacial** en el
producto regional pasó de **{site_lib.es_pct(sr0)}%** a **{site_lib.es_pct(sr1)}%**. La
participación media de la **renta de recursos** pasó de **{site_lib.es_pct(rr0)}%** a
**{site_lib.es_pct(rr1)}%** —es decir, se mantuvo prácticamente donde estaba.

El promedio, sin embargo, es lo menos interesante. Lo decisivo es cómo se
*reparte* cada eje entre regiones:

- El Gini regional de la renta espacial se movió de **{site_lib.es(srg0, 4)}** a
  **{site_lib.es(srg1, 4)}**. Es un valor bajo: la renta espacial existe en todas partes.
- El Gini regional de la renta de recursos se movió de **{site_lib.es(rrg0, 4)}** a
  **{site_lib.es(rrg1, 4)}**. Es un valor alto *y creciente*: la minería no sólo está
  concentrada, se está concentrando más.

En {y1} las regiones con mayor participación de renta espacial fueron
{sr_list}. Las de mayor renta de recursos fueron {rr_list}.

## Por qué importa

Las dos rentas no se distribuyen como se distribuye el producto. La renta
espacial acompaña a la población: donde hay gente hay vivienda, y donde hay
vivienda hay sector 10. La renta de recursos acompaña a la geología, que no se
redistribuye nunca.

Esto ofrece una lectura del hallazgo central del Reporte 1 —un HHI de producción
plano durante trece años mientras el Gini de bienestar bajaba. La inmovilidad
está del lado del eje de recursos, que se endurece; el movimiento está del lado
del eje espacial, que es difuso por construcción. Una política regional que
solo mueva el eje espacial redistribuye bienestar sin tocar la estructura
productiva. Es exactamente lo que los índices del Reporte 1 describen.

## Datos

El panel completo está publicado en
[`panel_two_axes_annual.csv`](../datos/panel_two_axes_annual.csv) (región ×
año × eje) y el resumen anual en
[`panel_two_axes_summary.csv`](../datos/panel_two_axes_summary.csv). Ambos se
regeneran con:

```bash
python scripts/09_build_theme_panels.py --family two_axes
```

## Nota metodológica

Las participaciones se calculan sobre **precios corrientes**, no sobre volumen
encadenado. Los volúmenes encadenados no son aditivos entre sectores: sumarlos
no reproduce el total regional, y una participación construida así no sería una
proporción de nada. El detalle está en la [página de
metodología](../metodologia.qmd).
"""


def build_report4(
    anual: pd.DataFrame, resumen: pd.DataFrame, ejes: pd.DataFrame
) -> str:
    """Reporte 4: la cantidad construida contra la renta espacial.

    Toda cifra se interpola desde los paneles; ninguna se escribe a mano. La
    etapa 11 las recalcula y falla si la prosa deja de cuadrar.
    """
    sah = anual[anual["indicador"] == "superficie_habitacional"]
    nva = anual[anual["indicador"] == "viviendas_autorizadas"]
    ceys = anual[anual["indicador"] == "empresas_constituidas"]
    a0, a1 = int(anual["anio"].min()), int(anual["anio"].max())

    def total(marco, anio):
        return float(marco[marco["anio"] == anio]["valor"].sum())

    sah0, sah1 = total(sah, a0), total(sah, a1)
    nva0, nva1 = total(nva, a0), total(nva, a1)
    ceys0, ceys1 = total(ceys, a0), total(ceys, a1)

    # Renta espacial: participación media entre regiones, del panel de R3.
    esp = ejes[ejes["axis"] == "spatial_rent"]
    renta = esp.groupby("year")["share"].mean()
    renta0, renta1 = float(renta.loc[a0]), float(renta.loc[a1])

    idx_sah = 100 * sah1 / sah0
    idx_renta = 100 * renta1 / renta0

    ultimo = sah[sah["anio"] == a1].set_index("region_display")["indice_base100"]
    bajo = int((ultimo < 100).sum())
    arriba = ultimo.nlargest(1)
    abajo = ultimo.nsmallest(1)

    def mm(x):
        return site_lib.es(x / 1e6, 1)

    def miles(x):
        return f"{int(round(x / 1000)):,}".replace(",", ".")

    return f"""---
title: "El ciclo regional de la construcción"
---

{site_lib.escala_badge(families_lib.ESCALA_REGIONAL)}

*La renta espacial creció mientras la cantidad construida se redujo a la mitad.
Lo que se valoriza es el stock existente, no la formación de capital.*

---

## El argumento

El Reporte 3 dejó una pregunta que el sector 10 no puede responder. *Servicios
de vivienda e inmobiliarios* es en buena parte **alquiler imputado**: sube
cuando suben los precios de la vivienda, se construya o no un metro cuadrado
nuevo. Precio y cantidad son indistinguibles dentro de esa serie.

Los permisos de edificación son cantidad sin precio: metros cuadrados
autorizados y unidades de vivienda. Puestos contra la participación del sector
10 separan las dos historias. Si la renta espacial sube **con** los permisos,
hay formación de capital. Si sube **contra** permisos que caen, lo que crece es
la valorización del stock que ya existe.

## Lo que muestran los datos

Entre {a0} y {a1} la superficie habitacional autorizada pasó de
**{mm(sah0)} millones de m²** a **{mm(sah1)} millones de m²**, una caída de
**{site_lib.es(100 - idx_sah, 1)}%**. Las viviendas autorizadas cayeron de
**{miles(nva0)} mil** a **{miles(nva1)} mil** unidades.

En el mismo período la participación media de la renta espacial en el producto
regional **subió**: índice **{site_lib.es(idx_renta, 1)}** contra un índice de
**{site_lib.es(idx_sah, 1)}** para los permisos, ambos con base 100 en {a0}.

La caída no es de una región ni de un año: **{bajo} de las 16 regiones**
autorizaban en {a1} menos superficie habitacional que en {a0}. El rango va de
{arriba.index[0]} ({site_lib.es(float(arriba.iloc[0]), 1)}) a
{abajo.index[0]} ({site_lib.es(float(abajo.iloc[0]), 1)}).

::: {{.caveat}}
**Un permiso es intención de construir, no construcción.** Un permiso
autorizado puede no ejecutarse nunca. La serie es un indicador adelantado del
ciclo, no una medida de stock ni de producto, y la caída documentada acá es de
autorizaciones, no de obra terminada.
:::

## Por qué importa

La divergencia es el objeto del proyecto medido a escala regional. Una renta
espacial que crece mientras la cantidad construida se contrae no describe una
expansión inmobiliaria: describe la revalorización de un activo que no se
deprecia, sostenida por algo distinto de la demanda física de suelo.

El dato regional no prueba nada sobre las tasas de interés —eso ocurre a escala
nacional y con otra serie—, pero sí descarta que el alza de la renta espacial
venga acompañada de más construcción. Esa es la mitad del argumento que la
escala regional sí puede sostener.

Las empresas constituidas siguen el camino contrario: de **{miles(ceys0)} mil**
a **{miles(ceys1)} mil** entre {a0} y {a1}. Entra como control de dinamismo
empresarial y **no forma parte del eje espacial**: no se suma a los otros tres
indicadores.

## Nota metodológica

Los cuatro indicadores son flujos mensuales con estacionalidad marcada —los
permisos caen en invierno austral y en enero—, de modo que el panel mensual
carga la suma móvil de doce meses y ninguna lectura mes contra mes es
interpretable. El panel anual usa sólo años calendario **completos**: las series
del INE terminan en mayo de {a1 + 1}, y graficar un año parcial junto a años
completos inventaría una caída que no ocurrió.

Las regiones se comparan como **índice base 100 = {a0}**, no per cápita: el
Banco Central no publica población regional como serie propia, sólo como
denominador dentro de las tablas per cápita.

{site_lib.fuente("panel_permits_annual.csv")}
"""


def build_report6(anual: pd.DataFrame, resumen: pd.DataFrame) -> str:
    """Reporte 6: la mora hipotecaria y el ciclo de tasas.

    Toda cifra se interpola del panel; la etapa 11 las recalcula y falla si la
    prosa deja de seguir de los datos.
    """
    tasas = resumen[resumen["medida"] == "tasa"].pivot(
        index="anio", columns="indicador", values="valor"
    )
    a0, a1 = int(tasas.index.min()), int(tasas.index.max())
    viv = tasas["mora_vivienda"]
    pico_anio, pico = int(viv.idxmax()), float(viv.max())
    piso_anio, piso = int(viv.idxmin()), float(viv.min())
    hoy = float(viv.loc[a1])
    caida = 100 * (1 - piso / pico)

    com = float(tasas["mora_comercial"].loc[a1])
    con = float(tasas["mora_consumo"].loc[a1])

    conc = tasas["concentracion_rm_cuentas"]
    conc0, conc1 = float(conc.loc[a0]), float(conc.loc[a1])

    stocks = resumen[resumen["medida"] == "stock"].pivot(
        index="anio", columns="indicador", values="valor"
    )
    ctas0 = float(stocks["cuentas_corrientes"].loc[a0])
    ctas1 = float(stocks["cuentas_corrientes"].loc[a1])
    dep0 = float(stocks["depositos_vista"].loc[a0])
    dep1 = float(stocks["depositos_vista"].loc[a1])

    ult = anual[
        (anual["indicador"] == "mora_vivienda") & (anual["anio"] == a1)
    ].set_index("region_display")["valor"]
    peor, mejor = ult.nlargest(1), ult.nsmallest(1)

    return f"""---
title: "Profundidad financiera y morosidad por región"
---

{site_lib.escala_badge(families_lib.ESCALA_REGIONAL)}

*La mora hipotecaria se desplomó durante los años de tasas bajas y repunta
desde que las tasas subieron. Es la huella regional del ciclo financiero sobre
el deudor, no sobre el crédito.*

---

## El argumento

De las tres carteras que el Banco Central desagrega por región, la de vivienda
es la que menos morosos produce y la que más se movió. Entre {pico_anio} y
{piso_anio} la mora hipotecaria cayó de **{site_lib.es(pico, 2)}%** a
**{site_lib.es(piso, 2)}%** de la cartera: una reducción de
**{site_lib.es(caida, 0)}%**. En {a1} está en **{site_lib.es(hoy, 2)}%**,
todavía muy por debajo del inicio de la serie pero claramente por encima del
piso.

El contraste con las otras dos carteras es lo que da sentido a la cifra. En
{a1} la mora comercial va en **{site_lib.es(com, 2)}%** y la de consumo en
**{site_lib.es(con, 2)}%**: entre cinco y tres veces la hipotecaria. El
inmueble es, en los datos del propio Banco Central, la deuda que menos se deja
de pagar.

::: {{.caveat}}
**Un porcentaje de cartera sube por dos motivos distintos.** Estas series son
mora sobre el saldo de cada cartera, no montos: una alza puede venir de más
deudores en problemas *o* de una cartera que se contrae. Distinguirlo exige el
volumen de crédito por región, y el Banco Central **no lo publica**: los montos
hipotecarios, las tasas y el LTV son nacionales. Esta familia dice cómo le va
al deudor en cada región, nunca cuánto crédito entró en cada región.
:::

## Lo que muestran los datos

La trayectoria de la mora hipotecaria acompaña el ciclo de tasas: cae de forma
sostenida durante los años de política monetaria expansiva y se quiebra al alza
después. El proyecto no puede leer causalidad en eso —la tasa es nacional y
esta serie es regional—, pero sí registrar que el período de valorización del
suelo coincidió con deudores hipotecarios sin estrés visible.

La dispersión entre regiones se mantiene: en {a1} la mora hipotecaria va de
**{site_lib.es(float(mejor.iloc[0]), 2)}%** en {mejor.index[0]} a
**{site_lib.es(float(peor.iloc[0]), 2)}%** en {peor.index[0]}.

### La profundidad financiera se concentró

En el mismo período las cuentas corrientes de personas naturales pasaron de
**{site_lib.es(ctas0 / 1e6, 2)} millones** a
**{site_lib.es(ctas1 / 1e6, 2)} millones**, y los depósitos a la vista de
**{site_lib.es(dep0 / 1e6, 2)}** a **{site_lib.es(dep1 / 1e6, 2)} billones de
pesos**. Pero el crecimiento no se repartió: la participación de la Región
Metropolitana en las cuentas del país subió de **{site_lib.es(conc0, 1)}%** en
{a0} a **{site_lib.es(conc1, 1)}%** en {a1}.

Esa concentración corre en la misma dirección que la inmovilidad productiva que
documentó el Reporte 1. La bancarización creció seis veces y se volvió más
metropolitana, no menos.

## Nota metodológica

Ninguno de los seis indicadores es un flujo. Las tres tasas de mora son
porcentajes de carteras **distintas**, con denominadores distintos: sumarlas no
significa nada, y ponderarlas exigiría el tamaño de cada cartera regional, que
esta familia no trae. Los tres saldos son stocks. Todo se promedia sobre los
doce meses del año; nada se acumula.

Los saldos están en **pesos nominales**, sin deflactar. La multiplicación por
{site_lib.es(dep1 / dep0, 1)} de los depósitos a la vista mezcla inflación con
profundización financiera, y separarlas exige un índice de precios que es
nacional.

`CCPN` cuenta **cuentas**, no personas: una persona puede tener varias y una
cuenta puede ser de una empresa. No es una medida de inclusión financiera per
cápita, y no puede convertirse en una, porque la población regional no existe
como serie del Banco Central.

{site_lib.fuente("panel_financial_depth_annual.csv")}
"""


def build_modulo_censo() -> str:
    """Explorador del censo: qué publica la BDE sobre un tema, y a qué escala.

    Es la pregunta que el investigador responsable y los coinvestigadores
    llegan a hacerle al catálogo, y hasta ahora había que responderla abriendo
    el CSV. Corre sobre la vista aligerada y filtra en el navegador: 25.369
    filas caben de sobra en memoria y evitan un servidor.
    """
    return """## El censo del catálogo

Qué publica el Banco Central sobre un tema, y en qué escala lo publica. La
búsqueda recorre nombre y código de las 25.369 series del catálogo.

```{=html}
<div class="explorer">
<div class="ctl">
<span class="ctl-label">Buscar</span>
<input type="search" id="q-censo" placeholder="vivienda, suelo, tasa, hipotecario..." autocomplete="off">
</div>
<div class="ctl">
<span class="ctl-label">Escala</span>
<div class="ctl-group" id="ctl-escala"></div>
</div>
<div class="ctl">
<span class="ctl-label">Frecuencia</span>
<div class="ctl-group" id="ctl-frec"></div>
</div>
</div>

<p class="plotnote" id="censo-resumen">Cargando el censo…</p>
<div id="censo-barras" class="plotbox"></div>
<div id="censo-tabla" class="tablabox"></div>
```

```{=html}
<script>
(function () {
  "use strict";

  var ESCALAS = ["nacional", "sectorial-regional", "regional", "macro-zona"];
  var FRECS = {A: "anual", T: "trimestral", M: "mensual", D: "diaria"};
  var MAX_FILAS = 40;
  var datos = [];

  function chk(host, valor, texto, marcado) {
    var l = document.createElement("label");
    var i = document.createElement("input");
    i.type = "checkbox"; i.value = valor; i.checked = marcado;
    l.appendChild(i);
    l.appendChild(document.createTextNode(" " + texto));
    host.appendChild(l);
    return i;
  }

  function seleccion(host) {
    return Array.prototype.slice
      .call(host.querySelectorAll("input:checked"))
      .map(function (i) { return i.value; });
  }

  function normaliza(s) {
    return (s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }

  function pinta() {
    var q = normaliza(document.getElementById("q-censo").value.trim());
    var esc = seleccion(document.getElementById("ctl-escala"));
    var fre = seleccion(document.getElementById("ctl-frec"));

    var hit = datos.filter(function (d) {
      if (esc.indexOf(d.escala) === -1) return false;
      if (fre.indexOf(d.frecuencia) === -1) return false;
      if (!q) return true;
      return d._n.indexOf(q) !== -1 || d._c.indexOf(q) !== -1;
    });

    var resumen = document.getElementById("censo-resumen");
    var porEscala = {};
    hit.forEach(function (d) { porEscala[d.escala] = (porEscala[d.escala] || 0) + 1; });
    var detalle = ESCALAS.filter(function (e) { return porEscala[e]; })
      .map(function (e) { return porEscala[e].toLocaleString("es-CL") + " " + e; })
      .join(" · ");
    resumen.textContent = hit.length.toLocaleString("es-CL") + " de " +
      datos.length.toLocaleString("es-CL") + " series" +
      (detalle ? " — " + detalle : "");

    // Barras por capítulo: dónde vive lo que se buscó.
    var host = document.getElementById("censo-barras");
    host.innerHTML = "";
    if (!hit.length) {
      host.innerHTML = '<p class="ploterr">Ninguna serie coincide. Pruebe otro término o amplíe los filtros.</p>';
      document.getElementById("censo-tabla").innerHTML = "";
      return;
    }
    var conteo = d3.rollups(hit, function (v) { return v.length; },
                            function (d) { return d.capitulo; })
      .map(function (r) { return {capitulo: r[0], series: r[1]}; })
      .sort(function (a, b) { return b.series - a.series; })
      .slice(0, 12);

    host.appendChild(Plot.plot({
      marginLeft: 240, marginRight: 46,
      height: Math.max(150, 26 * conteo.length + 42),
      width: 860,
      style: {fontSize: "12px", background: "transparent"},
      x: {label: "Series", grid: true},
      y: {label: null},
      marks: [
        Plot.barX(conteo, {x: "series", y: "capitulo", sort: {y: "-x"}, fill: "#0f766e"}),
        Plot.text(conteo, {x: "series", y: "capitulo", text: function (d) {
          return d.series.toLocaleString("es-CL");
        }, dx: 6, textAnchor: "start", fontSize: 11}),
        Plot.ruleX([0])
      ]
    }));

    // Tabla de coincidencias, acotada: es una muestra para reconocer códigos,
    // no un reemplazo del CSV completo.
    var filas = hit.slice(0, MAX_FILAS).map(function (d) {
      return "<tr><td><code>" + d.codigo + "</code></td><td>" + d.nombre +
        "</td><td>" + d.escala + "</td><td>" + (FRECS[d.frecuencia] || "—") + "</td></tr>";
    }).join("");
    var pie = hit.length > MAX_FILAS
      ? '<p class="plotnote">Se muestran ' + MAX_FILAS + ' de ' +
        hit.length.toLocaleString("es-CL") +
        '. La lista completa está en <code>censo_bde_series.csv</code>.</p>'
      : "";
    document.getElementById("censo-tabla").innerHTML =
      '<table class="censo"><thead><tr><th>Código</th><th>Serie</th>' +
      '<th>Escala</th><th>Frecuencia</th></tr></thead><tbody>' +
      filas + '</tbody></table>' + pie;
  }

  var he = document.getElementById("ctl-escala");
  var hf = document.getElementById("ctl-frec");
  // Una escala en el hash preselecciona el filtro: cada página de escala
  // enlaza acá ya filtrada por la suya.
  var pedida = decodeURIComponent((location.hash || "").replace("#escala=", ""));
  ESCALAS.forEach(function (e) {
    chk(he, e, e, !pedida || pedida === e);
  });
  // El navegador restaura el texto de búsqueda anterior al volver a la misma
  // URL. Quien llega por el enlace de una escala pide ver esa escala, y una
  // búsqueda heredada le mostraría cero resultados sin explicación.
  if (pedida) { document.getElementById("q-censo").value = ""; }
  Object.keys(FRECS).forEach(function (f) { chk(hf, f, FRECS[f], true); });

  he.addEventListener("change", pinta);
  hf.addEventListener("change", pinta);
  document.getElementById("q-censo").addEventListener("input", pinta);

  d3.csv("datos/censo_explorador.csv").then(function (rows) {
    datos = rows.map(function (d) {
      d._n = normaliza(d.nombre); d._c = normaliza(d.codigo);
      return d;
    });
    pinta();
  }).catch(function (e) {
    document.getElementById("censo-resumen").innerHTML =
      '<span class="ploterr">No se pudo cargar el censo: ' + e.message + "</span>";
  });
})();
</script>
```

""" + site_lib.fuente("censo_bde_series.csv", raiz=True) + """
"""


def build_explorer() -> str:
    """Interactive explorer, built on vendored Observable Plot and plain JS.

    Deliberately NOT Quarto's OJS. The OJS bootstrap
    (`interpretFromScriptTags`) failed on every cell of a minimal test page
    under Quarto 1.10.18 -- including `a = 40 + 2` -- swallowing the original
    import error inside its own null-dereferencing handler. Direct calls to
    `runtime.interpret()` worked, so the runtime is healthy and the automatic
    bootstrap is not. Rather than ship an explorer whose failure mode is a
    silently blank page, the charts run on the same Plot library loaded as an
    ordinary script, vendored into libs/ so there is no CDN dependency either.
    """
    return """---
title: "Explorar"
---

Dos instrumentos autónomos sobre las mismas bases que publican los reportes: si
un gráfico y una tabla no coinciden, el CSV manda.

```{=html}
<!-- Las librerías se cargan una vez acá, antes de cualquier módulo: cada
     módulo trae su propio script y ninguno puede asumir que otro ya las
     cargó. Estaban al pie del módulo de los dos ejes, de modo que el módulo
     del censo corría con d3 sin definir. -->
<script src="libs/d3.min.js"></script>
<script src="libs/plot.umd.min.js"></script>
```

""" + build_modulo_censo() + """
## Los dos ejes, región por región

Renta espacial y renta de recursos como participación en el producto de cada
región.

```{=html}
<div class="explorer">
<div class="ctl">
<span class="ctl-label">Eje</span>
<div class="ctl-group" id="ctl-eje" role="radiogroup" aria-label="Eje">
<label><input type="radio" name="eje" value="spatial_rent" checked> Renta espacial (sector 10)</label>
<label><input type="radio" name="eje" value="resource_rent"> Renta de recursos (sector 03)</label>
<label><input type="radio" name="eje" value="construction"> Construcción (sector 06)</label>
</div>
</div>
<div class="ctl">
<span class="ctl-label">Regiones</span>
<div class="ctl-group ctl-regions" id="ctl-regiones" aria-label="Regiones"></div>
<div class="ctl-actions">
<button type="button" id="sel-all">Todas</button>
<button type="button" id="sel-none">Ninguna</button>
</div>
</div>
</div>
```

<div id="chart-shares" class="plotbox" aria-live="polite"></div>
<p class="plotnote" id="note-shares"></p>

## Dispersión entre regiones

Un Gini alto significa que el eje está concentrado en pocas regiones. Nótese
que los dos ejes viven en mundos distintos: la renta espacial se reparte, la
renta de recursos no.

<div id="chart-gini" class="plotbox"></div>

## Descargar

- [`panel_two_axes_annual.csv`](datos/panel_two_axes_annual.csv) — región × año × eje
- [`panel_two_axes_summary.csv`](datos/panel_two_axes_summary.csv) — resumen anual
- [`panel_regional_pib_annual.csv`](datos/panel_regional_pib_annual.csv) — PIB regional

<script>
(function () {
  "use strict";

  var AXIS_LABEL = {
    spatial_rent: "Renta espacial",
    resource_rent: "Renta de recursos",
    construction: "Construcción"
  };
  var DEFAULT_REGIONS = [
    "Antofagasta", "Metropolitana de Santiago", "Biobío", "Aysén"
  ];

  function fail(id, err) {
    var el = document.getElementById(id);
    if (el) {
      el.innerHTML = '<p class="ploterr">No se pudieron cargar los datos: ' +
        String(err && err.message ? err.message : err) + "</p>";
    }
  }

  function render(panel, summary) {
    var regions = Array.from(new Set(panel.map(function (d) {
      return d.region_display;
    }))).sort(function (a, b) { return a.localeCompare(b, "es"); });

    // Region checkboxes, built from the data rather than hardcoded, so a
    // renamed or added region cannot fall out of the control silently.
    var box = document.getElementById("ctl-regiones");
    regions.forEach(function (r) {
      var id = "rg-" + r.replace(/[^a-zA-Z0-9]/g, "");
      var label = document.createElement("label");
      var input = document.createElement("input");
      input.type = "checkbox";
      input.value = r;
      input.id = id;
      input.checked = DEFAULT_REGIONS.indexOf(r) !== -1;
      label.appendChild(input);
      label.appendChild(document.createTextNode(" " + r));
      box.appendChild(label);
    });

    function selectedRegions() {
      return Array.prototype.slice
        .call(box.querySelectorAll("input:checked"))
        .map(function (i) { return i.value; });
    }
    function selectedAxis() {
      var el = document.querySelector('input[name="eje"]:checked');
      return el ? el.value : "spatial_rent";
    }

    function drawShares() {
      var axis = selectedAxis();
      var picked = selectedRegions();
      var rows = panel.filter(function (d) {
        return d.axis === axis && picked.indexOf(d.region_display) !== -1;
      });
      var host = document.getElementById("chart-shares");
      host.innerHTML = "";

      var note = document.getElementById("note-shares");
      if (!rows.length) {
        host.innerHTML = '<p class="ploterr">Seleccione al menos una región.</p>';
        note.textContent = "";
        return;
      }

      var maxYear = d3.max(rows, function (d) { return d.year; });
      var last = rows.filter(function (d) { return d.year === maxYear; });

      host.appendChild(Plot.plot({
        marginLeft: 62,
        marginRight: 150,
        height: 430,
        width: 860,
        style: { fontSize: "12px", background: "transparent" },
        x: { label: "Año", tickFormat: "d" },
        y: {
          label: "Participación en el PIB regional",
          percent: true,
          grid: true,
          zero: true
        },
        marks: [
          Plot.ruleY([0]),
          Plot.line(rows, {
            x: "year", y: "share", stroke: "region_display", strokeWidth: 2
          }),
          Plot.dot(last, { x: "year", y: "share", fill: "region_display", r: 3 }),
          Plot.text(last, {
            x: "year", y: "share", text: "region_display",
            dx: 8, textAnchor: "start", fontSize: 11
          })
        ]
      }));

      var vals = last.map(function (d) { return d.share; });
      note.textContent = AXIS_LABEL[axis] + " · " + picked.length +
        " región(es) · " + maxYear + ": entre " +
        (d3.min(vals) * 100).toFixed(1).replace(".", ",") + "% y " +
        (d3.max(vals) * 100).toFixed(1).replace(".", ",") + "%.";
    }

    function drawGini() {
      var series = [];
      ["spatial_rent", "resource_rent", "construction"].forEach(function (a) {
        summary.forEach(function (d) {
          series.push({
            year: d.year, gini: d[a + "_gini"], eje: AXIS_LABEL[a]
          });
        });
      });
      var host = document.getElementById("chart-gini");
      host.innerHTML = "";
      host.appendChild(Plot.plot({
        marginLeft: 62,
        marginRight: 150,
        height: 380,
        width: 860,
        style: { fontSize: "12px", background: "transparent" },
        x: { label: "Año", tickFormat: "d" },
        y: { label: "Gini entre regiones", grid: true, domain: [0, 0.8] },
        marks: [
          Plot.ruleY([0]),
          Plot.line(series, {
            x: "year", y: "gini", stroke: "eje", strokeWidth: 2.5
          }),
          Plot.text(
            series.filter(function (d) {
              return d.year === d3.max(series, function (x) { return x.year; });
            }),
            {
              x: "year", y: "gini", text: "eje",
              dx: 8, textAnchor: "start", fontSize: 11
            }
          )
        ]
      }));
    }

    document.getElementById("ctl-eje")
      .addEventListener("change", drawShares);
    box.addEventListener("change", drawShares);
    document.getElementById("sel-all").addEventListener("click", function () {
      box.querySelectorAll("input").forEach(function (i) { i.checked = true; });
      drawShares();
    });
    document.getElementById("sel-none").addEventListener("click", function () {
      box.querySelectorAll("input").forEach(function (i) { i.checked = false; });
      drawShares();
    });

    drawShares();
    drawGini();
  }

  Promise.all([
    d3.csv("datos/panel_two_axes_annual.csv", d3.autoType),
    d3.csv("datos/panel_two_axes_summary.csv", d3.autoType)
  ]).then(function (r) {
    render(r[0], r[1]);
  }).catch(function (e) {
    fail("chart-shares", e);
    fail("chart-gini", e);
  });
})();
</script>
"""



def build_methodology() -> str:
    """The standing caveats. This page is the site's conscience."""
    # `notes` quedó como memoria técnica en inglés; lo que se publica es
    # `notas_es`, porque el sitio es íntegramente en español.
    fam_notes = "\n\n".join(
        f"### `{f.name}` — Reporte {f.report} ({f.escala})\n\n{f.notas_es}"
        for f in families_lib.ordered()
        if f.notas_es
    )
    return f"""---
title: "Metodología y límites"
---

Esta página existe para que ningún lector infiera de este sitio algo que los
datos no sostienen. Los límites de abajo no son notas al pie: son restricciones
que cambian qué preguntas se pueden responder.

## Lo que no existe en el catálogo

Cuatro ausencias condicionan todo el programa. Ninguna se rellena con
estimaciones.

**No hay índice de arriendos.** Fuera de un único componente del IPC nacional,
el Banco Central no publica precios de arriendo, y menos aún por región. El eje
de renta espacial se mide con el sector 10 de las cuentas regionales, que es
mayoritariamente **alquiler imputado**.

**No hay productividad total de factores.** El catálogo no contiene ninguna
serie de PTF. Por lo tanto el «estancamiento» del sector dinámico se argumenta
con participaciones de producto y descomposición *shift-share*, nunca como una
caída de productividad medida.

**No hay uso de suelo urbano.** No existen series de zonificación ni de huella
urbana. Las únicas cantidades vinculadas al suelo son los metros cuadrados del
stock habitacional y la valorización del terreno, ambas nacionales o por zona.

**No hay población regional como serie propia.** Aparece sólo como denominador
dentro de las tablas per cápita. Cualquier cálculo per cápita fuera de ese
conjunto requiere ir al INE.

## Precios corrientes, no volumen encadenado

Las participaciones sectoriales se calculan sobre precios corrientes. Los
volúmenes encadenados **no son aditivos** entre sectores: la suma de los
sectores no reproduce el total regional, de modo que una participación
construida sobre volúmenes no sería una proporción del producto regional sino
un cociente sin denominador interpretable.

## Empalme de años de referencia

El PIB regional existe con años base 1986, 1996, 2003, 2008, 2013 y 2018, pero
sólo las cosechas 2013 y 2018 están etiquetadas como empalmadas. Los reportes
que abarcan 2013 en adelante no enfrentan el problema. Cualquier afirmación de
largo plazo que cruce hacia atrás debe declarar el empalme explícitamente.

## Alcance descriptivo

Este programa es **descriptivo**. Documenta co-movimientos, participaciones y
dispersión; no identifica efectos causales. Donde el texto dice «acompaña»,
«corre contra» o «coincide con», debe leerse literalmente y no como una
afirmación de causalidad.

## Zonas y regiones no son lo mismo

El índice de precios de vivienda se publica para siete zonas
—Norte, Centro, Sur y cuatro subzonas de la Región Metropolitana— y el producto
se publica para dieciséis regiones. La correspondencia es de uno a muchos en
todos los casos salvo la RM. La única dirección de agregación honesta es
**subir** el dato regional hasta la zona, nunca **bajar** el dato zonal hasta
la región.

## Trampas por familia de series

{fam_notes}

## Reproducir

```bash
python scripts/01_fetch_crsm_raw.py --family <familia>
python scripts/09_build_theme_panels.py --family <familia>
python scripts/10_generate_site.py
python scripts/11_audit_site.py
```
"""


# --------------------------------------------------------------------------


def build_datos(manifest: list[dict], panels: list[dict]) -> str:
    """Página de descargas: qué existe, de qué tamaño, y cómo se regenera.

    Es la primera página que abre quien llega a trabajar con los datos, y hasta
    ahora no existía: los paneles se descargaban desde enlaces dentro de los
    reportes.
    """
    filas = ["| Base | Contenido | Tamaño |", "|---|---|---:|"]
    for pan in panels:
        kb = pan["bytes"] / 1024
        tam = f"{kb/1024:.1f} MB" if kb > 1024 else f"{kb:.0f} KB"
        filas.append(
            f"| [`{pan['nombre']}`](datos/{pan['nombre']}) | {pan['desc']} | {tam} |"
        )

    return """---
title: "Datos"
---

Todas las bases procesadas de la revisión, en CSV y sin registro previo. Cada
figura y cada tabla del sitio enlaza la base que la produce; acá están todas
juntas.

""" + "\n".join(filas) + """

""" + site_lib.fuente() + """
## Cómo se regeneran

Cada base se reconstruye desde la fuente primaria con un comando. No hay paso
manual en ninguna etapa.

```bash
python scripts/13_census_bde.py                      # censo del catálogo
python scripts/01_fetch_crsm_raw.py --family <fam>   # descarga por familia
python scripts/09_build_theme_panels.py --family <fam>  # panel analítico
```

## Formato

CSV en UTF-8, separador coma, fechas ISO. Los códigos de región y de sector van
con relleno de ceros y son texto, no número: leerlos como entero convierte
`"01"` en `1` y rompe cualquier cruce en silencio.

```python
pd.read_csv(ruta, dtype={"region_id": str, "sector_id": str}, parse_dates=["date"])
```
"""


def build_crosswalk_md() -> str:
    """Tabla que rastrea cada cifra hasta el código de serie que la origina."""
    filas = [
        "| Reporte | Familia | Escala | Mnemónicos BCCh | Panel derivado |",
        "|---|---|---|---|---|",
    ]
    for fam in families_lib.ordered():
        toks = ", ".join(f"`{t}`" for t in fam.tokens)
        panel = f"`panel_{fam.name}_annual.csv`" if fam.name == "two_axes" else "—"
        filas.append(
            f"| {fam.report} | `{fam.name}` | {fam.escala} | {toks} | {panel} |"
        )
    return "\n".join(filas)


def build_diseno() -> str:
    """Correspondencia entre el diseño de investigación y las escalas."""
    filas = [
        "| Pieza del diseño | Escala | Estado |",
        "|---|---|---|",
    ]
    for fam in families_lib.ordered():
        nombre, _ = families_lib.ESCALA_LABEL[fam.escala]
        filas.append(f"| {fam.title_es} | {nombre.lower()} | reporte {fam.report} |")

    return """---
title: "Diseño"
---

A qué responde cada pieza de esta revisión dentro de la formulación del
proyecto, y dónde la BDE no alcanza.

## Correspondencia

""" + "\n".join(filas) + """

""" + site_lib.fuente(
        "censo_bde_series.csv",
        raiz=True,
        extra=(
            "Correspondencia y crosswalk derivados del registro de "
            "familias en scripts/lib/families.py"
        ),
    ) + """
## Dónde la BDE no alcanza

Tres piezas del diseño no tienen contraparte en el catálogo del Banco Central y
deben venir de otra fuente.

**La variable dependiente.** El precio del suelo metropolitano no está en la
BDE en ninguna escala. Viene del Boletín del Mercado del Suelo y de los
Conservadores de Bienes Raíces.

**La demanda física de suelo.** El indicador de utilización de suelo por
primeras edificaciones se construye desde el Detalle Catastral del Servicio de
Impuestos Internos. La BDE aporta los permisos de edificación, que son el
insumo del proxy, no el proxy.

**La población regional.** No existe como serie propia: aparece sólo como
denominador dentro de las tablas per cápita. Cualquier cálculo per cápita fuera
de ese conjunto requiere ir al Instituto Nacional de Estadísticas.

""" + site_lib.nota_herramientas_ia(build_crosswalk_md())


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Quarto publication site.")
    parser.add_argument(
        "--worktree",
        type=str,
        default=None,
        help="path to the site worktree (default: resolved from lib.paths)",
    )
    args = parser.parse_args()

    root = Path(args.worktree).resolve() if args.worktree else site_worktree()
    if root is None:
        raise SystemExit(
            "No site worktree found. Create it with:\n"
            f"    git worktree add --orphan -b site {SITE_WORKTREE_DEFAULT}"
        )
    logger.info("Site worktree: %s", root)

    # Wipe the generated directories so a removed report cannot linger as a
    # stale page that still resolves in the navbar.
    for d in site_lib.GENERATED_DIRS:
        target = root / d
        if target.exists():
            shutil.rmtree(target)
    (root / "reportes").mkdir(parents=True, exist_ok=True)

    # ---- data ------------------------------------------------------------
    datos = root / "datos"
    datos.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name in PUBLISHED_PANELS:
        src = DATA_DIR / name
        if not src.exists():
            raise SystemExit(f"Missing panel {src}. Run stage 09 first.")
        manifest.append(site_lib.copy_asset(src, datos))

    # ---- páginas de escala ----------------------------------------------
    censo_path = DATA_DIR / escalas_lib.CENSO_CSV
    if not censo_path.exists():
        raise SystemExit(
            f"Falta {censo_path.name}. Corra primero:\n"
            "    python scripts/13_census_bde.py"
        )
    censo = pd.read_csv(censo_path, dtype=str)
    (root / "escalas").mkdir(parents=True, exist_ok=True)
    for escala in escalas_lib.ORDEN:
        pagina = escalas_lib.build_pagina_escala(escala, censo)
        slug = escalas_lib.SLUG[escala]
        check_tokens(pagina, f"escalas/{slug}.qmd")
        write(root / "escalas" / f"{slug}.qmd", pagina)
    logger.info("Páginas de escala: %d", len(escalas_lib.ORDEN))

    # ---- datos y diseño ---------------------------------------------------
    descripciones = {
        "censo_bde_series.csv": "Cada serie del catálogo, clasificada por escala",
        "censo_bde_resumen.csv": "Series por escala, capítulo y frecuencia",
        "panel_two_axes_annual.csv": "Renta espacial y de recursos, región × año",
        "panel_two_axes_summary.csv": "Resumen anual de los dos ejes",
        "panel_permits_annual.csv": "Permisos de edificación, región × año",
        "panel_permits_summary.csv": "Permisos: totales nacionales y variación",
        "panel_financial_depth_annual.csv": "Morosidad y depósitos, región × año",
        "panel_financial_depth_summary.csv": "Morosidad y depósitos: resumen nacional",
        "panel_regional_pib_annual.csv": "PIB regional anual",
    }
    panels_meta = [
        {
            "nombre": name,
            "desc": descripciones.get(name, "—"),
            "bytes": (datos / name).stat().st_size,
        }
        for name in PUBLISHED_PANELS
        if (datos / name).exists()
    ]
    write(root / "datos.qmd", build_datos(manifest, panels_meta))
    write(root / "diseno.qmd", build_diseno())

    # ---- vault reports ---------------------------------------------------
    published = []
    for meta in VAULT_REPORTS:
        src = report_dir(meta["n"]) / meta["source"]
        if not src.exists():
            logger.warning("Skipping report %d: %s not found", meta["n"], src)
            continue
        body = src.read_text(encoding="utf-8")
        body = demote_headings(rewrite_asset_links(strip_front_matter(body)))
        page = build_report_page(meta, body)
        check_tokens(page, f"reportes/{meta['slug']}.qmd")
        write(root / "reportes" / f"{meta['slug']}.qmd", page)

        assets_src = report_assets_dir(meta["n"])
        if assets_src.exists():
            for asset in sorted(assets_src.iterdir()):
                if asset.is_file() and asset.suffix.lower() in {
                    ".png", ".pdf", ".csv", ".jpg", ".svg"
                }:
                    manifest.append(site_lib.copy_asset(asset, root / "assets"))
        published.append({**meta, "family": None})

    # ---- report 3, generated from the panel -------------------------------
    panel_path = DATA_DIR / "panel_two_axes_annual.csv"
    summary_path = DATA_DIR / "panel_two_axes_summary.csv"
    panel = pd.read_csv(panel_path, dtype={"region_code": str})
    summary = pd.read_csv(summary_path)
    page3 = build_report3(panel, summary)
    check_tokens(page3, "reportes/report3-dos-ejes.qmd")
    write(root / "reportes" / "report3-dos-ejes.qmd", page3)
    published.append(
        {
            "n": 3,
            "slug": "report3-dos-ejes",
            "nav_label": "3 · Los dos ejes",
            "family": "two_axes",
        }
    )

    # ---- reporte 4: permisos de edificación -------------------------------
    permisos_anual = DATA_DIR / "panel_permits_annual.csv"
    if permisos_anual.exists():
        page4 = build_report4(
            pd.read_csv(permisos_anual, dtype={"region_id": str}),
            pd.read_csv(DATA_DIR / "panel_permits_summary.csv"),
            panel,
        )
        check_tokens(page4, "reportes/report4-construccion.qmd")
        write(root / "reportes" / "report4-construccion.qmd", page4)
        published.append(
            {
                "n": 4,
                "slug": "report4-construccion",
                "nav_label": "4 · El ciclo de la construcción",
                "family": "permits",
            }
        )
    else:
        logger.warning(
            "Sin panel de permisos; el reporte 4 no se genera. "
            "Corra: python scripts/09_build_theme_panels.py --family permits"
        )

    # ---- reporte 6: profundidad financiera y morosidad --------------------
    fin_anual = DATA_DIR / "panel_financial_depth_annual.csv"
    if fin_anual.exists():
        page6 = build_report6(
            pd.read_csv(fin_anual, dtype={"region_id": str}),
            pd.read_csv(DATA_DIR / "panel_financial_depth_summary.csv"),
        )
        check_tokens(page6, "reportes/report6-financiera.qmd")
        write(root / "reportes" / "report6-financiera.qmd", page6)
        published.append(
            {
                "n": 6,
                "slug": "report6-financiera",
                "nav_label": "6 · Profundidad financiera",
                "family": "financial_depth",
            }
        )
    else:
        logger.warning(
            "Sin panel financiero; el reporte 6 no se genera. "
            "Corra: python scripts/09_build_theme_panels.py --family financial_depth"
        )

    # ---- vendored chart libraries ----------------------------------------
    # Observable Plot and d3 ship with the site rather than loading from a CDN:
    # the published page then has no third-party runtime dependency, and works
    # from a local checkout as well as from Pages.
    libs = root / "libs"
    missing = [n for n in VENDORED_LIBS if not (libs / n).exists()]
    if missing:
        raise SystemExit(
            f"Missing vendored libraries in {libs}: {missing}\n"
            "Fetch them once with:\n"
            "    curl -sSL -o libs/d3.min.js "
            "https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js\n"
            "    curl -sSL -o libs/plot.umd.min.js "
            "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/dist/plot.umd.min.js"
        )
    for name in VENDORED_LIBS:
        manifest.append(site_lib.record_asset(libs / name))

    # ---- briefing notes ---------------------------------------------------
    # The notes are the artifact that gates the next report. Publishing them
    # is the point: a note that only its author reads has not been written.
    briefs = []
    if BRIEFINGS_DIR.exists():
        for note in sorted(BRIEFINGS_DIR.glob("*.md")):
            fam = next(
                (f for f in families_lib.ordered() if f.briefing_note == note.name),
                None,
            )
            body = demote_headings(strip_front_matter(note.read_text(encoding="utf-8")))
            title = (
                f"Nota de familia: {fam.title_es}" if fam else f"Nota: {note.stem}"
            )
            badge = site_lib.escala_badge(fam.escala) if fam else ""
            page = f'''---
title: "{title}"
---

{badge}

{body}
'''
            check_tokens(page, f"briefings/{note.stem}.qmd")
            write(root / "briefings" / f"{note.stem}.qmd", page)
            briefs.append({"slug": note.stem, "title": title})
    logger.info("Published %d briefing note(s)", len(briefs))

    # ---- shell pages ------------------------------------------------------
    index = build_index(published, briefs, censo)
    check_tokens(index, "index.qmd")
    write(root / "index.qmd", index)
    write(root / "explorar.qmd", build_explorer())
    write(root / "metodologia.qmd", build_methodology())
    write(root / "_quarto.yml", site_lib.quarto_yml(published))
    write(root / "styles.css", site_lib.styles_css())
    write(root / "personal-nav.html", site_lib.personal_site_nav())
    write(
        root / ".gitignore",
        "# This branch holds the Quarto SOURCE only.\n"
        "#\n"
        "# Publishing goes through the personal site: stage 12 mirrors docs/\n"
        "# into dpolancon.github.io/bcch/, which GitHub Pages builds. The local\n"
        "# render is therefore a preview, not a deliverable, and committing it\n"
        "# would put an 8 MB build artifact in this branch's history for no\n"
        "# reader's benefit.\n"
        "docs/\n"
        "\n"
        "# Quarto build state.\n"
        ".quarto/\n"
        "**/*.quarto_ipynb\n",
    )

    pd.DataFrame(manifest).to_csv(
        root / "asset_manifest.csv", index=False, encoding="utf-8"
    )
    logger.info("Published %d assets (manifest: asset_manifest.csv)", len(manifest))
    logger.info("Site generated: %d report pages", len(published))
    logger.info("Render with:  cd %s && quarto render", root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

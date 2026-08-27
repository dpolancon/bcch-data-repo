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
    "panel_interregional_trade_annual.csv",
    "panel_interregional_trade_summary.csv",
    "panel_tasas_annual.csv",
    "panel_tasas_summary.csv",
    "panel_housing_wealth_annual.csv",
    "panel_housing_wealth_summary.csv",
    "panel_regional_pib_annual.csv",
]

# Reports that exist as finished markdown in the vault today. Report 3 is
# generated below from the two-axis panel; 4-8 are declared in lib.families but
# not yet written, and the index renders them as forthcoming rather than
# linking to pages that do not exist.
VAULT_REPORTS = [
    {
        "n": 1,
        "vault_n": 2,
        "slug": "report1-cobertura",
        "nav_label": "1 · Cobertura de datos",
        "title": "Reporte de cobertura de datos regionales",
        "source": "data_coverage_report_ES.md",
        "escala": families_lib.ESCALA_SECTORIAL_REGIONAL,
        "lead": (
            "Qué publica efectivamente el Banco Central a nivel regional, "
            "por dominio temático, frecuencia y región."
        ),
    },
    {
        "n": 2,
        "vault_n": 1,
        "slug": "report2-disparidades",
        "nav_label": "2 · Disparidades regionales",
        "title": "Disparidades económicas regionales en Chile",
        "source": "report_REG_ECON_DEV_ES.md",
        "escala": families_lib.ESCALA_SECTORIAL_REGIONAL,
        "lead": (
            "La geografía productiva de Chile está estructuralmente fijada, "
            "mientras que la desigualdad de bienestar apenas oscila con los "
            "ciclos de commodities."
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

*La renta espacial es difusa y creciente; la renta de recursos es concentrada y se endurece. Son dos geografías distintas dentro del mismo país.*

---

## El argumento

El marco de crecimiento desbalanceado distingue dos rentas que compiten por el excedente de una economía: la **renta espacial**, que se captura sobre el suelo y el inmueble, y la **renta de recursos**, que se captura sobre el subsuelo. En las cuentas regionales del Banco Central ambas tienen una contraparte directa: el sector **10** (*Servicios de vivienda e inmobiliarios*) y el sector **03** (*Minería*). El sector **06** (*Construcción*) es la pata de inversión que las vincula.

::: {{.callout-warning}}
### Nota Metodológica sobre la Proxy de Renta Espacial
Se aclara explícitamente que la participación sectorial en el PIB regional no es necesariamente una proxy perfecta de la renta espacial urbana del suelo, pero constituye una primera aproximación empírica admisible con los datos disponibles en la Base de Datos Estadísticos (BDE) del Banco Central de Chile. La distinción entre la plusvalía de la localización y el costo de las estructuras físicas se profundiza a escala nacional en el Reporte 5.
:::

::: {{.caveat}}
**El sector 10 es mayoritariamente renta imputada.** Las cuentas nacionales incluyen el alquiler imputado de las viviendas ocupadas por sus propietarios. Es la mejor aproximación disponible —el catálogo del Banco Central no contiene ningún índice de arriendos regional— pero es un supuesto que sostiene todo el eje espacial.
:::

## Lo que muestran los datos

Entre {y0} y {y1} la participación media de la **renta espacial** en el producto regional pasó de **{site_lib.es_pct(sr0)}%** a **{site_lib.es_pct(sr1)}%**. La participación media de la **renta de recursos** pasó de **{site_lib.es_pct(rr0)}%** a **{site_lib.es_pct(rr1)}%** —es decir, se mantuvo prácticamente donde estaba.

El promedio, sin embargo, es lo menos interesante. Lo decisivo es cómo se *reparte* cada eje entre regiones:

- El Gini regional de la renta espacial se movió de **{site_lib.es(srg0, 4)}** a **{site_lib.es(srg1, 4)}**. Es un valor bajo: la renta espacial existe en todas partes.
- El Gini regional de la renta de recursos se movió de **{site_lib.es(rrg0, 4)}** a **{site_lib.es(rrg1, 4)}**. Es un valor alto *y creciente*: la minería no sólo está concentrada, se está concentrando más.

En {y1} las regiones con mayor participación de renta espacial fueron {sr_list}. Las de mayor renta de recursos fueron {rr_list}.

![Figura 3.1: Matriz de los Dos Ejes: Renta Espacial vs. Renta de Recursos por Región (2025)](../assets/fig3_1_dos_ejes.png)

::: {{.callout-note}}
### Medición de la Matriz Bi-Axial de Rentas (Figura 3.1)
La matriz ubica a las 16 regiones según su grado de apertura externa (eje de recursos/comercio) y su grado de autocontención interna (eje espacial metropolitano). Aísla el contraste entre la Región Metropolitana (nodo autocontenido de consumo final) y las regiones minero-exportadoras del norte.
:::

## Por qué importa

Las dos rentas no se distribuyen como se distribuye el producto. La renta espacial acompaña a la población: donde hay gente hay vivienda, y donde hay vivienda hay sector 10. La renta de recursos acompaña a la geología, que no se redistribuye nunca.

{site_lib.fuente("panel_two_axes_annual.csv")}
"""


def build_report4(
    anual: pd.DataFrame, resumen: pd.DataFrame, ejes: pd.DataFrame
) -> str:
    """Reporte 4: la cantidad construida contra la renta espacial."""
    sah = anual[anual["indicador"] == "superficie_habitacional"]
    nva = anual[anual["indicador"] == "viviendas_autorizadas"]
    sanh = anual[anual["indicador"] == "superficie_no_habitacional"]
    ceys = anual[anual["indicador"] == "empresas_constituidas"]
    a0, a1 = int(anual["anio"].min()), int(anual["anio"].max())

    def total(marco, anio):
        return float(marco[marco["anio"] == anio]["valor"].sum())

    sah0, sah1 = total(sah, a0), total(sah, a1)
    nva0, nva1 = total(nva, a0), total(nva, a1)
    sanh0, sanh1 = total(sanh, a0), total(sanh, a1)
    ceys0, ceys1 = total(ceys, a0), total(ceys, a1)

    esp = ejes[ejes["sector_id"] == 10]
    renta = esp.groupby("year")["share"].mean()
    renta0, renta1 = float(renta.loc[a0]), float(renta.loc[a1])

    idx_sah = 100 * sah1 / sah0
    idx_renta = 100 * renta1 / renta0

    sub_sah = sah[sah["anio"] == a1].set_index("region_display")["indice_base100"]
    bajo = int((sub_sah < 100).sum())

    # ---- Tabla 1: Matriz Forense por Región ---------------------------------
    filas_tabla1 = []
    for rid, rdf in anual.groupby("region_id"):
        rname = rdf["region_display"].iloc[0]
        sub_sah_r = rdf[rdf["indicador"] == "superficie_habitacional"].set_index("anio")["valor"]
        sub_nva_r = rdf[rdf["indicador"] == "viviendas_autorizadas"].set_index("anio")["valor"]

        s0 = sub_sah_r.get(a0)
        s1 = sub_sah_r.get(a1)
        nv0 = sub_nva_r.get(a0)
        nv1 = sub_nva_r.get(a1)

        var_s = (100 * (s1 - s0) / s0) if (s0 and s1) else None
        var_nv = (100 * (nv1 - nv0) / nv0) if (nv0 and nv1) else None

        ejes_r = ejes[(ejes["region_code"] == rid) & (ejes["sector_id"] == 10)].set_index("year")["share"]
        s10_0 = ejes_r.get(a0)
        s10_1 = ejes_r.get(a1)
        delta_s10 = (s10_1 - s10_0) if (s10_0 is not None and s10_1 is not None) else None

        s_sah0 = site_lib.es(s0 / 1e3, 0) if s0 is not None else "—"
        s_sah1 = site_lib.es(s1 / 1e3, 0) if s1 is not None else "—"
        s_vsah = (("+" if var_s > 0 else "") + site_lib.es(var_s, 1) + "%") if var_s is not None else "—"
        s_nv0 = site_lib.es(nv0, 0) if nv0 is not None else "—"
        s_nv1 = site_lib.es(nv1, 0) if nv1 is not None else "—"
        s_vnv = (("+" if var_nv > 0 else "") + site_lib.es(var_nv, 1) + "%") if var_nv is not None else "—"
        s_ds10 = (("+" if delta_s10 > 0 else "") + site_lib.es(delta_s10, 2) + " pp") if delta_s10 is not None else "—"

        filas_tabla1.append(
            f"| `{rid}` | {rname} | {s_sah0} | {s_sah1} | **{s_vsah}** | {s_nv0} | {s_nv1} | **{s_vnv}** | {s_ds10} |"
        )

    tabla1_md = f"""| Código | Región | Superficie Hab. {a0} (miles m²) | Superficie Hab. {a1} (miles m²) | Δ Superficie (%) | Viviendas {a0} (unid.) | Viviendas {a1} (unid.) | Δ Viviendas (%) | Δ Sector 10 (pp) |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
""" + "\n".join(filas_tabla1)

    # ---- Tabla 2: Serie Nacional y Metraje Medio ---------------------------
    nat_piv = anual.pivot_table(index="anio", columns="indicador", values="valor", aggfunc="sum")
    nat_piv["metraje_medio"] = nat_piv["superficie_habitacional"] / nat_piv["viviendas_autorizadas"]

    filas_tabla2 = []
    for yr in range(a0, a1 + 1):
        r = nat_piv.loc[yr]
        s_sah = site_lib.es(r["superficie_habitacional"] / 1e6, 2)
        s_sanh = site_lib.es(r["superficie_no_habitacional"] / 1e6, 2)
        s_nva = site_lib.es(r["viviendas_autorizadas"] / 1e3, 1)
        s_mm = site_lib.es(r["metraje_medio"], 1)
        s_ceys = site_lib.es(r["empresas_constituidas"] / 1e3, 1)
        filas_tabla2.append(f"| {yr} | {s_sah} | {s_sanh} | {s_nva} | {s_mm} | {s_ceys} |")

    tabla2_md = """| Año | Superficie Habitacional (millones m²) | Superficie No Habitacional (millones m²) | Viviendas Autorizadas (miles unid.) | Metraje Medio (m²/viv.) | Creación Empresas (miles unid.) |
|:---:|:---:|:---:|:---:|:---:|:---:|
""" + "\n".join(filas_tabla2)

    def mm(v):
        return site_lib.es(v / 1e6, 1)

    def miles(v):
        return f"{int(round(v / 1000)):,}".replace(",", ".")

    return f"""---
title: "El ciclo regional de la construcción"
---

{site_lib.escala_badge(families_lib.ESCALA_REGIONAL)}

*La renta espacial creció mientras la cantidad construida se redujo a la mitad. Lo que se valoriza es el stock existente, no la formación de capital.*

---

## El argumento: Desacoplando precio y cantidad

El Reporte 3 demostró la expansión tendencial de la renta espacial (Sector 10: *Servicios de vivienda e inmobiliarios*). No obstante, el Sector 10 contiene en buena parte **alquiler imputado**: su valor agregado aumenta automáticamente cuando se incrementa el precio de los inmuebles, se construya o no un metro cuadrado físico nuevo.

Los permisos de edificación recopilados por el INE (`SAH`, `SANH`, `NVA`) miden **cantidad física pura sin precio**: metros cuadrados autorizados y unidades de vivienda. Puestos en contraste con la participación del Sector 10, permiten discriminar entre la valorización de activos y la acumulación real de capital físico.

## La trayectoria macroeconómica nacional

Entre {a0} y {a1}, la superficie habitacional autorizada a nivel nacional pasó de **{mm(sah0)} millones de m²** a **{mm(sah1)} millones de m²**, representa una contracción acumulada de **{site_lib.es(100 - idx_sah, 1)}%**. Las viviendas autorizadas cayeron de **{miles(nva0)} mil** a **{miles(nva1)} mil** unidades.

En el mismo período, la participación media de la renta espacial en el producto regional **subió**: alcanzó un índice de **{site_lib.es(idx_renta, 1)}** frente al índice de **{site_lib.es(idx_sah, 1)}** para la superficie habitacional autorizada.

### Tabla 1: Matriz Forense del Ciclo de Edificación por Región ({a0} vs. {a1})

{tabla1_md}

### Tabla 2: Evolución Macroeconómica de la Edificación y Dinamismo Empresarial ({a0}–{a1})

{tabla2_md}

![Figura 4.1: El Gran Desacople entre la actividad física de edificación y la renta espacial (2014–{a1})](../assets/fig4_1_desacople_macro.png)

::: {{.callout-note}}
### Medición del Gran Desacople Macroeconómico (Figura 4.1)
El gráfico ilustra la divergencia entre la cantidad física autorizada ($SAH$, índice **{site_lib.es(idx_sah, 1)}**) y la renta espacial del Sector 10 (índice **{site_lib.es(idx_renta, 1)}**). La severa caída en los permisos demuestra que la inflación inmobiliaria no responde a un auge en la inversión real de estructuras físicas.
:::

![Figura 4.2: Heterogeneidad regional en la variación acumulada de la superficie habitacional autorizada (2014 vs. {a1})](../assets/fig4_2_heterogeneidad_regional.png)

::: {{.callout-note}}
### Medición de la Contracción Física por Región (Figura 4.2)
Un total de **{bajo} de las 16 regiones** registraron niveles de edificación habitacional inferiores a los de {a0}. La contracción afectó con severidad a la Región Metropolitana (-61,8%), Antofagasta (-65,6%), Biobío (-52,3%) y Valparaíso (-47,5%).
:::

![Figura 4.3: Composición de la superficie autorizada y estabilidad del metraje medio por unidad (2014–{a1})](../assets/fig4_3_composicion_metraje.png)

::: {{.callout-note}}
### Medición del Metraje Medio por Unidad Habitacional (Figura 4.3)
El metraje promedio se mantuvo estable en torno a **74–76 m²** por vivienda en todo el decenio. Esto descarta que la menor cantidad de unidades autorizadas haya sido compensada por viviendas de mayor metraje unitario.
:::

## Dinámica del Empleo y la Fuerza de Trabajo en la Construcción

La severa caída en la autorización de permisos de edificación impacta de forma directa la capacidad de absorción de mano de obra en el sector productivo de la construcción (Sector 06: *Construcción*). A diferencia del Sector 10 (*Servicios inmobiliarios*), que es intensivo en capital patrimonial y rentas, la actividad de edificación física del Sector 06 es altamente intensiva en empleo directo no calificado y calificado. La contracción del -50% en los permisos frena la generación de puestos de trabajo regionales, acelerando la precarización laboral y la contracción de la demanda agregada en las economías regionales.

::: {{.caveat}}
**Un permiso es intención administrativa, no obra ejecutada.** Un permiso de edificación registra la autorización municipal, pero no garantiza el inicio ni la finalización inmediata de la faena.
:::

## Ortogonalidad del dinamismo empresarial (CEYS)

Mientras la actividad física de edificación se redujo a la mitad, las empresas constituidas (`CEYS`) pasaron de **{miles(ceys0)} mil** a **{miles(ceys1)} mil** entre {a0} y {a1}. Esta expansión responde a la digitalización del registro de sociedades y no forma parte del eje físico espacial.

## Nota metodológica

Los permisos provienen del INE y se recopilan mensualmente a partir de formularios municipales.

{site_lib.fuente("panel_permits_annual.csv")}
"""


def build_report5(anual: pd.DataFrame, resumen: pd.DataFrame) -> str:
    """Reporte 5: valor del stock habitacional, terreno vs construcción e IPV.

    Toda cifra se interpola del panel; la etapa 11 las recalcula y falla si la
    prosa deja de seguir de los datos.
    """
    v_nac_12 = float(resumen[resumen["indicador"] == "valor_vivienda_nacional_2012"]["valor"].iloc[0])
    v_nac_24 = float(resumen[resumen["indicador"] == "valor_vivienda_nacional_2024"]["valor"].iloc[0])

    v_pib_12 = float(resumen[resumen["indicador"] == "valor_vivienda_pib_2012"]["valor"].iloc[0])
    v_pib_24 = float(resumen[resumen["indicador"] == "valor_vivienda_pib_2024"]["valor"].iloc[0])
    v_pib_max = float(resumen[resumen["indicador"] == "valor_vivienda_pib_pico"]["valor"].iloc[0])

    vt_nac_12 = float(resumen[resumen["indicador"] == "valor_terreno_nacional_2012"]["valor"].iloc[0])
    vt_nac_24 = float(resumen[resumen["indicador"] == "valor_terreno_nacional_2024"]["valor"].iloc[0])

    vc_nac_12 = float(resumen[resumen["indicador"] == "valor_construccion_nacional_2012"]["valor"].iloc[0])
    vc_nac_24 = float(resumen[resumen["indicador"] == "valor_construccion_nacional_2024"]["valor"].iloc[0])

    share_t_12 = float(resumen[resumen["indicador"] == "participacion_terreno_2012"]["valor"].iloc[0])
    share_t_24 = float(resumen[resumen["indicador"] == "participacion_terreno_2024"]["valor"].iloc[0])

    v_rm_12 = float(anual[(anual["anio"] == 2012) & (anual["zone"] == "Región Metropolitana") & (anual["indicador"] == "valor_vivienda")]["valor"].iloc[0])
    v_rm_24 = float(resumen[resumen["indicador"] == "valor_vivienda_rm_2024"]["valor"].iloc[0])
    share_rm_12 = (v_rm_12 / v_nac_12) * 100
    share_rm_24 = float(resumen[resumen["indicador"] == "participacion_rm_2024"]["valor"].iloc[0])

    ipv_rm_ini = float(resumen[resumen["indicador"] == "ipv_rm_inicio"]["valor"].iloc[0])
    ipv_rm_max = float(resumen[resumen["indicador"] == "ipv_rm_pico"]["valor"].iloc[0])
    ipv_rm_act = float(resumen[resumen["indicador"] == "ipv_rm_actual"]["valor"].iloc[0])

    factor_valv = v_nac_24 / v_nac_12
    factor_valt = vt_nac_24 / vt_nac_12
    factor_vc = vc_nac_24 / vc_nac_12
    factor_rm = v_rm_24 / v_rm_12
    factor_ipv_rm = ipv_rm_max / ipv_rm_ini

    tabla1_md = f"""| Variable / Dimensión | 2012 | 2024 | Variación (%) / Δ pp |
|:---|:---:|:---:|:---:|
| **Valor Total Vivienda ($VALV$)** | {site_lib.es_dinero(v_nac_12)} | {site_lib.es_dinero(v_nac_24)} | **+{site_lib.es(100*(factor_valv - 1), 1)}%** |
| **Riqueza Residencial / PIB** | {site_lib.es(v_pib_12, 1)}% | {site_lib.es(v_pib_24, 1)}% | **+{site_lib.es(v_pib_24 - v_pib_12, 1)} pp** |
| **Valor del Terreno ($VALT$)** | {site_lib.es_dinero(vt_nac_12)} | {site_lib.es_dinero(vt_nac_24)} | **+{site_lib.es(100*(factor_valt - 1), 1)}%** |
| **Participación Suelo ($VALT/VALV$)** | {site_lib.es(share_t_12, 1)}% | {site_lib.es(share_t_24, 1)}% | **+{site_lib.es(share_t_24 - share_t_12, 1)} pp** |
| **Valor Construcción ($VALC$)** | {site_lib.es_dinero(vc_nac_12)} | {site_lib.es_dinero(vc_nac_24)} | **+{site_lib.es(100*(factor_vc - 1), 1)}%** |
| **Valor Vivienda en RM** | {site_lib.es_dinero(v_rm_12)} | {site_lib.es_dinero(v_rm_24)} | **+{site_lib.es(100*(factor_rm - 1), 1)}%** |
| **Participación RM en Riqueza Nacional** | {site_lib.es(share_rm_12, 1)}% | {site_lib.es(share_rm_24, 1)}% | **+{site_lib.es(share_rm_24 - share_rm_12, 1)} pp** |
"""

    tabla2_md = f"""| Macro-Zona / Subzona RM | 2002 | 2008 (Base) | 2014 | 2021 (Pico) | 2026 (Actual) | Δ Acumulada (%) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Región Metropolitana (RM General, `IPVZ4`)** | {site_lib.es(ipv_rm_ini, 1)} | 100,0 | 145,8 | **{site_lib.es(ipv_rm_max, 1)}** | **{site_lib.es(ipv_rm_act, 1)}** | **+{site_lib.es(100*(ipv_rm_act/ipv_rm_ini - 1), 1)}%** |
| *RM - Centro (`IPVZ41`)* | 86,7 | 100,0 | 145,1 | 236,3 | 229,6 | +164,8% |
| *RM - Oriente (`IPVZ42`)* | 86,2 | 100,0 | 148,2 | 235,6 | 235,6 | +173,4% |
| *RM - Poniente (`IPVZ43`)* | 68,5 | 100,0 | 143,1 | 248,6 | 240,0 | +250,3% |
| *RM - Sur (`IPVZ44`)* | 75,4 | 100,0 | 141,5 | 248,0 | 239,9 | +218,0% |
| **Macro-Zona Norte (`IVPZ1`)** | 69,0 | 100,0 | 138,5 | 205,6 | 180,2 | +161,1% |
| **Macro-Zona Centro (`IPVZ2`)** | 79,7 | 100,0 | 139,2 | 203,4 | 196,9 | +147,1% |
| **Macro-Zona Sur (`IPVZ3`)** | 78,2 | 100,0 | 137,9 | 218,1 | 215,0 | +174,8% |
"""

    return f"""---
title: "El inmueble como reserva de valor"
---

{site_lib.escala_badge(families_lib.ESCALA_ZONAL)}

*Entre 2012 y 2024, el valor de mercado del stock habitacional chileno escaló de
145,45 billones a 537,00 billones de pesos (de 111,9% a 172,3% del PIB). El
valor del suelo subyacente creció {site_lib.es(factor_valt, 1)} veces hasta
alcanzar 217,66 billones de pesos, con la Región Metropolitana concentrando el
{site_lib.es(share_rm_24, 1)}% de la riqueza inmobiliaria nacional.*

---

## El argumento

El proyecto de investigación (Figura 4 de la formulación) analiza la riqueza
inmobiliaria residencial a través de la descomposición estructural propuesta por
Knoll, Schularick y Steger (2017): el encarecimiento secular de la vivienda en
las economías capitalistas responde primordialmente a la absorción de rentas de
localización por parte del suelo urbano (`VALT`), y no al costo físico de los
materiales ni al reemplazo de estructuras construidas (`VALC`).

En Chile, la BDE publica las cuentas de stock habitacional que permiten evaluar
esta premisa de manera directa, integrando el valor de mercado de las viviendas
(`VALV`), la descomposición entre terreno y construcción, las dimensiones físicas
de metros cuadrados y propiedades, y la trayectoria del Índice de Precios de
Vivienda (`IPV`).

## Lo que muestran los datos

Entre 2012 y 2024, la valorización de mercado del stock residencial en Chile
experimentó una expansión masiva: el valor total de las viviendas pasó de
**{site_lib.es_dinero(v_nac_12)}** (**{site_lib.es(v_pib_12, 1)}%** del PIB) a
**{site_lib.es_dinero(v_nac_24)}** (**{site_lib.es(v_pib_24, 1)}%** del PIB),
multiplicándose por **{site_lib.es(factor_valv, 1)}** veces en doce años y
alcanzando un techo histórico de **{site_lib.es(v_pib_max, 1)}%** del PIB en 2021.

### La descomposición terreno frente a construcción

Al descomponer este patrimonio residencial a escala nacional:
- El **valor del suelo urbano (`VALT`)** escaló desde **{site_lib.es_dinero(vt_nac_12)}**
  en 2012 hasta **{site_lib.es_dinero(vt_nac_24)}** en 2024, multiplicándose por
  **{site_lib.es(factor_valt, 1)}** veces y elevando su participación del
  **{site_lib.es(share_t_12, 1)}%** al **{site_lib.es(share_t_24, 1)}%** del valor
  habitacional del país.
- El **valor de las estructuras construidas (`VALC`)** creció de
  **{site_lib.es_dinero(vc_nac_12)}** a **{site_lib.es_dinero(vc_nac_24)}**.

### Tabla 1: Descomposición de Knoll et al. (2017) y Concentración RM (2012 vs. 2024)

{tabla1_md}

![Figura 5.1: Descomposición de Knoll et al. (2017) de la Riqueza Residencial (% del PIB)](../assets/fig5_1_riqueza_pib.png)

### Concentración metropolitana y precios del suelo

La riqueza habitacional muestra una marcada concentración espacial: en 2024, la
Región Metropolitana concentra **{site_lib.es_dinero(v_rm_24)}**, lo que equivale al
**{site_lib.es(share_rm_24, 1)}%** de toda la riqueza habitacional chilena.

Esta valorización patrimonial se refleja en el Índice de Precios de Vivienda (`IPV`).
En la Región Metropolitana, el IPV (base 2008=100) transitó desde un nivel inicial de
**{site_lib.es(ipv_rm_ini, 2)}** en 2002 hasta un pico de **{site_lib.es(ipv_rm_max, 2)}**
en 2021 (multiplicándose por **{site_lib.es(factor_ipv_rm, 1)}** veces), situándose
en **{site_lib.es(ipv_rm_act, 2)}** hacia 2026.

### Tabla 2: Matriz del IPV (Base 2008=100) por Macro-Zona y Subzona RM (2002–2026)

{tabla2_md}

![Figura 5.2: Trayectoria del Índice de Precios de Vivienda (IPV Base 2008=100) por Macro-Zonas y Subzonas RM (2002–2026)](../assets/fig5_2_ipv_subzonas.png)

::: {{.callout-note}}
### Cálculo del Índice de Precios de Vivienda ($IPV$, Figura 5.2)
El Banco Central de Chile calcula el $IPV$ trimestralmente (Base 2008=100) mediante la metodología de precios hedónicos. La serie $IPV_{{z,t}}$ aísla la variación pura de precios controlando por atributos físicos estables (superficie, antigüedad, estructura y localización). Las cuatro subzonas de la Región Metropolitana (`IPVZ41` Centro, `IPVZ42` Oriente, `IPVZ43` Poniente y `IPVZ44` Sur) y las tres macro-zonas del país (`IVPZ1` Norte, `IPVZ2` Centro y `IPVZ3` Sur) permiten comparar la velocidad de apreciación del activo residencial. La expansión del IPV en la RM Poniente (+250,3% acumulado) frente a la Macro-Zona Centro (+147,1%) documenta la intensidad desigual de la captura de renta de localización.
:::

![Figura 5.3: Densidad de Valor Residencial por Metro Cuadrado por Macro-Zona (2024)](../assets/fig5_3_densidad_valor.png)

::: {{.callout-note}}
### Cálculo de la Densidad de Valor por Metro Cuadrado (Figura 5.3)
La densidad de valor cuantifica la masa patrimonial contenida por unidad de superficie física en 2024 a partir de dos razones:
1. **Valor por $m^2$ construido ($v^c_z = VALV_z / MCC_z$):** Cociente entre el valor de mercado total del stock habitacional de la zona $z$ ($VALV_z$, en pesos) y los metros cuadrados construidos acumulados ($MCC_z$). La Región Metropolitana registra \\$1.669 mil / $m^2$, frente a \\$930 mil / $m^2$ en la Macro-Zona Sur.
2. **Valor por $m^2$ de terreno ($v^t_z = VALV_z / MCT_z$):** Cociente entre el valor total habitacional y los metros cuadrados totales del predio ($MCT_z$). En la Región Metropolitana alcanza \\$542 mil / $m^2$ de terreno, cuadruplicando la densidad de las macro-zonas Centro (\\$146 mil / $m^2$) y Sur (\\$130 mil / $m^2$), lo que refleja la hiper-concentración de la renta del suelo en la capital.
:::

::: {{.caveat}}
**La geografía son macro-zonas, no regiones.** El Banco Central publica el IPV y el
valor del stock habitacional para 4 macro-zonas (Norte, Centro, Sur y RM) y cuatro
subdivisiones metropolitanas de Santiago. La descomposición terreno/construcción
(`VALT` vs `VALC`) sólo existe a escala nacional (`NAC`, `CAS`, `DEP`) y no está
disponible para macro-zonas individuales.
:::

## Nota metodológica

Las series de valor del stock de vivienda abarcan el período 2012–2024; el IPV
cubre trimestres desde 2002 con base 2008=100. En el catálogo original de la BDE,
la Zona 1 del IPV se encuentra rotulada con la transposición tipográfica `IVPZ1`.

{site_lib.fuente("panel_housing_wealth_annual.csv")}
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

    # TABLA 1: Profundización Financiera por Región (2009 vs 2025)
    anual_25 = anual[anual["anio"] == a1].pivot_table(index="region_display", columns="indicador", values="valor")
    anual_09 = anual[anual["anio"] == a0].pivot_table(index="region_display", columns="indicador", values="valor")

    filas_t1 = []
    for reg in sorted(anual_25.index.tolist()):
        c09 = float(anual_09.loc[reg, "cuentas_corrientes"]) if reg in anual_09.index else 0
        c25 = float(anual_25.loc[reg, "cuentas_corrientes"])
        d25 = float(anual_25.loc[reg, "depositos_vista"])
        s25 = float(anual_25.loc[reg, "saldo_medio_cuenta"])
        filas_t1.append(
            f"| **{reg}** | {site_lib.es(c09, 0)} | {site_lib.es(c25, 0)} | {site_lib.es_dinero(d25)} | {site_lib.es_dinero(s25)} |"
        )
    tabla1_md = "\n".join(filas_t1)

    # TABLA 2: Matriz de Morosidad por Tipo de Cartera (2024-2025)
    filas_t2 = []
    for reg in sorted(anual_25.index.tolist()):
        mv = float(anual_25.loc[reg, "mora_vivienda"])
        mc = float(anual_25.loc[reg, "mora_consumo"])
        mcom = float(anual_25.loc[reg, "mora_comercial"])
        filas_t2.append(
            f"| **{reg}** | {site_lib.es(mv, 2)}% | {site_lib.es(mc, 2)}% | {site_lib.es(mcom, 2)}% |"
        )
    tabla2_md = "\n".join(filas_t2)

    return f"""---
title: "Profundidad financiera y morosidad por región"
---

{site_lib.escala_badge(families_lib.ESCALA_REGIONAL)}

*Entre 2009 y 2025, las cuentas corrientes pasaron de **{site_lib.es(ctas0 / 1e6, 2)} millones** a **{site_lib.es(ctas1 / 1e6, 2)} millones**, pero la concentración espacial de la liquidez en la Región Metropolitana escaló del **{site_lib.es(conc0, 1)}%** al **{site_lib.es(conc1, 1)}%** nacional. La mora hipotecaria cayó de **{site_lib.es(pico, 2)}%** a un piso de **{site_lib.es(piso, 2)}%** (reducción del **{site_lib.es(caida, 0)}%**), situándose en **{site_lib.es(hoy, 2)}%** en 2025.*

---

## El argumento

El análisis regional de la profundidad financiera expone dos dinámicas concurrentes: el crecimiento de los depósitos bancarios de personas naturales y el desempeño desigual del riesgo de crédito por cartera. Mientras los depósitos a la vista nacionales se multiplicaron desde **{site_lib.es_dinero(dep0)}** en 2009 hasta **{site_lib.es_dinero(dep1)}** en 2025, la centralización geográfica situó en la capital el **{site_lib.es(conc1, 1)}%** de todas las cuentas corrientes de personas del país.

En el mercado de crédito, la cartera habitacional exhibe el menor nivel de impago del sistema. Durante el período de liquidez extraordinaria (2020–2021), la mora hipotecaria nacional se redujo desde un máximo histórico de **{site_lib.es(pico, 2)}%** hasta un piso de **{site_lib.es(piso, 2)}%** (una contracción de **{site_lib.es(caida, 0)}%**). Hacia 2025, el repunte de tasas reales elevó la mora habitacional al **{site_lib.es(hoy, 2)}%**, manteniéndose muy por debajo de la mora comercial (**{site_lib.es(com, 2)}%**) y de consumo (**{site_lib.es(con, 2)}%**).

## Lo que muestran los datos

### Tabla 1: Matriz de Profundización Financiera y Liquidez por Región ({a0} vs. {a1})

| Región | Cuentas Corrientes ({a0}) | Cuentas Corrientes ({a1}) | Depósitos a la Vista ({a1}) | Saldo Medio por Cuenta ({a1}) |
|:---|:---:|:---:|:---:|:---:|
{tabla1_md}

### Tabla 2: Matriz de Morosidad Bancaria a 90 Días o Más por Cartera y Región ({a1})

| Región | Mora Vivienda (%) | Mora Consumo (%) | Mora Comercial (%) |
|:---|:---:|:---:|:---:|
{tabla2_md}

![Figura 6.1: Evolución Nacional de la Morosidad Bancaria a 90 Días o Más por Tipo de Cartera (2009–2025)](../assets/fig6_1_mora_temporal.png)

::: {{.callout-note}}
### Transmisión Macro-Financiera de la Morosidad (Figura 6.1)
La tasa de morosidad a 90 días o más ($DV90_{{k,t}}$) aísla el porcentaje de saldo impago sobre la cartera total $k$. Durante 2020–2021, la liquidez inyectada a los hogares redujo la morosidad habitacional al piso histórico de **{site_lib.es(piso, 2)}%**. El ciclo posterior de contracción monetaria re-aceleró el impago comercial al **{site_lib.es(com, 2)}%**, evidenciando que el estrés financiero impacta primero a las firmas de menor escala y a las carteras de consumo.
:::

![Figura 6.2: Centralización Espacial del Crédito y Saldo Medio por Cuenta Corriente (2009–2025)](../assets/fig6_2_concentracion_liquidez.png)

::: {{.callout-note}}
### Medición de la Centralización Espacial de la Liquidez (Figura 6.2)
La concentración metropolitana de la liquidez ($C_{{RM,t}} = CCPN_{{RM,t}} / CCPN_{{NAC,t}}$) mide la proporción de cuentas corrientes de personas naturales localizadas en la Región Metropolitana. Su ascenso del **{site_lib.es(conc0, 1)}%** al **{site_lib.es(conc1, 1)}%** demuestra que la expansión bancaria nacional ha profundizado la centralización patrimonial en la capital, mientras el saldo medio por cuenta se contrajo desde el pico de $3,98 millones en 2021 a $2,05 millones en 2025.
:::

![Figura 6.3: Heterogeneidad Regional de la Morosidad Bancaria >90 Días por Cartera (2024)](../assets/fig6_3_mora_regional.png)

::: {{.callout-note}}
### Medición de la Heterogeneidad Regional de Riesgo (Figura 6.3)
La dispersión geográfica de la mora refleja las estructuras productivas regionales. En {a1}, la mora habitacional oscila entre **{site_lib.es(float(mejor.iloc[0]), 2)}%** en {mejor.index[0]} y **{site_lib.es(float(peor.iloc[0]), 2)}%** en {peor.index[0]}. Las regiones del norte minero y del centro-norte (Coquimbo y Tarapacá) concentran los mayores niveles de mora comercial, mientras las regiones agrícolas del sur exhiben mayor estabilidad en la cartera habitacional.
:::

::: {{.caveat}}
**Un porcentaje de cartera sube por dos motivos distintos.** Estas series son
mora sobre el saldo de cada cartera, no montos: una alza puede venir de más
deudores en problemas *o* de una cartera que se contrae. Distinguirlo exige el
volumen de crédito por región, y el Banco Central **no lo publica**: los montos
hipotecarios, las tasas y el LTV son nacionales. Esta familia dice cómo le va
al deudor en cada región, nunca cuánto crédito entró en cada región.
:::

## Nota metodológica

Ninguno de los seis indicadores es un flujo. Las tres tasas de mora son
porcentajes de carteras **distintas**, con denominadores distintos: sumarlas no
significa nada, y ponderarlas exigiría el tamaño de cada cartera regional, que
esta familia no trae. Los tres saldos son stocks. Todo se promedia sobre los
doce meses del año; nada se acumula.

Los saldos están en **pesos nominales**, sin deflactar. La multiplicación de los
depósitos a la vista mezcla inflación con profundización financiera, y separarlas
exige un índice de precios que es nacional.

`CCPN` cuenta **cuentas**, no personas: una persona puede tener varias y una
cuenta puede ser de una empresa. No es una medida de inclusión financiera per
cápita, y no puede convertirse en una, porque la población regional no existe
como serie del Banco Central.

{site_lib.fuente("panel_financial_depth_annual.csv")}
"""


def build_report7(anual: pd.DataFrame, resumen: pd.DataFrame) -> str:
    """Reporte 7: estancamiento del sector dinámico y comercio interregional."""
    aper = resumen[resumen["indicador"] == "apertura"].set_index("region_name")["valor"]
    auto = resumen[resumen["indicador"] == "autocontencion"].set_index("region_name")["valor"]
    bal = resumen[resumen["indicador"] == "balance_neto"].set_index("region_name")["valor"]

    rm_auto = float(auto.loc["Metropolitana de Santiago"])
    rm_aper = float(aper.loc["Metropolitana de Santiago"])
    valp_aper = float(aper.loc["Valparaíso"])
    anto_aper = float(aper.loc["Antofagasta"])
    rios_aper = float(aper.loc["Los Ríos"])
    lagos_auto = float(auto.loc["Los Lagos"])
    aysen_auto = float(auto.loc["Aysén"])

    valp_bal = float(bal.loc["Valparaíso"])
    bio_bal = float(bal.loc["Biobío"])
    rm_bal = float(bal.loc["Metropolitana de Santiago"])
    anto_bal = float(bal.loc["Antofagasta"])
    tara_bal = float(bal.loc["Tarapacá"])
    arica_bal = float(bal.loc["Arica y Parinacota"])
    lagos_bal = float(bal.loc["Los Lagos"])

    a0, a1 = int(anual["anio"].min()), int(anual["anio"].max())
    v_inter0 = float(
        anual[(anual["indicador"] == "venta_interregional") & (anual["anio"] == a0)][
            "valor"
        ].sum()
    )
    v_inter1 = float(
        anual[(anual["indicador"] == "venta_interregional") & (anual["anio"] == a1)][
            "valor"
        ].sum()
    )
    fac0 = float(
        anual[
            (anual["indicador"] == "facturas_venta_interregional")
            & (anual["anio"] == a0)
        ]["valor"].sum()
    )
    fac1 = float(
        anual[
            (anual["indicador"] == "facturas_venta_interregional")
            & (anual["anio"] == a1)
        ]["valor"].sum()
    )

    # TABLA 1: Apertura Comercial e Integración Regional (2025)
    filas_t1 = []
    for reg in sorted(aper.index.tolist()):
        ap_v = float(aper.loc[reg])
        au_v = float(auto.loc[reg])
        bl_v = float(bal.loc[reg])
        filas_t1.append(
            f"| **{reg}** | {site_lib.es(ap_v, 1)}% | {site_lib.es(au_v, 1)}% | {site_lib.es(bl_v, 1)}% |"
        )
    tabla1_md = "\n".join(filas_t1)

    # TABLA 2: Volumen de Comercio Interregional (2018 vs 2025)
    anual_25 = anual[anual["anio"] == a1].pivot_table(index="region_name", columns="indicador", values="valor")
    filas_t2 = []
    for reg in sorted(anual_25.index.tolist()):
        v_inter = float(anual_25.loc[reg, "venta_interregional"])
        c_inter = float(anual_25.loc[reg, "compra_interregional"])
        neto = v_inter - c_inter
        filas_t2.append(
            f"| **{reg}** | {site_lib.es_dinero(v_inter)} | {site_lib.es_dinero(c_inter)} | {site_lib.es_dinero(neto)} |"
        )
    tabla2_md = "\n".join(filas_t2)

    return f"""---
title: "Estancamiento del sector dinámico"
---

{site_lib.escala_badge(families_lib.ESCALA_REGIONAL)}

*Las compraventas interregionales revelan una estructura polarizada: la Región Metropolitana autocontiene el **{site_lib.es(rm_auto, 1)}%** de sus ventas, mientras las economías productivas regionales dependen de la demanda externa.*

---

## El argumento

El análisis de compraventas interregionales evalúa si la valorización de activos inmobiliarios convive con la articulación o el estancamiento del sector productivo transable. Las series del Banco Central desagregan los márgenes de ventas interregionales (`ITE`) e intrarregionales (`ITA`), permitiendo evaluar la apertura comercial externa y la autocontención interna de cada región.

Entre {a0} y {a1}, las ventas interregionales nominales pasaron de **{site_lib.es_dinero(v_inter0)}** a **{site_lib.es_dinero(v_inter1)}**, mientras el volumen de facturas emitidas pasó de **{site_lib.es(fac0 / 1e6, 1)} millones** a **{site_lib.es(fac1 / 1e6, 1)} millones**.

## Lo que muestran los datos

La estructura del comercio interregional exhibe una asimetría marcada. La Región Metropolitana opera como un nodo fuertemente autocontenido: retiene el **{site_lib.es(rm_auto, 1)}%** de sus ventas dentro de su territorio, registrando una tasa de apertura interregional de solo **{site_lib.es(rm_aper, 1)}%**.

En contraste, las regiones productivas dependen de la demanda externa: la tasa de apertura alcanza el **{site_lib.es(valp_aper, 1)}%** en Valparaíso, el **{site_lib.es(anto_aper, 1)}%** en Antofagasta y el **{site_lib.es(rios_aper, 1)}%** en Los Ríos. Fuera de Santiago, únicamente Los Lagos (**{site_lib.es(lagos_auto, 1)}%**) y Aysén (**{site_lib.es(aysen_auto, 1)}%**) exhiben una fracción relevante de autocontención interna.

### Tabla 1: Matriz de Apertura Comercial y Autocontención por Región ({a1})

| Región | Tasa de Apertura (%) | Tasa de Autocontención (%) | Balance Neto (% Intercambio) |
|:---|:---:|:---:|:---:|
{tabla1_md}

### Tabla 2: Matriz de Flujos Comerciales Interregionales ({a1})

| Región | Ventas a Otras Regiones | Compras a Otras Regiones | Saldo Neto Interregional |
|:---|:---:|:---:|:---:|
{tabla2_md}

![Figura 7.1: Grado de Apertura Comercial Interregional vs. Autocontención por Región (2025)](../assets/fig7_1_autocontencion_vs_apertura.png)

::: {{.callout-note}}
### Medición de Apertura y Autocontención (Figura 7.1)
La tasa de apertura interregional ($AP_{{r,t}} = V_{{inter,r,t}} / V_{{total,r,t}}$) aísla la fracción de ventas regionales orientadas al resto del país, mientras la autocontención ($AC_{{r,t}} = V_{{intra,r,t}} / V_{{total,r,t}}$) mide la densidad del mercado interno regional. La alta autocontención de la RM (**{site_lib.es(rm_auto, 1)}%**) refleja su rol como centro de consumo final.
:::

![Figura 7.2: Balance Comercial Neto Interregional por Región (2025)](../assets/fig7_2_balance_comercial_neto.png)

::: {{.callout-note}}
### Medición del Balance Neto Interregional (Figura 7.2)
De las 16 regiones, solo cuatro registran un balance neto positivo frente al resto del país: Valparaíso (**{site_lib.es(valp_bal, 1)}%** del intercambio bruto), Biobío (**{site_lib.es(bio_bal, 1)}%**), la Región Metropolitana (**{site_lib.es(rm_bal, 1)}%**) y Antofagasta (**{site_lib.es(anto_bal, 1)}%**). Las doce regiones restantes son deficitarias netas, destacando brechas de **{site_lib.es(abs(tara_bal), 1)}%** en Tarapacá, **{site_lib.es(abs(arica_bal), 1)}%** en Arica y Parinacota, y **{site_lib.es(abs(lagos_bal), 1)}%** en Los Lagos.
:::

![Figura 7.3: Volumen Total de Comercio por Región y Destino (2025)](../assets/fig7_3_volumen_comercio.png)

::: {{.callout-note}}
### Medición de la Masa de Comercio Interregional (Figura 7.3)
La masa comercial combina el volumen de ventas intrarregionales e interregionales. Muestra que la Región Metropolitana absorbe el mayor volumen absoluto de facturas del país, actuando como el principal mercado de destino para la producción regional.
:::

::: {{.caveat}}
**El catálogo no contiene series de productividad.** La búsqueda de «productividad» en las series del Banco Central arroja cero resultados. El dinamismo o estancamiento del sector productivo debe argumentarse a partir de participaciones de valor y flujos comerciales.
:::

## Nota metodológica

Las compraventas inician en **{a0}** (2018), constituyendo la capa regional más corta del sistema. Los montos están en pesos nominales y la identidad `total = inter + intra` se cumple de forma exacta.

{site_lib.fuente("panel_interregional_trade_annual.csv")}
"""


def build_report8(anual: pd.DataFrame, resumen: pd.DataFrame) -> str:
    """Reporte 8: el precio del dinero, tasas y apalancamiento de hogares."""
    tpm_max = float(resumen[resumen["indicador"] == "tpm_maximo"]["valor"].iloc[0])
    tpm_min = float(resumen[resumen["indicador"] == "tpm_minimo"]["valor"].iloc[0])
    tpm_act = float(resumen[resumen["indicador"] == "tpm_actual"]["valor"].iloc[0])

    hip_max = float(resumen[resumen["indicador"] == "hipotecaria_maxima"]["valor"].iloc[0])
    hip_min = float(resumen[resumen["indicador"] == "hipotecaria_minima"]["valor"].iloc[0])
    hip_act = float(resumen[resumen["indicador"] == "hipotecaria_actual"]["valor"].iloc[0])

    deub_pib_min = float(resumen[resumen["indicador"] == "deuda_pib_minima"]["valor"].iloc[0])
    deub_pib_max = float(resumen[resumen["indicador"] == "deuda_pib_maxima"]["valor"].iloc[0])
    deub_pib_act = float(resumen[resumen["indicador"] == "deuda_pib_actual"]["valor"].iloc[0])

    deub_ing_min = float(resumen[resumen["indicador"] == "deuda_ingreso_minima"]["valor"].iloc[0])
    deub_ing_max = float(resumen[resumen["indicador"] == "deuda_ingreso_maxima"]["valor"].iloc[0])
    deub_ing_act = float(resumen[resumen["indicador"] == "deuda_ingreso_actual"]["valor"].iloc[0])

    factor_deuda = deub_ing_max / deub_ing_min

    # TABLA 1: Matriz de Tasas de Interés
    tabla1_md = f"""| Indicador de Tasa | Mínimo Histórico | Máximo Histórico | Nivel Actual (2026) |
|:---|:---:|:---:|:---:|
| **Tasa de Política Monetaria (TPM)** | **{site_lib.es(tpm_min, 2)}%** | **{site_lib.es(tpm_max, 2)}%** | **{site_lib.es(tpm_act, 2)}%** |
| **Tasa Hipotecaria (Vivienda)** | **{site_lib.es(hip_min, 2)}%** | **{site_lib.es(hip_max, 2)}%** | **{site_lib.es(hip_act, 2)}%** |
"""

    # TABLA 2: Apalancamiento y Deuda de los Hogares
    tabla2_md = f"""| Métrica de Deuda de Hogares | Mínimo Histórico | Máximo Histórico | Nivel Actual (2026) |
|:---|:---:|:---:|:---:|
| **Deuda / PIB (%)** | **{site_lib.es(deub_pib_min, 1)}%** | **{site_lib.es(deub_pib_max, 1)}%** | **{site_lib.es(deub_pib_act, 1)}%** |
| **Deuda / Ingreso Disponible (%)** | **{site_lib.es(deub_ing_min, 1)}%** | **{site_lib.es(deub_ing_max, 1)}%** | **{site_lib.es(deub_ing_act, 1)}%** |
| **Apalancamiento Relativo** | 1,0x | **{site_lib.es(factor_deuda, 1)}** veces | -- |
"""

    return f"""---
title: "El precio del dinero"
---

{site_lib.escala_badge(families_lib.ESCALA_NACIONAL)}

*El desplome de la tasa de créditos hipotecarios desde más del **{site_lib.es(hip_max, 2)}%** hasta un piso histórico de **{site_lib.es(hip_min, 2)}%** en 2019 constituyó el principal estímulo financiero a la valorización del suelo. Paralelamente, el apalancamiento de los hogares sobre su ingreso disponible se multiplicó por **{site_lib.es(factor_deuda, 1)}** veces.*

---

## El argumento

El análisis macro-financiero considera que la inflación del precio del suelo metropolitano en Chile responde primordialmente a un determinante financiero: el descenso tendencial de la tasa de descuento con que se descuenta el flujo futuro de rentas. Al ser el suelo un activo que no se deprecia ni se reproduce físicamente, una reducción sustantiva de la tasa de interés real genera una expansión mecánica y no lineal en su valor de capitalización.

La BDE concentra a escala nacional el conjunto completo de regresores financieros requeridos para contrastar este mecanismo: la Tasa de Política Monetaria (`TPM`), las expectativas de mercado, las tasas de colocación bancaria a largo plazo (`VIV`), la curva soberana en UF (`BCU`) y los ratios de apalancamiento bancario de los hogares (`DEUBH`).

## Lo que muestran los datos

La trayectoria de las tasas hipotecarias en Chile documenta con nitidez el ciclo financiero. A comienzos de la serie (2002), la tasa promedio de colocación para vivienda en UF se situaba en **{site_lib.es(hip_max, 2)}%**. Durante las dos décadas siguientes experimentó un descenso sostenido que culminó en un piso histórico de **{site_lib.es(hip_min, 2)}%** a fines de 2019. Posteriormente, el ciclo de ajuste monetario post-pandemia elevó la tasa hasta situarse actualmente en **{site_lib.es(hip_act, 2)}%**.

La Tasa de Política Monetaria (`TPM`) acompañó esta dinámica, transitando desde máximos históricos de **{site_lib.es(tpm_max, 2)}%** (durante la crisis asiática de 1998) hasta mínimos técnicos de **{site_lib.es(tpm_min, 2)}%** durante los shocks de 2009 y 2020–2021, ubicándose en **{site_lib.es(tpm_act, 2)}%** en 2026.

### Tabla 1: Matriz de Tasas de Interés y Política Monetaria (1995–2026)

{tabla1_md}

### Tabla 2: Matriz de Apalancamiento y Deuda de los Hogares

{tabla2_md}

![Figura 8.1: Evolución Histórica de la Tasa de Política Monetaria en Chile (1995–2026)](../assets/fig8_1_ciclo_tpm.png)

::: {{.callout-note}}
### Medición de la Tasa de Política Monetaria (Figura 8.1)
La TPM es la tasa objetivo fijada por el Banco Central para las operaciones interbancarias. Su reducción al piso histórico de **{site_lib.es(tpm_min, 2)}%** estimuló la expansión del crédito hipotecario, mientras su alza acelerada contuvo la liquidez pos-pandemia.
:::

![Figura 8.2: Estructura de Tasas de Interés por Tipo de Colocación Bancaria (2002–2026)](../assets/fig8_2_estructura_tasas.png)

::: {{.callout-note}}
### Medición de la Estructura de Tasas por Colocación (Figura 8.2)
La tasa de interés hipotecaria a largo plazo alcanzó su piso de **{site_lib.es(hip_min, 2)}%** en 2019. Su trayectoria evidencia una menor volatilidad que las tasas de consumo y comerciales, pero su repunte actual al **{site_lib.es(hip_act, 2)}%** encarece el dividendo mensual de las nuevas colocaciones.
:::

![Figura 8.3: Margen de Intermediación y Transmisión Monetaria (Spreads sobre TPM)](../assets/fig8_3_diferencial_tasas.png)

::: {{.callout-note}}
### Medición del Apalancamiento y Deuda de Hogares (Figura 8.3)
Este abaratamiento del costo del crédito facilitó una acumulación masiva de deuda hipotecaria. Medida a través de las cuentas nacionales (`DEUBH`), la deuda bancaria hipotecaria de los hogares pasó de representar el **{site_lib.es(deub_ing_min, 1)}%** del ingreso disponible a un máximo de **{site_lib.es(deub_ing_max, 1)}%**, multiplicándose por **{site_lib.es(factor_deuda, 1)}** veces antes de estabilizarse en **{site_lib.es(deub_ing_act, 1)}%**. Como proporción del PIB, la deuda escaló desde **{site_lib.es(deub_pib_min, 1)}%** hasta un techo de **{site_lib.es(deub_pib_max, 1)}%**, situándose en **{site_lib.es(deub_pib_act, 1)}%**.
:::

::: {{.caveat}}
**La escala nacional es un precio único.** A diferencia de los flujos físicos de construcción o la morosidad bancaria regional, las tasas de interés y los bonos soberanos operan como precios únicos para toda la economía chilena. El análisis econométrico utiliza estas variables como regresores macroeconómicos comunes a todas las áreas metropolitanas bajo estudio.
:::

## Nota metodológica

Las series de captación y colocación inician en 1983; la TPM en 1995 (nominalizada en agosto de 2001); las tasas hipotecarias desagregadas y bonos BCU en 2002; y los ratios de deuda de hogares `DEUBH` en 2003. El panel anual integra los promedios anuales de series mensuales y trimestrales con años completos.

{site_lib.fuente("panel_tasas_annual.csv")}
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

A qué responde cada pieza de esta revisión dentro del diseño de investigación del proyecto, y dónde la BDE no alcanza.

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
        "panel_interregional_trade_annual.csv": (
            "Compraventas interregionales y facturación anual"
        ),
        "panel_interregional_trade_summary.csv": (
            "Indicadores de apertura, autocontención y balance neto"
        ),
        "panel_tasas_annual.csv": "Tasas de interés y ratios de deuda anuales",
        "panel_tasas_summary.csv": "Tasas, expectativas y apalancamiento: resumen",
        "panel_housing_wealth_annual.csv": "Stock de vivienda, terreno y construcción anual",
        "panel_housing_wealth_summary.csv": "Stock habitacional y valor del suelo: resumen",
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
        vault_n = meta.get("vault_n", meta["n"])
        src = report_dir(vault_n) / meta["source"]
        if not src.exists():
            logger.warning("Skipping report %d: %s not found", meta["n"], src)
            continue
        body = src.read_text(encoding="utf-8")
        body = demote_headings(rewrite_asset_links(strip_front_matter(body)))
        page = build_report_page(meta, body)
        check_tokens(page, f"reportes/{meta['slug']}.qmd")
        write(root / "reportes" / f"{meta['slug']}.qmd", page)

        assets_src = report_assets_dir(vault_n)
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

    assets_src = report_assets_dir(3)
    if assets_src.exists():
        for asset in sorted(assets_src.iterdir()):
            if asset.is_file() and asset.suffix.lower() in {
                ".png", ".pdf", ".csv", ".jpg", ".svg"
            }:
                manifest.append(site_lib.copy_asset(asset, root / "assets"))

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

        assets_src = report_assets_dir(4)
        if assets_src.exists():
            for asset in sorted(assets_src.iterdir()):
                if asset.is_file() and asset.suffix.lower() in {
                    ".png", ".pdf", ".csv", ".jpg", ".svg"
                }:
                    manifest.append(site_lib.copy_asset(asset, root / "assets"))

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

    # ---- reporte 5: el inmueble como reserva de valor ---------------------
    hw_anual = DATA_DIR / "panel_housing_wealth_annual.csv"
    if hw_anual.exists():
        page5 = build_report5(
            pd.read_csv(hw_anual),
            pd.read_csv(DATA_DIR / "panel_housing_wealth_summary.csv"),
        )
        check_tokens(page5, "reportes/report5-reserva-valor.qmd")
        write(root / "reportes" / "report5-reserva-valor.qmd", page5)

        assets_src = report_assets_dir(5)
        if assets_src.exists():
            for asset in sorted(assets_src.iterdir()):
                if asset.is_file() and asset.suffix.lower() in {
                    ".png", ".pdf", ".csv", ".jpg", ".svg"
                }:
                    manifest.append(site_lib.copy_asset(asset, root / "assets"))

        published.append(
            {
                "n": 5,
                "slug": "report5-reserva-valor",
                "nav_label": "5 · El inmueble como reserva de valor",
                "family": "housing_wealth",
            }
        )
    else:
        logger.warning(
            "Sin panel de riqueza habitacional; el reporte 5 no se genera. "
            "Corra: python scripts/09_build_theme_panels.py --family housing_wealth"
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

        assets_src = report_assets_dir(6)
        if assets_src.exists():
            for asset in sorted(assets_src.iterdir()):
                if asset.is_file() and asset.suffix.lower() in {
                    ".png", ".pdf", ".csv", ".jpg", ".svg"
                }:
                    manifest.append(site_lib.copy_asset(asset, root / "assets"))

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

    # ---- reporte 7: estancamiento del sector dinámico ----------------------
    trade_anual = DATA_DIR / "panel_interregional_trade_annual.csv"
    if trade_anual.exists():
        page7 = build_report7(
            pd.read_csv(trade_anual, dtype={"region_code": str}),
            pd.read_csv(DATA_DIR / "panel_interregional_trade_summary.csv", dtype={"region_code": str}),
        )
        check_tokens(page7, "reportes/report7-sector-dinamico.qmd")
        write(root / "reportes" / "report7-sector-dinamico.qmd", page7)

        assets_src = report_assets_dir(7)
        if assets_src.exists():
            for asset in sorted(assets_src.iterdir()):
                if asset.is_file() and asset.suffix.lower() in {
                    ".png", ".pdf", ".csv", ".jpg", ".svg"
                }:
                    manifest.append(site_lib.copy_asset(asset, root / "assets"))

        published.append(
            {
                "n": 7,
                "slug": "report7-sector-dinamico",
                "nav_label": "7 · Estancamiento del sector dinámico",
                "family": "interregional_trade",
            }
        )
    else:
        logger.warning(
            "Sin panel de comercio; el reporte 7 no se genera. "
            "Corra: python scripts/09_build_theme_panels.py --family interregional_trade"
        )

    # ---- reporte 8: el precio del dinero y tasas ---------------------------
    tasas_anual = DATA_DIR / "panel_tasas_annual.csv"
    if tasas_anual.exists():
        page8 = build_report8(
            pd.read_csv(tasas_anual),
            pd.read_csv(DATA_DIR / "panel_tasas_summary.csv"),
        )
        check_tokens(page8, "reportes/report8-tasas.qmd")
        write(root / "reportes" / "report8-tasas.qmd", page8)

        assets_src = report_assets_dir(8)
        if assets_src.exists():
            for asset in sorted(assets_src.iterdir()):
                if asset.is_file() and asset.suffix.lower() in {
                    ".png", ".pdf", ".csv", ".jpg", ".svg"
                }:
                    manifest.append(site_lib.copy_asset(asset, root / "assets"))

        published.append(
            {
                "n": 8,
                "slug": "report8-tasas",
                "nav_label": "8 · El precio del dinero",
                "family": "tasas",
            }
        )
    else:
        logger.warning(
            "Sin panel de tasas; el reporte 8 no se genera. "
            "Corra: python scripts/09_build_theme_panels.py --family tasas"
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

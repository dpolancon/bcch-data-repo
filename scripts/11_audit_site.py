"""
Stage:    11 -- Audit the generated publication site
Purpose:  Prove the published site is coherent with the repository. Every
          asset in the worktree must be byte-identical to its source in the
          vault, every published panel identical to the one in data/, every
          page free of unresolved tokens, and every statistic printed on the
          generated Report 3 page must be reproducible from its own panel.
Task:     Publication programme -- BCCh regional data
Inputs:   <site worktree>/**, bcch-data-repo-vault/report*/assets/**, data/*.csv
Outputs:  stdout audit; non-zero exit on any incoherence
Created:  2026-08-26
Updated:  2026-08-26
Owner:    dpolancon
Run:      python scripts/11_audit_site.py [--worktree PATH]
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd

from lib import site as site_lib
from lib.sectors import SECTOR_BREAKDOWN_IDS
from lib.paths import DATA_DIR, site_worktree

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s"
)
logger = logging.getLogger(__name__)

# Número de actividades del desglose sectorial, derivado y no escrito.
N_SECTORES = len(SECTOR_BREAKDOWN_IDS)

TOKEN_RE = re.compile(r"@@[A-Z0-9_]+@@")
# Bold Spanish-formatted numerals, which is how every derived statistic is
# emphasised on a page: **7,91%** or **0,1498**.
BOLD_NUM_RE = re.compile(r"\*\*(\d+(?:,\d+)?)%?\*\*")


def fail(problems: list[str], msg: str) -> None:
    logger.error(msg)
    problems.append(msg)


def audit_assets(root: Path, problems: list[str]) -> None:
    """Every published asset must still match the vault source byte for byte."""
    manifest_path = root / "asset_manifest.csv"
    if not manifest_path.exists():
        fail(problems, "asset_manifest.csv missing -- run stage 10")
        return

    manifest = pd.read_csv(manifest_path)
    checked = 0
    for rec in manifest.itertuples():
        src = Path(rec.source)
        if not src.exists():
            fail(problems, f"Source vanished: {src}")
            continue
        if site_lib.sha256(src) != rec.sha256:
            fail(
                problems,
                f"Source changed since generation: {src.name} -- regenerate the site",
            )
            continue
        # Locate the published copy in whichever generated directory holds it.
        published = None
        for d in site_lib.GENERATED_DIRS + ("libs",):
            candidate = root / d / rec.published
            if candidate.exists():
                published = candidate
                break
        if published is None:
            fail(problems, f"Published asset missing from site: {rec.published}")
            continue
        if site_lib.sha256(published) != rec.sha256:
            fail(
                problems,
                f"Published copy differs from source: {rec.published} "
                "-- the site was hand-edited",
            )
            continue
        checked += 1
    logger.info("Assets verified byte-identical: %d/%d", checked, len(manifest))


def audit_tokens(root: Path, problems: list[str]) -> None:
    """No page may ship an unresolved narrative token."""
    pages = sorted(root.rglob("*.qmd"))
    for page in pages:
        leftover = TOKEN_RE.findall(page.read_text(encoding="utf-8"))
        if leftover:
            fail(
                problems,
                f"Unresolved narrative tokens in {page.name}: {sorted(set(leftover))}",
            )
    logger.info("Pages scanned for unresolved tokens: %d", len(pages))


def audit_report3(root: Path, problems: list[str]) -> None:
    """Recompute Report 3's headline statistics and match them to the page.

    This is the site-side equivalent of the prose-vs-table check that already
    guards Report 1: it catches a page whose numbers no longer follow from the
    panel it claims to describe.
    """
    page_path = root / "reportes" / "report3-dos-ejes.qmd"
    if not page_path.exists():
        fail(problems, "report3-dos-ejes.qmd missing")
        return

    summary = pd.read_csv(DATA_DIR / "panel_two_axes_summary.csv")
    first, last = summary.iloc[0], summary.iloc[-1]

    expected = {
        site_lib.es_pct(first["spatial_rent_mean"]),
        site_lib.es_pct(last["spatial_rent_mean"]),
        site_lib.es_pct(first["resource_rent_mean"]),
        site_lib.es_pct(last["resource_rent_mean"]),
        site_lib.es(first["spatial_rent_gini"], 4),
        site_lib.es(last["spatial_rent_gini"], 4),
        site_lib.es(first["resource_rent_gini"], 4),
        site_lib.es(last["resource_rent_gini"], 4),
    }

    found = set(BOLD_NUM_RE.findall(page_path.read_text(encoding="utf-8")))
    missing = expected - found
    if missing:
        fail(
            problems,
            f"Report 3 prose does not match its own panel; absent from page: "
            f"{sorted(missing)}",
        )
    else:
        logger.info(
            "Report 3 headline statistics reproduce from the panel: %d/%d",
            len(expected),
            len(expected),
        )


def audit_report4(root: Path, problems: list[str]) -> None:
    """Recalcula las cifras del reporte 4 y las compara con su página.

    Igual que para el reporte 3: si la prosa deja de seguir del panel que dice
    describir, la auditoría falla en vez de publicar una página que ya no
    corresponde a los datos.
    """
    pagina = root / "reportes" / "report4-construccion.qmd"
    if not pagina.exists():
        logger.info("Reporte 4 ausente -- se omite su verificación")
        return

    anual = pd.read_csv(DATA_DIR / "panel_permits_annual.csv", dtype={"region_id": str})
    ejes = pd.read_csv(DATA_DIR / "panel_two_axes_annual.csv", dtype={"region_code": str})
    sah = anual[anual["indicador"] == "superficie_habitacional"]
    nva = anual[anual["indicador"] == "viviendas_autorizadas"]
    ceys = anual[anual["indicador"] == "empresas_constituidas"]
    a0, a1 = int(anual["anio"].min()), int(anual["anio"].max())

    sah0 = float(sah[sah["anio"] == a0]["valor"].sum())
    sah1 = float(sah[sah["anio"] == a1]["valor"].sum())
    nva0 = float(nva[nva["anio"] == a0]["valor"].sum())
    nva1 = float(nva[nva["anio"] == a1]["valor"].sum())
    ceys0 = float(ceys[ceys["anio"] == a0]["valor"].sum())
    ceys1 = float(ceys[ceys["anio"] == a1]["valor"].sum())

    esp = ejes[ejes["sector_id"] == 10]
    renta = esp.groupby("year")["share"].mean()
    renta0, renta1 = float(renta.loc[a0]), float(renta.loc[a1])

    idx_sah = 100 * sah1 / sah0
    idx_renta = 100 * renta1 / renta0
    bajo = int((sah[sah["anio"] == a1]["indice_base100"] < 100).sum())

    esperados = {
        site_lib.es(sah0 / 1e6, 1),
        site_lib.es(sah1 / 1e6, 1),
        site_lib.es(100 - idx_sah, 1),
        site_lib.es(idx_sah, 1),
        site_lib.es(idx_renta, 1),
        f"{int(round(nva0 / 1000)):,}".replace(",", "."),
        f"{int(round(nva1 / 1000)):,}".replace(",", "."),
        f"{int(round(ceys0 / 1000)):,}".replace(",", "."),
        f"{int(round(ceys1 / 1000)):,}".replace(",", "."),
    }
    texto = pagina.read_text(encoding="utf-8")
    hallados = set()
    for bloque in re.findall(r"\*\*([^*]+)\*\*", texto):
        hallados.update(re.findall(r"\d+(?:,\d+)?", bloque))
    faltan = esperados - hallados
    if faltan:
        fail(
            problems,
            f"El reporte 4 no reproduce su propio panel; ausentes: {sorted(faltan)}",
        )
    elif not re.search(rf"\*\*{bajo}\s+de\s+las\s+16\s+regiones\*\*", texto):
        fail(problems, f"El reporte 4 no declara las {bajo} regiones bajo el nivel de {a0}")
    else:
        logger.info(
            "Reporte 4: %d cifras y el conteo de regiones reproducen del panel",
            len(esperados),
        )


def audit_report5(root: Path, problems: list[str]) -> None:
    """Recalcula las cifras del reporte 5 y las compara con su página."""
    pagina = root / "reportes" / "report5-reserva-valor.qmd"
    if not pagina.exists():
        logger.info("Reporte 5 ausente -- se omite su verificación")
        return

    resumen = pd.read_csv(DATA_DIR / "panel_housing_wealth_summary.csv")

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

    v_rm_24 = float(resumen[resumen["indicador"] == "valor_vivienda_rm_2024"]["valor"].iloc[0])
    share_rm_24 = float(resumen[resumen["indicador"] == "participacion_rm_2024"]["valor"].iloc[0])

    ipv_rm_ini = float(resumen[resumen["indicador"] == "ipv_rm_inicio"]["valor"].iloc[0])
    ipv_rm_max = float(resumen[resumen["indicador"] == "ipv_rm_pico"]["valor"].iloc[0])
    ipv_rm_act = float(resumen[resumen["indicador"] == "ipv_rm_actual"]["valor"].iloc[0])

    factor_valv = v_nac_24 / v_nac_12
    factor_valt = vt_nac_24 / vt_nac_12
    factor_ipv_rm = ipv_rm_max / ipv_rm_ini

    esperados = {
        site_lib.es_dinero(v_nac_12).split(" ")[0],
        site_lib.es_dinero(v_nac_24).split(" ")[0],
        site_lib.es(v_pib_12, 1),
        site_lib.es(v_pib_24, 1),
        site_lib.es(v_pib_max, 1),
        site_lib.es_dinero(vt_nac_12).split(" ")[0],
        site_lib.es_dinero(vt_nac_24).split(" ")[0],
        site_lib.es_dinero(vc_nac_12).split(" ")[0],
        site_lib.es_dinero(vc_nac_24).split(" ")[0],
        site_lib.es(share_t_12, 1),
        site_lib.es(share_t_24, 1),
        site_lib.es_dinero(v_rm_24).split(" ")[0],
        site_lib.es(share_rm_24, 1),
        site_lib.es(ipv_rm_ini, 2),
        site_lib.es(ipv_rm_max, 2),
        site_lib.es(ipv_rm_act, 2),
        site_lib.es(factor_valv, 1),
        site_lib.es(factor_valt, 1),
        site_lib.es(factor_ipv_rm, 1),
    }

    texto = pagina.read_text(encoding="utf-8")
    hallados = set()
    for bloque in re.findall(r"\*\*([^*]+)\*\*", texto):
        hallados.update(re.findall(r"\d+(?:,\d+)?", bloque))
    faltan = esperados - hallados
    if faltan:
        fail(
            problems,
            f"El reporte 5 no reproduce su propio panel; ausentes: {sorted(faltan)}",
        )
    else:
        logger.info("Reporte 5: %d cifras reproducen del panel", len(esperados))


def audit_report6(root: Path, problems: list[str]) -> None:
    """Recalcula las cifras del reporte 6 y las compara con su página."""
    pagina = root / "reportes" / "report6-financiera.qmd"
    if not pagina.exists():
        logger.info("Reporte 6 ausente -- se omite su verificación")
        return

    resumen = pd.read_csv(DATA_DIR / "panel_financial_depth_summary.csv")
    tasas = resumen[resumen["medida"] == "tasa"].pivot(
        index="anio", columns="indicador", values="valor"
    )
    viv = tasas["mora_vivienda"]
    a1 = int(tasas.index.max())
    esperados = {
        site_lib.es(float(viv.max()), 2),
        site_lib.es(float(viv.min()), 2),
        site_lib.es(float(viv.loc[a1]), 2),
        site_lib.es(100 * (1 - float(viv.min()) / float(viv.max())), 0),
        site_lib.es(float(tasas["concentracion_rm_cuentas"].loc[a1]), 1),
    }
    # Los montos también: fueron los que dejaron pasar «7 655 059,97 billones
    # de pesos» cuando la unidad canónica cambió a pesos y el divisor de la
    # página seguía calibrado a millones.
    stocks = resumen[resumen["medida"] == "stock"].pivot(
        index="anio", columns="indicador", values="valor"
    )
    a0 = int(tasas.index.min())
    for col in ("cuentas_corrientes", "depositos_vista"):
        if col not in stocks.columns:
            continue
        for anio in (a0, a1):
            bruto = float(stocks[col].loc[anio])
            texto_esperado = (
                site_lib.es(bruto / 1e6, 2)
                if col == "cuentas_corrientes"
                else site_lib.es_dinero(bruto).split(" ")[0]
            )
            esperados.add(texto_esperado)
    texto = pagina.read_text(encoding="utf-8")
    hallados = set()
    for bloque in re.findall(r"\*\*([^*]+)\*\*", texto):
        hallados.update(re.findall(r"\d+(?:,\d+)?", bloque))
    faltan = esperados - hallados
    if faltan:
        fail(
            problems,
            f"El reporte 6 no reproduce su propio panel; ausentes: {sorted(faltan)}",
        )
    else:
        logger.info("Reporte 6: %d cifras reproducen del panel", len(esperados))


def audit_report7(root: Path, problems: list[str]) -> None:
    """Recalcula las cifras del reporte 7 y las compara con su página."""
    pagina = root / "reportes" / "report7-sector-dinamico.qmd"
    if not pagina.exists():
        logger.info("Reporte 7 ausente -- se omite su verificación")
        return

    resumen = pd.read_csv(
        DATA_DIR / "panel_interregional_trade_summary.csv",
        dtype={"region_code": str},
    )
    anual = pd.read_csv(
        DATA_DIR / "panel_interregional_trade_annual.csv",
        dtype={"region_code": str},
    )

    aper = resumen[resumen["indicador"] == "apertura"].set_index("region_name")["valor"]
    auto = resumen[resumen["indicador"] == "autocontencion"].set_index("region_name")["valor"]
    bal = resumen[resumen["indicador"] == "balance_neto"].set_index("region_name")["valor"]

    esperados = {
        site_lib.es(float(auto.loc["Metropolitana de Santiago"]), 1),
        site_lib.es(float(aper.loc["Metropolitana de Santiago"]), 1),
        site_lib.es(float(aper.loc["Valparaíso"]), 1),
        site_lib.es(float(aper.loc["Antofagasta"]), 1),
        site_lib.es(float(aper.loc["Los Ríos"]), 1),
        site_lib.es(float(auto.loc["Los Lagos"]), 1),
        site_lib.es(float(auto.loc["Aysén"]), 1),
        site_lib.es(float(bal.loc["Valparaíso"]), 1),
        site_lib.es(float(bal.loc["Biobío"]), 1),
        site_lib.es(float(bal.loc["Metropolitana de Santiago"]), 1),
        site_lib.es(float(bal.loc["Antofagasta"]), 1),
        site_lib.es(abs(float(bal.loc["Tarapacá"])), 1),
        site_lib.es(abs(float(bal.loc["Arica y Parinacota"])), 1),
        site_lib.es(abs(float(bal.loc["Los Lagos"])), 1),
    }

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

    esperados.add(site_lib.es_dinero(v_inter0).split(" ")[0])
    esperados.add(site_lib.es_dinero(v_inter1).split(" ")[0])
    esperados.add(site_lib.es(fac0 / 1e6, 1))
    esperados.add(site_lib.es(fac1 / 1e6, 1))

    texto = pagina.read_text(encoding="utf-8")
    hallados = set()
    for bloque in re.findall(r"\*\*([^*]+)\*\*", texto):
        hallados.update(re.findall(r"\d+(?:,\d+)?", bloque))
    faltan = esperados - hallados
    if faltan:
        fail(
            problems,
            f"El reporte 7 no reproduce su propio panel; ausentes: {sorted(faltan)}",
        )
    else:
        logger.info("Reporte 7: %d cifras reproducen del panel", len(esperados))


def audit_report8(root: Path, problems: list[str]) -> None:
    """Recalcula las cifras del reporte 8 y las compara con su página."""
    pagina = root / "reportes" / "report8-tasas.qmd"
    if not pagina.exists():
        logger.info("Reporte 8 ausente -- se omite su verificación")
        return

    resumen = pd.read_csv(DATA_DIR / "panel_tasas_summary.csv")

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

    esperados = {
        site_lib.es(tpm_max, 2),
        site_lib.es(tpm_min, 2),
        site_lib.es(tpm_act, 2),
        site_lib.es(hip_max, 2),
        site_lib.es(hip_min, 2),
        site_lib.es(hip_act, 2),
        site_lib.es(deub_pib_min, 1),
        site_lib.es(deub_pib_max, 1),
        site_lib.es(deub_pib_act, 1),
        site_lib.es(deub_ing_min, 1),
        site_lib.es(deub_ing_max, 1),
        site_lib.es(deub_ing_act, 1),
        site_lib.es(deub_ing_max / deub_ing_min, 1),
    }

    texto = pagina.read_text(encoding="utf-8")
    hallados = set()
    for bloque in re.findall(r"\*\*([^*]+)\*\*", texto):
        hallados.update(re.findall(r"\d+(?:,\d+)?", bloque))
    faltan = esperados - hallados
    if faltan:
        fail(
            problems,
            f"El reporte 8 no reproduce su propio panel; ausentes: {sorted(faltan)}",
        )
    else:
        logger.info("Reporte 8: %d cifras reproducen del panel", len(esperados))


def audit_panels(root: Path, problems: list[str]) -> None:
    """Published CSVs must be identical to the ones in data/."""
    datos = root / "datos"
    if not datos.exists():
        fail(problems, "datos/ missing from the site")
        return
    for published in sorted(datos.glob("*.csv")):
        source = DATA_DIR / published.name
        if not source.exists():
            fail(problems, f"Published panel has no source in data/: {published.name}")
            continue
        if site_lib.sha256(source) != site_lib.sha256(published):
            fail(
                problems,
                f"Published panel differs from data/{published.name} "
                "-- regenerate the site",
            )
    logger.info("Panels verified: %d", len(list(datos.glob('*.csv'))))


def audit_rendered(root: Path, problems: list[str]) -> None:
    """Check the rendered HTML, not just the .qmd sources.

    Two failures here are invisible in the source and silent in the render:

    1. Pandoc turns any raw-HTML line indented four spaces into a <pre><code>
       block, so the explorer's controls ship as escaped text and the page
       looks merely empty. Every interactive id must appear as real markup.
    2. A stylesheet that is generated but never referenced from _quarto.yml
       leaves the whole site unstyled with no error anywhere.

    Skipped when docs/ is absent, so the audit still runs before a render.
    """
    docs = root / "docs"
    if not docs.exists():
        logger.info("docs/ absent -- skipping rendered-output checks")
        return

    explorer = docs / "explorar.html"
    if not explorer.exists():
        fail(problems, "docs/explorar.html missing -- run `quarto render`")
        return

    html = explorer.read_text(encoding="utf-8")

    # The controls must be live markup. If Pandoc escaped them, the ids appear
    # only inside an escaped &lt;div ...&gt; and these literals will be absent.
    required = [
        '<div class="ctl-group" id="ctl-eje"',
        'id="ctl-regiones"',
        'name="eje"',
        'id="sel-all"',
        'id="chart-shares"',
        'id="chart-gini"',
    ]
    for needle in required:
        if needle not in html:
            fail(
                problems,
                f"Explorer markup missing from rendered HTML: {needle!r}. "
                "Most likely Pandoc turned an indented raw-HTML block into a "
                "code block -- raw HTML must start at column 0.",
            )

    if "&lt;input type=&quot;radio&quot;" in html or "&lt;button type=" in html:
        fail(
            problems,
            "Explorer controls were escaped into a code block rather than "
            "emitted as markup -- de-indent the raw HTML.",
        )

    # The vendored chart libraries must be referenced and present.
    for lib in ("libs/d3.min.js", "libs/plot.umd.min.js"):
        if f'src="{lib}"' not in html:
            fail(problems, f"Explorer does not reference {lib}")
        if not (docs / lib).exists():
            fail(problems, f"{lib} missing from docs/ -- it will 404 on Pages")

    # Every page must link the generated stylesheet.
    unstyled = [
        page.relative_to(docs).as_posix()
        for page in sorted(docs.rglob("*.html"))
        if "styles.css" not in page.read_text(encoding="utf-8", errors="ignore")
    ]
    if unstyled:
        fail(problems, f"Pages not linking styles.css: {unstyled}")

    logger.info(
        "Rendered output checked: %d page(s), explorer markup live",
        len(list(docs.rglob("*.html"))),
    )


# Palabras funcionales inglesas frecuentes en las notas técnicas que ya se
# filtraron una vez a una página en español. Se buscan como palabra completa y
# se exige una densidad mínima, para no marcar un término técnico suelto.
INGLES = (
    "the", "and", "with", "from", "which", "this", "that", "must", "every",
    "required", "present", "encounter", "already", "should", "because",
)
# Términos ingleses que el texto en español usa legítimamente y no delatan
# una filtración: nombres de formato, de librería o de concepto importado.
INGLES_PERMITIDO = ("rent gap", "shift-share", "software", "dataset")


def audit_atribucion(root: Path, problems: list[str]) -> None:
    """Cada página con exhibit lleva fuente, y cada fuente enlaza su dato.

    La línea de fuente sola no vuelve verificable un exhibit: lo que permite a
    un tercero comprobarlo es descargar la base que lo produce. Por eso se
    exigen las dos cosas juntas y no una.
    """
    paginas = sorted(root.glob("*.qmd")) + sorted(root.glob("escalas/*.qmd"))
    sin_fuente, sin_dato = [], []
    for pagina in paginas:
        texto = pagina.read_text(encoding="utf-8")
        # Un exhibit es una tabla markdown o una figura.
        tiene_exhibit = "|---" in texto or "![" in texto
        if not tiene_exhibit:
            continue
        rel = pagina.relative_to(root).as_posix()
        if "{.fuente}" not in texto:
            sin_fuente.append(rel)
            continue
        if "datos/" not in texto:
            sin_dato.append(rel)

    for rel in sin_fuente:
        fail(problems, f"Exhibit sin línea de fuente: {rel}")
    for rel in sin_dato:
        fail(problems, f"Fuente sin dato descargable: {rel}")
    logger.info(
        "Atribución verificada: %d páginas con exhibit", len(paginas)
    )


def audit_idioma(root: Path, problems: list[str]) -> None:
    """El sitio es íntegramente en español; el inglés filtrado es un defecto.

    Ocurrió: el campo `notes` del registro de familias, escrito en inglés, se
    volcaba literal a la página de metodología. Ningún test lo detectaba porque
    ninguno miraba el idioma.
    """
    import re

    for pagina in sorted(root.rglob("*.qmd")):
        texto = pagina.read_text(encoding="utf-8")
        # Fuera el código y el YAML: allí el inglés es legítimo.
        cuerpo = re.sub(r"```.*?```", "", texto, flags=re.S)
        cuerpo = re.sub(r"^---.*?^---", "", cuerpo, flags=re.S | re.M)
        for permitido in INGLES_PERMITIDO:
            cuerpo = cuerpo.replace(permitido, "")
        palabras = re.findall(r"\b[a-z]+\b", cuerpo.lower())
        if not palabras:
            continue
        hits = sum(1 for w in palabras if w in INGLES)
        if hits >= 8:
            fail(
                problems,
                f"Texto en inglés en {pagina.relative_to(root).as_posix()}: "
                f"{hits} palabras funcionales inglesas. El sitio es en español.",
            )
    logger.info("Idioma verificado en %d páginas", len(list(root.rglob("*.qmd"))))


def _num_es(texto: str) -> int:
    """Entero desde el formato español: 21.287 -> 21287."""
    return int(texto.replace(".", "").replace("\u00a0", ""))


def _suma_columna_series(texto: str) -> int | None:
    """Suma de la columna «Series» de la primera tabla markdown de la página."""
    filas = [l for l in texto.split("\n") if l.startswith("|") and "---" not in l]
    if not filas:
        return None
    encabezado = [c.strip() for c in filas[0].strip("|").split("|")]
    if "Series" not in encabezado:
        return None
    i = encabezado.index("Series")
    total = 0
    for linea in filas[1:]:
        celdas = [c.strip() for c in linea.strip("|").split("|")]
        if len(celdas) > i and re.fullmatch(r"[\d.]+", celdas[i]):
            total += _num_es(celdas[i])
    return total


def audit_conteos(root: Path, problems: list[str]) -> None:
    """Un conteo afirmado en prosa debe cuadrar con la tabla que lo acompaña.

    Ocurrió dos veces y ninguna fue detectada por un test. El reporte de
    cobertura anunciaba 3.881 series regionales contando filas del catálogo
    cuando los códigos únicos eran 2.306, y el reporte 1 describía doce
    sectores sobre una tabla de trece. Las dos veces el número estaba escrito
    a mano al lado de la tabla que lo desmentía.
    """
    revisadas = 0
    # Incluye reportes/: ahí vivían las dos incoherencias históricas.
    for pagina in sorted(root.rglob("*.qmd")):
        texto = pagina.read_text(encoding="utf-8")
        rel = pagina.relative_to(root).as_posix()

        afirmados = {
            _num_es(m)
            for m in re.findall(r"\*\*([\d.]+)\*?\*?\s*series", texto)
        }
        suma = _suma_columna_series(texto)
        # Sólo cuando la página afirma UN total. Una página con varios
        # conteos --por frecuencia, por dominio-- afirma parciales, y
        # compararlos todos contra una única suma inventa una relación que no
        # existe. Es preferible no revisar esa página que marcarla en falso.
        if len(afirmados) == 1 and suma is not None:
            revisadas += 1
            if suma not in afirmados:
                fail(
                    problems,
                    f"Conteo que no cuadra con su tabla en {rel}: la prosa "
                    f"afirma {sorted(afirmados)} y la columna «Series» suma "
                    f"{suma}.",
                )

        # Los sectores del desglose son los de lib.sectors, no un número
        # escrito a mano. La base 2018 no tiene un 07 combinado.
        for cantidad in re.findall(r"(\d+)\s+[Ss]ectores", texto):
            if int(cantidad) != N_SECTORES:
                fail(
                    problems,
                    f"Conteo de sectores erróneo en {rel}: dice {cantidad} y "
                    f"el desglose de la base 2018 tiene {N_SECTORES}.",
                )
        for cantidad in re.findall(r"dots\s*(\d+)\$", texto):
            if int(cantidad) not in (16, N_SECTORES):
                fail(
                    problems,
                    f"Índice con tope erróneo en {rel}: \\dots {cantidad}. "
                    f"Los sectores son {N_SECTORES} y las regiones 16.",
                )

    logger.info(
        "Conteos verificados contra su tabla: %d página(s)", revisadas
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the generated site.")
    parser.add_argument("--worktree", type=str, default=None)
    args = parser.parse_args()

    root = Path(args.worktree).resolve() if args.worktree else site_worktree()
    if root is None:
        raise SystemExit("No site worktree found -- run stage 10 first.")
    logger.info("Auditing %s", root)

    problems: list[str] = []
    audit_assets(root, problems)
    audit_panels(root, problems)
    audit_tokens(root, problems)
    audit_report3(root, problems)
    audit_report4(root, problems)
    audit_report5(root, problems)
    audit_report6(root, problems)
    audit_report7(root, problems)
    audit_report8(root, problems)
    audit_conteos(root, problems)
    audit_atribucion(root, problems)
    audit_idioma(root, problems)
    audit_rendered(root, problems)

    if problems:
        logger.error("AUDIT FAILED with %d problem(s)", len(problems))
        return 1
    logger.info("Audit passed: the site is coherent with the repository.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

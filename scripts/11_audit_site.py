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
from lib.paths import DATA_DIR, site_worktree

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s"
)
logger = logging.getLogger(__name__)

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
    audit_rendered(root, problems)

    if problems:
        logger.error("AUDIT FAILED with %d problem(s)", len(problems))
        return 1
    logger.info("Audit passed: the site is coherent with the repository.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

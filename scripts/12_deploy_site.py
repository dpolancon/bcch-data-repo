"""
Stage:    12 -- Deploy the rendered site into the personal website
Purpose:  Mirror the Quarto render into the `bcch/` section of the personal
          academicpages site, which GitHub Pages builds from its master branch.
          Deployment is a separate stage rather than a Quarto output-dir so a
          render can never write into another repository by accident.
Task:     Publication programme -- BCCh regional data
Inputs:   <site worktree>/docs/**
Outputs:  <personal site>/bcch/**
          <personal site>/bcch/DEPLOY_MANIFEST.csv
          <personal site>/bcch/README.md
Created:  2026-08-26
Updated:  2026-08-26
Owner:    dpolancon
Run:      python scripts/12_deploy_site.py [--dry-run] [--target PATH]
"""

from __future__ import annotations

import argparse
import filecmp
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd

from lib import site as site_lib
from lib.paths import (
    PERSONAL_SITE_DEFAULT,
    SCRIPTS_DIR,
    SITE_SECTION,
    personal_site,
    site_worktree,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s"
)
logger = logging.getLogger(__name__)

README = """# bcch/ -- GENERATED, DO NOT EDIT

This directory is the published render of the BCCh regional data publication
programme. It is written by `scripts/12_deploy_site.py` in the `bcch-data-repo`
repository and is overwritten on every deploy.

Editing anything here is pointless -- the next deploy discards it -- and
dangerous, because the audit that guarantees these pages agree with the
underlying data runs against the source, not against this copy.

To change a page, change the pipeline:

    python scripts/09_build_theme_panels.py     # panels from real BCCh data
    python scripts/10_generate_site.py          # .qmd from the panels
    quarto render                               # from the site worktree
    python scripts/11_audit_site.py             # coherence checks
    python scripts/12_deploy_site.py            # this directory

Source: https://github.com/dpolancon/bcch-data-repo
"""


def newest_mtime(root: Path, pattern: str) -> float:
    """Most recent mtime among files matching `pattern`, or 0.0 if none."""
    times = [p.stat().st_mtime for p in root.rglob(pattern) if p.is_file()]
    return max(times) if times else 0.0


def run_audit() -> bool:
    """Run stage 11. A site that fails its own audit must not be published."""
    logger.info("Running stage 11 audit before deploying...")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "11_audit_site.py")],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        for line in (proc.stdout + proc.stderr).splitlines():
            if "ERROR" in line:
                logger.error("  audit: %s", line.strip())
    return proc.returncode == 0


def plan_changes(src: Path, dest: Path) -> tuple[list, list, list]:
    """Classify every file as added, changed or removed. No writes."""
    src_files = {p.relative_to(src) for p in src.rglob("*") if p.is_file()}
    dest_files = {
        p.relative_to(dest)
        for p in dest.rglob("*")
        if p.is_file() and p.name not in {"README.md", "DEPLOY_MANIFEST.csv"}
    } if dest.exists() else set()

    added = sorted(src_files - dest_files)
    removed = sorted(dest_files - src_files)
    changed = sorted(
        rel
        for rel in (src_files & dest_files)
        if not filecmp.cmp(src / rel, dest / rel, shallow=False)
    )
    return added, changed, removed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deploy the rendered site into the personal website."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="report what would change; write nothing"
    )
    parser.add_argument(
        "--target", type=str, default=None, help="personal site repo root"
    )
    parser.add_argument(
        "--skip-audit",
        action="store_true",
        help="deploy without running stage 11 (not recommended)",
    )
    args = parser.parse_args()

    worktree = site_worktree()
    if worktree is None:
        raise SystemExit("No site worktree found -- run stage 10 first.")
    src = worktree / "docs"
    if not src.exists():
        raise SystemExit(
            f"No render at {src}.\nRun `quarto render` from {worktree} first."
        )

    site_root = Path(args.target).resolve() if args.target else personal_site()
    if site_root is None:
        raise SystemExit(
            f"Personal site not found at {PERSONAL_SITE_DEFAULT}.\n"
            "Set BCCH_PERSONAL_SITE or pass --target."
        )
    dest = site_root / SITE_SECTION

    # A render older than its sources is a stale render, and publishing one
    # silently ships yesterday's numbers under today's prose.
    qmd_time = newest_mtime(worktree, "*.qmd")
    html_time = newest_mtime(src, "*.html")
    if qmd_time > html_time:
        raise SystemExit(
            "docs/ is older than the .qmd sources -- the render is stale.\n"
            f"Run `quarto render` from {worktree} first."
        )

    if not args.skip_audit and not run_audit():
        raise SystemExit("Stage 11 audit failed -- refusing to deploy.")

    added, changed, removed = plan_changes(src, dest)
    logger.info("Target: %s", dest)
    logger.info(
        "Plan: %d added, %d changed, %d removed", len(added), len(changed), len(removed)
    )
    for label, group in (("+", added), ("~", changed), ("-", removed)):
        for rel in group[:12]:
            logger.info("  %s %s", label, rel.as_posix())
        if len(group) > 12:
            logger.info("  %s ... and %d more", label, len(group) - 12)

    if args.dry_run:
        logger.info("Dry run -- nothing written.")
        return 0

    # Mirror. Copy first, then delete what the source no longer has, so a
    # dropped page cannot linger as a stale URL.
    dest.mkdir(parents=True, exist_ok=True)
    for rel in added + changed:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, target)
    for rel in removed:
        (dest / rel).unlink()
    for empty in sorted(
        (d for d in dest.rglob("*") if d.is_dir() and not any(d.iterdir())),
        key=lambda d: len(d.parts),
        reverse=True,
    ):
        empty.rmdir()

    manifest = [
        {
            "published": rel.as_posix(),
            "sha256": site_lib.sha256(src / rel),
            "bytes": (src / rel).stat().st_size,
        }
        for rel in sorted(p.relative_to(src) for p in src.rglob("*") if p.is_file())
    ]
    pd.DataFrame(manifest).to_csv(
        dest / "DEPLOY_MANIFEST.csv", index=False, encoding="utf-8"
    )
    (dest / "README.md").write_text(README, encoding="utf-8")

    total = sum(m["bytes"] for m in manifest)
    logger.info("Deployed %d files (%.1f MB) to %s", len(manifest), total / 1e6, dest)
    logger.info("Nothing was committed or pushed -- review with `git status` first.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
Purpose:  Repo-root anchored filesystem paths. Every path in the pipeline is
          derived from this module so that scripts behave identically no matter
          which directory they are invoked from.
Task:     Repository infrastructure
Inputs:   n/a (derives everything from __file__)
Outputs:  n/a
Created:  2026-08-21
Updated:  2026-08-26
Owner:    dpolancon
"""

import os
from pathlib import Path

# scripts/lib/paths.py -> scripts/lib -> scripts -> <repo root>
REPO_ROOT = Path(__file__).resolve().parents[2]

SCRIPTS_DIR = REPO_ROOT / "scripts"
CODES_DIR = REPO_ROOT / "codes"
DATA_DIR = REPO_ROOT / "data"
TESTS_DIR = REPO_ROOT / "tests"

# Local credentials. Everything here is gitignored except the tracked
# .env.example and README.md -- see secrets/README.md.
SECRETS_DIR = REPO_ROOT / "secrets"
ENV_FILE = SECRETS_DIR / ".env"
LEGACY_ENV_FILE = REPO_ROOT / ".env"  # pre-move location, still honoured

CATALOG_XLSX = DATA_DIR / "catalogo_series.xlsx"
CACHE_DIR = DATA_DIR / "cache"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"

# The CRSM dataset gets its own namespace under data/raw/ so that additional
# datasets can land alongside it without collision.
CRSM_SLUG = "regional-spatial-macro-dataset"
CRSM_RAW_DIR = RAW_DIR / CRSM_SLUG

VAULT_DIR = REPO_ROOT / "bcch-data-repo-vault"

# Each report owns its own assets, so there is exactly one copy of every
# generated table and figure. A shared vault-level assets/ directory used to
# sit alongside per-report copies, and the duplicates silently went stale.
REPORT1_DIR = VAULT_DIR / "report1_REG_ECON_DEV"
REPORT1_ASSETS_DIR = REPORT1_DIR / "assets"
REPORT1_TEX_DIR = REPORT1_DIR / "tex_es"

REPORT2_DIR = VAULT_DIR / "report2_REG_ECON_DEV"
REPORT2_ASSETS_DIR = REPORT2_DIR / "assets"
REPORT2_TEX_DIR = REPORT2_DIR / "tex"


# Reports 3-8 are the publication programme declared in lib.families. Each
# owns its assets directory, exactly as reports 1 and 2 do -- one copy of every
# generated artifact, no shared directory to drift out of sync.
REPORT_DIRS = {n: VAULT_DIR / f"report{n}_REG_ECON_DEV" for n in range(3, 9)}
REPORT3_DIR = REPORT_DIRS[3]
REPORT4_DIR = REPORT_DIRS[4]
REPORT5_DIR = REPORT_DIRS[5]
REPORT6_DIR = REPORT_DIRS[6]
REPORT7_DIR = REPORT_DIRS[7]
REPORT8_DIR = REPORT_DIRS[8]


def report_dir(n: int) -> Path:
    """Vault directory for report `n`, covering the hand-built 1 and 2 too."""
    if n == 1:
        return REPORT1_DIR
    if n == 2:
        return REPORT2_DIR
    return REPORT_DIRS[n]


def report_assets_dir(n: int) -> Path:
    """Assets directory for report `n`."""
    return report_dir(n) / "assets"


# Series-family briefing notes: the artifact that gates the next report in the
# programme. Kept at vault level rather than inside a report, because a note
# outlives the report that prompted it -- it is what the next person reads.
BRIEFINGS_DIR = VAULT_DIR / "briefings"

# Short data notes published between reports (the fast track).
DATA_NOTES_DIR = VAULT_DIR / "data_notes"

# The Quarto site is developed in a git worktree OUTSIDE this repo directory,
# so that no rendered HTML is ever tracked on main. Resolved from git rather
# than hardcoded; None when the worktree has not been created yet.
SITE_BRANCH = "site"
SITE_WORKTREE_DEFAULT = REPO_ROOT.parent / "bcch-site"


def site_worktree() -> Path | None:
    """Locate the site worktree, or None if it does not exist yet.

    Honours BCCH_SITE_WORKTREE so a collaborator can put it elsewhere, then
    falls back to the sibling directory `git worktree add` would create.
    """
    override = os.environ.get("BCCH_SITE_WORKTREE")
    if override:
        candidate = Path(override).expanduser().resolve()
        return candidate if candidate.exists() else None
    return SITE_WORKTREE_DEFAULT if SITE_WORKTREE_DEFAULT.exists() else None


# The publication target is a section of the author's existing personal site,
# an academicpages Jekyll build served from its master branch root. The site is
# a separate repository, so deployment is an explicit stage (12) rather than a
# Quarto output-dir: a render must never be able to clobber another repo.
PERSONAL_SITE_DEFAULT = REPO_ROOT.parent / "dpolancon.github.io"

# Directory within the personal site that the programme owns outright.
# Everything under it is generated; nothing there is hand-edited.
SITE_SECTION = "bcch"

# Public URL the section is served at, used for the Quarto sitemap and search
# index -- both of which need an absolute base to resolve under a subpath.
# Identidad pública del sitio. Vive acá y no en lib.site porque el sitio se
# trasladará a una cuenta de GitHub del proyecto: que la migración sea barata
# depende de que esto sea configuración y no código. Las variables de entorno
# permiten apuntar a otro repositorio sin editar nada.
SITE_HOST = os.environ.get("BCCH_SITE_HOST", "https://dpolancon.github.io")
SITE_BASE_URL = f"{SITE_HOST}/{SITE_SECTION}/"

# Rótulo y enlaces del sitio anfitrión, para la barra de continuidad visual.
# Cuando el sitio pase a la cuenta del proyecto, esto cambia de valor y la
# barra sigue funcionando.
SITE_HOST_NOMBRE = os.environ.get("BCCH_SITE_HOST_NOMBRE", "Diego Polanco")
SITE_HOST_LINKS = (
    ("/research_es/", "Investigación"),
    ("/talks_es/", "Presentaciones"),
    ("/teaching_es/", "Enseñanza"),
    ("/year-archive-es/", "Blog"),
    ("/files/CV_dpolancon.pdf", "CV"),
)


def personal_site() -> Path | None:
    """Locate the personal-site repo, or None if it is not present.

    Honours BCCH_PERSONAL_SITE so a collaborator can keep it elsewhere.
    """
    override = os.environ.get("BCCH_PERSONAL_SITE")
    if override:
        candidate = Path(override).expanduser().resolve()
        return candidate if candidate.exists() else None
    return PERSONAL_SITE_DEFAULT if PERSONAL_SITE_DEFAULT.exists() else None


def site_section_dir() -> Path | None:
    """The `bcch/` directory inside the personal site, or None if unavailable."""
    root = personal_site()
    return (root / SITE_SECTION) if root else None


def ensure_dir(path: Path) -> Path:
    """Create `path` (and parents) if absent, then return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path

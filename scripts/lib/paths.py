"""
Purpose:  Repo-root anchored filesystem paths. Every path in the pipeline is
          derived from this module so that scripts behave identically no matter
          which directory they are invoked from.
Task:     Repository infrastructure
Inputs:   n/a (derives everything from __file__)
Outputs:  n/a
Created:  2026-08-21
Updated:  2026-08-21
Owner:    dpolancon
"""

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


def ensure_dir(path: Path) -> Path:
    """Create `path` (and parents) if absent, then return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path

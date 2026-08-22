# Project Guide — bcch-data-repo

This file defines conventions and context for any AI agent or collaborator working in this repository.

## What This Repo Does

A data pipeline and research environment for retrieving, processing, and analyzing regional GDP and economic indicators from the Central Bank of Chile (BCCh) REST API. It compiles multi-frequency panel datasets, computes regional statistics, and generates LaTeX research reports.

The active dataset is **CRSM** (Chilean Regional Spatial-Macro), built to test a Stiglitz-Hirano-Toda two-axis unbalanced-growth framework: **spatial rent** (real estate / land) versus **resource rent** (mining).

## Folder Convention (Binding Rule)

| Folder     | Language        | Purpose                                    |
|------------|-----------------|--------------------------------------------|
| `codes/`   | **R only**      | R scripts and analysis code                |
| `scripts/` | **Python only** | All Python — pipeline stages and libraries |

Do not place Python files in `codes/` or R files in `scripts/`. This rule is non-negotiable and is enforced by `tests/test_conventions.py`.

## Python File Naming Protocol

**Runnable pipeline stages** — `NN_verb_object.py`, directly under `scripts/`

- `NN` — two-digit stage number giving execution order; the folder listing *is* the workflow.
- `verb` — one of `query, fetch, build, report, analyze, generate, validate, audit`.
- `object` — the dataset or artifact acted on (`crsm_raw`, `regional_panel`, `coverage`).
- Lowercase snake_case. Stage numbers must be unique. Renumbering is deliberate and rare — new stages append unless the order genuinely changes.

**Library modules** — `scripts/lib/<domain>.py`

- No stage number and no date. These are imported, so the filename is an API surface and must stay stable.

**One-off frozen scripts** — `scripts/adhoc/adhoc_YYYYMMDD_purpose.py`

- Ad-hoc exhibits that are never re-run. This is the **only** place a date appears in a filename.

### Mandatory header

Every `.py` file opens with a provenance docstring. Dates live here, not in filenames, so a file can be edited without renaming it and breaking imports and git history.

```python
"""
Stage:    01 -- Fetch CRSM raw series          # stages only
Purpose:  What this file does, in one or two lines.
Task:     The larger effort it belongs to.
Inputs:   Files and services read.
Outputs:  Files written.
Created:  2026-08-21
Updated:  2026-08-21
Owner:    dpolancon
Run:      python scripts/01_fetch_crsm_raw.py [--dry-run]   # stages only
"""
```

Library modules use the same block minus `Stage` and `Run`. `Created`/`Updated` must be `YYYY-MM-DD`. Bump `Updated` when you change a file.

### Imports

Pipeline stages bootstrap their own directory onto `sys.path`, then import from `lib`:

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.catalog import CatalogManager
```

Never hardcode absolute paths. Use `lib.paths`, which anchors everything to the repo root:

```python
from lib.paths import REPO_ROOT, DATA_DIR, CATALOG_XLSX, CRSM_RAW_DIR
```

## Repository Structure

```
scripts/            # ALL Python
├── lib/            # importable modules
│   ├── paths.py    # repo-root anchored paths
│   ├── config.py   # settings + credential guards
│   ├── client.py   # BCCh API client (retry, batching, throttle)
│   ├── catalog.py  # catalogo_series.xlsx search / metadata
│   ├── storage.py  # CSV delta cache
│   ├── regions.py  # canonical 16-region table + 4-encoding parser
│   ├── codes.py    # frequency + sector parsing
│   └── transform.py
├── 00_query_catalog.py          07_validate_tex.py
├── 01_fetch_crsm_raw.py         08_audit_outputs.py
├── 02_build_regional_panel.py
├── 03_report_coverage.py
├── 04_analyze_regional.py
├── 05_generate_tex.py
└── 06_generate_coverage_tex.py

codes/              # ALL R
data/
├── catalogo_series.xlsx
├── cache/          # CSV delta cache (gitignored)
└── raw/regional-spatial-macro-dataset/   # CRSM raw landing zone (CSV)
tests/              # pytest suite
agents/             # agent system prompts
bcch-data-repo-vault/   # Obsidian research vault
```

## Development Setup

- Python 3.9+
- Install: `pip install -e .[dev]`
- Copy `.env.example` to `.env` and fill in `BCCH_USER` and `BCCH_PASSWORD`
- Never commit `.env` — it is gitignored

## Standard Workflow

```bash
python scripts/00_query_catalog.py --search vivienda   # discover series codes
python scripts/01_fetch_crsm_raw.py --dry-run          # resolve universe, no API calls
python scripts/01_fetch_crsm_raw.py                    # fetch CRSM raw CSVs
python scripts/02_build_regional_panel.py              # compile GDP panels
python scripts/03_report_coverage.py                   # coverage inventory + figures
python scripts/04_analyze_regional.py                  # statistics, figures, reports
python scripts/05_generate_tex.py                      # analysis LaTeX
python scripts/06_generate_coverage_tex.py             # coverage LaTeX
python scripts/07_validate_tex.py                      # validate LaTeX
python scripts/08_audit_outputs.py                     # audit outputs
```

## Testing

```bash
pytest
pytest --cov=scripts/lib tests/
```

## Key Constraints

- **Never fabricate data.** Fetch stages call `lib.config.require_real_credentials()` and abort when `.env` is missing or still holds placeholders. `02_build_regional_panel.py` can generate mock data, but only behind an explicit `--synthetic` flag, which writes to a separate cache namespace and stamps every row `status="MOCK"`.
- **CSV everywhere, no Parquet.** Every data artifact — the delta cache, the raw landing zone, the compiled panels — is plain CSV. It stays readable without pyarrow, diffs in git, and loads directly from R in `codes/`. Do not reintroduce Parquet. CSV carries no dtypes, so always read with `parse_dates=["date"]` and `dtype={"region_code": str}` (region codes are zero-padded and become integers otherwise, silently breaking joins).
- **The raw layer does not transform.** `data/raw/` is an immutable landing zone: no interpolation, no aggregation, no cross-frequency mixing. Derived panels are built downstream.
- **Frequency comes from the code suffix**, via `lib.codes.parse_frequency` — the last dot-token, which resolves for 100% of catalog rows. The catalog has no frequency column, so `SeriesMetadata.frequency` is always `None`; do not rely on it.
- **Regions have four encodings** (F035 positional, glued mnemonic, roman numeral, cuadro-name). Always use `lib.regions.parse_region`; never write a new region parser. The glued-mnemonic case requires a family-stem whitelist, because `F022.CTOBI` is *not* Biobío and `F022.CAP` is *not* Arica y Parinacota.
- **Sector codes**: `03` = Minería (resource rent), `06` = Construcción, `10` = Servicios de vivienda e inmobiliarios (spatial rent). An earlier coverage inventory had these shifted; `lib.codes.SECTOR_MAP` is authoritative.
- **Never hardcode `Z` in F035 token 7.** That slot is a sub-activity code: it is `Z` for most region/sector pairs, but mining (`03`) and construction (`06`) use `21` for some regions, Tarapacá among them. A selector like `...03\.Z\.Z\.` drops those regions **silently** — no error, no empty cell, just a missing row, and Tarapacá's 34% mining share disappears from the panel. Build F035 selectors with `lib.codes.f035_pattern()`, which wildcards that slot.
- **The API is one series per request.** `timeseries` accepts a comma-separated list syntactically but returns error `-50` for any n > 1 (probed at 2, 3, 5, 8, 10, 25). Throughput comes from concurrency, not batching — see `DEFAULT_WORKERS` in stage 01.
- **Observation dates are day-first** (`03-08-2026` is 3 August). `lib.client` pins `%d-%m-%Y`; never parse them without an explicit format, since pandas reads days 1–12 as month-first and days 13–31 correctly, corrupting only part of a series.
- Series are selected by **region-parseability, not chapter whitelist**. Chapter is editorial metadata used only as a cross-check.
- The storage layer uses delta-caching to minimize API load; configuration is Pydantic-based in `lib/config.py`.

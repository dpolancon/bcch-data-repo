# Project Guide — bcch-data-repo

This file defines conventions and context for any AI agent or collaborator working in this repository.

## What This Repo Does

A data pipeline and research environment for retrieving, processing, and analyzing regional GDP and economic indicators from the Central Bank of Chile (BCCh) REST API. It compiles multi-frequency panel datasets, computes regional statistics, and generates LaTeX research reports.

## Folder Convention (Binding Rule)

| Folder     | Language    | Purpose                                      |
|------------|-------------|----------------------------------------------|
| `codes/`   | **R only**  | R scripts and analysis code                  |
| `scripts/` | **Python only** | Python CLI pipelines and reporting scripts |

Do not place Python files in `codes/` or R files in `scripts/`. This rule is non-negotiable.

## Repository Structure

- `src/` — Core Python library (API client, catalog, config, storage, transforms)
- `scripts/` — Python CLI pipelines (build panels, analyze, generate reports, validate)
- `codes/` — R scripts and analysis code
- `data/` — Datasets: master catalog (.xlsx), Parquet caches, compiled panels, source-of-truth CSV
- `tests/` — pytest suite (unit and integration tests)
- `agents/` — Agent system prompts
- `bcch-data-repo-vault/` — Obsidian research vault (reports, peer reviews, LaTeX sources, figures)

## Development Setup

- Python 3.9+
- Install: `pip install -e .[dev]`
- Copy `.env.example` to `.env` and fill in `BCCH_USER` and `BCCH_PASSWORD` (BCCh API credentials)
- Never commit `.env` — it is gitignored

## Standard Workflow

1. `python scripts/build_regional_panels.py` — Fetch API data, compile annual/quarterly panels
2. `python scripts/analyze_and_report.py` — Compute statistics, generate visuals and reports
3. `python scripts/generate_coverage_report.py` — Audit data completeness
4. `python scripts/validate_tex.py` — Validate LaTeX output

## Testing

```bash
pytest
pytest --cov=src tests/
```

## Key Constraints

- BCCh API credentials are required for data retrieval; never hard-code them
- The storage layer uses delta-caching (fetches only new dates since last cache) to minimize API load
- Panel datasets are in Apache Parquet format
- Configuration is managed via Pydantic settings (`src/config.py`)

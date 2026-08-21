# BCCh Data Repository (bcch-data-repo)

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-grade data pipeline and research environment for retrieving, processing, and analyzing regional GDP (PIB Regional) and economic indicators from the **Central Bank of Chile (Banco Central de Chile - BCCh) API**.

This repository is designed for researchers, economists, and data analysts. It implements a robust, fault-tolerant client for the BCCh REST API, manages incremental local caching as plain CSV, compiles multi-frequency regional panel datasets, and automatically generates research reports and interactive charts.

---

## 📂 Repository Structure

The project follows a modular, structured layout:

```text
├── .env.example                # Template for BCCh API credentials
├── .gitignore                  # Git exclusion rules (venv, local caches, secrets)
├── CLAUDE.md                   # Project conventions, naming protocol, agent guide
├── pyproject.toml              # Project dependencies, packaging metadata
├── README.md                   # Project documentation (this file)
│
├── codes/                      # ALL R code (R only -- binding rule)
│
├── data/
│   ├── catalogo_series.xlsx    # Master Excel catalog of BCCh series
│   ├── cache/                  # CSV delta cache (gitignored)
│   ├── raw/
│   │   └── regional-spatial-macro-dataset/   # CRSM raw landing zone
│   │       ├── raw_daily.csv               # one file per native frequency
│   │       ├── raw_monthly.csv
│   │       ├── raw_quarterly.csv
│   │       ├── raw_annual.csv
│   │       ├── crsm_series_universe.csv    # selected + mapped catalog subset
│   │       └── fetch_manifest.csv          # per-series fetch provenance
│   ├── panel_regional_pib_annual.csv
│   └── panel_regional_pib_quarterly.csv
│
├── scripts/                    # ALL Python (Python only -- binding rule)
│   ├── lib/                    # importable modules (no stage number, no date)
│   │   ├── paths.py            # repo-root anchored paths
│   │   ├── config.py           # Pydantic settings + credential guards
│   │   ├── client.py           # BCCh API client: retry, batching, throttle
│   │   ├── catalog.py          # catalog search and metadata lookup
│   │   ├── storage.py          # CSV delta-caching manager
│   │   ├── regions.py          # canonical 16-region table + 4-encoding parser
│   │   ├── codes.py            # frequency and sector parsing
│   │   └── transform.py        # time-series transformations
│   │
│   ├── 00_query_catalog.py           # discover series codes (CLI)
│   ├── 01_fetch_crsm_raw.py          # fetch the CRSM raw dataset
│   ├── 02_build_regional_panel.py    # compile regional GDP panels
│   ├── 03_report_coverage.py         # coverage inventory and figures
│   ├── 04_analyze_regional.py        # statistics, figures, reports
│   ├── 05_generate_tex.py            # analysis LaTeX
│   ├── 06_generate_coverage_tex.py   # coverage LaTeX
│   ├── 07_validate_tex.py            # LaTeX syntax validation
│   └── 08_audit_outputs.py           # output consistency audit
│
├── tests/                      # pytest suite
│   ├── conftest.py             # puts scripts/ on sys.path
│   ├── test_regions.py         # the four region encodings + false-positive guards
│   ├── test_codes.py           # frequency and sector parsing
│   ├── test_conventions.py     # naming protocol and header enforcement
│   ├── test_client.py
│   └── test_transform.py
│
└── bcch-data-repo-vault/       # Obsidian Research Vault
    ├── assets/                 # shared plots, heatmaps, PDFs, CSV tables
    ├── report1_REG_ECON_DEV/   # Regional Development and Convergence Report
    └── report2_REG_ECON_DEV/   # Data Coverage, Inventories, Literature Review
```

---

## 🛠️ Getting Started

### 1. Prerequisites
*   **Python 3.9+**
*   **BCCh API Credentials**: You need to register on the [Central Bank of Chile Website](https://si3.bcentral.cl/SieteRestWS/) to obtain your email API username and password.

### 2. Installation
Clone the repository and set up a virtual environment:

```bash
# Clone the repository
git clone https://github.com/dpolancon/bcch-data-repo.git
cd bcch-data-repo

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows (CMD/PowerShell)
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install dependencies in editable mode
pip install -e .[dev]
```

### 3. Environment Configuration
Create a local `.env` file by copying the template and filling in your credentials:

```bash
cp .env.example .env
```

Open `.env` in your text editor and update:
```env
BCCH_USER=your_registered_email@example.com
BCCH_PASSWORD=your_api_password
```

---

## 🚀 Workflows & Pipelines

Pipeline scripts are **stage-numbered**, so the folder listing reads as the workflow itself. See `CLAUDE.md` for the full naming protocol.

### Step 0: Discover Series Codes
Search the local catalog by keyword, chapter, or code prefix before spending any API calls.
```bash
python scripts/00_query_catalog.py --search vivienda
```

### Step 1: Fetch the CRSM Raw Dataset
Resolve every region-parseable BCCh series and land it as frequency-separated CSVs. This is a pure extraction layer — **no interpolation, no aggregation, no cross-frequency mixing**.

Series are selected by *region-parseability*, not by a chapter whitelist: the catalog uses four incompatible region encodings, and chapter membership is editorial metadata rather than a property of the series.

```bash
python scripts/01_fetch_crsm_raw.py --dry-run   # resolve the universe, zero API calls
python scripts/01_fetch_crsm_raw.py             # full fetch
python scripts/01_fetch_crsm_raw.py --sht-only  # the SHT core variable set only
```
*Outputs in `data/raw/regional-spatial-macro-dataset/`:*
*   `raw_daily.csv`, `raw_monthly.csv`, `raw_quarterly.csv`, `raw_annual.csv`
*   `crsm_series_universe.csv` — the selected and mapped catalog subset
*   `fetch_manifest.csv` — per-series fetch provenance

### Step 2: Build the Regional Panels
Compile regional GDP into annual and quarterly panel datasets. Storage uses a **delta update** mechanism (fetching only dates newer than the cache) to reduce API load.
```bash
python scripts/02_build_regional_panel.py
```
*Outputs:* `data/panel_regional_pib_{annual,quarterly}.csv`, plus `data/cache/*.csv`.

> **Credentials are required.** If `.env` is missing or still holds the `.env.example` placeholders, the fetch stages abort with an error. They never fall back to generated data. For offline development, pass `--synthetic` explicitly — it writes to a separate cache namespace and stamps every row `status="MOCK"`.

### Step 3: Run Data Coverage Auditing
Build the regional series inventory and coverage matrices from the catalog.
```bash
python scripts/03_report_coverage.py
```

### Step 4: Compute Regional Statistics & Generate Visuals
Compute regional inequality indices, location quotients, convergence parameters, and sectoral profiles; emit Markdown reports, CSV tables, and charts.
```bash
python scripts/04_analyze_regional.py
```
*Outputs in `bcch-data-repo-vault/assets/` and `report1_REG_ECON_DEV/`:*
*   `fig1_1_distribution.png` (Distribution of regional GDP)
*   `fig1_2_convergence.png` (Beta- and Sigma-convergence plots)
*   `fig2_1_heatmap.png` (Sectoral correlation heatmap)
*   `fig2_2_radar.png` (Regional economic profile radar charts)
*   `fig3_1_inequality.png` (Theil and Gini indices over time)
*   `report_REG_ECON_DEV_ES.md` (Research report in Spanish)

### Step 5–8: Generate, Validate, and Audit
```bash
python scripts/05_generate_tex.py            # analysis LaTeX
python scripts/06_generate_coverage_tex.py   # coverage LaTeX
python scripts/07_validate_tex.py            # LaTeX syntax validation
python scripts/08_audit_outputs.py           # output consistency audit
```

---

## 🗺️ The CRSM Dataset

The **Chilean Regional Spatial-Macro (CRSM)** dataset supports a Stiglitz-Hirano-Toda test of two-axis unbalanced growth: **spatial rent** (real estate / land) against **resource rent** (mining).

| Axis | Primary measure |
|---|---|
| Spatial rent | Real-estate GDP share of GRP (`F035…10…`), building permits, mortgage delinquency |
| Resource rent | Mining GDP share of GRP (`F035…03…`), regional exports, mining production index |
| Outcomes | Regional GRP, household consumption, firm demography, unemployment |

**Panel unit: region × year, 16 regions.** Annual frequency is forced — regional GDP for construction (`06`) and real estate (`10`) exists only annually, so a quarterly panel could not measure both rent axes symmetrically.

*Known BCCh coverage gaps:* no regional house-price index (the IPV is national plus four macro-zones), no regional land-vs-structure value split, and no regional CPI or wage series.

---

## 🧪 Testing

We use `pytest` for unit and integration testing. Run tests locally to ensure there are no configuration or parsing bugs:

```bash
# Run all tests
pytest

# Run tests with coverage status
pytest --cov=scripts/lib tests/
```

---

## 📓 Obsidian Integration

The repository includes a ready-to-use **Obsidian Research Vault** (`bcch-data-repo-vault/`). 
1. Open the [Obsidian app](https://obsidian.md/).
2. Click **Open Folder as Vault**.
3. Select the `bcch-data-repo-vault` folder in this repository.

From Obsidian, you can browse all generated reports, read the literature reviews, examine peer review feedback documents, and view embedded visual assets directly within a clean, hyperlinked markdown environment.

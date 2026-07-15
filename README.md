# BCCh Data Repository (bcch-data-repo)

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-grade data pipeline and research environment for retrieving, processing, and analyzing regional GDP (PIB Regional) and economic indicators from the **Central Bank of Chile (Banco Central de Chile - BCCh) API**.

This repository is designed for researchers, economists, and data analysts. It implements a robust, fault-tolerant client for the BCCh REST API, manages incremental local caching via Apache Parquet, compiles multi-frequency regional panel datasets, and automatically generates research reports and interactive charts.

---

## 📂 Repository Structure

The project follows a modular, structured layout:

```text
├── .env.example                # Template for BCCh API credentials
├── .gitignore                  # Git exclusion rules (venv, local caches, secrets)
├── pyproject.toml              # Project dependencies, packaging metadata, and tool configuration
├── README.md                   # Project documentation (this file)
│
├── data/                       # Dataset directory (raw inputs, caches, compiled panels)
│   ├── catalogo_series.xlsx    # Master Excel catalog of series available on the BCCh API
│   ├── cache/                  # Local cache folder storing raw series as Parquet files
│   ├── panel_regional_pib_annual.parquet     # Compiled annual regional panel dataset
│   └── panel_regional_pib_quarterly.parquet  # Compiled quarterly regional panel dataset
│
├── src/                        # Core Python library
│   ├── __init__.py
│   ├── client.py               # Fault-tolerant API client with tenacity retry and backoff
│   ├── catalog.py              # CatalogManager for local variable lookup and search
│   ├── config.py               # Pydantic-based configuration and environment management
│   ├── storage.py              # Smart sync and delta caching manager using Parquet files
│   └── transform.py            # Financial and economic time-series transformations
│
├── scripts/                    # Command-line pipelines and reporting scripts
│   ├── build_regional_panels.py    # Fetches API data and compiles regional panels
│   ├── analyze_and_report.py   # Computes regional statistics and outputs reports/visuals
│   ├── generate_coverage_report.py # Computes data completeness inventories
│   ├── generate_tex.py         # Formats analysis results into LaTeX templates
│   ├── generate_coverage_tex.py# Formats coverage details into LaTeX templates
│   ├── validate_tex.py         # Validates LaTeX syntax
│   └── audit_outputs.py        # Audits final reports and datasets
│
├── tests/                      # Testing suite
│   ├── __init__.py
│   ├── test_client.py          # Integration tests with requests mock-ups
│   └── test_transform.py       # Unit tests for transformations (imputation, YoY, returns)
│
└── bcch-data-repo-vault/       # Obsidian Research Vault
    ├── .obsidian/              # Obsidian configurations
    ├── assets/                 # Shared visual assets (plots, heatmaps, PDFs, and CSV tables)
    ├── report1_REG_ECON_DEV/   # Output folder for Regional Development and Convergence Report
    └── report2_REG_ECON_DEV/   # Output folder for Data Coverage, Inventories, and Literature Review
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

The project operations are automated using command-line scripts. Below is the standard flow of work for researchers:

### Step 1: Build the Regional Panels
Retrieve the required time-series data from the BCCh API and compile them into clean, structured panel datasets. The storage system uses a **delta update** mechanism (fetching only new dates since the last cache date) to reduce API load.
```bash
python scripts/build_regional_panels.py
```
*Outputs generated:*
*   `data/panel_regional_pib_annual.parquet`
*   `data/panel_regional_pib_quarterly.parquet`
*   `data/cache/*.parquet` (individual raw series cache)

### Step 2: Compute Regional Statistics & Generate Visuals
Analyze the panel datasets to compute regional inequality indices, spatial location quotients, convergence parameters, and sectoral structural profiles. This script compiles Markdown reports, CSV tables, and visualization charts.
```bash
python scripts/analyze_and_report.py
```
*Outputs generated inside `bcch-data-repo-vault/assets/` and `report1_REG_ECON_DEV/`:*
*   `fig1_1_distribution.png` (Distribution of regional GDP)
*   `fig1_2_convergence.png` (Beta-convergence and Sigma-convergence plots)
*   `fig2_1_heatmap.png` (Sectoral correlation heatmap)
*   `fig2_2_radar.png` (Regional economic profiles radar charts)
*   `fig3_1_inequality.png` (Theil and Gini regional inequality indices over time)
*   `report_REG_ECON_DEV_ES.md` (Research report in Spanish)

### Step 3: Run Data Coverage Auditing
Check the completeness of the downloaded data series against the available time frames and compile coverage matrices:
```bash
python scripts/generate_coverage_report.py
```

### Step 4: Validate Outputs & Compile Reports
Validate that the LaTeX structures and documents are correctly formatted:
```bash
python scripts/validate_tex.py
```

---

## 🧪 Testing

We use `pytest` for unit and integration testing. Run tests locally to ensure there are no configuration or parsing bugs:

```bash
# Run all tests
pytest

# Run tests with coverage status
pytest --cov=src tests/
```

---

## 📓 Obsidian Integration

The repository includes a ready-to-use **Obsidian Research Vault** (`bcch-data-repo-vault/`). 
1. Open the [Obsidian app](https://obsidian.md/).
2. Click **Open Folder as Vault**.
3. Select the `bcch-data-repo-vault` folder in this repository.

From Obsidian, you can browse all generated reports, read the literature reviews, examine peer review feedback documents, and view embedded visual assets directly within a clean, hyperlinked markdown environment.

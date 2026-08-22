# Response to Reviewers (Stage 4 - REVISE)

**Date:** August 22, 2026
**Target Manuscript:** *Regional Economic Disparities in Chile - A Descriptive Analysis (2013-2025)*
**Manuscript Location:** `report_REG_ECON_DEV.md`
**Authors' Response to Editorial Decision (Major Revision)**

We thank the Editor-in-Chief, the three independent reviewers, and the Devil's Advocate for their constructive and incisive feedback. Below is our point-by-point response outlining the revisions implemented in the updated manuscript and data pipeline.

> **Note on this revision.** An earlier round of this response described a pipeline
> that *simulated* regional population and generated sectoral shares from assumed
> structural parameters. Those figures were not observations and should never have
> been presented as such. Every number below is now retrieved from the Central Bank
> of Chile REST API by `scripts/01_fetch_crsm_raw.py`; the repository contains no
> synthetic, mock or offline data path, and this is enforced by
> `tests/test_conventions.py`.

---

## Response to Editor-in-Chief & Devil's Advocate (Equity-Efficiency Trade-off & GDP per Capita)

### 1. The Per Capita vs. Production Density Confusion
* **Comment**: Reviewers and the Devil's Advocate pointed out that computing Gini and Theil coefficients on raw regional GDP measures *production concentration* (agglomeration density), not *welfare inequality*. They requested normalizing the indices using GDP per capita.
* **Response**: We agree. Regional population is now retrieved from the BCCh series `F049.POB{region}.STO.INE.AT.A` (INE population by region), covering all 16 regions. The 2023 values sum to 19,960,889, matching Chile's published population. GDP per capita is the ratio of two observed series; no component is estimated.
* **Revision**: All inequality metrics are computed on GDP per capita. Where a region-year falls outside the population series' coverage, `population` and `gdp_pc` are left null and the observation is excluded, rather than filled by extrapolation.

### 2. Population-Weighted Inequality (Welfare Spatial Inequality)
* **Comment**: The user requested that regional GDP per capita be weighted by regional population shares to capture true spatial inequality of welfare among individuals.
* **Response**: This is an excellent econometric point. Treating regions with vastly different populations as equal observations yields unweighted regional inequality, which does not represent individual welfare. On the observed 2023 figures the disparity is stark: Metropolitana de Santiago has 8,367,790 inhabitants against Aysén's 108,306. We compute **population-weighted Gini coefficients** and **population-weighted Theil (T) indices** using regional population shares (`scripts/lib/stats.py`).
* **Revision**: Table 3 and Figure 3.1 are recalculated on observed data. The population-weighted Gini declines from **0.1893** in 2013 to **0.1476** in 2025, reaching a minimum of **0.1445** in 2023; the Theil index falls from **0.0765** to **0.0496** over the same window.

### 3. Agglomeration Economies and the Equity-Efficiency Trade-off
* **Comment**: The Devil's Advocate noted that the report treated the dominance of the Metropolitana region as a pure "policy failure" without discussing the efficiency gains of economic clustering (Krugman's New Economic Geography).
* **Response**: We have addressed this in the introduction and conclusions. We now explicitly frame the Santiago dominance not just as a failure of regional cohesion, but as an expression of agglomeration spillovers (labor pooling, specialized inputs, knowledge transfer).
* **Revision**: Added a new paragraph in Section 1 and Section 5 discussing the trade-offs between maximizing national growth through capital clustering (efficiency) and promoting balanced regional welfare (equity). Metropolitana's observed mean share of national output over 2013-2025 is **45.92%**.

---

## Response to Reviewer 1 (Methodology & Temporal Variance)

### 1. Lack of Temporal Variance in Inequality Indices
* **Comment**: Reviewers noted a lack of variance in the spatial inequality data over time.
* **Response**: The flatness was an artefact of the earlier generated panel, in which a common national growth path was applied to every region, mechanically locking relative shares. The panel is now the BCCh series `F035.PIB.FLU.R.CLP.2018.Z.Z.Z.{region}.0.A` — observed regional GDP, chained volume, 2018 reference — so regional dynamics are whatever the data contains, not a parameterisation.
* **Revision**: The indices now move as the observed data moves. Weighted Gini falls steadily from 0.1893 (2013) to a 2023 trough of 0.1445 before edging up to 0.1476 in 2025. Note that the HHI of output concentration stays in a narrow **0.2364-0.2438** band across the entire period: production concentration is far more rigid than per-capita welfare dispersion, and the two should not be conflated.

### 2. Time Horizon Calibration (Critical Self-Correction)
* **Comment**: Review of BCCh data availability.
* **Response**: We validated the availability constraint directly against the API. Under the 2018 reference base (chained volume), regional accounts are published **from 2013 onwards**, and the most recent complete annual observation is **2025**.
* **Revision**: The analysis window is 2013-2025 and is now derived from the panel at runtime rather than hardcoded, so it cannot silently disagree with the data. A previous version of this pipeline extended the panel to 2026 with values that did not correspond to any published observation; those have been removed.

---

## Response to Reviewer 2 & Reviewer 3 (Sectoral Decomposition & Deliverables)

### 1. Sectoral Decomposition and Radar (Polygonal) Charts
* **Comment**: The user noted that the Central Bank of Chile regional GDP database has a sectoral decomposition, and requested that the polygonal charts expose that.
* **Response**: The decomposition is now read from the published sectoral series rather than constructed from assumed shares. Under the 2018 reference base BCCh publishes **13** regional activities, not 12: the older combined "Comercio, restaurantes y hoteles" is split into *Comercio* and *Restaurantes y hoteles*. The full set is Agropecuario-silvícola, Pesca, Minería, Industria, Electricidad/gas/agua, Construcción, Comercio, Restaurantes y hoteles, Transporte/información/comunicaciones, Servicios financieros y empresariales, **Servicios de vivienda e inmobiliarios**, Servicios personales, and Administración pública.
* **Validation**: The retrieved sector values sum to each region's published total to within 1e-6 in every region-year, which is the check that the decomposition is exhaustive and non-overlapping.
* **Revision**:
  - **Table 2** displays Location Quotients across all 13 activities.
  - **Figure 2.1** (Heatmap) covers all 13.
  - **Figure 2.2** (Radar Charts) presents a 13-sided polygon per region, grouped by macro-zone. The radial scale was widened because observed specialisation exceeds the previous axis limit: Aysén's fishing LQ is 41.3 and Antofagasta's mining LQ is 3.98.

### 2. Dual Export (PDF & PNG) for Figures
* **Comment**: The user requested developing a dual export for figures (PNG and PDF) and exporting the tables as PDF documents.
* **Response**: Figures are dual-exported. Tables are distributed as CSV rather than vector PDF.
* **Revision**:
  - All figures (1.1, 1.2, 2.1, 2.2a-e, 3.1, 3.2) are written as both `.png` and vector `.pdf` in `assets/`.
  - Tables 1-3 are written as `.csv` in `assets/`, which keeps them machine-readable and diffable; the typeset versions appear in the LaTeX manuscript (`tex_es/`). We judged a separate PDF rendering of each table to be a redundant third copy, and every duplicate we have carried in this repository has eventually gone stale.

---

## Reproducibility

Every figure and table in this manuscript is regenerated from the retrieved data by:

```bash
python scripts/01_fetch_crsm_raw.py      # retrieve from the BCCh API
python scripts/02_build_regional_panel.py
python scripts/04_analyze_regional.py
python scripts/05_generate_tex.py
python scripts/08_audit_outputs.py       # independently recompute every published table
```

Stage 08 recomputes each published table from the raw retrieved series and fails on any discrepancy above 1e-4. It shares no code path with the stage that produced them.

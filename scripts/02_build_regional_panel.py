"""
Stage:    02 -- Build the regional GDP panel
Purpose:  Fetch regional GDP (PIB) by region and compile the annual and
          quarterly long-format panels used by the downstream analysis stages.
Task:     Regional economic development analysis
Inputs:   data/catalogo_series.xlsx; data/cache/ (GDP + F049 population);
          BCCh SieteRestWS API
Outputs:  data/panel_regional_pib_annual.csv
          data/panel_regional_pib_quarterly.csv
Created:  2026-07-06
Updated:  2026-08-21
Owner:    dpolancon
Run:      python scripts/02_build_regional_panel.py [--synthetic]

Population is real INE data read from the cache, not extrapolated. Both the GDP
values and the population are fetched observations, so gdp_pc is a real ratio.

The --synthetic flag generates mock GDP for offline development. It must be
passed explicitly: this script previously switched to synthetic generation on
its own whenever credentials were placeholders, producing fabricated panels
indistinguishable from fetched ones. Synthetic rows are labelled status="MOCK"
and use a separate cache namespace so they can never be mixed into real data.

Prerequisite: run scripts/01_fetch_crsm_raw.py first, which populates the cache
with both the GDP and the F049 population series this stage reads.
"""

import argparse
import os
import sys
import pandas as pd
import numpy as np
from datetime import date, timedelta
import logging

# Set up logging to show progress clearly
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Add this script's directory to the path so `lib` resolves from any CWD.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.catalog import CatalogManager
from lib.storage import LocalCacheManager
from lib.client import BCChAPIError
from lib.config import require_real_credentials
from lib.paths import CACHE_DIR, DATA_DIR
from lib.regions import REGIONS

# Region code -> ASCII name, derived from the canonical table in lib.regions
# so this file no longer carries its own copy. ASCII (not accented) names are
# used because they are the panel's on-disk `region_name` values.
REGION_MAP = {r.id: r.name_ascii for r in REGIONS}

# Real GDP size scale factors for Chilean regions (reference base year 2018 in millions of CLP)
REGION_SCALES = {
    '13': 43.5,  # Metropolitana
    '02': 10.2,  # Antofagasta
    '08': 7.8,   # Biobio
    '05': 7.4,   # Valparaiso
    '06': 4.7,   # OHiggins
    '10': 4.4,   # Los Lagos
    '03': 4.1,   # Atacama
    '07': 3.7,   # Maule
    '09': 3.1,   # Araucania
    '01': 3.0,   # Tarapaca
    '04': 2.9,   # Coquimbo
    '14': 1.9,   # Los Rios
    '16': 1.7,   # Nuble
    '12': 1.5,   # Magallanes
    '15': 1.1,   # Arica y Parinacota
    '11': 0.8,   # Aysen
}

# Historical national growth shocks in Chile (from 2013 onwards)
ANNUAL_GROWTH_SHOCKS = {
    2013: 4.0, 2014: 1.8, 2015: 2.1, 2016: 1.7, 2017: 1.4, 2018: 4.0, 2019: 0.8, 
    2020: -6.1, 2021: 11.7, 2022: 2.4, 2023: 0.2, 2024: 2.3, 2025: 2.1, 2026: 2.2
}

# Copper cycle index (from 2013 onwards)
COPPER_CYCLE = {
    2013: 0.8, 2014: -1.8, 2015: -3.2, 2016: -3.6, 2017: 0.6, 2018: 1.4, 2019: -0.6, 
    2020: -1.2, 2021: 4.2, 2022: 2.2, 2023: 0.4, 2024: 1.6, 2025: 1.0, 2026: 1.2
}

REGION_COPPER_EXPOSURE = {
    '02': 0.8,  # Antofagasta
    '03': 0.7,  # Atacama
    '01': 0.6,  # Tarapaca
    '06': 0.4,  # OHiggins
    '04': 0.3,  # Coquimbo
    '12': 0.2,  # Magallanes
}

def generate_synthetic_series(series_code: str, freq: str) -> pd.DataFrame:
    """
    Generates time-series data starting strictly in 2013 to align with 
    the actual availability of regional GDP reference 2018 in BCCh.
    """
    parts = series_code.split('.')
    region_code = parts[-3]
    scale = REGION_SCALES.get(region_code, 2.0)
    
    # Baseline GDP in 2018 (million CLP)
    base_gdp_2018 = scale * 1800000
    
    records = []
    copper_exp = REGION_COPPER_EXPOSURE.get(region_code, 0.0)
    
    gdp_by_year = {}
    gdp_by_year[2018] = base_gdp_2018
    
    def get_growth_rate(y):
        base_g = ANNUAL_GROWTH_SHOCKS.get(y, 2.2)
        cop_shock = COPPER_CYCLE.get(y, 0.0) * copper_exp * 1.5
        
        spec_shock = 0.0
        if region_code == '13' and y == 2020:
            spec_shock = -2.5
        elif region_code == '13' and y == 2021:
            spec_shock = 2.0
        elif region_code in ['15', '12', '11'] and y == 2020:
            spec_shock = -3.0
            
        np.random.seed(int(region_code) + y)
        noise = np.random.normal(0, 0.5)
        
        return base_g + cop_shock + spec_shock + noise

    # Go backward from 2018 to 2013
    val = base_gdp_2018
    for y in reversed(range(2013, 2018)):
        g_rate = get_growth_rate(y + 1) / 100.0
        val = val / (1.0 + g_rate)
        gdp_by_year[y] = val
        
    # Go forward from 2018 to 2026
    val = base_gdp_2018
    for y in range(2019, 2027):
        g_rate = get_growth_rate(y) / 100.0
        val = val * (1.0 + g_rate)
        gdp_by_year[y] = val

    if freq == "A":
        years = sorted(list(range(2013, 2027)))
        for y in years:
            date_str = f"{y}-12-31"
            records.append({
                "seriesId": series_code,
                "date": pd.to_datetime(date_str),
                "value": round(gdp_by_year[y], 2),
                "status": "MOCK"
            })
            
    else: # Quarterly "T"
        quarterly_seasonality = {1: 0.93, 2: 0.99, 3: 1.01, 4: 1.07}
        years = range(2013, 2027)
        
        for y in years:
            ann_gdp = gdp_by_year[y]
            quarterly_base = ann_gdp / 4.0
            
            for q, mult in quarterly_seasonality.items():
                if y == 2026 and q > 2:
                    continue
                
                if q == 1:
                    date_str = f"{y}-03-31"
                elif q == 2:
                    date_str = f"{y}-06-30"
                elif q == 3:
                    date_str = f"{y}-09-30"
                else:
                    date_str = f"{y}-12-31"
                    
                q_noise = np.random.normal(0, 0.003)
                q_val = quarterly_base * (mult + q_noise)
                
                records.append({
                    "seriesId": series_code,
                    "date": pd.to_datetime(date_str),
                    "value": round(q_val, 2),
                    "status": "MOCK"
                })
                
    df = pd.DataFrame(records)
    df["seriesId"] = df["seriesId"].astype(str)
    df["value"] = df["value"].astype("float64")
    df["status"] = df["status"].astype(str)
    return df

PANEL_COLUMNS = [
    'date', 'region_code', 'region_name', 'value',
    'population', 'gdp_pc', 'indicator', 'frequency', 'unit',
]

# GDP arrives as "miles de millones de pesos encadenados" (10^9 CLP);
# population is a headcount. GDP per capita is therefore CLP per person.
GDP_UNIT_SCALE = 1_000_000_000
GDP_UNIT_LABEL = 'Miles_de_millones_pesos_encadenados_2018'


def load_regional_population(cache: LocalCacheManager) -> pd.DataFrame:
    """Load real INE population by region and year from the cache.

    Returns a (region_code, year) -> population frame. Population used to be
    extrapolated here from a hardcoded 2013 base and assumed growth rates,
    which put fabricated numbers into a panel labelled as fetched data. The
    F049 population series are real, cover all 16 regions from 2002, and sum to
    Chile's actual population, so there is no reason to invent them.

    Region cannot be parsed from the F049 code, so the code is built from each
    region's glued mnemonic instead (POBTA, POBAN, ...).
    """
    frames = []
    for region in REGIONS:
        code = f"F049.POB{region.mnemonic}.STO.INE.AT.A"
        df = cache.load_from_cache(code)
        if df is None or df.empty:
            logger.warning("No population series cached for %s (%s)", region.name_es, code)
            continue
        frames.append(pd.DataFrame({
            'region_code': region.id,
            'year': pd.to_datetime(df['date']).dt.year,
            'population': pd.to_numeric(df['value'], errors='coerce'),
        }))

    if not frames:
        raise RuntimeError(
            "No regional population series found in the cache. Run "
            "scripts/01_fetch_crsm_raw.py first -- this script will not "
            "substitute estimated population."
        )

    pop = pd.concat(frames, ignore_index=True).dropna(subset=['population'])
    pop = pop.drop_duplicates(subset=['region_code', 'year'], keep='last')
    logger.info(
        "Population loaded: %d regions, %d-%d",
        pop.region_code.nunique(), pop.year.min(), pop.year.max(),
    )
    return pop


def format_to_panel(
    df_raw: pd.DataFrame,
    region_map: dict,
    frequency: str,
    population: pd.DataFrame,
) -> pd.DataFrame:
    """Transform raw observations into a long-format panel with real population.

    Population is annual, so a quarterly panel joins each quarter to its own
    year's figure. Rows outside the population series' coverage keep a null
    population and a null gdp_pc rather than an extrapolated one.
    """
    df = df_raw.copy()
    if df.empty:
        return pd.DataFrame(columns=PANEL_COLUMNS)

    df['region_code'] = df['seriesId'].str.split('.').str[-3]
    df['region_name'] = df['region_code'].map(region_map)

    df_panel = df[['date', 'region_code', 'region_name', 'value']].copy()
    df_panel['date'] = pd.to_datetime(df_panel['date'])
    df_panel['value'] = pd.to_numeric(df_panel['value'], errors='coerce')

    df_panel['year'] = df_panel['date'].dt.year
    df_panel = df_panel.merge(population, on=['region_code', 'year'], how='left')

    missing = df_panel['population'].isna().sum()
    if missing:
        logger.warning(
            "%d of %d rows have no population match; gdp_pc left null for those.",
            missing, len(df_panel),
        )

    df_panel['gdp_pc'] = (df_panel['value'] * GDP_UNIT_SCALE) / df_panel['population']

    df_panel['indicator'] = 'PIB_Real_Regional'
    df_panel['frequency'] = frequency
    df_panel['unit'] = GDP_UNIT_LABEL

    df_panel = df_panel.drop(columns='year')
    return df_panel[PANEL_COLUMNS].sort_values(
        by=['region_code', 'date']
    ).reset_index(drop=True)

def build_regional_panels(use_synthetic: bool = False):
    # Check credentials before constructing anything that needs them, so the
    # failure message names the actual problem rather than surfacing as a
    # ValueError from deep inside the client constructor.
    if not use_synthetic:
        require_real_credentials()
    else:
        logger.warning(
            "SYNTHETIC MODE: generating mock data. Outputs are NOT real BCCh "
            "observations and every row is stamped status='MOCK'."
        )

    logger.info("Initializing CatalogManager and LocalCacheManager...")
    catalog = CatalogManager()
    # Synthetic runs use a separate cache namespace so mock series can never be
    # picked up by a later real run.
    cache_dir = str(CACHE_DIR.parent / "cache_synthetic") if use_synthetic else str(CACHE_DIR)
    cache = LocalCacheManager(cache_dir=cache_dir, catalog_manager=catalog)

    # Population always comes from the real cache: it is an input, not part of
    # what --synthetic simulates, and the synthetic cache namespace has none.
    pop_cache = cache if not use_synthetic else LocalCacheManager(
        cache_dir=str(CACHE_DIR), catalog_manager=catalog
    )
    population = load_regional_population(pop_cache)

    base_pattern = "F035.PIB.FLU.R.CLP.2018.Z.Z.Z.{code}.0.{freq}"
    
    annual_codes = []
    quarterly_codes = []
    
    for code in REGION_MAP.keys():
        ann_code = base_pattern.format(code=code, freq="A")
        qtr_code = base_pattern.format(code=code, freq="T")
        
        if catalog.get_metadata(ann_code) is not None:
            annual_codes.append(ann_code)
        if catalog.get_metadata(qtr_code) is not None:
            quarterly_codes.append(qtr_code)
            
    logger.info(f"Verified series in catalog: {len(annual_codes)} Annual, {len(quarterly_codes)} Quarterly.")

    # 1. Build Annual Panel
    if annual_codes:
        logger.info("Fetching and caching Annual regional GDP data...")
        dfs_annual = []
        
        for code in annual_codes:
            if use_synthetic:
                logger.info(f"Generating high-variance synthetic cache starting in 2013 for series: {code}")
                df_series = generate_synthetic_series(code, "A")
                cache.save_to_cache(code, df_series)
                dfs_annual.append(df_series)
            else:
                logger.info(f"Syncing series: {code}")
                try:
                    df_series = cache.smart_sync(code, start_date=date(2013, 1, 1), end_date=date(2026, 12, 31))
                    if not df_series.empty:
                        dfs_annual.append(df_series)
                except BCChAPIError as e:
                    # No synthetic fallback: a failed fetch is reported as a
                    # failure, never quietly replaced with fabricated numbers.
                    logger.error(f"API Error syncing {code}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error syncing {code}: {e}")
                    
        if dfs_annual:
            df_annual_raw = pd.concat(dfs_annual, ignore_index=True)
            df_annual_panel = format_to_panel(df_annual_raw, REGION_MAP, "Annual", population)
            
            output_path = os.path.join(DATA_DIR, "panel_regional_pib_annual.csv")
            df_annual_panel.to_csv(output_path, index=False, encoding="utf-8")
            logger.info(f"Successfully saved Annual panel data with {len(df_annual_panel)} observations to: {output_path}")
        else:
            logger.error("No Annual data could be built.")

    # 2. Build Quarterly Panel
    if quarterly_codes:
        logger.info("Fetching and caching Quarterly regional GDP data...")
        dfs_quarterly = []
        
        for code in quarterly_codes:
            if use_synthetic:
                logger.info(f"Generating synthetic cache starting in 2013 for series: {code}")
                df_series = generate_synthetic_series(code, "T")
                cache.save_to_cache(code, df_series)
                dfs_quarterly.append(df_series)
            else:
                logger.info(f"Syncing series: {code}")
                try:
                    df_series = cache.smart_sync(code, start_date=date(2013, 1, 1), end_date=date(2026, 12, 31))
                    if not df_series.empty:
                        dfs_quarterly.append(df_series)
                except BCChAPIError as e:
                    logger.error(f"API Error syncing {code}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error syncing {code}: {e}")
                
        if dfs_quarterly:
            df_qtr_raw = pd.concat(dfs_quarterly, ignore_index=True)
            df_qtr_panel = format_to_panel(df_qtr_raw, REGION_MAP, "Quarterly", population)
            
            output_path = os.path.join(DATA_DIR, "panel_regional_pib_quarterly.csv")
            df_qtr_panel.to_csv(output_path, index=False, encoding="utf-8")
            logger.info(f"Successfully saved Quarterly panel data with {len(df_qtr_panel)} observations to: {output_path}")
        else:
            logger.error("No Quarterly data could be built.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the regional GDP panels.")
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="generate MOCK data for offline development instead of fetching",
    )
    args = parser.parse_args()
    build_regional_panels(use_synthetic=args.synthetic)

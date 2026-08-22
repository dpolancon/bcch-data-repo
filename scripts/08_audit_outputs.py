"""
Stage:    08 -- Audit pipeline outputs
Purpose:  Cross-check the generated tables, figures and panels for internal
          consistency and emit the source-of-truth regional GDP extract.
Task:     Regional reporting quality control
Inputs:   data/panel_regional_pib_annual.csv; bcch-data-repo-vault/assets/*
Outputs:  data/source_of_truth_regional_pib.csv
Created:  2026-07-06
Updated:  2026-08-21
Owner:    dpolancon
Run:      python scripts/08_audit_outputs.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.paths import REPO_ROOT, DATA_DIR, REPORT1_ASSETS_DIR, REPORT1_DIR
from lib.regions import REGIONS
from lib.sectors import compute_location_quotients
from lib.stats import compute_hhi, compute_weighted_gini, compute_weighted_theil

import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
VAULT_DIR = str(REPORT1_DIR)
ASSETS_DIR = str(REPORT1_ASSETS_DIR)
DATA_DIR = str(DATA_DIR)

# Numeric tolerance for comparing regenerated values against published tables.
TOLERANCE = 1e-4

REGION_MAP = {r.id: r.name_es for r in REGIONS}



# ----------------------------------------------------
# Inequality Calculators (Weighted)
# ----------------------------------------------------

def run_final_audit():
    logger.info("Initializing Final PASS Audit...")
    
    # 1. Load the annual panel and write the Source of Truth CSV
    panel_path = os.path.join(DATA_DIR, "panel_regional_pib_annual.csv")
    if not os.path.exists(panel_path):
        raise FileNotFoundError(f"Annual panel not found at: {panel_path}")
        
    df_panel = pd.read_csv(panel_path, parse_dates=["date"], dtype={"region_code": str})
    df_panel['year'] = df_panel['date'].dt.year
    
    sot_path = os.path.join(DATA_DIR, "source_of_truth_regional_pib.csv")
    df_panel.to_csv(sot_path, index=False)
    logger.info(f"Successfully generated Source of Truth CSV: {sot_path}")
    
    # Reload from CSV to ensure we are auditing the CSV file directly
    # Same dtype as the panel: without it region_code becomes int64 here while
    # other comparison sites expect the zero-padded string, so a join silently
    # matches nothing.
    df_sot = pd.read_csv(sot_path, dtype={"region_code": str})
    
    # 2. Load Output tables for verification
    t1_path = os.path.join(ASSETS_DIR, "table1_summary_stats.csv")
    t2_path = os.path.join(ASSETS_DIR, "table2_location_quotients.csv")
    t3_path = os.path.join(ASSETS_DIR, "table3_spatial_inequality.csv")
    
    df_t1_out = pd.read_csv(t1_path)
    df_t2_out = pd.read_csv(t2_path)
    df_t3_out = pd.read_csv(t3_path)
    
    audit_failed = False
    discrepancies = []
    
    # ----------------------------------------------------
    # Audit Table 1: Summary Statistics
    # ----------------------------------------------------
    logger.info("Auditing Table 1 (Summary Statistics)...")
    national_gdp = df_sot.groupby("year")["value"].sum().to_dict()
    
    for _, row in df_t1_out.iterrows():
        reg_name = row['region']
        
        # Get region code
        reg_code = None
        for k, v in REGION_MAP.items():
            if v == reg_name:
                reg_code = k
                break
                
        if reg_code is None:
            audit_failed = True
            discrepancies.append(f"Table 1 region '{reg_name}' could not be mapped to code.")
            continue
            
        df_reg = df_sot[df_sot['region_code'] == reg_code].sort_values("year")
        
        # Independent calculations
        expected_mean = df_reg['value'].mean() / 1000.0
        
        shares = [r['value'] / national_gdp[r['year']] * 100 for _, r in df_reg.iterrows()]
        expected_share = np.mean(shares)
        
        growth = df_reg['value'].pct_change().dropna() * 100
        expected_growth = growth.mean()
        expected_vol = growth.std()
        
        tol = TOLERANCE
        if abs(row['mean_gdp'] - expected_mean) > tol:
            audit_failed = True
            discrepancies.append(f"Table 1 '{reg_name}' mean GDP mismatch: Output={row['mean_gdp']:.4f}, Expected={expected_mean:.4f}")
        if abs(row['share'] - expected_share) > tol:
            audit_failed = True
            discrepancies.append(f"Table 1 '{reg_name}' Share mismatch: Output={row['share']:.4f}, Expected={expected_share:.4f}")
        if abs(row['growth'] - expected_growth) > tol:
            audit_failed = True
            discrepancies.append(f"Table 1 '{reg_name}' Growth mismatch: Output={row['growth']:.4f}, Expected={expected_growth:.4f}")
        if abs(row['volatility'] - expected_vol) > tol:
            audit_failed = True
            discrepancies.append(f"Table 1 '{reg_name}' Volatility mismatch: Output={row['volatility']:.4f}, Expected={expected_vol:.4f}")
            
    # ----------------------------------------------------
    # Audit Table 2: Location Quotients (12 Sectors)
    # ----------------------------------------------------
    logger.info("Auditing Table 2 (Location Quotients)...")

    # Recompute location quotients from the raw fetched series.
    #
    # This block used to re-run the producer's sector generator with the same
    # random seed, so it only ever verified that two copies of one RNG agreed --
    # an audit that certified fabricated numbers. It now recomputes from
    # data/raw/, which is an input neither script derives from the other.
    year_lq = int(df_t2_out.attrs.get("year", 0)) or None
    lq_expected = compute_location_quotients(year=year_lq, valuation="N")
    year_lq = int(lq_expected["year"].iloc[0])
    logger.info("  recomputed independently for %d", year_lq)

    ascii_to_display = {r.name_ascii: r.name_es for r in REGIONS}
    lq_expected["Region"] = lq_expected["region_name"].map(ascii_to_display).fillna(
        lq_expected["region_name"]
    )
    expected_lookup = {
        (row["Region"], row["sector_name"]): row["lq"]
        for _, row in lq_expected.iterrows()
    }

    sector_cols = [c for c in df_t2_out.columns if c != "Region"]
    for _, row in df_t2_out.iterrows():
        reg_name = row["Region"]
        for sec in sector_cols:
            expected = expected_lookup.get((reg_name, sec))
            if expected is None:
                audit_failed = True
                discrepancies.append(
                    f"Table 2 '{reg_name}' sector '{sec}' has no counterpart in the raw data"
                )
                continue
            if abs(row[sec] - expected) > TOLERANCE:
                audit_failed = True
                discrepancies.append(
                    f"Table 2 '{reg_name}' Sector '{sec}' LQ Mismatch: "
                    f"Output={row[sec]:.4f}, Expected={expected:.4f}"
                )

    # ----------------------------------------------------
    # Audit Table 3: Spatial Inequality Indices
    # ----------------------------------------------------
    logger.info("Auditing Table 3 (Inequality Indices)...")
    
    for _, row in df_t3_out.iterrows():
        y = int(row['Year'])
        df_y = df_sot[df_sot['year'] == y]
        
        vals = df_y['gdp_pc'].values
        pop = df_y['population'].values
        gdp_raw = df_y['value'].values
        
        expected_gini = compute_weighted_gini(vals, pop)
        expected_theil = compute_weighted_theil(vals, pop)
        expected_hhi = compute_hhi(gdp_raw)
        
        tol = TOLERANCE
        if abs(row['Gini Coefficient'] - expected_gini) > tol:
            audit_failed = True
            discrepancies.append(f"Table 3 Year {y} Gini Mismatch: Output={row['Gini Coefficient']:.4f}, Expected={expected_gini:.4f}")
        if abs(row['Theil Index'] - expected_theil) > tol:
            audit_failed = True
            discrepancies.append(f"Table 3 Year {y} Theil Mismatch: Output={row['Theil Index']:.4f}, Expected={expected_theil:.4f}")
        if abs(row['HHI (Output Concentration)'] - expected_hhi) > tol:
            audit_failed = True
            discrepancies.append(f"Table 3 Year {y} HHI Mismatch: Output={row['HHI (Output Concentration)']:.4f}, Expected={expected_hhi:.4f}")

    # ----------------------------------------------------
    # Report Verification Outcomes
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("             FINAL AUDIT REPORT")
    print("="*50)
    
    if audit_failed:
        print("STATUS: FAILED [X]")
        print(f"Total Discrepancies Found: {len(discrepancies)}")
        for idx, desc in enumerate(discrepancies):
            print(f" {idx+1}. {desc}")
        print("\nACTION REQUIRED: Please verify the calculation seeds or formulas.")
        exit(1)
    else:
        print("STATUS: PASSED [OK]")
        print("All output tables are 100% mathematically and structurally consistent with the Source of Truth CSV!")
        print("="*50)
        
if __name__ == "__main__":
    run_final_audit()

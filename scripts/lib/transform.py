"""
Purpose:  Single-series time-series transformations -- imputation, resampling,
          and growth-rate computations.
Task:     BCCh data pipeline infrastructure
Inputs:   n/a (operates on DataFrames with `date` / `value` columns)
Outputs:  n/a (pure functions)
Created:  2026-07-06
Updated:  2026-08-21
Owner:    dpolancon

None of these are groupby-aware: apply them per series, never to a stacked
multi-series panel. They are also NOT used in the CRSM raw layer, which stores
observations exactly as fetched with no interpolation or resampling.
"""

import numpy as np
import pandas as pd
from typing import Optional

def fill_missing(
    df: pd.DataFrame, 
    method: str = "ffill", 
    value_col: str = "value", 
    date_col: str = "date"
) -> pd.DataFrame:
    """
    Fills missing values (NaNs) in the time series using the specified method
    and adds an auxiliary 'imputed' flag column.
    
    Parameters:
    -----------
    df: pd.DataFrame
        Input DataFrame.
    method: str
        Imputation method: 'ffill' (forward fill), 'bfill' (backward fill), or 'interpolate' (linear).
    """
    df_clean = df.copy()
    if df_clean.empty or value_col not in df_clean.columns:
        return df_clean

    df_clean = df_clean.sort_values(by=date_col).reset_index(drop=True)
    
    # Mark values that are currently NaN
    original_nan = df_clean[value_col].isna()
    
    # Apply filling method
    if method == "ffill":
        df_clean[value_col] = df_clean[value_col].ffill()
    elif method == "bfill":
        df_clean[value_col] = df_clean[value_col].bfill()
    elif method == "interpolate":
        df_clean[value_col] = df_clean[value_col].interpolate(method="linear")
    else:
        raise ValueError(f"Unknown fill method: {method}")
        
    # Mark imputed rows (excluding those that remained NaN at the boundaries)
    df_clean["imputed"] = original_nan & df_clean[value_col].notna()
    return df_clean

def resample_series(
    df: pd.DataFrame, 
    freq: str, 
    agg_rule: str = "last", 
    value_col: str = "value", 
    date_col: str = "date"
) -> pd.DataFrame:
    """
    Resamples time-series data to a different frequency (e.g. 'ME' for Monthly, 'QE' for Quarterly).
    
    Parameters:
    -----------
    df: pd.DataFrame
        Input DataFrame.
    freq: str
        Pandas frequency offset (e.g., 'ME', 'QE', 'YE').
    agg_rule: str
        Aggregation rule: 'last' (end-of-period), 'mean' (average), or 'sum' (cumulative).
    """
    if df.empty or value_col not in df.columns:
        return df.copy()

    df_res = df.copy()
    df_res = df_res.set_index(date_col)
    
    # Resample based on the aggregation rule
    resampler = df_res.resample(freq)
    
    if agg_rule == "last":
        df_agg = resampler.last()
    elif agg_rule == "mean":
        df_agg = resampler.mean()
    elif agg_rule == "sum":
        df_agg = resampler.sum()
    else:
        raise ValueError(f"Unknown aggregation rule: {agg_rule}")
        
    df_agg = df_agg.reset_index()
    return df_agg

def compute_yoy(df: pd.DataFrame, value_col: str = "value", date_col: str = "date", freq: str = "M") -> pd.Series:
    """Computes year-over-year percentage change (e.g. 12 periods back for monthly data)."""
    if df.empty or value_col not in df.columns:
        return pd.Series(dtype="float64")
        
    periods = 12 if freq.upper().startswith("M") else (4 if freq.upper().startswith("Q") else 1)
    return df[value_col].pct_change(periods=periods) * 100

def compute_mom(df: pd.DataFrame, value_col: str = "value") -> pd.Series:
    """Computes month-over-month (or period-over-period) percentage change."""
    if df.empty or value_col not in df.columns:
        return pd.Series(dtype="float64")
    return df[value_col].pct_change(periods=1) * 100

def compute_log_returns(df: pd.DataFrame, value_col: str = "value") -> pd.Series:
    """Computes log-differenced returns: ln(x_t) - ln(x_t-1)."""
    if df.empty or value_col not in df.columns:
        return pd.Series(dtype="float64")
    return np.log(df[value_col]) - np.log(df[value_col].shift(1))

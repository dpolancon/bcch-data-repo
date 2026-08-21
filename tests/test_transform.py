import pytest
import pandas as pd
import numpy as np
from lib.transform import fill_missing, resample_series, compute_yoy, compute_mom, compute_log_returns

def test_fill_missing():
    # Construct a sample df with a missing observation
    df = pd.DataFrame({
        "date": pd.to_datetime(["2026-07-01", "2026-07-02", "2026-07-03", "2026-07-04"]),
        "value": [10.0, np.nan, 12.0, 13.0]
    })
    
    # Test forward fill
    df_ffill = fill_missing(df, method="ffill")
    assert df_ffill.iloc[1]["value"] == 10.0
    assert bool(df_ffill.iloc[1]["imputed"]) is True
    assert bool(df_ffill.iloc[0]["imputed"]) is False

    # Test linear interpolation
    df_interp = fill_missing(df, method="interpolate")
    assert df_interp.iloc[1]["value"] == 11.0
    assert bool(df_interp.iloc[1]["imputed"]) is True

def test_resample_series():
    dates = pd.date_range(start="2026-01-01", end="2026-01-31", freq="D")
    values = np.linspace(1.0, 31.0, len(dates))
    df = pd.DataFrame({"date": dates, "value": values})
    
    # Resample daily to monthly using mean aggregation
    df_monthly = resample_series(df, freq="ME", agg_rule="mean")
    assert len(df_monthly) == 1
    assert df_monthly.iloc[0]["value"] == 16.0

def test_compute_metrics():
    # Simple monthly sequence
    df = pd.DataFrame({
        "date": pd.date_range(start="2025-01-01", periods=13, freq="ME"),
        "value": [100.0] * 12 + [110.0]  # Value is 100 for 12 months, then 110
    })
    
    mom = compute_mom(df)
    assert mom.iloc[-1] == pytest.approx(10.0)  # 100 to 110 is 10%
    
    yoy = compute_yoy(df, freq="M")
    assert yoy.iloc[-1] == pytest.approx(10.0)  # YoY from previous year (month 0 to month 12) is 10%

    log_ret = compute_log_returns(df)
    assert np.isclose(log_ret.iloc[-1], np.log(110) - np.log(100))

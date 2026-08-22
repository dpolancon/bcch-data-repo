"""
Purpose:  Population-weighted inequality and concentration measures used by the
          regional analysis and audit stages.
Task:     Regional economic development analysis
Inputs:   n/a (pure functions over numpy arrays)
Outputs:  n/a
Created:  2026-08-21
Updated:  2026-08-21
Owner:    dpolancon

These lived in both 04_analyze_regional.py and 08_audit_outputs.py, and the two
copies had diverged: 04's guarded against empty slices and zero population,
08's did not and would raise or return nan. The guarded behaviour is kept here,
so the audit and the analysis can no longer disagree by construction.
"""

from typing import Sequence

import numpy as np


def _as_array(values: Sequence[float]) -> np.ndarray:
    return np.asarray(values, dtype="float64")


def compute_weighted_gini(y: Sequence[float], pop: Sequence[float]) -> float:
    """Population-weighted Gini coefficient of `y` (typically GDP per capita).

    Returns 0.0 for an empty slice or zero total population rather than
    raising, since callers iterate over year slices that may be empty.
    """
    y = _as_array(y)
    pop = _as_array(pop)
    n = len(y)
    if n == 0 or np.nansum(pop) == 0:
        return 0.0

    shares = pop / np.nansum(pop)
    mu = np.nansum(shares * y)
    if mu == 0:
        return 0.0

    # Mean absolute difference, weighted by the product of population shares.
    diffs = np.abs(y[:, None] - y[None, :])
    double_sum = float(np.nansum(shares[:, None] * shares[None, :] * diffs))
    return double_sum / (2.0 * mu)


def compute_weighted_theil(y: Sequence[float], pop: Sequence[float]) -> float:
    """Population-weighted Theil T index."""
    y = _as_array(y)
    pop = _as_array(pop)
    pop_sum = np.nansum(pop)
    if len(y) == 0 or pop_sum == 0:
        return 0.0

    shares = pop / pop_sum
    mu = np.nansum(shares * y)
    if mu == 0:
        return 0.0

    ratio = np.divide(y, mu, out=np.zeros_like(y), where=mu != 0)
    # log is undefined at zero or below; those observations contribute nothing.
    valid = ratio > 0
    return float(np.nansum(shares[valid] * ratio[valid] * np.log(ratio[valid])))


def compute_hhi(values: Sequence[float]) -> float:
    """Herfindahl-Hirschman index of output concentration."""
    values = _as_array(values)
    total = np.nansum(values)
    if len(values) == 0 or total == 0:
        return float("nan")
    shares = values / total
    return float(np.nansum(shares**2))

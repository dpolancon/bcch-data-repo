"""
Purpose:  Tests for the CSV delta cache -- round-trip typing, atomic writes,
          and the code-derived frequency used for staleness decisions.
Task:     BCCh data pipeline infrastructure
Inputs:   n/a (uses tmp_path)
Outputs:  n/a
Created:  2026-08-21
Updated:  2026-08-21
Owner:    dpolancon
"""

import pandas as pd
import pytest

from lib.storage import LocalCacheManager


@pytest.fixture
def cache(tmp_path):
    """A cache wired to stub collaborators so no API or Excel is touched."""

    class _StubClient:
        user = "test@example.org"

        def get_series(self, *args, **kwargs):
            raise AssertionError("no API call expected in this test")

    class _StubCatalog:
        def get_metadata(self, code):
            return None

    return LocalCacheManager(
        cache_dir=str(tmp_path / "cache"),
        api_client=_StubClient(),
        catalog_manager=_StubCatalog(),
    )


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "seriesId": ["F035.PIB.FLU.R.CLP.2018.Z.Z.Z.13.0.A"] * 3,
            "date": pd.to_datetime(["2020-12-31", "2021-12-31", "2022-12-31"]),
            "value": [1.5, 2.5, 3.5],
            "status": ["OK", "OK", "OK"],
        }
    )


class TestCachePaths:
    def test_cache_files_are_csv(self, cache):
        path = cache._get_cache_path("F035.PIB.FLU.R.CLP.2018.Z.Z.Z.13.0.A")
        assert path.endswith(".csv")
        assert not path.endswith(".parquet")

    def test_dots_become_underscores(self, cache):
        path = cache._get_cache_path("F034.SAHAP.FLU.INE.Z.0.M")
        assert "F034_SAHAP_FLU_INE_Z_0_M.csv" in path


class TestRoundTrip:
    def test_preserves_values_and_dtypes(self, cache, sample_df):
        """CSV stores no dtypes, so load_from_cache must restore them."""
        code = "F035.PIB.FLU.R.CLP.2018.Z.Z.Z.13.0.A"
        cache.save_to_cache(code, sample_df)
        loaded = cache.load_from_cache(code)

        assert loaded is not None
        assert len(loaded) == len(sample_df)
        assert pd.api.types.is_datetime64_any_dtype(loaded["date"])
        assert pd.api.types.is_numeric_dtype(loaded["value"])
        pd.testing.assert_series_equal(
            loaded["value"], sample_df["value"], check_names=False
        )

    def test_missing_series_returns_none(self, cache):
        assert cache.load_from_cache("F035.NOT.CACHED.Z.Z.Z.Z.Z.Z.13.0.A") is None

    def test_empty_frame_is_not_written(self, cache):
        import os

        code = "F035.EMPTY.Z.Z.Z.Z.Z.Z.Z.13.0.A"
        cache.save_to_cache(code, pd.DataFrame())
        assert not os.path.exists(cache._get_cache_path(code))

    def test_corrupt_file_returns_none_rather_than_raising(self, cache, tmp_path):
        code = "F035.CORRUPT.Z.Z.Z.Z.Z.Z.Z.13.0.A"
        path = cache._get_cache_path(code)
        import os

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("not,a,valid\nheader\x00\x00")
        assert cache.load_from_cache(code) is None


class TestAtomicWrite:
    def test_no_temp_file_survives_a_successful_write(self, cache, sample_df):
        import glob
        import os

        code = "F035.PIB.FLU.R.CLP.2018.Z.Z.Z.13.0.A"
        cache.save_to_cache(code, sample_df)
        leftovers = glob.glob(os.path.join(cache.cache_dir, "*.tmp"))
        assert not leftovers, f"temp files left behind: {leftovers}"

    def test_overwrite_replaces_cleanly(self, cache, sample_df):
        code = "F035.PIB.FLU.R.CLP.2018.Z.Z.Z.13.0.A"
        cache.save_to_cache(code, sample_df)
        cache.save_to_cache(code, sample_df.head(1))
        assert len(cache.load_from_cache(code)) == 1

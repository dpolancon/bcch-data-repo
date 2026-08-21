"""
Stage:    01 -- Fetch CRSM raw series
Purpose:  Resolve every region-parseable BCCh series from the catalog, fetch it,
          and land it as frequency-separated raw CSVs. Strictly an extraction
          layer: no interpolation, no aggregation, no cross-frequency mixing.
Task:     CRSM dataset construction (SHT spatial rent vs resource rent)
Inputs:   data/catalogo_series.xlsx; BCCh SieteRestWS API
Outputs:  data/raw/regional-spatial-macro-dataset/raw_{daily,monthly,quarterly,annual}.csv
          data/raw/regional-spatial-macro-dataset/crsm_series_universe.csv
          data/raw/regional-spatial-macro-dataset/fetch_manifest.csv
Created:  2026-08-21
Updated:  2026-08-21
Owner:    dpolancon
Run:      python scripts/01_fetch_crsm_raw.py [--dry-run] [--limit N] [--sht-only] [--refresh]

Selection principle
-------------------
Series are selected by REGION-PARSEABILITY, not by chapter whitelist. Chapter
membership is editorial metadata -- the same code appears under several
chapters, regional GDP lives under both "Regionales" and "Cuentas Nacionales",
and regional population lives under "Genero". Parseability is a property of the
code itself. Chapter is retained on every row and used only as a cross-check:
a regional match in an unexpected chapter is flagged for review.
"""

import argparse
import logging
import os
import pathlib
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import pandas as pd
import requests

from lib import codes as codes_lib
from lib import config as config_lib
from lib.catalog import CatalogManager
from lib.client import BCChAPIClient, BCChAPIError
from lib.paths import CRSM_RAW_DIR, ensure_dir
from lib.regions import PARSE_CUADRO, parse_region
from lib.storage import LocalCacheManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s"
)
logger = logging.getLogger("crsm.fetch")

COL_CHAPTER = "CAPÍTULO"
COL_TABLE = "NOMBRE CUADRO"
COL_CODE = "CÓDIGO"
COL_NAME = "NOMBRE DE LA SERIE"

# Chapters where a regional match is expected. A match outside this set is not
# rejected -- it is flagged, because that is how parser false positives surface.
EXPECTED_CHAPTERS = frozenset(
    {
        "Regionales",
        "Cuentas Nacionales",
        "Estadísticas Experimentales",
        "Género",
        "Indicadores Sectoriales",
        "Mercado Laboral y Demografía",
        "Estadísticas Monetarias y Financieras",
        "Indicadores Mercado de la Vivienda",
    }
)

# Code stems that carry the SHT framework's core constructs. Used by --sht-only
# to fetch a focused subset instead of the full regional universe.
SHT_CORE_TOKENS = (
    "PIB",        # regional GDP, total and sectoral (both rent axes + outcome)
    "CPRIPSFL",   # regional household consumption
    "XSE",        # regional exports (resource-rent flow)
    "SAH", "SANH", "NVA",          # building permits (spatial-rent quantity)
    "DV90", "DCS90", "DCM90",      # debt delinquency incl. mortgages
    "TEMP", "TEAMV", "SEVC", "ICNE",  # firm demography
    "PMI",        # mining production index
    "POB",        # population (for per-capita outcomes)
    "CVRV", "CVRC",  # inter/intra-regional trade
)

OUTPUT_COLUMNS = [
    "series_code",
    "series_name",
    "region_id",
    "region_name",
    "date",
    "value",
    "frequency",
    "unit",
    # provenance
    "chapter",
    "sector_id",
    "sector_name",
    "region_parse_method",
    "status",
]

DEFAULT_START = date(1980, 1, 1)

# Concurrent workers for the cold load. The API is single-series per request,
# so throughput comes from concurrency; keep this modest to stay polite.
DEFAULT_WORKERS = 6


def load_catalog(catalog: CatalogManager) -> pd.DataFrame:
    """Load the catalog and collapse it to one row per unique series code.

    The raw file has 30,873 rows but only 25,369 distinct codes -- a code is
    listed once per chapter it appears under. Counting without deduping
    double-counts. We keep the "Cuentas Nacionales" row when a code is
    duplicated, since its NOMBRE CUADRO carries the reference base and units.
    """
    df = catalog.df.copy()
    df.columns = [c.strip() for c in df.columns]

    df["_chapter_rank"] = (df[COL_CHAPTER] != "Cuentas Nacionales").astype(int)
    df = (
        df.sort_values("_chapter_rank")
        .drop_duplicates(subset=[COL_CODE], keep="first")
        .drop(columns="_chapter_rank")
        .reset_index(drop=True)
    )
    logger.info("Catalog loaded: %d unique series codes", len(df))
    return df


def build_universe(df: pd.DataFrame, sht_only: bool = False) -> pd.DataFrame:
    """Resolve region, frequency and sector for every catalog row.

    Returns only rows that resolve to one of the 16 regions -- national and
    unparseable series are dropped here, which is the single point where
    national leakage is prevented.
    """
    rows = []
    for code, name, table, chapter in zip(
        df[COL_CODE], df[COL_NAME], df[COL_TABLE], df[COL_CHAPTER]
    ):
        match = parse_region(str(code), str(name), str(table))
        if match is None or match.region is None:
            continue  # national aggregate or not regional at all

        frequency = codes_lib.parse_frequency(str(code))
        if frequency is None:
            logger.warning("Unresolvable frequency, skipping: %s", code)
            continue

        sector_id, sector_name = codes_lib.parse_sector(str(code))
        rows.append(
            {
                "series_code": str(code).strip(),
                "series_name": str(name).strip(),
                "region_id": match.region.id,
                "region_name": match.region.name_es,
                "frequency": frequency,
                "chapter": str(chapter).strip(),
                "table_name": str(table).strip(),
                "sector_id": sector_id,
                "sector_name": sector_name,
                "region_parse_method": match.method,
            }
        )

    universe = pd.DataFrame(rows)
    if universe.empty:
        return universe

    if sht_only:
        pattern = "|".join(SHT_CORE_TOKENS)
        keep = universe["series_code"].str.contains(pattern, regex=True, na=False)
        logger.info("--sht-only: %d of %d series retained", keep.sum(), len(universe))
        universe = universe[keep].reset_index(drop=True)

    return universe.sort_values(["frequency", "region_id", "series_code"]).reset_index(
        drop=True
    )


def report_universe(universe: pd.DataFrame) -> None:
    """Log the shape of the selected universe and flag suspicious matches."""
    logger.info("--- Selected universe: %d series ---", len(universe))
    logger.info(
        "By frequency: %s",
        universe["frequency"].map(codes_lib.FREQ_LABEL).value_counts().to_dict(),
    )
    logger.info("By parse method: %s", universe["region_parse_method"].value_counts().to_dict())
    logger.info("Distinct regions: %d", universe["region_id"].nunique())

    sectoral = universe[universe["sector_id"].notna()]
    if not sectoral.empty:
        for sid, label in (
            (codes_lib.SECTOR_MINING, "mining (resource rent)"),
            (codes_lib.SECTOR_CONSTRUCTION, "construction"),
            (codes_lib.SECTOR_REAL_ESTATE, "real estate (spatial rent)"),
        ):
            n = int((sectoral["sector_id"] == sid).sum())
            logger.info("  sector %s %-28s : %4d series", sid, label, n)

    unexpected = universe[~universe["chapter"].isin(EXPECTED_CHAPTERS)]
    if not unexpected.empty:
        logger.warning(
            "%d regional matches in unexpected chapters -- review for false positives: %s",
            len(unexpected),
            unexpected["chapter"].value_counts().to_dict(),
        )

    # The cuadro-name fallback is the loosest parser; surface its footprint.
    n_fallback = int((universe["region_parse_method"] == PARSE_CUADRO).sum())
    if n_fallback:
        logger.info("%d series resolved via the cuadro-name fallback", n_fallback)


def cold_load_uncached(
    universe: pd.DataFrame,
    cache: LocalCacheManager,
    start_date: date,
    end_date: date,
    workers: int = DEFAULT_WORKERS,
) -> None:
    """Populate the cache for series not yet held, one request per series.

    The API rejects multi-series requests (lib.client.MAX_SERIES_PER_REQUEST),
    so a cold load is inherently one round trip per series. Each request is
    latency-bound rather than compute-bound -- roughly 1.5 s, almost all of it
    waiting -- so a small thread pool cuts a ~100-minute serial load to ~20
    minutes without raising the request rate much above 3/s.

    Each worker gets its own client, so the per-client throttle stays correct
    without a shared lock. Results are written per series as they arrive, which
    keeps the load resumable: an interrupted run picks up where it stopped.
    """
    uncached = [
        code
        for code in universe["series_code"]
        if not os.path.exists(cache._get_cache_path(code))
    ]
    if not uncached:
        logger.info("Cache is warm: all %d series already present.", len(universe))
        return

    logger.info(
        "Cold-loading %d uncached series, %d workers (1 series per request)...",
        len(uncached), workers,
    )

    thread_local = threading.local()

    def client_for_thread() -> BCChAPIClient:
        if not hasattr(thread_local, "client"):
            thread_local.client = BCChAPIClient()
        return thread_local.client

    def fetch_one(code: str):
        try:
            df = client_for_thread().get_series(
                [code], firstdate=start_date, lastdate=end_date
            )
            return code, df, ""
        except Exception as exc:  # noqa: BLE001 - one bad series must not abort the load
            return code, pd.DataFrame(), str(exc)[:200]

    done = failed = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_one, code): code for code in uncached}
        for future in as_completed(futures):
            code, df, error = future.result()
            done += 1
            if error:
                failed += 1
                logger.warning("  %s: %s", code, error)
            elif not df.empty:
                cache.save_to_cache(code, df)

            if done % 200 == 0 or done == len(uncached):
                logger.info(
                    "  cold load %d/%d (%d failed)", done, len(uncached), failed
                )

    logger.info("Cold load complete: %d fetched, %d failed.", done - failed, failed)


def _read_cached(
    cache: LocalCacheManager, code: str, start_date: date, end_date: date
) -> pd.DataFrame:
    """Read one series from cache and clip it to the requested window."""
    df = cache.load_from_cache(code)
    if df is None or df.empty:
        return pd.DataFrame(columns=["seriesId", "date", "value", "status"])
    if start_date:
        df = df[df["date"].dt.date >= start_date]
    if end_date:
        df = df[df["date"].dt.date <= end_date]
    return df.reset_index(drop=True)


def fetch_series(
    universe: pd.DataFrame,
    cache: LocalCacheManager,
    start_date: date,
    end_date: date,
    refresh: bool = False,
    workers: int = DEFAULT_WORKERS,
) -> tuple:
    """Assemble every series in the universe. Returns (observations, manifest).

    A batched cold load populates the cache, then assembly reads straight from
    it. Assembly deliberately does NOT call smart_sync by default: a series
    just fetched still looks "stale" to the freshness rule (an annual series
    whose last observation is last December is older than the annual
    threshold), so every one of the ~4,000 series would fire a redundant delta
    request immediately after being downloaded. Pass refresh=True on a later
    run to pick up revisions and new observations.
    """
    cold_load_uncached(universe, cache, start_date, end_date, workers=workers)

    meta_by_code = universe.set_index("series_code").to_dict("index")
    frames, manifest = [], []
    total = len(universe)

    for i, code in enumerate(universe["series_code"], start=1):
        if i % 500 == 0 or i == total:
            logger.info("Assembling %d/%d ...", i, total)

        fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            if refresh:
                df = cache.smart_sync(code, start_date=start_date, end_date=end_date)
            else:
                df = _read_cached(cache, code, start_date, end_date)
            error = ""
        except (BCChAPIError, Exception) as exc:  # noqa: BLE001 - one bad series must not abort the run
            logger.error("Failed %s: %s", code, exc)
            df, error = pd.DataFrame(), str(exc)[:200]

        meta = meta_by_code[code]
        manifest.append(
            {
                "series_code": code,
                "fetched_at_utc": fetched_at,
                "n_obs": len(df),
                "date_min": df["date"].min() if not df.empty else pd.NaT,
                "date_max": df["date"].max() if not df.empty else pd.NaT,
                "frequency": meta["frequency"],
                "region_id": meta["region_id"],
                "error": error,
            }
        )

        if df.empty:
            continue

        out = pd.DataFrame(
            {
                "series_code": code,
                "series_name": meta["series_name"],
                "region_id": meta["region_id"],
                "region_name": meta["region_name"],
                "date": df["date"],
                "value": df["value"],
                "frequency": meta["frequency"],
                "unit": meta["table_name"],  # units live in the cuadro string
                "chapter": meta["chapter"],
                "sector_id": meta["sector_id"],
                "sector_name": meta["sector_name"],
                "region_parse_method": meta["region_parse_method"],
                "status": df["status"],
            }
        )
        frames.append(out)

    observations = (
        pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=OUTPUT_COLUMNS)
    )
    return observations, pd.DataFrame(manifest)


def write_outputs(observations: pd.DataFrame, out_dir: pathlib.Path) -> None:
    """Split strictly by native frequency and write one CSV per frequency."""
    for letter, slug in codes_lib.FREQ_SLUG.items():
        subset = observations[observations["frequency"] == letter]
        path = out_dir / f"raw_{slug}.csv"
        subset[OUTPUT_COLUMNS].to_csv(path, index=False, encoding="utf-8-sig")
        logger.info(
            "Wrote %-22s %7d rows | %5d series",
            path.name,
            len(subset),
            subset["series_code"].nunique(),
        )


def summarize(observations: pd.DataFrame) -> None:
    """Print the verification summary: coverage, span, NaNs, and a preview."""
    print("\n" + "=" * 78)
    print("CRSM RAW EXTRACTION SUMMARY")
    print("=" * 78)

    for letter, slug in codes_lib.FREQ_SLUG.items():
        s = observations[observations["frequency"] == letter]
        print(f"\n--- {codes_lib.FREQ_LABEL[letter].upper()} (raw_{slug}.csv) ---")
        if s.empty:
            print("  no observations")
            continue
        print(f"  series      : {s['series_code'].nunique()}")
        print(f"  regions     : {s['region_id'].nunique()}")
        print(f"  observations: {len(s)}")
        print(f"  date range  : {s['date'].min():%Y-%m-%d} -> {s['date'].max():%Y-%m-%d}")
        print(f"  missing vals: {int(s['value'].isna().sum())}")
        print(s[["series_code", "region_name", "date", "value"]].head().to_string(index=False))

    # National-leakage assertion: every row must carry a real region id.
    bad = observations[~observations["region_id"].isin([f"{i:02d}" for i in range(1, 17)])]
    print("\n" + "-" * 78)
    if bad.empty:
        print("PASS: no national data leaked -- every row carries a region id in 01-16.")
    else:
        print(f"FAIL: {len(bad)} rows without a valid region id.")

    if not observations.empty and (observations["status"] == "MOCK").any():
        print("FAIL: MOCK rows present -- synthetic data has contaminated this run.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch the CRSM raw regional dataset.")
    parser.add_argument("--dry-run", action="store_true", help="resolve the universe only; no API calls")
    parser.add_argument("--limit", type=int, default=None, help="fetch at most N series (smoke test)")
    parser.add_argument("--sht-only", action="store_true", help="restrict to the SHT core variable set")
    parser.add_argument("--start", type=str, default=None, help="start date, YYYY-MM-DD")
    parser.add_argument("--end", type=str, default=None, help="end date, YYYY-MM-DD")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="concurrent requests during cold load")
    parser.add_argument("--refresh", action="store_true", help="delta-update already-cached series")
    args = parser.parse_args()

    out_dir = ensure_dir(CRSM_RAW_DIR)
    catalog = CatalogManager()

    universe = build_universe(load_catalog(catalog), sht_only=args.sht_only)
    if universe.empty:
        logger.error("No regional series resolved -- aborting.")
        return 1

    report_universe(universe)
    universe_path = out_dir / "crsm_series_universe.csv"
    universe.to_csv(universe_path, index=False, encoding="utf-8-sig")
    logger.info("Wrote %s (%d rows)", universe_path.name, len(universe))

    if args.dry_run:
        logger.info("Dry run complete -- no API calls made.")
        return 0

    # Fail loudly rather than fabricating: see lib.config.require_real_credentials.
    config_lib.require_real_credentials()

    if args.limit:
        universe = universe.head(args.limit)
        logger.info("--limit: restricted to %d series", len(universe))

    start = date.fromisoformat(args.start) if args.start else DEFAULT_START
    end = date.fromisoformat(args.end) if args.end else date.today()

    cache = LocalCacheManager(catalog_manager=catalog)
    observations, manifest = fetch_series(universe, cache, start, end, refresh=args.refresh, workers=args.workers)

    write_outputs(observations, out_dir)
    manifest.to_csv(out_dir / "fetch_manifest.csv", index=False, encoding="utf-8-sig")
    logger.info("Wrote fetch_manifest.csv (%d rows)", len(manifest))

    summarize(observations)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
Purpose:  Fault-tolerant REST client for the BCCh SieteRestWS API, with
          connection pooling, bounded retries, request throttling and parsing
          into tidy DataFrames.
Task:     BCCh data pipeline infrastructure
Inputs:   BCCh SieteRestWS API; BCCH_TOKEN (preferred) or
          BCCH_USER + BCCH_PASSWORD from .env
Outputs:  n/a (returns DataFrames)
Created:  2026-07-06
Updated:  2026-08-21
Owner:    dpolancon
"""

import logging
import time
import requests
import pandas as pd
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from datetime import date

logger = logging.getLogger(__name__)

# The API accepts a comma-separated series list. Keep batches modest so the
# request URL stays well inside server limits.
DEFAULT_BATCH_SIZE = 25

# Minimum seconds between requests. The API publishes no documented rate limit,
# so we self-throttle rather than discover one mid-run.
DEFAULT_MIN_REQUEST_INTERVAL = 0.34

# The API returns observation dates as DD-MM-YYYY.
BCCH_DATE_FORMAT = "%d-%m-%Y"


class BCChAPIError(Exception):
    """Custom exception for BCCh API errors."""
    pass


def _is_retryable(exc: BaseException) -> bool:
    """Retry transport failures, but not client errors.

    A 4xx means the request itself is wrong -- bad credentials, unknown series.
    Retrying it five times with exponential backoff just burns ~30s per series
    to arrive at the same failure, so we fail fast instead.
    """
    if isinstance(exc, requests.HTTPError):
        response = getattr(exc, "response", None)
        if response is not None and 400 <= response.status_code < 500:
            return False
        return True
    return isinstance(exc, requests.RequestException)


class BCChAPIClient:
    """
    Fault-tolerant REST API client for the Central Bank of Chile (BCCh).
    Implements connection pooling, tenacity retries with exponential backoff,
    and robust JSON parsing to clean Pandas DataFrames.
    """
    def __init__(
        self,
        user: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        min_request_interval: float = DEFAULT_MIN_REQUEST_INTERVAL,
    ):
        # Two auth schemes are supported. The API Key token is the one BCCh
        # now recommends for REST; user/password is the legacy pair. Token
        # wins when both are available.
        self.token = token
        self.user = user
        self.password = password

        if not self.token and not (self.user and self.password):
            from lib.config import settings
            if not settings:
                raise ValueError(
                    "BCCh API credentials must be set via .env (BCCH_TOKEN, or "
                    "BCCH_USER + BCCH_PASSWORD) or constructor arguments."
                )
            self.token = self.token or settings.bcch_token
            self.user = self.user or settings.bcch_user
            self.password = self.password or settings.bcch_password

        if not self.token and not (self.user and self.password):
            raise ValueError(
                "No usable BCCh credentials: set BCCH_TOKEN, or both "
                "BCCH_USER and BCCH_PASSWORD."
            )

        self.base_url = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"
        self.session = requests.Session()
        self.min_request_interval = min_request_interval
        self._last_request_at = 0.0

    def _auth_params(self) -> dict:
        """Return the auth query params for whichever scheme is configured."""
        if self.token:
            return {"token": self.token}
        return {"user": self.user, "pass": self.password}

    def _throttle(self) -> None:
        """Space out requests so a wide fan-out does not hammer the API."""
        if self.min_request_interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self._last_request_at = time.monotonic()

    @retry(
        reraise=True,
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=16),
        retry=retry_if_exception_type(requests.RequestException),
    )
    def _make_request(self, params: dict) -> dict:
        """Makes an HTTP GET request to the BCCh API with automatic retry and backoff."""
        self._throttle()
        try:
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            json_data = response.json()
        except requests.RequestException as e:
            logger.error(f"HTTP Request failed: {e}")
            if not _is_retryable(e):
                # Wrap so tenacity's retry predicate does not see a
                # RequestException and keep hammering a doomed request.
                raise BCChAPIError(f"Non-retryable HTTP error: {e}") from e
            raise
        
        # Check if the response contains API-level error envelopes
        # The BCCh API often returns a root dictionary with 'Codigo' and 'Descripcion' for errors
        if isinstance(json_data, dict):
            if "Codigo" in json_data and json_data.get("Codigo") != 0:
                # If there's an error code but it's not a success (0), raise an exception
                error_msg = json_data.get("Descripcion", "Unknown API error")
                raise BCChAPIError(f"BCCh API returned error code {json_data.get('Codigo')}: {error_msg}")
            
            # Check for nested validation message
            if json_data.get("status") == "Error" or "error" in json_data:
                raise BCChAPIError(f"BCCh API returned error: {json_data}")
                
        return json_data

    def get_series_batched(
        self,
        series_codes: List[str],
        firstdate: Optional[date] = None,
        lastdate: Optional[date] = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        on_error: str = "skip",
    ) -> pd.DataFrame:
        """Fetch many series in chunks, one request per `batch_size` codes.

        The API already accepts a comma-separated series list, but callers
        historically passed one code at a time -- for a universe of thousands of
        series that is thousands of round trips. Chunking cuts that by ~batch_size.

        on_error='skip' logs and drops a failed batch so one bad code cannot
        abort a long run; on_error='raise' propagates.
        """
        if not series_codes:
            return pd.DataFrame(columns=["seriesId", "date", "value", "status"])

        frames = []
        for start in range(0, len(series_codes), batch_size):
            chunk = series_codes[start : start + batch_size]
            try:
                frames.append(self.get_series(chunk, firstdate=firstdate, lastdate=lastdate))
            except (BCChAPIError, requests.RequestException) as exc:
                if on_error == "raise":
                    raise
                logger.error(
                    "Batch %d-%d failed (%d codes): %s",
                    start, start + len(chunk), len(chunk), exc,
                )

        if not frames:
            return pd.DataFrame(columns=["seriesId", "date", "value", "status"])
        return (
            pd.concat(frames, ignore_index=True)
            .sort_values(by=["seriesId", "date"])
            .reset_index(drop=True)
        )

    def get_series(
        self,
        series_codes: List[str],
        firstdate: Optional[date] = None,
        lastdate: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Fetches time-series data from the BCCh API.

        Parameters:
        -----------
        series_codes: List[str]
            A list of series codes (e.g. ["G073.IPC.IND.2018.M"]).
        firstdate: Optional[date]
            Starting date of the query range.
        lastdate: Optional[date]
            Ending date of the query range.
            
        Returns:
        --------
        pd.DataFrame
            Cleaned and typed DataFrame containing the observations.
        """
        from lib.config import settings

        # Resolve start/end dates
        fdate_str = (firstdate or (settings.default_start_date if settings else date(1980, 1, 1))).strftime("%Y-%m-%d")
        ldate_str = (lastdate or (settings.default_end_date if settings else date.today())).strftime("%Y-%m-%d")

        params = {
            **self._auth_params(),
            "firstdate": fdate_str,
            "lastdate": ldate_str,
            "timeseries": ",".join(series_codes),
            "function": "GetSeries"
        }
        
        json_data = self._make_request(params)
        return self._parse_series_response(json_data)

    def search_series(self, frequency: Optional[str] = None) -> dict:
        """
        Queries the BCCh API to discover metadata for available series.
        """
        params = {
            **self._auth_params(),
            "function": "SearchSeries"
        }
        if frequency:
            params["frequency"] = frequency.upper()
            
        return self._make_request(params)

    def _parse_series_response(self, json_data: dict) -> pd.DataFrame:
        """Parses the nested JSON response into a flat, strictly typed Pandas DataFrame."""
        records = []
        
        series_list = json_data.get("Series", [])
        # Sometimes BCCh returns it as a dictionary if there's only one series, though usually it's a list
        if isinstance(series_list, dict):
            series_list = [series_list]
            
        for series in series_list:
            series_id = series.get("seriesId")
            obs_list = series.get("Obs", [])
            if isinstance(obs_list, dict):
                obs_list = [obs_list]
                
            for obs in obs_list:
                val_raw = obs.get("value")
                # Clean and convert value to float (handling possible empty or non-numeric strings)
                try:
                    value = float(val_raw) if val_raw is not None and str(val_raw).strip() != "" else None
                except ValueError:
                    value = None
                
                records.append({
                    "seriesId": series_id,
                    "date": obs.get("indexDateString"),
                    "value": value,
                    "status": obs.get("statusCode")
                })
                
        df = pd.DataFrame(records)
        
        # If no records were found, return an empty DataFrame with the expected columns
        if df.empty:
            return pd.DataFrame(columns=["seriesId", "date", "value", "status"])
            
        # Clean and type the columns.
        #
        # BCCh returns indexDateString as DAY-first: "03-08-2026" is 3 August.
        # Parsing without an explicit format is not merely wrong, it is
        # inconsistently wrong -- pandas reads 03-08-2026 as 8 March but
        # 13-08-2026 as 13 August, so days 1-12 silently swap month and day
        # while days 13-31 come out correct. Pin the format.
        df["seriesId"] = df["seriesId"].astype(str)
        df["date"] = pd.to_datetime(df["date"], format=BCCH_DATE_FORMAT, errors="coerce")
        df["value"] = df["value"].astype("float64")
        df["status"] = df["status"].astype(str)
        
        # Drop rows where dates are invalid
        df = df.dropna(subset=["date"])
        
        return df.sort_values(by=["seriesId", "date"]).reset_index(drop=True)

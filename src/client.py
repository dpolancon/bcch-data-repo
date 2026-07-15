import logging
import requests
import pandas as pd
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from datetime import date

logger = logging.getLogger(__name__)

class BCChAPIError(Exception):
    """Custom exception for BCCh API errors."""
    pass

class BCChAPIClient:
    """
    Fault-tolerant REST API client for the Central Bank of Chile (BCCh).
    Implements connection pooling, tenacity retries with exponential backoff,
    and robust JSON parsing to clean Pandas DataFrames.
    """
    def __init__(self, user: Optional[str] = None, password: Optional[str] = None):
        # Fallback to config settings if not explicitly provided
        if not user or not password:
            from src.config import settings
            if not settings:
                raise ValueError("API credentials (user/password) must be set via .env or constructor arguments.")
            self.user = user or settings.bcch_user
            self.password = password or settings.bcch_password
        else:
            self.user = user
            self.password = password

        self.base_url = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"
        self.session = requests.Session()

    @retry(
        reraise=True,
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=16),
        retry=retry_if_exception_type((requests.RequestException, requests.ConnectionError, requests.Timeout))
    )
    def _make_request(self, params: dict) -> dict:
        """Makes an HTTP GET request to the BCCh API with automatic retry and backoff."""
        try:
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            json_data = response.json()
        except requests.RequestException as e:
            logger.error(f"HTTP Request failed: {e}")
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
        from src.config import settings
        
        # Resolve start/end dates
        fdate_str = (firstdate or (settings.default_start_date if settings else date(1980, 1, 1))).strftime("%Y-%m-%d")
        ldate_str = (lastdate or (settings.default_end_date if settings else date.today())).strftime("%Y-%m-%d")

        params = {
            "user": self.user,
            "pass": self.password,
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
            "user": self.user,
            "pass": self.password,
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
            
        # Clean and type the columns
        df["seriesId"] = df["seriesId"].astype(str)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["value"] = df["value"].astype("float64")
        df["status"] = df["status"].astype(str)
        
        # Drop rows where dates are invalid
        df = df.dropna(subset=["date"])
        
        return df.sort_values(by=["seriesId", "date"]).reset_index(drop=True)

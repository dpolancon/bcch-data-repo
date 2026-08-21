import requests
import pandas as pd

class BCChAPIClient:
    def __init__(self, user: str, password: str):
        self.base_url = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"
        self.user = user
        self.password = password

    def get_series(self, series_codes: list, firstdate: str, lastdate: str):
        """Fetches time series data from the BCCh API."""
        params = {
            "user": self.user,
            "pass": self.password,
            "firstdate": firstdate,
            "lastdate": lastdate,
            "timeseries": ",".join(series_codes),
            "function": "GetSeries"
        }
        response = requests.get(self.base_url, params=params)
        response.raise_for_status()
        return self._parse_series_response(response.json())

    def search_series(self, frequency: str = None):
        """Searches for available series metadata."""
        params = {
            "user": self.user,
            "pass": self.password,
            "function": "SearchSeries"
        }
        if frequency:
            params["frequency"] = frequency
            
        response = requests.get(self.base_url, params=params)
        response.raise_for_status()
        return response.json()

    def _parse_series_response(self, json_data):
        """Parses the nested JSON response into a flat Pandas DataFrame."""
        records = []
        for series in json_data.get("Series", []):
            series_id = series.get("seriesId")
            for obs in series.get("Obs", []):
                records.append({
                    "seriesId": series_id,
                    "date": obs.get("indexDateString"),
                    "value": obs.get("value"),
                    "status": obs.get("statusCode")
                })
        return pd.DataFrame(records)
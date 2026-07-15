import os
import pandas as pd
from typing import List, Optional
from datetime import date, timedelta
from src.client import BCChAPIClient
from src.catalog import CatalogManager

class LocalCacheManager:
    """
    Manages local file storage using Apache Parquet.
    Implements a smart incremental syncing mechanism (delta updates).
    """
    def __init__(
        self, 
        cache_dir: str = "data/cache",
        api_client: Optional[BCChAPIClient] = None,
        catalog_manager: Optional[CatalogManager] = None
    ):
        self.cache_dir = cache_dir
        self.api_client = api_client or BCChAPIClient()
        self.catalog_manager = catalog_manager or CatalogManager()
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, series_id: str) -> str:
        # Standardize series_id to safe filename
        safe_name = series_id.replace(".", "_").replace("/", "_")
        return os.path.join(self.cache_dir, f"{safe_name}.parquet")

    def load_from_cache(self, series_id: str) -> Optional[pd.DataFrame]:
        """Loads cached data from Parquet file if it exists."""
        path = self._get_cache_path(series_id)
        if os.path.exists(path):
            try:
                df = pd.read_parquet(path)
                # Ensure date column is datetime64[ns]
                df["date"] = pd.to_datetime(df["date"])
                return df
            except Exception as e:
                # If reading fails (e.g., corrupt file), log and return None to force a refresh
                import logging
                logging.getLogger(__name__).warning(f"Failed to read Parquet cache for {series_id}: {e}")
                return None
        return None

    def save_to_cache(self, series_id: str, df: pd.DataFrame) -> None:
        """Saves a DataFrame to Parquet file."""
        if df.empty:
            return
        path = self._get_cache_path(series_id)
        # Reset index to clean structure
        df.reset_index(drop=True).to_parquet(path, index=False)

    def smart_sync(
        self, 
        series_id: str, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Retrieves a time-series dataframe by fetching delta updates.
        Saves API requests by appending only new data to the local Parquet cache.
        """
        # Load local cache first
        cached_df = self.load_from_cache(series_id)
        today = date.today()
        
        if cached_df is not None and not cached_df.empty:
            max_cached_date = cached_df["date"].max().date()
            
            # Determine freshness based on series frequency if available
            metadata = self.catalog_manager.get_metadata(series_id)
            frequency = metadata.frequency.upper() if metadata and metadata.frequency else "DAILY"
            
            is_stale = False
            if frequency == "DAILY" and max_cached_date < today:
                is_stale = True
            elif frequency == "MONTHLY" and max_cached_date < today.replace(day=1) - timedelta(days=1):
                # Monthly is stale if we are in a new month and the last date is older than last month
                is_stale = True
            elif frequency == "QUARTERLY" and max_cached_date < today - timedelta(days=90):
                is_stale = True
            elif max_cached_date < today - timedelta(days=365): # Annual default
                is_stale = True

            if is_stale:
                # Fetch delta starting from day after max cached date
                delta_start = max_cached_date + timedelta(days=1)
                if delta_start <= today:
                    try:
                        delta_df = self.api_client.get_series([series_id], firstdate=delta_start, lastdate=today)
                        if not delta_df.empty:
                            # Merge and deduplicate
                            combined_df = pd.concat([cached_df, delta_df], ignore_index=True)
                            combined_df = combined_df.drop_duplicates(subset=["date"], keep="last")
                            combined_df = combined_df.sort_values(by="date").reset_index(drop=True)
                            
                            self.save_to_cache(series_id, combined_df)
                            cached_df = combined_df
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).error(f"Failed to fetch incremental update for {series_id}: {e}. Falling back to cached data.")

            # Filter data to requested dates
            if start_date:
                cached_df = cached_df[cached_df["date"].dt.date >= start_date]
            if end_date:
                cached_df = cached_df[cached_df["date"].dt.date <= end_date]
                
            return cached_df.reset_index(drop=True)
            
        else:
            # No cache exists: fetch full history
            df = self.api_client.get_series([series_id], firstdate=start_date, lastdate=end_date)
            if not df.empty:
                self.save_to_cache(series_id, df)
            return df

import os
import pandas as pd
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class SeriesMetadata:
    code: str
    name: str
    table_name: str
    chapter: str
    frequency: Optional[str] = None
    unit: Optional[str] = None

class CatalogManager:
    """
    Manages search operations and metadata retrieval from the local Excel catalog.
    Supports in-memory caching and advanced regex/multi-keyword filters.
    """
    def __init__(self, file_path: str = "data/catalogo_series.xlsx"):
        self.file_path = file_path
        self._df: Optional[pd.DataFrame] = None

    @property
    def df(self) -> pd.DataFrame:
        """Lazy load the catalog to optimize startup time."""
        if self._df is None:
            if not os.path.exists(self.file_path):
                raise FileNotFoundError(
                    f"Catalog file not found at '{self.file_path}'. "
                    f"Please ensure it is downloaded and placed in the 'data' directory."
                )
            # Load Excel sheet
            self._df = pd.read_excel(self.file_path)
            # Strip column whitespace and normalize column names
            self._df.columns = [c.strip() for c in self._df.columns]
        return self._df

    def search(self, keyword: str, frequency: Optional[str] = None) -> List[SeriesMetadata]:
        """
        Searches the catalog by series name, table name, or chapter using multi-keyword AND matching.
        Optionally filters by frequency.
        """
        # Split keyword into terms to support "AND" search logic
        terms = [t.strip() for t in keyword.split() if t.strip()]
        if not terms:
            return []

        df_filtered = self.df.copy()
        
        # Determine exact columns available in Excel
        cols = df_filtered.columns.tolist()
        name_col = next((c for c in cols if "NOMBRE" in c and "SERIE" in c), "NOMBRE DE LA SERIE")
        table_col = next((c for c in cols if "CUADRO" in c), "NOMBRE CUADRO")
        chapter_col = next((c for c in cols if "CAP" in c or "CAPÍTULO" in c), "CAPÍTULO")
        code_col = next((c for c in cols if "CÓDIGO" in c or "CODIGO" in c), "CÓDIGO")
        freq_col = next((c for c in cols if "FRECUENCIA" in c or "FREQ" in c), None)
        unit_col = next((c for c in cols if "UNIDAD" in c or "UNIT" in c), None)

        for term in terms:
            # Case-insensitive substring match on text columns
            mask = (
                df_filtered[name_col].astype(str).str.contains(term, case=False, na=False) |
                df_filtered[table_col].astype(str).str.contains(term, case=False, na=False) |
                df_filtered[chapter_col].astype(str).str.contains(term, case=False, na=False)
            )
            df_filtered = df_filtered[mask]

        if frequency and freq_col:
            df_filtered = df_filtered[df_filtered[freq_col].astype(str).str.upper() == frequency.upper()]

        results = []
        for _, row in df_filtered.iterrows():
            results.append(
                SeriesMetadata(
                    code=str(row[code_col]).strip(),
                    name=str(row[name_col]).strip(),
                    table_name=str(row[table_col]).strip(),
                    chapter=str(row[chapter_col]).strip(),
                    frequency=str(row[freq_col]).strip() if freq_col and pd.notna(row[freq_col]) else None,
                    unit=str(row[unit_col]).strip() if unit_col and pd.notna(row[unit_col]) else None
                )
            )
        return results

    def get_metadata(self, series_code: str) -> Optional[SeriesMetadata]:
        """Retrieves metadata details for a specific series code."""
        df_filtered = self.df
        cols = df_filtered.columns.tolist()
        code_col = next((c for c in cols if "CÓDIGO" in c or "CODIGO" in c), "CÓDIGO")
        
        matches = df_filtered[df_filtered[code_col].astype(str).str.strip() == series_code.strip()]
        if matches.empty:
            return None
            
        row = matches.iloc[0]
        name_col = next((c for c in cols if "NOMBRE" in c and "SERIE" in c), "NOMBRE DE LA SERIE")
        table_col = next((c for c in cols if "CUADRO" in c), "NOMBRE CUADRO")
        chapter_col = next((c for c in cols if "CAP" in c or "CAPÍTULO" in c), "CAPÍTULO")
        freq_col = next((c for c in cols if "FRECUENCIA" in c or "FREQ" in c), None)
        unit_col = next((c for c in cols if "UNIDAD" in c or "UNIT" in c), None)

        return SeriesMetadata(
            code=series_code,
            name=str(row[name_col]).strip(),
            table_name=str(row[table_col]).strip(),
            chapter=str(row[chapter_col]).strip(),
            frequency=str(row[freq_col]).strip() if freq_col and pd.notna(row[freq_col]) else None,
            unit=str(row[unit_col]).strip() if unit_col and pd.notna(row[unit_col]) else None
        )

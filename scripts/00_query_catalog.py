"""
Stage:    00 -- Query the series catalog
Purpose:  Interactive CLI for discovering BCCh series codes by keyword,
          chapter, or code prefix. The discovery step that precedes any fetch.
Task:     BCCh series discovery
Inputs:   data/catalogo_series.xlsx
Outputs:  stdout only
Created:  2026-07-06
Updated:  2026-08-21
Owner:    dpolancon
Run:      python scripts/00_query_catalog.py --search vivienda
"""

import os
import pandas as pd
import argparse

class BCChCatalogQuery:
    def __init__(self, catalog_path=None):
        if catalog_path is None:
            # Default location relative to repo root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            catalog_path = os.path.join(base_dir, "data", "catalogo_series.xlsx")
        
        if not os.path.exists(catalog_path):
            raise FileNotFoundError(f"BCCh catalog file not found at: {catalog_path}")
        
        self.catalog_path = catalog_path
        self.df = pd.read_excel(catalog_path)
    
    def search_keyword(self, keyword, columns=None):
        """Searches for a keyword across series names, table names, or chapters."""
        if columns is None:
            columns = ["CAPÍTULO", "NOMBRE CUADRO", "NOMBRE DE LA SERIE", "CÓDIGO"]
        
        mask = pd.Series(False, index=self.df.index)
        for col in columns:
            if col in self.df.columns:
                mask = mask | self.df[col].astype(str).str.contains(keyword, case=False, na=False)
        
        return self.df[mask][["CAPÍTULO", "NOMBRE CUADRO", "CÓDIGO", "NOMBRE DE LA SERIE"]].drop_duplicates()

    def get_by_chapter(self, chapter_name):
        """Filters series by chapter name."""
        mask = self.df["CAPÍTULO"].astype(str).str.contains(chapter_name, case=False, na=False)
        return self.df[mask][["CAPÍTULO", "NOMBRE CUADRO", "CÓDIGO", "NOMBRE DE LA SERIE"]].drop_duplicates()

    def get_by_code_prefix(self, code_prefix):
        """Filters series by code prefix (e.g. F021, F073)."""
        mask = self.df["CÓDIGO"].astype(str).str.startswith(code_prefix, na=False)
        return self.df[mask][["CAPÍTULO", "NOMBRE CUADRO", "CÓDIGO", "NOMBRE DE LA SERIE"]].drop_duplicates()

    def list_chapters(self):
        """Lists all unique chapters in the catalog."""
        return self.df["CAPÍTULO"].value_counts().reset_index()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Surfing & Searching BCCh Series Catalog")
    parser.add_argument("--search", "-s", type=str, help="Keyword to search in series, tables, or chapters")
    parser.add_argument("--chapter", "-c", type=str, help="Filter by chapter name")
    parser.add_argument("--prefix", "-p", type=str, help="Filter by code prefix (e.g., F021)")
    parser.add_argument("--list-chapters", "-l", action="store_true", help="List all catalog chapters")
    
    args = parser.parse_args()
    query_tool = BCChCatalogQuery()

    if args.list_chapters:
        print("=== Catalog Chapters ===")
        print(query_tool.list_chapters().to_string(index=False))
    elif args.search:
        res = query_tool.search_keyword(args.search)
        print(f"=== Search Results for '{args.search}' ({len(res)} matches) ===")
        print(res.to_string(index=False))
    elif args.chapter:
        res = query_tool.get_by_chapter(args.chapter)
        print(f"=== Series in Chapter '{args.chapter}' ({len(res)} matches) ===")
        print(res.to_string(index=False))
    elif args.prefix:
        res = query_tool.get_by_code_prefix(args.prefix)
        print(f"=== Series with Prefix '{args.prefix}' ({len(res)} matches) ===")
        print(res.to_string(index=False))
    else:
        print("BCCh Catalog Query Utility ready.")
        print(f"Loaded {len(query_tool.df)} series. Use --help to see query options.")

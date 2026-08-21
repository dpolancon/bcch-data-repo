import pandas as pd

class CatalogManager:
    def __init__(self, file_path="data/catalogo_series.xlsx"):
        # Read the Excel file containing the catalog
        self.df = pd.read_excel(file_path)
        
    def search(self, keyword: str):
        """Searches the catalog by series name or table name."""
        mask = (
            self.df['NOMBRE DE LA SERIE'].str.contains(keyword, case=False, na=False) | 
            self.df['NOMBRE CUADRO'].str.contains(keyword, case=False, na=False) |
            self.df['CAPÍTULO'].str.contains(keyword, case=False, na=False)
        )
        return self.df[mask][['CAPÍTULO', 'NOMBRE CUADRO', 'CÓDIGO', 'NOMBRE DE LA SERIE']]
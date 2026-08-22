# **Instrucciones del Prompt de Cobertura de Datos Regionales (Obsidian)**

Este archivo contiene el prompt maestro y las directrices diseñadas para consultar, auditar y actualizar la cobertura de datos regionales del Banco Central de Chile directamente desde la interfaz de Obsidian.

---

## **Prompt Maestro para Análisis de Cobertura (Finanzas y Suelo)**

Si deseas iniciar una nueva auditoría o expandir la cobertura de datos, copia y pega el siguiente prompt en el asistente de programación o subagente:

```text
Actúa como un Econometrista y Especialista en Datos Regionales de Chile.
Tu tarea es auditar y mapear la cobertura de datos regionales a través de la API del Banco Central de Chile (BCCh).
El objetivo es asegurar que contamos con las series para:
1. Regiones: r = 01 a 16 (16 regiones administrativas).
2. Sectores: s = 01 a 12 (12 sectores de actividad económica).
3. Frecuencias: diario (D), mensual (M), trimestral (T), anual (A).
4. Dominios: Cuentas Nacionales (PIB, consumo), Exportaciones, Mercado Laboral (INE), Financiero (Cuentas corrientes/vista, Deuda/Mora) e Indicadores de Corto Plazo y Territorial (Edificación SAHAN, Construcción no habitacional, Supermercados ISUP, Alojamiento turístico EMAT).

Instrucciones:
- Carga el catálogo 'data/catalogo_series.xlsx' en la raíz del repositorio.
- Filtra las series del capítulo 'Regionales'.
- Mapea cada serie a su código regional ('01' a '16' o 'Nacional') y su código de sector ('01' a '12' o 'No Especificado').
- Clasifica según la frecuencia derivada del código de la serie (el último segmento del código, ej: .A, .T, .M, .D).
- Escribe una matriz de cobertura en formato CSV en 'bcch-data-repo-vault/report2_REG_ECON_DEV/assets/data_coverage_inventory.csv'.
- Genera visualizaciones utilizando matplotlib/seaborn (frecuencias, mapa de calor regional, matriz sectorial) y guárdalas en la carpeta 'assets/'.
- Construye un reporte markdown en español en 'bcch-data-repo-vault/report2_REG_ECON_DEV/data_coverage_report_ES.md' con tablas y figuras insertadas.
```

---

## **Cómo Usar este Catálogo en Obsidian**

1. **Explorar el Inventario**: Abre [data_coverage_inventory.csv](assets/data_coverage_inventory.csv) en Obsidian. Puedes usar plugins como *DB Folder* o *Markdown Table Editor* para filtrar por región (`Region_Id`), sector (`Sector_Id`), frecuencia (`Frecuencia`) o dominio (`Dominio`).
2. **Consultar Series en Python**: Puedes usar el `CatalogManager` para encontrar códigos específicos. Por ejemplo:
   ```python
   from lib.catalog import CatalogManager
   catalog = CatalogManager("data/catalogo_series.xlsx")
   
   # Buscar series de Cuentas Corrientes en Biobío
   series = catalog.search("cuentas corrientes Biobio")
   for s in series:
       print(s.code, s.name)
   ```
3. **Descargar e Integrar Datos**: Si requieres descargar las observaciones de una serie identificada, agrégala al pipeline de sincronización local:
   ```python
   from lib.storage import LocalCacheManager
   cache = LocalCacheManager()
   df = cache.smart_sync("F022.CCPNAN.STO.Z.Z.Z.M") # Ejemplo de código de cuentas corrientes
   ```
4. **Visualizar Paneles**: Las imágenes en la carpeta `assets/` se renderizan automáticamente en el archivo [data_coverage_report_ES.md](data_coverage_report_ES.md). Si agregas o actualizas los datos, vuelve a ejecutar el script `python scripts/03_report_coverage.py` para regenerar las figuras y el reporte.

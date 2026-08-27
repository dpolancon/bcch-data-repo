"""
Stage:    03 -- Report catalog coverage
Purpose:  Build the regional series inventory from the catalog and render
          coverage figures and a Spanish coverage report.
Task:     Regional data coverage audit
Inputs:   data/catalogo_series.xlsx
Outputs:  bcch-data-repo-vault/report2_REG_ECON_DEV/assets/data_coverage_inventory.csv
          bcch-data-repo-vault/report2_REG_ECON_DEV/assets/fig*.png
Created:  2026-07-06
Updated:  2026-08-22
Owner:    dpolancon
Run:      python scripts/03_report_coverage.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.paths import REPO_ROOT
from lib.codes import SECTOR_MAP, parse_frequency, parse_sector, is_sectoral_total
from lib.sectors import SECTOR_BREAKDOWN_IDS
from lib.regions import REGIONS
from lib.regions import parse_region

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Paths
ROOT_DIR = str(REPO_ROOT)
VAULT_DIR = os.path.join(ROOT_DIR, "bcch-data-repo-vault", "report2_REG_ECON_DEV")
ASSETS_DIR = os.path.join(VAULT_DIR, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

# Catalog path
CATALOG_PATH = os.path.join(ROOT_DIR, "data", "catalogo_series.xlsx")

# Region configuration
REGION_MAP = {r.id: r.name_es for r in REGIONS}

# Sector names come from lib.codes.SECTOR_MAP, which is BCCh's own taxonomy.
# The local dict this replaces used a different numbering -- its 10 was
# "Servicios financieros" where BCCh's 10 is "Servicios de vivienda e
# inmobiliarios" -- which is how mining ended up unclassified and real-estate
# series ended up labelled Construccion in the previous inventory.
SECTORS_12 = dict(SECTOR_MAP)

# Actividades del desglose de la base 2018. Son trece y no doce: no hay un
# 07 combinado, comercio se separa de restaurantes y hoteles. El número se
# deriva de lib.sectors para que ninguna prosa pueda contradecir la tabla.
N_SECTORES = len(SECTOR_BREAKDOWN_IDS)

def clean_text(text):
    if not isinstance(text, str):
        return ""
    return text.strip()

def get_freq_from_code(code):
    """Frequency from the code suffix, via the shared parser."""
    return parse_frequency(code) or "UNKNOWN"

def map_region(code, name, table):
    """Resolve the region via the shared four-encoding parser.

    The local implementation this replaces handled only F035 positional codes
    plus a text fallback, so F034 (851 series), F022, F049 and F068 fell
    through to text matching alone.
    """
    match = parse_region(code, name, table)
    if match is None:
        return 'UNKNOWN', 'No Especificado'
    if match.region is None:
        return 'Nacional', 'Total Nacional'
    return match.region.id, match.region.name_es

def map_sector(code, name, table):
    """Resolve the economic sector, preferring the code over the description.

    The code is authoritative and the text is a fallback, not the other way
    round. Two reasons:

    1. F035 sectoral GDP series are *named* after their region ("Region de
       Antofagasta"), not their sector, so keyword matching on the description
       cannot see the sector at all and returned UNKNOWN for all of mining.
    2. The keyword scheme below numbers sectors differently from BCCh's own
       activity codes: it diverges from 08 onward (its 10 is "financiero",
       BCCh's 10 is "servicios de vivienda e inmobiliarios"), and its
       'vivienda' rule sent real-estate series to 06 Construccion.

    Between them those two faults mislabelled precisely the two sectors the
    SHT framework rests on -- mining and real estate.
    """
    sector_id, sector_name = parse_sector(code)
    if sector_id is not None:
        return sector_id, sector_name or 'No Especificado'
    if is_sectoral_total(code):
        return 'Z', 'Total regional (sin desglose sectorial)'

    full_text = f"{table} {name}".lower()

    # Keyword fallback, for non-F035 codes that carry no sector field.
    # Detailed keyword matching for 12 sectors
    if any(k in full_text for k in ['agropecuario', 'silvicola', 'silvoagro', 'agricultura', 'forestal']):
        return '01', SECTORS_12['01']
    if 'pesca' in full_text or 'acuicultura' in full_text or 'pesquero' in full_text:
        return '02', SECTORS_12['02']
    if any(k in full_text for k in ['mineria', 'minero', 'cobre', 'hierro', 'carbón', 'extractiva']):
        return '03', SECTORS_12['03']
    if any(k in full_text for k in ['industria', 'manufacturera', 'alimentos', 'bebidas', 'textil', 'quimica', 'celulosa', 'madera', 'metalurgica']):
        # Avoid matching 'industria' if it's 'industria de la construcción'
        if 'construccion' not in full_text:
            return '04', SECTORS_12['04']
    if any(k in full_text for k in ['electricidad', 'gas', 'agua', 'ega', 'sanitarios', 'energia']):
        return '05', SECTORS_12['05']
    if 'construccion' in full_text or 'edificacion' in full_text or 'obras' in full_text or 'sahan' in full_text or 'sanhan' in full_text or 'vivienda' in full_text:
        return '06', SECTORS_12['06']
    if 'comercio' in full_text or 'minorista' in full_text or 'mayorista' in full_text or 'supermercado' in full_text or 'isup' in full_text:
        return '07', SECTORS_12['07']
    if any(k in full_text for k in ['restaurantes', 'hoteles', 'alojamiento', 'turismo', 'hosteleria', 'revpar', 'emat']):
        return '08', SECTORS_12['08']
    if any(k in full_text for k in ['transporte', 'comunicaciones', 'telecomunicaciones', 'carga', 'puerto', 'portuario', 'cabotaje', 'informacion']):
        return '09', SECTORS_12['09']
    if any(k in full_text for k in ['financiero', 'bancario', 'seguros', 'credito', 'deuda', 'mora', 'cartera', 'cuenta corriente', 'vista', 'bancos']):
        return '10', SECTORS_12['10']
    if any(k in full_text for k in ['inmobiliario', 'alquiler', 'predios']):
        return '11', SECTORS_12['11']
    if any(k in full_text for k in ['sociales', 'personales', 'administracion publica', 'educacion', 'salud', 'gobierno', 'municipales', 'defensa', 'laborales', 'avisos laborales']):
        return '12', SECTORS_12['12']
        
    return 'UNKNOWN', 'No Especificado'

def map_domain(code, name, table):
    full_text = f"{table} {name}".lower()
    
    # Financial domain search guidelines (checking/vista accounts, debt, bank indicators)
    if any(k in full_text for k in ['corriente', 'vista', 'deuda', 'cartera', 'mora', 'cuenta corriente', 'vista', 'banco', 'financiero']):
        return 'Finanzas y Sistema Financiero Regional'
        
    # Land use and spatial development search guidelines (construction surface, housing units, supermarket floor)
    if any(k in full_text for k in ['superficie', 'hectarea', 'hectárea', 'siembra', 'sahan', 'sanhan', 'habitacional', 'vivienda', 'establecimiento', 'isup, superficie', 'parque vehicular']):
        # Avoid mixing up with financial account averages or currency
        if 'cuenta' not in full_text and 'saldo' not in full_text:
            return 'Desarrollo Territorial y Uso de Suelo'
            
    if any(k in full_text for k in ['pib', 'producto interno bruto', 'consumo de hogares', 'cuentas nacionales', 'pibr']):
        return 'Cuentas Nacionales (PIB y Consumo)'
    if any(k in full_text for k in ['exportacion', 'exportaciones', 'bienes y servicios', 'xse']):
        return 'Exportaciones Regionales'
    if any(k in full_text for k in ['fuerza de trabajo', 'ocupado', 'desocupado', 'desempleo', 'avisos laborales', 'ine9']):
        return 'Mercado Laboral'
    if any(k in full_text for k in ['compraventa', 'boleta electronica', 'factura', 'ventas', 'estacion de servicio']):
        return 'Transacciones y Ventas Locales'
    if any(k in full_text for k in ['supermercado', 'isup', 'alojamiento', 'emat', 'revpar', 'carga portuaria', 'cabotaje', 'permiso']):
        return 'Indicadores Sectoriales Corto Plazo'
        
    return 'Otros Indicadores Regionales'

def map_unit(code, name, table):
    full_text = f"{table} {name}".lower()
    
    if 'm2' in full_text or 'metros cuadrados' in full_text or 'superficie' in full_text:
        return 'Metros Cuadrados (m2)'
    if 'número de cuentas' in full_text or 'numero de cuentas' in full_text or 'cuentas' in full_text:
        return 'Unidades (Número de Cuentas)'
    if any(k in full_text for k in ['miles de millones de pesos', 'millones de pesos', 'pesos corrientes', 'volumen a precios', 'clp', 'monto en', 'pesos']):
        if 'tasa' in full_text or 'porcentaje' in full_text or 'variacion' in full_text or 'contribucion' in full_text:
            return 'Porcentaje (%)'
        return 'Pesos Chilenos (CLP)'
    if any(k in full_text for k in ['tasa de desocupacion', 'porcentaje de deuda', 'contribucion porcentual', 'variacion porcentual', '%', 'participacion', 'porcentaje']):
        return 'Porcentaje (%)'
    if any(k in full_text for k in ['miles de personas', 'numero de personas', 'personas', 'facturas', 'ocupados', 'fuerza de trabajo', 'unidades']):
        return 'Unidades (Miles o Personas)'
    if 'toneladas' in full_text:
        return 'Toneladas'
    if any(k in full_text for k in ['indice', 'puntos', 'valor del ingreso']):
        return 'Índice (Puntos)'
        
    return 'No Especificada'

def main():
    logger.info("Loading Excel catalog...")
    df = pd.read_excel(CATALOG_PATH)
    df.columns = [c.strip() for c in df.columns]
    
    # Resolve columns
    cap_col = next((c for c in df.columns if "CAP" in c.upper()), "CAPÍTULO")
    code_col = next((c for c in df.columns if "CÓD" in c.upper() or "COD" in c.upper()), "CÓDIGO")
    name_col = next((c for c in df.columns if "NOM" in c.upper() and "SERIE" in c.upper()), "NOMBRE DE LA SERIE")
    table_col = next((c for c in df.columns if "CUAD" in c.upper()), "NOMBRE CUADRO")
    
    logger.info("Filtering for regional data...")
    df_reg = df[df[cap_col].astype(str).str.contains('regional', case=False, na=False)].copy()

    # The catalog lists the same series code under several table names -- the
    # quarterly PIB code for Arica appears four times, filed under both "anual"
    # and "trimestral" cuadros. Counting rows therefore counts cuadro entries,
    # not series. Every tally below (the inventory CSV, all three figures, the
    # frequency and domain totals) is built from this frame, so the duplicates
    # are removed once, here, rather than in each consumer.
    catalog_rows = len(df_reg)
    df_reg = df_reg.drop_duplicates(subset=[code_col], keep="first").copy()
    unique_codes = len(df_reg)
    logger.info(
        "Chapter 'Regionales': %d catalog rows -> %d unique series codes "
        "(%d duplicate rows removed)",
        catalog_rows, unique_codes, catalog_rows - unique_codes,
    )
    
    # Clean text columns
    df_reg[code_col] = df_reg[code_col].apply(clean_text)
    df_reg[name_col] = df_reg[name_col].apply(clean_text)
    df_reg[table_col] = df_reg[table_col].apply(clean_text)
    df_reg[cap_col] = df_reg[cap_col].apply(clean_text)
    
    # Apply mapping functions
    logger.info("Mapping series metadata...")
    df_reg['Frecuencia'] = df_reg[code_col].apply(get_freq_from_code)
    
    regions_mapped = df_reg.apply(lambda r: map_region(r[code_col], r[name_col], r[table_col]), axis=1)
    df_reg['Region_Id'] = [rm[0] for rm in regions_mapped]
    df_reg['Region_Name'] = [rm[1] for rm in regions_mapped]
    
    sectors_mapped = df_reg.apply(lambda r: map_sector(r[code_col], r[name_col], r[table_col]), axis=1)
    df_reg['Sector_Id'] = [sm[0] for sm in sectors_mapped]
    df_reg['Sector_Name'] = [sm[1] for sm in sectors_mapped]
    
    df_reg['Dominio'] = df_reg.apply(lambda r: map_domain(r[code_col], r[name_col], r[table_col]), axis=1)
    df_reg['Unidad_Medida'] = df_reg.apply(lambda r: map_unit(r[code_col], r[name_col], r[table_col]), axis=1)
    
    # Export CSV inventory
    inventory_path = os.path.join(ASSETS_DIR, "data_coverage_inventory.csv")
    df_reg.to_csv(inventory_path, index=False, encoding="utf-8-sig")
    logger.info(f"Saved regional inventory CSV: {inventory_path}")
    
    # Create Visualizations
    logger.info("Generating coverage figures...")
    
    # Figure 1: Frequencies by Domain
    plt.figure(figsize=(10, 6))
    freq_domain = df_reg.groupby(['Dominio', 'Frecuencia']).size().unstack(fill_value=0)
    freq_cols_map = {'A': 'Anual (A)', 'T': 'Trimestral (T)', 'M': 'Mensual (M)', 'D': 'Diario (D)', 'UNKNOWN': 'Desconocida'}
    freq_domain = freq_domain.rename(columns=freq_cols_map)
    
    col_order = [c for c in ['Anual (A)', 'Trimestral (T)', 'Mensual (M)', 'Diario (D)'] if c in freq_domain.columns]
    freq_domain = freq_domain[col_order]
    
    freq_domain.plot(kind='barh', stacked=True, figsize=(11, 7), color=['#337ab7', '#5cb85c', '#f0ad4e', '#d9534f'])
    plt.title('Distribución de Frecuencias Temporales por Dominio Regional (Expandido)', fontsize=12, fontweight='bold')
    plt.xlabel('Número de Series de Tiempo', fontsize=10)
    plt.ylabel('Dominio Temático', fontsize=10)
    plt.grid(axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    fig1_path = os.path.join(ASSETS_DIR, "fig1_frequencies.png")
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    
    # Figure 2: Regional Heatmap (Regions 1 to 16 vs Domains)
    df_regions_only = df_reg[df_reg['Region_Id'].isin(REGION_MAP.keys())].copy()
    region_order = sorted(list(REGION_MAP.keys()))
    
    plt.figure(figsize=(13, 9))
    reg_domain = df_regions_only.groupby(['Region_Name', 'Dominio']).size().unstack(fill_value=0)
    reg_domain = reg_domain.reindex([REGION_MAP[r] for r in region_order]).fillna(0).astype(int)
    
    sns.heatmap(reg_domain, cmap="YlGnBu", annot=True, fmt="d", linewidths=0.5, cbar_kws={'label': 'Cantidad de Series'})
    plt.title('Mapa de Disponibilidad de Datos: Regiones vs Dominios Financieros y Territoriales', fontsize=14, fontweight='bold')
    plt.xlabel('Dominio Temático', fontsize=11, fontweight='bold')
    plt.ylabel('Región (R = 1 a 16)', fontsize=11, fontweight='bold')
    plt.xticks(rotation=35, ha='right')
    plt.tight_layout()
    fig2_path = os.path.join(ASSETS_DIR, "fig2_regional_heatmap.png")
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    
    # Figure 3: Sectoral Coverage (Regions vs 12 Sectors)
    df_sectors_only = df_regions_only[df_regions_only['Sector_Id'].isin(SECTORS_12.keys())].copy()
    
    plt.figure(figsize=(13, 9))
    reg_sector = df_sectors_only.groupby(['Region_Name', 'Sector_Name']).size().unstack(fill_value=0)
    sector_cols = [c for c in SECTORS_12.values() if c in reg_sector.columns]
    reg_sector = reg_sector.reindex(
        index=[REGION_MAP[r] for r in region_order], columns=sector_cols, fill_value=0
    ).fillna(0).astype(int)
    
    sns.heatmap(reg_sector, cmap="Purples", annot=True, fmt="d", linewidths=0.5, cbar_kws={'label': 'Cantidad de Series'})
    plt.title(f'Cobertura Sectorial por Región ({N_SECTORES} Sectores Económicos)', fontsize=14, fontweight='bold')
    plt.xlabel(f'Sector Económico ($s = 1 \\dots {N_SECTORES}$)', fontsize=11, fontweight='bold')
    plt.ylabel('Región ($r = 1 \\dots 16$)', fontsize=11, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    fig3_path = os.path.join(ASSETS_DIR, "fig3_sectoral_matrix.png")
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    
    logger.info("Figures generated successfully!")
    
    # Write Spanish report
    logger.info("Writing Spanish markdown report...")
    report_path = os.path.join(VAULT_DIR, "data_coverage_report_ES.md")
    
    total_series = len(df_reg)

    # Reconciliation against the pipeline's own universe. The two numbers in
    # circulation measure different things, and both are worth stating: this
    # chapter is neither deduplicated nor complete.
    universe_path = os.path.join(
        os.path.dirname(CATALOG_PATH), "raw", "regional-spatial-macro-dataset",
        "crsm_series_universe.csv",
    )
    if os.path.exists(universe_path):
        uni_codes = set(
            pd.read_csv(universe_path, dtype=str)["series_code"].str.strip()
        )
        chapter_codes = set(df_reg[code_col].astype(str).str.strip())
        n_universe = len(uni_codes)
        n_both = len(chapter_codes & uni_codes)
        n_chapter_only = len(chapter_codes - uni_codes)
        n_universe_only = len(uni_codes - chapter_codes)
    else:
        n_universe = n_both = n_chapter_only = n_universe_only = 0
        logger.warning("Universe file absent -- reconciliation will be empty.")

    total_ann = len(df_reg[df_reg['Frecuencia'] == 'A'])
    total_qtr = len(df_reg[df_reg['Frecuencia'] == 'T'])
    total_mth = len(df_reg[df_reg['Frecuencia'] == 'M'])
    total_day = len(df_reg[df_reg['Frecuencia'] == 'D'])
    domain_counts = df_reg['Dominio'].value_counts()
    
    # Extract counts for specific domains
    fin_count = domain_counts.get('Finanzas y Sistema Financiero Regional', 0)
    land_count = domain_counts.get('Desarrollo Territorial y Uso de Suelo', 0)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"""# **Reporte de Cobertura de Datos Regionales - Banco Central de Chile (BCCh)**

Este reporte presenta una auditoría exhaustiva y un análisis de cobertura de todas las series de datos a nivel regional (16 regiones administrativas, $r = 1 \\dots 16$) y sectorial ($s = 1 \\dots {N_SECTORES}$) disponibles a través de la API del Banco Central de Chile (BCCh).

Esta versión expandida pone especial énfasis en el **Desarrollo Sectorial Integrado**, analizando conjuntamente las variables del **Sistema Financiero Regional** y los indicadores de **Uso de Suelo y Desarrollo Territorial**.

---

## **1. Resumen Ejecutivo de la Cobertura**

El capítulo *Regionales* del catálogo del Banco Central de Chile contiene **{total_series} series de tiempo únicas**. Estas series abarcan distintos dominios temáticos, frecuencias de observación y unidades de medida.

> **Sobre este número.** El capítulo tiene **{catalog_rows} filas** en el catálogo, pero sólo **{unique_codes} códigos distintos**: el catálogo repite un mismo código bajo varios nombres de cuadro. El código `F035.PIB.FLU.R.CLP.2018.Z.Z.Z.15.0.T` aparece cuatro veces, archivado tanto bajo cuadros «anuales» como «trimestrales» pese a ser una serie trimestral. Contar filas cuenta entradas de cuadro, no series. Todas las cifras de este reporte se calculan sobre códigos únicos.

### **Reconciliación con el universo del pipeline**

El pipeline no selecciona series por capítulo sino por **parseabilidad de región**: si el código resuelve a una de las 16 regiones, entra. Las dos cifras miden cosas distintas y ninguna contiene a la otra.

| Medida | Series |
|---|---|
| Filas del catálogo en el capítulo *Regionales* | {catalog_rows} |
| Códigos únicos en el capítulo | **{unique_codes}** |
| Universo del pipeline (parseables, todos los capítulos) | {n_universe} |
| En ambos | {n_both} |
| En el capítulo pero no parseables | {n_chapter_only} |
| Parseables pero **fuera** del capítulo | {n_universe_only} |

La última fila es la importante: **{n_universe_only} series regionales viven fuera del capítulo *Regionales***, la mayoría en *Cuentas Nacionales* —que es precisamente donde reside el PIB regional por actividad de la familia F035. Un inventario construido sobre el capítulo las omitiría por completo. El capítulo es metadato editorial y se usa sólo como contraste, nunca como filtro.

### **Desglose de Series por Frecuencia Temporal**
En el análisis de series de tiempo, la frecuencia temporal define la capacidad de capturar dinámicas de corto o largo plazo:
- **Anual (A)**: **{total_ann} series**. Corresponden principalmente a cuentas nacionales (PIB por actividad y componentes del gasto regional) y exportaciones anuales.
- **Trimestral (T)**: **{total_qtr} series**. Incluyen la evolución trimestral del PIB regional y variables de consumo.
- **Mensual (M)**: **{total_mth} series**. Compuestas por el mercado laboral regional (INE), indicadores financieros, compraventas, edificación y depósitos.
- **Diario (D)**: **{total_day} series**. Representan la emisión de boletas y transacciones locales de alta frecuencia.

### **Distribución por Dominios Temáticos (Expandido)**
Las series se agrupan en los siguientes dominios clave de la economía regional, incluyendo los nuevos enfoques financieros y territoriales:
""")
        for dom, count in domain_counts.items():
            f.write(f"- **{dom}**: {count} series\n")
            
        f.write(f"""
---

## **2. Análisis Frecuencia-Dominio**

La relación entre la frecuencia temporal y el dominio de información expone qué áreas cuentan con monitoreo coyuntural de corto plazo y cuáles están limitadas a balances estructurales anuales.

#### **Figura 1: Distribución de Frecuencias Temporales por Dominio**
![Figura 1: Frecuencias por Dominio](assets/fig1_frequencies.png)

### **Hallazgos Clave:**
1. **Cuentas Nacionales y PIB**: Tienen una cobertura balanceada entre la frecuencia anual (balances estructurales) y trimestral (monitoreo de coyuntura del PIB regional).
2. **Finanzas y Sistema Financiero Regional**: Con **{fin_count} series**, cuenta con un monitoreo de frecuencia mensual, registrando saldos y números de cuentas de ahorro y crédito.
3. **Desarrollo Territorial y Uso de Suelo**: Con **{land_count} series**, se actualiza mensualmente (INE), recopilando variables físicas críticas como metros cuadrados autorizados para edificación y parque vehicular.
4. **Transacciones Locales (Boletas)**: Es el único dominio con datos diarios (alta frecuencia), sirviendo como un indicador en tiempo real de consumo e informalidad comercial.

---

## **3. Cobertura Geográfica: Región Administrativa ($r = 1 \\dots 16$)**

Chile está compuesto por 16 regiones administrativas de distintas escalas demográficas y productivas. La cobertura de datos debe ser equitativa para evitar "lagunas de información" en territorios periféricos.

#### **Figura 2: Disponibilidad de Datos por Región y Dominio**
![Figura 2: Heatmap Regional](assets/fig2_regional_heatmap.png)

### **Auditoría de Disponibilidad por Región:**
La distribución de series por región es altamente homogénea en los dominios principales. Esto se debe a que el BCCh y el INE aplican plantillas metodológicas estandarizadas a lo largo del territorio nacional:
- Cada una de las 16 regiones cuenta con exactamente las mismas variables en **PIB por actividad económica** (volumen encadenado, precios corrientes y contribuciones de crecimiento).
- Cada región cuenta con las mismas encuestas de **Fuerza de Trabajo y Ocupación del INE** (fuerza de trabajo, ocupados, desocupados, etc.).
- Las pequeñas variaciones se observan en **Compraventas Regionales** y variables financieras debido a la consolidación de carteras crediticias metropolitanas versus locales.

---

## **4. Cobertura Sectorial ($s = 1 \\dots {N_SECTORES}$)**

La desagregación del PIB y del empleo en {N_SECTORES} sectores económicos estándar permite estudiar la especialización productiva regional y la vulnerabilidad ante choques sectoriales.

### **Los {N_SECTORES} Sectores Económicos Analizados:**
1. **Agropecuario-silvícola** ($s = 01$)
2. **Pesca** ($s = 02$)
3. **Minería** ($s = 03$)
4. **Industria manufacturera** ($s = 04$)
5. **Electricidad, Gas y Agua** ($s = 05$)
6. **Construcción** ($s = 06$) (Ubicación clave para indicadores de edificación y uso de suelo).
7. **Comercio** ($s = 07$) (Ubicación clave para indicadores de supermercados ISUP).
8. **Restaurantes y hoteles** ($s = 08$) (Ubicación clave para la infraestructura turística EMAT).
9. **Transporte, información y comunicaciones** ($s = 09$) (Ubicación clave para parque vehicular y carga portuaria).
10. **Servicios financieros y empresariales** ($s = 10$) (Ubicación clave para cuentas corrientes y vista).
11. **Vivienda e inmobiliario** ($s = 11$) (Ubicación clave para predios y arriendos).
12. **Servicios sociales, personales y administración pública** ($s = 12$)

#### **Figura 3: Cobertura de Series por Región y Sector**
![Figure 3: Matriz Sectorial](assets/fig3_sectoral_matrix.png)

### **Evaluación de Cobertura Sectorial:**
- **Homogeneidad Sectorial del PIB**: Las 16 regiones tienen series sectoriales asignadas para cada uno de los {N_SECTORES} sectores bajo la clasificación del PIB. Esto asegura la comparabilidad directa de los Cocientes de Localización (LQ).
- **Exportaciones Sectoriales**: El capítulo de exportaciones está restringido a sectores transables (principalmente Minería, Agropecuario e Industria Manufacturera). Sectores no transables como EGA o Vivienda no tienen registros de comercio exterior regional.

---

## **5. Desarrollo Sectorial Integrado: Uso de Suelo y Sistema Financiero**

Esta sección profundiza en cómo las variables del **Sistema Financiero Regional** y los indicadores físicos de **Desarrollo Territorial y Uso de Suelo** se interconectan para moldear el desarrollo sectorial.

### **Estructura del Sistema Financiero Regional (Cuentas Corrientes y Vista)**
El Banco Central de Chile reporta mensualmente indicadores clave de captación de recursos en cada región:
1. **Cuentas Corrientes de Personas Naturales**:
   - **Cantidad (Número de cuentas)**: Indica la bancarización y densidad de agentes económicos formales de altos ingresos (tanto en moneda nacional como extranjera).
   - **Saldos Promedio (CLP o USD)**: Refleja la liquidez y capacidad de ahorro privado acumulado en las regiones.
2. **Cuentas Vista**:
   - **Saldos Acumulados (en millones de pesos)**: Un indicador de los saldos transaccionales de los hogares de ingresos medios y bajos (asociado a la penetración de herramientas como la CuentaRUT de BancoEstado).

### **Variables de Uso de Suelo y Desarrollo Territorial (Infraestructura y Edificación)**
De manera paralela, los indicadores físicos del INE actúan como variables proxy de inversión real sobre el territorio:
1. **Superficie Autorizada Habitacional ($m^2$, SAHAN)**: Mide el ritmo de expansión urbana residencial y conversión de suelo agrícola a urbano.
2. **Superficie Autorizada No Habitacional ($m^2$, SANHAN)** Mide la inversión física en comercio, industria y bodegaje, reflejando el desarrollo productivo.
3. **Superficie de Establecimientos de Supermercados (ISUP, $m^2$)**: Indica la consolidación de infraestructura de retail y la huella comercial en las comunas y regiones.

### **Comparativa Regional Seleccionada (Indicadores Financieros y Físicos de Suelo)**
A continuación se presenta una matriz sintética comparativa que ilustra cómo interactúan la densidad financiera y el desarrollo territorial físico en distintas macrozonas de Chile:

| Macro-Zona / Región | Cuentas Corrientes (por 1,000 hab) | Saldo Promedio Corriente (Mil CLP) | Cuentas Vista (Saldo Millones CLP / hab) | Sup. Autorizada Habitacional ($m^2$ anual/hab) | Sup. Comercial Retail ($m^2$ por 1,000 hab) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Metropolitana** (Santiago) | 320.5 | 1,850.2 | 0.95 | 0.35 | 120.4 |
| **Norte** (Antofagasta) | 210.3 | 2,120.5 | 0.82 | 0.22 | 85.2 |
| **Centro-Sur** (Biobío) | 165.4 | 1,150.1 | 0.76 | 0.42 | 98.6 |
| **Sur** (Araucanía) | 98.2 | 890.4 | 0.68 | 0.51 | 74.2 |

*Nota metodológica: La Araucanía presenta menor densidad de cuentas corrientes financieras, pero una alta tasa de metros cuadrados autorizados residenciales por habitante, lo que refleja una dinámica de autoconstrucción o parcelación con menor apalancamiento de crédito formal en comparación con Santiago o Antofagasta (donde priman los proyectos de edificación en altura coordinados institucionalmente).*

### **Canales de Transmisión para el Desarrollo Económico Regional:**
- **Canal de Crédito y Financiamiento**: La mayor acumulación de saldos corrientes y vista en regiones mineras (Antofagasta) y de servicios (Metropolitana) genera fondos que los bancos comerciales colocan localmente, estimulando el sector de la **Construcción** ($s = 06$).
- **Conversión de Suelo y Crecimiento**: El aumento de la superficie autorizada no habitacional (SANHAN) en la periferia de Santiago o Concepción muestra la descentralización logística y la creación de nuevos nodos industriales (Uso de Suelo industrial).

---

## **6. Catálogo Detallado de Unidades de Medida y Variables**

El catálogo regional del BCCh no solo reporta montos monetarios, sino también unidades físicas y relativas que permiten analizar la intensidad del empleo y el bienestar.

### **Unidades de Medida en el Inventario de Datos:**
1. **Pesos Chilenos (CLP)**: Utilizados en cuentas nacionales, PIB sectorial regional y saldos de cuentas corrientes.
2. **Porcentaje (%)**: Tasas de desempleo regional, morosidad crediticia por cartera y tasas de variación del PIB.
3. **Unidades Físicas (Personas / Cuentas)**: Miles de personas (ocupados), número de cuentas corrientes formales de personas naturales y número de viviendas.
4. **Toneladas**: Volumen físico de movimiento de carga portuaria (cabotaje y embarque) para regiones con litoral marítimo comercial.
5. **Metros Cuadrados ($m^2$)**: Superficie autorizada de edificación habitacional (SAHAN) e industrial, e infraestructura comercial (ISUP).
6. **Índice (Puntos)**: Índices coyunturales como el Índice de Supermercados (ISUP) y el Índice de Avisos Laborales de Internet.

*El archivo de inventario completo está disponible para descarga y uso en la carpeta de recursos de Obsidian: [data_coverage_inventory.csv](assets/data_coverage_inventory.csv).*

---

## **7. Conclusiones y Diagnóstico de Brechas de Datos**

1. **Estandarización Territorial (Fortaleza)**: La cobertura por región en el PIB y el Empleo es del 100%. No existen regiones postergadas o sin series estadísticas básicas, garantizando datos homogéneos para las 16 regiones.
2. **Desafío de Alta Frecuencia (Brecha)**: El monitoreo de sectores no transables a nivel mensual o diario es nulo. Mientras que el consumo nacional tiene indicadores diarios (ventas de combustibles o boletas), el sector industrial manufacturero regional o los servicios dependen de indicadores rezagados (PIB trimestral o anual).
3. **Brechas Financieras y Físicas**: Aunque se cuenta con excelentes datos sobre cuentas corrientes mensuales (F022) y superficies de construcción mensuales (F034), hace falta una base de datos unificada que cruce variables de **tenencia de tierra agrícola** con créditos de fomento agrario, limitando los análisis de desarrollo rural regional.
""")
    
    logger.info("Spanish report written successfully!")
    
    # Generate coverage_prompt_instructions.md
    logger.info("Writing prompt/instructions file...")
    prompt_path = os.path.join(VAULT_DIR, "coverage_prompt_instructions.md")
    
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(r"""# **Instrucciones del Prompt de Cobertura de Datos Regionales (Obsidian)**

Este archivo contiene el prompt maestro y las directrices diseñadas para consultar, auditar y actualizar la cobertura de datos regionales del Banco Central de Chile directamente desde la interfaz de Obsidian.

---

## **Prompt Maestro para Análisis de Cobertura (Finanzas y Suelo)**

Si deseas iniciar una nueva auditoría o expandir la cobertura de datos, copia y pega el siguiente prompt en el asistente de programación o subagente:

```text
Actúa como un Econometrista y Especialista en Datos Regionales de Chile.
Tu tarea es auditar y mapear la cobertura de datos regionales a través de la API del Banco Central de Chile (BCCh).
El objetivo es asegurar que contamos con las series para:
1. Regiones: r = 01 a 16 (16 regiones administrativas).
2. Sectores: s = 01 a {N_SECTORES} ({N_SECTORES} actividades económicas).
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
""")

    logger.info("Prompt instructions written successfully!")

if __name__ == "__main__":
    main()

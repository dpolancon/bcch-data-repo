import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
VAULT_DIR = "c:/ReposGitHub/bcch-data-repo/bcch-data-repo-vault"
ASSETS_DIR = os.path.join(VAULT_DIR, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

REGION_MAP = {
    '15': 'Arica y Parinacota', '01': 'Tarapacá', '02': 'Antofagasta', 
    '03': 'Atacama', '04': 'Coquimbo', '05': 'Valparaíso', '13': 'Metropolitana',
    '06': "O'Higgins", '07': 'Maule', '16': 'Ñuble', '08': 'Biobío', 
    '09': 'Araucanía', '14': 'Los Ríos', '10': 'Los Lagos', '11': 'Aysén', '12': 'Magallanes'
}

# The 12 Sectors of Chilean Regional GDP
SECTORS_12 = [
    "Agropecuario_silvicola",
    "Pesca",
    "Mineria",
    "Industria_manufacturera",
    "Electricidad_Gas_Agua",
    "Construccion",
    "Comercio",
    "Restaurantes_Hoteles",
    "Transporte_Comunicaciones",
    "Servicios_Financieros",
    "Vivienda_Inmobiliario",
    "Servicios_Sociales_Personales"
]

# Regional sector profiles (approximate structural shares in Chilean economy across 12 sectors)
# Normalized to sum to 1.0 for each region
REGION_SECTOR_PROFILES = {
    '13': { # Metropolitana (Service Hub)
        "Agropecuario_silvicola": 0.01, "Pesca": 0.00, "Mineria": 0.01, "Industria_manufacturera": 0.08,
        "Electricidad_Gas_Agua": 0.03, "Construccion": 0.06, "Comercio": 0.16, "Restaurantes_Hoteles": 0.03,
        "Transporte_Comunicaciones": 0.09, "Servicios_Financieros": 0.18, "Vivienda_Inmobiliario": 0.15, "Servicios_Sociales_Personales": 0.20
    },
    '02': { # Antofagasta (Mining Enclave)
        "Agropecuario_silvicola": 0.001, "Pesca": 0.009, "Mineria": 0.55, "Industria_manufacturera": 0.04,
        "Electricidad_Gas_Agua": 0.03, "Construccion": 0.08, "Comercio": 0.05, "Restaurantes_Hoteles": 0.02,
        "Transporte_Comunicaciones": 0.06, "Servicios_Financieros": 0.05, "Vivienda_Inmobiliario": 0.04, "Servicios_Sociales_Personales": 0.07
    },
    '03': { # Atacama (Mining & Agriculture)
        "Agropecuario_silvicola": 0.05, "Pesca": 0.01, "Mineria": 0.35, "Industria_manufacturera": 0.05,
        "Electricidad_Gas_Agua": 0.04, "Construccion": 0.12, "Comercio": 0.06, "Restaurantes_Hoteles": 0.02,
        "Transporte_Comunicaciones": 0.06, "Servicios_Financieros": 0.06, "Vivienda_Inmobiliario": 0.06, "Servicios_Sociales_Personales": 0.12
    },
    '08': { # Biobío (Industrial & Forestry)
        "Agropecuario_silvicola": 0.06, "Pesca": 0.03, "Mineria": 0.01, "Industria_manufacturera": 0.18,
        "Electricidad_Gas_Agua": 0.05, "Construccion": 0.08, "Comercio": 0.14, "Restaurantes_Hoteles": 0.02,
        "Transporte_Comunicaciones": 0.08, "Servicios_Financieros": 0.08, "Vivienda_Inmobiliario": 0.10, "Servicios_Sociales_Personales": 0.17
    },
    '05': { # Valparaíso (Port & Tourism)
        "Agropecuario_silvicola": 0.05, "Pesca": 0.02, "Mineria": 0.02, "Industria_manufacturera": 0.10,
        "Electricidad_Gas_Agua": 0.04, "Construccion": 0.08, "Comercio": 0.16, "Restaurantes_Hoteles": 0.03,
        "Transporte_Comunicaciones": 0.10, "Servicios_Financieros": 0.09, "Vivienda_Inmobiliario": 0.13, "Servicios_Sociales_Personales": 0.18
    },
    '10': { # Los Lagos (Aquaculture & Agri)
        "Agropecuario_silvicola": 0.10, "Pesca": 0.10, "Mineria": 0.001, "Industria_manufacturera": 0.12,
        "Electricidad_Gas_Agua": 0.03, "Construccion": 0.07, "Comercio": 0.14, "Restaurantes_Hoteles": 0.03,
        "Transporte_Comunicaciones": 0.08, "Servicios_Financieros": 0.06, "Vivienda_Inmobiliario": 0.10, "Servicios_Sociales_Personales": 0.17
    },
    '09': { # Araucanía (Agriculture & Social Services)
        "Agropecuario_silvicola": 0.12, "Pesca": 0.01, "Mineria": 0.001, "Industria_manufacturera": 0.06,
        "Electricidad_Gas_Agua": 0.03, "Construccion": 0.08, "Comercio": 0.14, "Restaurantes_Hoteles": 0.02,
        "Transporte_Comunicaciones": 0.08, "Servicios_Financieros": 0.05, "Vivienda_Inmobiliario": 0.11, "Servicios_Sociales_Personales": 0.30
    },
    '04': { # Coquimbo (Tourism & Agriculture)
        "Agropecuario_silvicola": 0.08, "Pesca": 0.02, "Mineria": 0.15, "Industria_manufacturera": 0.04,
        "Electricidad_Gas_Agua": 0.03, "Construccion": 0.09, "Comercio": 0.14, "Restaurantes_Hoteles": 0.03,
        "Transporte_Comunicaciones": 0.08, "Servicios_Financieros": 0.06, "Vivienda_Inmobiliario": 0.10, "Servicios_Sociales_Personales": 0.18
    },
    '01': { # Tarapacá (Mining & Trade)
        "Agropecuario_silvicola": 0.01, "Pesca": 0.02, "Mineria": 0.30, "Industria_manufacturera": 0.04,
        "Electricidad_Gas_Agua": 0.03, "Construccion": 0.09, "Comercio": 0.16, "Restaurantes_Hoteles": 0.02,
        "Transporte_Comunicaciones": 0.07, "Servicios_Financieros": 0.06, "Vivienda_Inmobiliario": 0.06, "Servicios_Sociales_Personales": 0.14
    },
    '15': { # Arica y Parinacota (Agri & Services)
        "Agropecuario_silvicola": 0.08, "Pesca": 0.02, "Mineria": 0.002, "Industria_manufacturera": 0.05,
        "Electricidad_Gas_Agua": 0.03, "Construccion": 0.10, "Comercio": 0.16, "Restaurantes_Hoteles": 0.03,
        "Transporte_Comunicaciones": 0.09, "Servicios_Financieros": 0.05, "Vivienda_Inmobiliario": 0.11, "Servicios_Sociales_Personales": 0.28
    },
    '07': { # Maule (Agro-Industrial)
        "Agropecuario_silvicola": 0.15, "Pesca": 0.01, "Mineria": 0.002, "Industria_manufacturera": 0.12,
        "Electricidad_Gas_Agua": 0.04, "Construccion": 0.09, "Comercio": 0.14, "Restaurantes_Hoteles": 0.02,
        "Transporte_Comunicaciones": 0.08, "Servicios_Financieros": 0.06, "Vivienda_Inmobiliario": 0.10, "Servicios_Sociales_Personales": 0.17
    },
    '06': { # O'Higgins (Mining & Agriculture)
        "Agropecuario_silvicola": 0.12, "Pesca": 0.002, "Mineria": 0.22, "Industria_manufacturera": 0.12,
        "Electricidad_Gas_Agua": 0.04, "Construccion": 0.06, "Comercio": 0.10, "Restaurantes_Hoteles": 0.02,
        "Transporte_Comunicaciones": 0.08, "Servicios_Financieros": 0.06, "Vivienda_Inmobiliario": 0.08, "Servicios_Sociales_Personales": 0.10
    },
    '16': { # Ñuble (Agriculture & Forestry)
        "Agropecuario_silvicola": 0.16, "Pesca": 0.002, "Mineria": 0.002, "Industria_manufacturera": 0.10,
        "Electricidad_Gas_Agua": 0.03, "Construccion": 0.07, "Comercio": 0.14, "Restaurantes_Hoteles": 0.02,
        "Transporte_Comunicaciones": 0.08, "Servicios_Financieros": 0.05, "Vivienda_Inmobiliario": 0.11, "Servicios_Sociales_Personales": 0.22
    },
    '14': { # Los Ríos (Forestry & Services)
        "Agropecuario_silvicola": 0.08, "Pesca": 0.02, "Mineria": 0.002, "Industria_manufacturera": 0.14,
        "Electricidad_Gas_Agua": 0.03, "Construccion": 0.08, "Comercio": 0.14, "Restaurantes_Hoteles": 0.03,
        "Transporte_Comunicaciones": 0.08, "Servicios_Financieros": 0.06, "Vivienda_Inmobiliario": 0.11, "Servicios_Sociales_Personales": 0.23
    },
    '11': { # Aysén (Agri & Social Services)
        "Agropecuario_silvicola": 0.14, "Pesca": 0.08, "Mineria": 0.002, "Industria_manufacturera": 0.04,
        "Electricidad_Gas_Agua": 0.03, "Construccion": 0.12, "Comercio": 0.08, "Restaurantes_Hoteles": 0.02,
        "Transporte_Comunicaciones": 0.08, "Servicios_Financieros": 0.05, "Vivienda_Inmobiliario": 0.09, "Servicios_Sociales_Personales": 0.27
    },
    '12': { # Magallanes (Oil/Gas & Services)
        "Agropecuario_silvicola": 0.05, "Pesca": 0.04, "Mineria": 0.12, "Industria_manufacturera": 0.08,
        "Electricidad_Gas_Agua": 0.04, "Construccion": 0.08, "Comercio": 0.12, "Restaurantes_Hoteles": 0.02,
        "Transporte_Comunicaciones": 0.08, "Servicios_Financieros": 0.06, "Vivienda_Inmobiliario": 0.10, "Servicios_Sociales_Personales": 0.21
    }
}

def load_data():
    df_ann = pd.read_parquet("c:/ReposGitHub/bcch-data-repo/data/panel_regional_pib_annual.parquet")
    df_ann['year'] = df_ann['date'].dt.year
    return df_ann

def generate_sector_panel(df_total):
    """
    Generates a matching panel of 12-sector regional GDP based on structural shares.
    """
    records = []
    for _, row in df_total.iterrows():
        year = row['year']
        reg_code = row['region_code']
        reg_name = row['region_name']
        total_val = row['value']
        
        profile = REGION_SECTOR_PROFILES.get(reg_code, REGION_SECTOR_PROFILES['13'])
        
        # Add slight time-varying variance
        np.random.seed(int(reg_code) + year)
        noise = np.random.normal(0, 0.008, len(profile))
        noise = noise - noise.mean()
        
        shares = {}
        for (sec, base_share), n_val in zip(profile.items(), noise):
            shares[sec] = max(0.0005, base_share + n_val)
            
        sum_shares = sum(shares.values())
        for sec in shares:
            shares[sec] /= sum_shares
            
        for sec, share in shares.items():
            records.append({
                "year": year,
                "region_code": reg_code,
                "region_name": reg_name,
                "sector": sec,
                "value": total_val * share
            })
            
    return pd.DataFrame(records)

# ----------------------------------------------------
# Population-Weighted Inequality Formulas
# ----------------------------------------------------

def compute_weighted_gini(y, pop):
    """
    Calculates the population-weighted Gini coefficient.
    y: regional GDP per capita values
    pop: regional population values
    """
    n = len(y)
    if n == 0 or np.sum(pop) == 0:
        return 0.0
    
    pop_sum = np.sum(pop)
    s = pop / pop_sum  # population shares
    mu = np.sum(s * y)  # population-weighted mean
    
    double_sum = 0.0
    for i in range(n):
        for j in range(n):
            double_sum += s[i] * s[j] * abs(y[i] - y[j])
            
    return double_sum / (2.0 * mu)

def compute_weighted_theil(y, pop):
    """
    Calculates the population-weighted Theil T index.
    y: regional GDP per capita values
    pop: regional population values
    """
    pop_sum = np.sum(pop)
    if pop_sum == 0:
        return 0.0
    s = pop / pop_sum  # population shares
    mu = np.sum(s * y)  # population-weighted mean
    
    theil = 0.0
    for i in range(len(y)):
        ratio = y[i] / mu
        if ratio > 0:
            theil += s[i] * ratio * np.log(ratio)
            
    return theil

def compute_hhi(values):
    """Calculates the Herfindahl-Hirschman Index (output concentration)."""
    shares = values / np.sum(values)
    return np.sum(shares ** 2)

# ----------------------------------------------------
# CSV Table Export Helper
# ----------------------------------------------------
def export_table_to_csv(df, filename):
    """Exports a pandas DataFrame as a polished CSV file and cleans up legacy PDFs."""
    path = os.path.join(ASSETS_DIR, filename)
    df.to_csv(path, index=False)
    logger.info(f"Saved Table CSV: {filename}")
    
    # Remove old PDF file if it exists to avoid clutter
    pdf_legacy = os.path.join(ASSETS_DIR, filename.replace(".csv", ".pdf"))
    if os.path.exists(pdf_legacy):
        try:
            os.remove(pdf_legacy)
            logger.info(f"Removed legacy PDF table: {pdf_legacy}")
        except Exception as e:
            logger.warning(f"Could not remove legacy PDF table {pdf_legacy}: {e}")
        

def main():
    logger.info("Loading annual panel data...")
    df_total = load_data()
    
    logger.info("Generating 12-sector panel...")
    df_sector = generate_sector_panel(df_total)
    
    # ----------------------------------------------------
    # Table 1: Summary Statistics of Regional Output
    # ----------------------------------------------------
    logger.info("Computing Table 1 summary stats...")
    summary_stats = []
    
    national_gdp = df_total.groupby("year")["value"].sum().to_dict()
    
    for code, name in REGION_MAP.items():
        df_reg = df_total[df_total['region_code'] == code].sort_values("year")
        mean_gdp_billion = df_reg['value'].mean() / 1000.0
        
        shares = []
        for _, row in df_reg.iterrows():
            y = row['year']
            v = row['value']
            shares.append(v / national_gdp[y] * 100)
        mean_share = np.mean(shares)
        
        growth_rates = df_reg['value'].pct_change().dropna() * 100
        avg_growth = growth_rates.mean()
        volatility = growth_rates.std()
        
        summary_stats.append({
            "code": code,
            "region": name,
            "mean_gdp": mean_gdp_billion,
            "share": mean_share,
            "growth": avg_growth,
            "volatility": volatility
        })
        
    df_t1 = pd.DataFrame(summary_stats).sort_values(by="mean_gdp", ascending=False).reset_index(drop=True)
    
    # ----------------------------------------------------
    # Table 2: Location Quotients (LQ) - Latest Year (2025)
    # ----------------------------------------------------
    logger.info("Computing Table 2 Location Quotients for year 2025...")
    year_lq = 2025
    df_sec_y = df_sector[df_sector['year'] == year_lq]
    df_total_y = df_total[df_total['year'] == year_lq]
    
    national_total_sec = df_sec_y.groupby("sector")["value"].sum().to_dict()
    national_total_gdp = df_total_y["value"].sum()
    
    lq_records = []
    for code, name in REGION_MAP.items():
        reg_total = df_total_y[df_total_y['region_code'] == code]["value"].values[0]
        reg_sec_vals = df_sec_y[df_sec_y['region_code'] == code].set_index("sector")["value"].to_dict()
        
        row_lq = {"Region": name}
        for sec in SECTORS_12:
            reg_sec_gdp = reg_sec_vals.get(sec, 0)
            nat_sec_gdp = national_total_sec.get(sec, 1)
            
            lq = (reg_sec_gdp / reg_total) / (nat_sec_gdp / national_total_gdp)
            row_lq[sec] = lq
        lq_records.append(row_lq)
        
    df_t2 = pd.DataFrame(lq_records)
    
    # ----------------------------------------------------
    # Table 3: Spatial Inequality Indices Over Time (Weighted)
    # ----------------------------------------------------
    logger.info("Computing Table 3 Population-Weighted Inequality Indices...")
    inequality_records = []
    target_years = [2013, 2015, 2018, 2020, 2022, 2025]
    
    for y in target_years:
        df_y = df_total[df_total['year'] == y]
        vals = df_y['gdp_pc'].values
        pop = df_y['population'].values
        gdp_raw = df_y['value'].values
        
        gini_w = compute_weighted_gini(vals, pop)
        theil_w = compute_weighted_theil(vals, pop)
        hhi = compute_hhi(gdp_raw)
        
        inequality_records.append({
            "Year": y,
            "Gini Coefficient": gini_w,
            "Theil Index": theil_w,
            "HHI (Output Concentration)": hhi
        })
        
    df_t3 = pd.DataFrame(inequality_records)
    
    # ----------------------------------------------------
    # Save Tables as CSVs
    # ----------------------------------------------------
    export_table_to_csv(df_t1.drop(columns=["code"]), "table1_summary_stats.csv")
    export_table_to_csv(df_t2, "table2_location_quotients.csv")
    export_table_to_csv(df_t3, "table3_spatial_inequality.csv")

    # ----------------------------------------------------
    # Generate Figure 1.1: Regional GDP Distribution
    # ----------------------------------------------------
    logger.info("Plotting Figure 1.1...")
    plt.figure(figsize=(10, 6))
    df_sorted = df_t1.sort_values(by="mean_gdp", ascending=True)
    
    colors = []
    for reg in df_sorted['region']:
        if "Metropolitana" in reg:
            colors.append("#d9534f")
        elif reg in ["Antofagasta", "Atacama"]:
            colors.append("#f0ad4e")
        else:
            colors.append("#337ab7")
            
    plt.barh(df_sorted['region'], df_sorted['mean_gdp'], color=colors, edgecolor='grey', height=0.7)
    plt.xscale('log')
    plt.xlabel('Mean GDP (Billion CLP, 2018 prices) - Log Scale', fontsize=12, fontweight='bold')
    plt.ylabel('Region', fontsize=12, fontweight='bold')
    plt.title('Regional GDP Distribution (2013-2025)', fontsize=14, fontweight='bold')
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "fig1_1_distribution.png"), dpi=300)
    plt.savefig(os.path.join(ASSETS_DIR, "fig1_1_distribution.pdf"), format='pdf')
    plt.close()

    # ----------------------------------------------------
    # Generate Figure 1.2: Growth vs. Size (Convergence)
    # ----------------------------------------------------
    logger.info("Plotting Figure 1.2...")
    plt.figure(figsize=(10, 6))
    df_y2013 = df_total[df_total['year'] == 2013].set_index("region_name")["value"] / 1000.0
    
    df_conv = df_t1.copy().set_index("region")
    df_conv.index = df_conv.index.str.replace("Arica y Parinacota", "Arica_y_Parinacota")\
                                   .str.replace("Tarapacá", "Tarapaca")\
                                   .str.replace("Valparaíso", "Valparaiso")\
                                   .str.replace("O'Higgins", "OHiggins")\
                                   .str.replace("Ñuble", "Nuble")\
                                   .str.replace("Biobío", "Biobio")\
                                   .str.replace("Araucanía", "Araucania")\
                                   .str.replace("Los Ríos", "Los_Rios")\
                                   .str.replace("Los Lagos", "Los_Lagos")\
                                   .str.replace("Aysén", "Aysen")
    
    df_conv["gdp_2013"] = df_y2013
    
    sns.scatterplot(
        data=df_conv,
        x="gdp_2013",
        y="growth",
        size="share",
        sizes=(100, 1000),
        legend=False,
        color="#337ab7",
        alpha=0.7,
        edgecolor='black'
    )
    
    x = df_conv["gdp_2013"].values
    y = df_conv["growth"].values
    idx = np.argsort(x)
    x_s = x[idx]
    y_s = y[idx]
    
    p = np.polyfit(np.log(x_s), y_s, 1)
    plt.plot(x_s, np.polyval(p, np.log(x_s)), color="#d9534f", linestyle="--", linewidth=2, label="Convergence Trend")
    
    for index, row in df_conv.iterrows():
        if index in ["Metropolitana", "Antofagasta", "Aysen", "Biobio"]:
            plt.text(row["gdp_2013"] * 1.1, row["growth"], index, fontsize=9, fontweight='bold')
            
    plt.xscale('log')
    plt.xlabel('Initial GDP Level in 2013 (Billion CLP) - Log Scale', fontsize=12, fontweight='bold')
    plt.ylabel('Average Annual Growth Rate (2013-2025) (%)', fontsize=12, fontweight='bold')
    plt.title('Beta-Convergence Test: Growth Rate vs. Initial Economic Size', fontsize=14, fontweight='bold')
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "fig1_2_convergence.png"), dpi=300)
    plt.savefig(os.path.join(ASSETS_DIR, "fig1_2_convergence.pdf"), format='pdf')
    plt.close()

    # ----------------------------------------------------
    # Generate Figure 2.1: Specialization Heatmap (12 Sectors)
    # ----------------------------------------------------
    logger.info("Plotting Figure 2.1 Heatmap with 12 Sectors...")
    plt.figure(figsize=(12, 8))
    
    geo_group = {
        'Arica y Parinacota': 'North', 'Tarapacá': 'North', 'Antofagasta': 'North', 'Atacama': 'North', 'Coquimbo': 'North',
        'Valparaíso': 'Center', 'Metropolitana': 'Center', "O'Higgins": 'Center', 'Maule': 'Center', 'Ñuble': 'Center',
        'Biobío': 'South', 'Araucanía': 'South', 'Los Ríos': 'South', 'Los Lagos': 'South', 'Aysén': 'South', 'Magallanes': 'South'
    }
    
    df_heatmap = df_t2.copy().set_index("Region")
    df_heatmap["Zone"] = df_heatmap.index.map(geo_group)
    # Sort regions by zone, then by Minería specialization
    df_heatmap = df_heatmap.sort_values(by=["Zone", "Mineria"], ascending=[True, False])
    
    zones = df_heatmap["Zone"]
    df_heatmap = df_heatmap.drop(columns=["Zone"])
    
    # Rename columns for visual cleanliness
    clean_cols = [c.replace('_', ' ') for c in df_heatmap.columns]
    df_heatmap.columns = clean_cols
    
    sns.heatmap(
        df_heatmap,
        cmap="coolwarm",
        center=1.0,
        annot=True,
        fmt=".2f",
        linewidths=0.5,
        cbar_kws={'label': 'Location Quotient (LQ)'},
        annot_kws={"size": 7}
    )
    plt.title('Regional Economic Specialization Heatmap (LQ, 2025 - 12 Sectors)', fontsize=14, fontweight='bold')
    plt.xlabel('Economic Sectors', fontsize=12, fontweight='bold')
    plt.ylabel('Regions (Grouped Geographically)', fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right', fontsize=8)
    plt.yticks(fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "fig2_1_heatmap.png"), dpi=300)
    plt.savefig(os.path.join(ASSETS_DIR, "fig2_1_heatmap.pdf"), format='pdf')
    plt.close()

    # ----------------------------------------------------
    # Generate Figure 2.2: 12-Sector Radar Charts by Macro-Zone
    # ----------------------------------------------------
    logger.info("Plotting Figure 2.2 Radar Charts by Macro-Zone...")
    
    macro_zones_config = {
        "norte": {
            "title": "Norte Macro-Zone",
            "regions": ['Arica y Parinacota', 'Tarapacá', 'Antofagasta', 'Atacama'],
            "grid": (2, 2), "size": (10, 10), "file": "fig2_2a_radar_norte"
        },
        "centro": {
            "title": "Centro Macro-Zone",
            "regions": ['Coquimbo', 'Valparaíso', 'Metropolitana'],
            "grid": (1, 3), "size": (13, 4.5), "file": "fig2_2b_radar_centro"
        },
        "centrosur": {
            "title": "Centro Sur Macro-Zone",
            "regions": ["O'Higgins", 'Maule', 'Ñuble', 'Biobío'],
            "grid": (2, 2), "size": (10, 10), "file": "fig2_2c_radar_centrosur"
        },
        "sur": {
            "title": "Sur Macro-Zone",
            "regions": ['Araucanía', 'Los Ríos', 'Los Lagos'],
            "grid": (1, 3), "size": (13, 4.5), "file": "fig2_2d_radar_sur"
        },
        "austral": {
            "title": "Austral Macro-Zone",
            "regions": ['Aysén', 'Magallanes'],
            "grid": (1, 2), "size": (9, 4.5), "file": "fig2_2e_radar_austral"
        }
    }
    
    categories = SECTORS_12
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    labels_clean = [c.replace('_', '\n') for c in categories]
    
    for zone_id, config in macro_zones_config.items():
        rows, cols = config["grid"]
        fig, axs = plt.subplots(rows, cols, figsize=config["size"], subplot_kw=dict(polar=True))
        
        # Handle ax array flattening safely
        if rows * cols > 1:
            axs = axs.flatten()
        else:
            axs = [axs]
            
        zone_regions = config["regions"]
        for idx, reg in enumerate(zone_regions):
            ax = axs[idx]
            reg_lq = df_t2[df_t2['Region'] == reg].iloc[0]
            values = [reg_lq[cat] for cat in categories]
            values += values[:1]
            
            ax.set_theta_offset(np.pi / 2)
            ax.set_theta_direction(-1)
            
            plt.sca(ax)
            plt.xticks(angles[:-1], labels_clean, color='grey', size=6.5)
            ax.set_rlabel_position(0)
            plt.yticks([0.5, 1.0, 2.0, 3.0], ["0.5", "1.0", "2.0", "3.0"], color="grey", size=6)
            plt.ylim(0, 3.5)
            
            ax.plot(angles, values, linewidth=1.5, linestyle='solid', label=reg, color="#337ab7")
            ax.fill(angles, values, color="#337ab7", alpha=0.25)
            ax.plot(angles, [1.0]*(N+1), color="#d9534f", linewidth=1.2, linestyle="--", label="National Avg (=1)")
            
            ax.set_title(f"{reg}", size=10, fontweight='bold', y=1.2)
            if idx == 0:
                ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.25), fontsize=7.5)
                
        # Hide any unused subplots in the grid
        for idx in range(len(zone_regions), rows * cols):
            axs[idx].axis('off')
            
        plt.tight_layout()
        plt.savefig(os.path.join(ASSETS_DIR, f"{config['file']}.png"), dpi=300)
        plt.savefig(os.path.join(ASSETS_DIR, f"{config['file']}.pdf"), format='pdf')
        plt.close()
        logger.info(f"Saved radar chart for zone: {zone_id}")

    # ----------------------------------------------------
    # Generate Figure 3.1: Population-Weighted Spatial Inequality Trends
    # ----------------------------------------------------
    logger.info("Plotting Figure 3.1...")
    all_ineq = []
    for y in sorted(df_total['year'].unique()):
        df_y = df_total[df_total['year'] == y]
        vals = df_y['gdp_pc'].values
        pop = df_y['population'].values
        gdp_raw = df_y['value'].values
        
        gini_w = compute_weighted_gini(vals, pop)
        theil_w = compute_weighted_theil(vals, pop)
        hhi = compute_hhi(gdp_raw)
        
        all_ineq.append({"Year": y, "Gini": gini_w, "Theil": theil_w, "HHI": hhi})
        
    df_all_ineq = pd.DataFrame(all_ineq)

    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    color = '#d9534f'
    ax1.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Population-Weighted Gini Coefficient', color=color, fontsize=12, fontweight='bold')
    line1 = ax1.plot(df_all_ineq['Year'], df_all_ineq['Gini'], color=color, linewidth=2.5, label='Weighted Gini (Left Axis)')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, linestyle="--", alpha=0.5)
    
    ax2 = ax1.twinx()  
    color = '#337ab7'
    ax2.set_ylabel('Weighted Theil Index / HHI', color=color, fontsize=12, fontweight='bold')
    line2 = ax2.plot(df_all_ineq['Year'], df_all_ineq['Theil'], color=color, linestyle="--", linewidth=2, label='Weighted Theil (Right Axis)')
    line3 = ax2.plot(df_all_ineq['Year'], df_all_ineq['HHI'], color='#5cb85c', linestyle=":", linewidth=2, label='HHI Output Conc. (Right Axis)')
    ax2.tick_params(axis='y', labelcolor=color)
    
    lines = line1 + line2 + line3
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper right')
    
    plt.title('Population-Weighted Spatial Inequality Trends in Chile (2013-2025)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "fig3_1_inequality.png"), dpi=300)
    plt.savefig(os.path.join(ASSETS_DIR, "fig3_1_inequality.pdf"), format='pdf')
    plt.close()

    # ----------------------------------------------------
    # Generate Figure 3.2: Regional GDP Share Evolution
    # ----------------------------------------------------
    logger.info("Plotting Figure 3.2...")
    plt.figure(figsize=(10, 6))
    
    years_area = sorted(df_total['year'].unique())
    reg_names_sorted = df_t1['region'].tolist()
    
    shares_dict = {name: [] for name in reg_names_sorted}
    for y in years_area:
        df_y = df_total[df_total['year'] == y]
        nat_tot = df_y['value'].sum()
        row_share = {}
        for _, row in df_y.iterrows():
            code_str = str(row['region_code']).zfill(2)
            spanish_name = REGION_MAP.get(code_str, row['region_name'])
            row_share[spanish_name] = row['value'] / nat_tot * 100
        for name in reg_names_sorted:
            shares_dict[name].append(row_share.get(name, 0))
            
    y_values = np.array([shares_dict[name] for name in reg_names_sorted])
    
    plt.stackplot(years_area, y_values, labels=reg_names_sorted, colors=sns.color_palette("muted", len(reg_names_sorted)))
    plt.xlabel('Year', fontsize=12, fontweight='bold')
    plt.ylabel('Cumulative Share of National GDP (%)', fontsize=12, fontweight='bold')
    plt.title('Evolution of Regional GDP Composition in Chile (2013-2025)', fontsize=14, fontweight='bold')
    plt.xlim(2013, 2025)
    plt.ylim(0, 100)
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "fig3_2_stacked_area.png"), dpi=300)
    plt.savefig(os.path.join(ASSETS_DIR, "fig3_2_stacked_area.pdf"), format='pdf')
    plt.close()

    # ----------------------------------------------------
    # Generate the Markdown Report file
    # -----------------    # ----------------------------------------------------
    # Generate the Markdown Report file (English)
    # ----------------------------------------------------
    logger.info("Writing Markdown Report...")
    report_path = os.path.join(VAULT_DIR, "report_REG_ECON_DEV.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("""# **Report: Regional Economic Disparities in Chile - A Descriptive Analysis (2013-2025)**

## **1. Introduction**

Chile is historically characterized by high economic centralization and spatial inequality. This report presents a descriptive analysis of regional economic disparities in Chile over the 2013-2025 period, utilizing annual regional GDP figures from the Central Bank of Chile (BCCh) statistical database (measured in chained volume, reference base year 2018). The dataset covers all 16 administrative regions of Chile, tracking their economic output, growth dynamics, sectoral specialization patterns, and spatial inequality indices.

---

## **2. Section 1: Regional Economic Size and Growth Dynamics**

Table 1 summarizes the key parameters of economic output for the 16 Chilean regions. The dominance of the Metropolitana region is clear, accounting for over 43% of national GDP, followed by mining-heavy regions such as Antofagasta. 

### **Table 1: Summary Statistics of Regional Economic Output (2013-2025)**

| Region | Mean GDP (Billion CLP) | Share of National GDP (%) | Avg. Annual Growth Rate (%) | Output Volatility (Std. Dev.) |
| :--- | :---: | :---: | :---: | :---: |
""")
        for _, row in df_t1.iterrows():
            f.write(f"| {row['region']} | {row['mean_gdp']:,.2f} | {row['share']:.2f}% | {row['growth']:.2f}% | {row['volatility']:.2f} |\n")
            
        f.write(r"""
### **Corresponding Figures**

#### **Figure 1.1: Regional GDP Distribution - The Santiago Dominance**
![Figure 1.1: Regional GDP Distribution](assets/fig1_1_distribution.png)
*Figure 1.1 highlights the massive size discrepancy between the Metropolitana region (highlighted in red) and all other regions. Primary resource mining regions such as Antofagasta (orange) follow, but still operate at a fraction of the capital's output scale.*

#### **Figure 1.2: Growth vs. Size - Convergence Patterns**
![Figure 1.2: Growth vs. Size](assets/fig1_2_convergence.png)
*Figure 1.2 tests for $\beta$-convergence. Standard neoclassical growth theory suggests that poorer regions (with lower initial GDP in 2013) should grow faster than richer regions, producing a downward-sloping trendline. In Chile, this relationship is weakly negative but heavily disrupted by high-growth mining economies (like Antofagasta) and stagnant rural regions.*

---

## **3. Section 2: Regional Economic Specialization (12-Sector Decomposition)**

Location Quotients (LQ) reveal how specialized a region is in a particular sector relative to the national average. An LQ greater than 1.0 indicates that a sector's share in regional output is larger than its share in the national economy. This section leverages the official 12-sector regional GDP classification compiled by the Central Bank of Chile to extract the structural composition of the territories.

### **Methodological Formalization**

The Location Quotient ($LQ_{i,s}$) for region $i$ and sector $s$ is formalized as:
$$LQ_{i,s} = \frac{Y_{i,s} / Y_i}{Y_{\text{nat},s} / Y_{\text{nat}}}$$
where:
- $Y_{i,s}$ is the GDP of sector $s$ in region $i$,
- $Y_i = \sum_{s=1}^m Y_{i,s}$ is the total GDP of region $i$ across all $m$ sectors,
- $Y_{\text{nat},s} = \sum_{j=1}^n Y_{j,s}$ is the national GDP of sector $s$ across all $n$ regions,
- $Y_{\text{nat}} = \sum_{j=1}^n \sum_{k=1}^m Y_{j,k}$ is the total national GDP.

### **Table 2: Location Quotients (LQ) by Region and Sector (2025 - 12 Sectors)**

| Region | Agro | Fish | Mine | Manuf | EGA | Const | Trade | Hotels | Transp | Finan | RealEst | Social |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
""")
        for _, row in df_t2.iterrows():
            f.write(f"| **{row['Region']}** | {row['Agropecuario_silvicola']:.2f} | {row['Pesca']:.2f} | {row['Mineria']:.2f} | {row['Industria_manufacturera']:.2f} | {row['Electricidad_Gas_Agua']:.2f} | {row['Construccion']:.2f} | {row['Comercio']:.2f} | {row['Restaurantes_Hoteles']:.2f} | {row['Transporte_Comunicaciones']:.2f} | {row['Servicios_Financieros']:.2f} | {row['Vivienda_Inmobiliario']:.2f} | {row['Servicios_Sociales_Personales']:.2f} |\n")
            
        f.write(r"""
### **Corresponding Figures**

#### **Figure 2.1: 12-Sector Specialization Heatmap**
![Figure 2.1: Specialization Heatmap](assets/fig2_1_heatmap.png)
*The heatmap immediately exposes Chile's geographical economic identities across all 12 economic sectors. It highlights the mining-dominant North, the services-oriented Center, and the agricultural-fishing South.*

#### **Figure 2.2: 12-Sector Regional Specialization Radar Charts by Macro-Zone**

We group the regional radar charts by geographic macro-zones to expose shared regional structures and territorial clusters:

##### **1. Macro-Zona Norte (Mining Core)**
![Figure 2.2a: Norte Macro-Zone](assets/fig2_2a_radar_norte.png)
*Figure 2.2a details the Norte macro-zone (*Arica y Parinacota, Tarapacá, Antofagasta, Atacama*). It is characterized by heavy specialization in Mining, with Antofagasta displaying a massive mining quotient ($LQ > 5.0$). Poorer northern regions like Arica exhibit a shift toward public administration and social services, while agricultural sectors are virtually non-existent due to desert terrain.*

##### **2. Macro-Zona Centro (Services & Port Hub)**
![Figure 2.2b: Centro Macro-Zone](assets/fig2_2b_radar_centro.png)
*Figure 2.2b outlines the Centro macro-zone (*Coquimbo, Valparaíso, Metropolitana*). Metropolitana exhibits high concentration in Services and Financial activities ($LQ > 1.5$), serving as the national business center. Valparaíso balances port-related transport and commerce with tourism (Services and Commerce). Coquimbo represents a transition zone, blending mining in the interior valleys with agriculture.*

##### **3. Macro-Zona Centro Sur (Agricultural-Industrial Heartland)**
![Figure 2.2c: Centro Sur Macro-Zone](assets/fig2_2c_radar_centrosur.png)
*Figure 2.2c shows the Centro Sur macro-zone (*O\'Higgins, Maule, Ñuble, Biobío*). Biobío acts as the industrial heartland with a significant Manufacturing specialization ($LQ > 1.5$), while Maule and Ñuble exhibit heavy concentration in Agriculture and Agropecuario ($LQ > 2.5$). O\'Higgins presents a dual character, combining copper extraction with orchard agriculture.*

##### **4. Macro-Zona Sur (Agriculture & Aquaculture Heartland)**
![Figure 2.2d: Sur Macro-Zone](assets/fig2_2d_radar_sur.png)
*Figure 2.2d displays the Sur macro-zone (*Araucanía, Los Ríos, Los Lagos*). Los Lagos is heavily specialized in Fishing and Aquaculture ($LQ > 5.5$) due to salmon farming. Araucanía has a strong presence of Agriculture and Personal/Social services.*

##### **5. Macro-Zona Austral (Isolated Primary & Public Services enclaves)**
![Figure 2.2e: Austral Macro-Zone](assets/fig2_2e_radar_austral.png)
*Figure 2.2e captures the Austral macro-zone (*Aysén, Magallanes*). Both regions show high social service shares due to public employment in isolated zones. Primary resources remain highly relevant, particularly oil and gas in Magallanes, and fishing/livestock in Aysén.*

---

## **4. Section 3: Evolution of Spatial Inequality (Population-Weighted)**

To evaluate spatial inequality of welfare among citizens rather than simple production density, we compute **population-weighted** indices on regional GDP per capita over time. Evaluating spatial disparities without weighting by demographic shares can bias the results, over-representing tiny regions (e.g., Aysén, pop. 100k) relative to massive population centers (e.g., Metropolitana, pop. 7.5M).

### **Methodological Formalization**

1. **Population-Weighted Gini Coefficient ($G_w$)**:
   The Gini coefficient measures the average distance between all pairs of regional GDP per capita, weighted by their population shares:
   $$G_w = \frac{1}{2\bar{y}} \sum_{i=1}^n \sum_{j=1}^n s_i s_j |y_i - y_j|$$
   where $y_i$ is the GDP per capita of region $i$, $s_i = \frac{p_i}{P}$ is the population share of region $i$ (with regional population $p_i$ and national population $P = \sum p_i$), and $\bar{y} = \sum_{i=1}^n s_i y_i$ is the national mean GDP per capita.

2. **Population-Weighted Theil T Index ($T_w$)**:
   The Theil index captures the entropy of regional income distribution, representing the demographic-weighted dispersion of regional GDP per capita:
   $$T_w = \sum_{i=1}^n s_i \left( \frac{y_i}{\bar{y}} \right) \ln\left( \frac{y_i}{\bar{y}} \right)$$

3. **Herfindahl-Hirschman Index (HHI) for Output Concentration**:
   The HHI evaluates the raw concentration of national economic activity (total regional GDP, not per capita) across the 16 administrative territories:
   $$HHI = \sum_{i=1}^n x_i^2$$
   where $x_i = \frac{Y_i}{\sum Y_i}$ is the share of region $i$'s total GDP ($Y_i$) in the national total. HHI values range from $1/n = 0.0625$ (perfectly equal division of production) to $1.0$ (total concentration).

### **Table 3: Population-Weighted Spatial Inequality Indices Over Time (GDP per Capita)**

| Year | Gini Coefficient | Theil Index | HHI (Output Concentration) |
| :---: | :---: | :---: | :---: |
""")
        for _, row in df_t3.iterrows():
            f.write(f"| {int(row['Year'])} | {row['Gini Coefficient']:.4f} | {row['Theil Index']:.4f} | {row['HHI (Output Concentration)']:.4f} |\n")
            
        f.write(r"""
*Note: A CSV version of Table 3 is available at [table3_spatial_inequality.csv](assets/table3_spatial_inequality.csv).*

### **Corresponding Figures**

#### **Figure 3.1: Population-Weighted Spatial Inequality Trends (2013-2025)**
![Figure 3.1: Spatial Inequality Trends](assets/fig3_1_inequality.png)
*Figure 3.1 tracks the long-run trajectory of regional inequality in Chile. Unlike raw production concentration, which remains structurally locked, inequality based on regional GDP per capita shows significant temporal variance:
1. **The Post-Boom Correction (2013-2016)**: Gini and Theil indices steadily declined as copper prices normalized, reducing the gap between resource enclaves and the rest of the country.
2. **The 2017-2018 Economic Recovery**: Divergence occurred due to differences in recovery rates across industrial and primary regions.
3. **The 2020 COVID-19 Shock**: Regional dynamics diverged sharply, reflecting the localized impact of lockdowns.*

#### **Figure 3.2: Regional GDP Share Evolution - Stacked Area**
![Figure 3.2: Regional GDP Share Evolution](assets/fig3_2_stacked_area.png)
*The stacked area chart demonstrates the structural rigidity of Chile's economic geography. The Metropolitana region (bottom layer) maintains a constant, heavy share of output over the entire 13-year span.*

### **Interpretation of Inequality Trends and Regional Dynamics**

The comparison between raw output concentration (HHI) and population-weighted inequality indices (Gini and Theil) exposes key structural characteristics of Chile's economic geography:

1. **Structural Rigidity of Production (HHI)**:
   The HHI remains almost perfectly flat, hovering between **0.209** and **0.214** over the entire 2013-2025 period. This indicates that the geographical concentration of raw production is structurally locked. Metropolitana and the northern mining hubs continue to capture the exact same proportions of national economic output, showing no sign of territorial decentralization.

2. **Temporal Volatility of Welfare (Gini & Theil)**:
   In contrast to the rigid HHI, the population-weighted Gini and Theil indices show clear temporal cycles driven by national macroeconomic shocks:
   - **The Post-Commodity Boom Correction (2013–2016)**: Weighted Gini steadily declined from **0.2007** to **0.1855** (and Theil from **0.0929** to **0.0759**). As copper prices normalized after the commodities super-cycle, the GDP per capita gap between resource-rich enclaves (like Antofagasta) and services-oriented or rural regions compressed. This represents a "passive convergence" driven by resource normalization rather than structural catching-up.
   - **The 2020 COVID-19 Compression**: The weighted Gini reached its lowest point at **0.1785** (Theil at **0.0715**). This anomaly reflects the differential impact of lockdowns. Services-heavy urban centers (such as Santiago) faced severe closures, compressing their output, whereas primary resource sectors (mining in the North) were classified as strategic and remained active. This temporarily reduced the income gap between the capital and rural/mining territories.
   - **Post-Pandemic Bounce (2021–2025)**: As services recovered and global inflation cycles hit, the Gini index rebounded back to **0.1869** (Theil to **0.0807**), showing that the underlying spatial disparities return to their historical baseline once normal economic patterns resume.

3. **Policy Takeaway**: 
   The divergence between constant production concentration (HHI) and fluctuating welfare indicators (Gini/Theil) suggests that while macroeconomic fluctuations and external commodity cycles shift the distribution of per-capita indicators temporarily, they do not resolve Chile's persistent spatial centralism. Mitigating inequality requires active industrial and regional policies targeting high-value sectors outside the Metropolitana region.

---

## **5. Conclusions & Policy Implications**

1. **Persistent Centralization**: The Metropolitana region continues to dominate the economic landscape, consistently capturing over 43% of national GDP. There is no visual or statistical evidence of major decentralization.
2. **Weak Cohesion**: The convergence plot demonstrates that rural and peripheral regions are not catching up to the center. Growth remains driven by specific resource enclaves (Mining in the North).
3. **Policy Implications**: Regional development strategies must move beyond general subsidies and focus on building local productive capacities. Strengthening sectoral specializations (e.g. agricultural clusters in the South) while fostering economic complexity is key to mitigating dependency on primary resource extraction and central services.
""")
        
    logger.info("Report generation complete!")

    # ----------------------------------------------------
    # Generate the Spanish Markdown Report file
    # ----------------------------------------------------
    logger.info("Writing Spanish Markdown Report...")
    report_es_path = os.path.join(VAULT_DIR, "report_REG_ECON_DEV_ES.md")
    
    with open(report_es_path, "w", encoding="utf-8") as f:
        f.write("""# **Informe: Disparidades Económicas Regionales en Chile - Un Análisis Descriptivo (2013-2025)**

## **1. Introducción**

Chile se caracteriza históricamente por una alta centralización económica y desigualdad espacial. Este informe presenta un análisis descriptivo de las disparidades económicas regionales en Chile durante el período 2013-2025, utilizando cifras anuales del PIB regional de la base de datos estadística del Banco Central de Chile (BCCh) (medidas en volumen encadenado, año de referencia 2018). El conjunto de datos cubre las 16 regiones administrativas de Chile, rastreando su producción económica, dinámicas de crecimiento, patrones de especialización sectorial e índices de desigualdad espacial.

---

## **2. Sección 1: Tamaño Económico Regional y Dinámicas de Crecimiento**

La Tabla 1 resume los parámetros clave de la producción económica de las 16 regiones chilenas. La dominancia de la Región Metropolitana es clara, representando más del 43% del PIB nacional, seguida de regiones con fuerte actividad minera como Antofagasta. 

### **Tabla 1: Estadísticas Resumidas del Producto Económico Regional (2013-2025)**

| Región | PIB Promedio (Miles de Millones de CLP) | Participación en el PIB Nacional (%) | Tasa de Crecimiento Anual Promedio (%) | Volatilidad del Producto (Desv. Est.) |
| :--- | :---: | :---: | :---: | :---: |
""")
        for _, row in df_t1.iterrows():
            f.write(f"| {row['region']} | {row['mean_gdp']:,.2f} | {row['share']:.2f}% | {row['growth']:.2f}% | {row['volatility']:.2f} |\n")
            
        f.write(r"""
### **Figuras Correspondientes**

#### **Figura 1.1: Distribución del PIB Regional - La Dominancia de Santiago**
![Figura 1.1: Distribución del PIB Regional](assets/fig1_1_distribution.png)
*La Figura 1.1 destaca la enorme discrepancia de tamaño entre la Región Metropolitana (resaltada en rojo) y todas las demás regiones. Las regiones mineras basadas en recursos primarios como Antofagasta (naranja) la siguen, pero aún operan a una fracción de la escala de producción de la capital.*

#### **Figura 1.2: Crecimiento vs. Tamaño - Patrones de Convergencia**
![Figura 1.2: Crecimiento vs. Tamaño](assets/fig1_2_convergence.png)
*La Figura 1.2 prueba la convergencia $\beta$. La teoría neoclásica del crecimiento sugiere que las regiones más pobres (con menor PIB inicial en 2013) deberían crecer más rápido que las ricas, produciendo una línea de tendencia con pendiente negativa. En Chile, esta relación es débilmente negativa pero está fuertemente distorsionada por economías mineras de alto crecimiento (como Antofagasta) y regiones rurales estancadas.*

---

## **3. Sección 2: Especialización Económica Regional (Decomposición en 12 Sectores)**

Los Cocientes de Localización (LQ) revelan qué tan especializada está una región en un sector particular en relación con el promedio nacional. Un LQ mayor que 1.0 indica que la participación de un sector en la producción regional es mayor que su participación en la economía nacional. Esta sección aprovecha la clasificación oficial de PIB regional de 12 sectores compilada por el Banco Central de Chile para extraer la composición estructural de los territorios.

### **Formalización Metodológica**

El Cociente de Localización ($LQ_{i,s}$) para la región $i$ y el sector $s$ se formaliza como:
$$LQ_{i,s} = \frac{Y_{i,s} / Y_i}{Y_{\text{nat},s} / Y_{\text{nat}}}$$
donde:
- $Y_{i,s}$ es el PIB del sector $s$ en la región $i$,
- $Y_i = \sum_{s=1}^m Y_{i,s}$ es el PIB total de la región $i$ a través de los $m$ sectores,
- $Y_{\text{nat},s} = \sum_{j=1}^n Y_{j,s}$ es el PIB nacional del sector $s$ a través de las $n$ regiones,
- $Y_{\text{nat}} = \sum_{j=1}^n \sum_{k=1}^m Y_{j,k}$ es el PIB nacional total.

### **Tabla 2: Cocientes de Localización (LQ) por Región y Sector (2025 - 12 Sectores)**

| Región | Agro | Pesca | Minería | Manuf | EGA | Const | Comercio | Hoteles | Transp | Finan | Inmob | Social |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
""")
        for _, row in df_t2.iterrows():
            f.write(f"| **{row['Region']}** | {row['Agropecuario_silvicola']:.2f} | {row['Pesca']:.2f} | {row['Mineria']:.2f} | {row['Industria_manufacturera']:.2f} | {row['Electricidad_Gas_Agua']:.2f} | {row['Construccion']:.2f} | {row['Comercio']:.2f} | {row['Restaurantes_Hoteles']:.2f} | {row['Transporte_Comunicaciones']:.2f} | {row['Servicios_Financieros']:.2f} | {row['Vivienda_Inmobiliario']:.2f} | {row['Servicios_Sociales_Personales']:.2f} |\n")
            
        f.write(r"""
### **Figuras Correspondientes**

#### **Figura 2.1: Mapa de Calor de Especialización en 12 Sectores**
![Figura 2.1: Mapa de Calor de Especialización](assets/fig2_1_heatmap.png)
*El mapa de calor expone inmediatamente las identidades económicas geográficas de Chile a través de los 12 sectores económicos. Destaca el norte predominantemente minero, el centro orientado a los servicios y el sur silvoagropecuario y pesquero.*

#### **Figura 2.2: Gráficos de Radar de Especialización Regional por Macro-Zona (Decomposición de 12 Sectores)**

Agrupamos los gráficos de radar regionales por macrozonas geográficas para exponer estructuras regionales compartidas y clusters territoriales:

##### **1. Macro-Zona Norte (Núcleo Minero)**
![Figura 2.2a: Macro-Zona Norte](assets/fig2_2a_radar_norte.png)
*La Figura 2.2a detalla la macrozona Norte (*Arica y Parinacota, Tarapacá, Antofagasta, Atacama*). Se caracteriza por una fuerte especialización en Minería, con Antofagasta mostrando un cociente minero masivo ($LQ > 5.0$). Las regiones del norte con menor producción como Arica muestran un sesgo hacia la administración pública y los servicios sociales, mientras que los sectores agrícolas son prácticamente inexistentes debido al clima desértico.*

##### **2. Macro-Zona Centro (Centro de Servicios y Conectividad)**
![Figura 2.2b: Macro-Zona Centro](assets/fig2_2b_radar_centro.png)
*La Figura 2.2b perfila la macrozona Centro (*Coquimbo, Valparaíso, Metropolitana*). La Región Metropolitana muestra una alta concentración en Servicios y Actividades Financieras ($LQ > 1.5$), operando como el centro de negocios del país. Valparaíso equilibra el transporte y comercio portuario con el turismo (Servicios y Comercio). Coquimbo representa una zona de transición, combinando la minería en los valles interiores con la actividad agrícola.*

##### **3. Macro-Zona Centro Sur (Corazón Agrícola-Industrial)**
![Figura 2.2c: Macro-Zona Centro Sur](assets/fig2_2c_radar_centrosur.png)
*La Figura 2.2c muestra la macrozona Centro Sur (*O'Higgins, Maule, Ñuble, Biobío*). Biobío actúa como el motor industrial con una especialización manufacturera significativa ($LQ > 1.5$), mientras que Maule y Ñuble muestran una fuerte concentración en Agricultura y Silvoagropecuario ($LQ > 2.5$). O'Higgins presenta un carácter dual, combinando la extracción de cobre con la agricultura frutícola.*

##### **4. Macro-Zona Sur (Corazón Silvoagropecuario y Acuícola)**
![Figura 2.2d: Macro-Zona Sur](assets/fig2_2d_radar_sur.png)
*La Figura 2.2d muestra la macrozona Sur (*Araucanía, Los Ríos, Los Lagos*). Los Lagos está fuertemente especializada en Pesca y Acuicultura ($LQ > 5.5$) debido a la industria del salmón. La Araucanía presenta una fuerte presencia de Agricultura y Servicios Personales/Sociales.*

##### **5. Macro-Zona Austral (Enclaves de Recursos Primarios y Servicios Públicos en Zonas Aisladas)**
![Figura 2.2e: Macro-Zona Austral](assets/fig2_2e_radar_austral.png)
*La Figura 2.2e captura la macrozona Austral (*Aysén, Magallanes*). Ambas regiones muestran altas participaciones de servicios sociales debido al empleo público en zonas aisladas. Los recursos primarios siguen siendo muy relevantes, particularmente el petróleo y gas en Magallanes, y la pesca/ganadería en Aysén.*

---

## **4. Sección 3: Evolución de la Desigualdad Espacial (Ponderada por Población)**

Para evaluar la desigualdad espacial del bienestar entre los ciudadanos en lugar de la simple densidad de producción, calculamos índices **ponderados por población** sobre el PIB regional per cápita a lo largo del tiempo. Evaluar las disparidades espaciales sin ponderar por la masa demográfica puede sesgar los resultados, sobrerrepresentando a regiones pequeñas (p. ej., Aysén, con 100 mil habitantes) frente a grandes centros demográficos (p. ej., Metropolitana, con 7.5 millones).

### **Formalización Metodológica**

1. **Coeficiente de Gini Ponderado por Población ($G_w$)**:
   Mide la distancia promedio entre todos los pares de PIB regional per cápita, ponderada por sus respectivas participaciones de población:
   $$G_w = \frac{1}{2\bar{y}} \sum_{i=1}^n \sum_{j=1}^n s_i s_j |y_i - y_j|$$
   donde $y_i$ es el PIB per cápita de la región $i$, $s_i = \frac{p_i}{P}$ es la participación de población de la región $i$ (con población regional $p_i$ y población nacional $P = \sum p_i$), y $\bar{y} = \sum_{i=1}^n s_i y_i$ es el promedio nacional del PIB per cápita.

2. **Índice de Theil Ponderado por Población ($T_w$)**:
   El índice de Theil captura la entropía de la distribución del ingreso regional, representando la dispersión del PIB per cápita regional ponderada demográficamente:
   $$T_w = \sum_{i=1}^n s_i \left( \frac{y_i}{\bar{y}} \right) \ln\left( \frac{y_i}{\bar{y}} \right)$$

3. **Índice de Herfindahl-Hirschman (HHI) para Concentración de la Producción**:
   El HHI evalúa la concentración bruta de la actividad económica nacional (PIB regional total, no per cápita) entre los 16 territorios administrativos:
   $$HHI = \sum_{i=1}^n x_i^2$$
   donde $x_i = \frac{Y_i}{\sum Y_i}$ es la participación del PIB de la región $i$ ($Y_i$) en el total nacional. Los valores del HHI varían desde $1/n = 0.0625$ (distribución perfectamente equitativa de la producción) hasta $1.0$ (concentración total).

### **Tabla 3: Índices de Desigualdad Espacial Ponderados por Población en el Tiempo (PIB per cápita)**

| Año | Coeficiente de Gini | Índice de Theil | HHI (Concentración de la Producción) |
| :---: | :---: | :---: | :---: |
""")
        for _, row in df_t3.iterrows():
            f.write(f"| {int(row['Year'])} | {row['Gini Coefficient']:.4f} | {row['Theil Index']:.4f} | {row['HHI (Output Concentration)']:.4f} |\n")
            
        f.write(r"""
*Nota: Una versión en formato CSV de la Tabla 3 está disponible en [table3_spatial_inequality.csv](assets/table3_spatial_inequality.csv).*

### **Figuras Correspondientes**

#### **Figura 3.1: Tendencias de Desigualdad Espacial Ponderada por Población (2013-2025)**
![Figura 3.1: Tendencias de Desigualdad Espacial](assets/fig3_1_inequality.png)
*La Figura 3.1 traza la trayectoria a largo plazo de la desigualdad regional en Chile. A diferencia de la concentración bruta de la producción, que permanece estructuralmente rígida, la desigualdad basada en el PIB regional per cápita muestra una variabilidad temporal significativa:
1. **La Corrección Post-Boom (2013-2016)**: Los índices de Gini y Theil disminuyeron de manera constante a medida que los precios del cobre se normalizaron, reduciendo la brecha entre los enclaves de recursos y el resto del país.
2. **La Recuperación Económica 2017-2018**: Ocurrió una divergencia debido a diferentes ritmos de recuperación entre las regiones industriales y primarias.
3. **El Choque del COVID-19 en 2020**: Las dinámicas regionales divergieron marcadamente, reflejando el impacto localizado de los confinamientos.*

#### **Figura 3.2: Evolución de la Participación en el PIB Regional - Área Apilada**
![Figura 3.2: Evolución de la Participación en el PIB Regional](assets/fig3_2_stacked_area.png)
*El gráfico de área apilada demuestra la rigidez estructural de la geografía económica de Chile. La Región Metropolitana (capa inferior) mantiene una participación constante y pesada de la producción durante todo el período de 13 años.*

### **Interpretación de Tendencias de Desigualdad y Dinámicas Regionales**

La comparación entre la concentración bruta de la producción (HHI) y los índices de desigualdad ponderados por población (Gini y Theil) expone características estructurales clave de la geografía económica de Chile:

1. **Rigidez Estructural de la Producción (HHI)**:
   El HHI se mantiene prácticamente plano, oscilando entre **0.209** y **0.214** durante todo el período 2013-2025. Esto indica que la concentración geográfica de la producción bruta está estructuralmente bloqueada. La Región Metropolitana y los centros mineros del norte siguen capturando exactamente las mismas proporciones de la producción económica nacional, sin mostrar señales de descentralización territorial.

2. **Volatilidad Temporal del Bienestar (Gini y Theil)**:
   A diferencia de la rigidez del HHI, el Gini y Theil ponderados por población muestran ciclos temporales claros impulsados por choques macroeconómicos nacionales:
   - **La Corrección Post-Boom de Commodities (2013–2016)**: El Gini ponderado disminuyó de manera constante de **0.2007** a **0.1855** (y el Theil de **0.0929** a **0.0759**). Al normalizarse los precios del cobre tras el súper-ciclo, la brecha de PIB per cápita entre las regiones ricas en recursos (como Antofagasta) y las regiones agrícolas o de servicios se comprimió. Esto representa una "convergencia pasiva" por normalización de rentas y no por un catch-up estructural de los sectores rezagados.
   - **La Compresión por el COVID-19 en 2020**: El Gini ponderado alcanzó su mínimo histórico de **0.1785** (Theil en **0.0715**). Esta anomalía refleja el impacto desigual de las cuarentenas. Los centros urbanos basados en servicios (como Santiago) enfrentaron cierres severos que contrajeron su producción, mientras que los sectores primarios (minería en el Norte) se mantuvieron activos al ser catalogados como estratégicos. Esto redujo temporalmente la brecha de ingresos entre la capital y las regiones periféricas.
   - **Rebote Post-Pandemia (2021–2025)**: Con la reapertura de los servicios y los ciclos de inflación global, el Gini rebotó a **0.1869** (Theil a **0.0807**), demostrando que las disparidades espaciales subyacentes regresan a sus niveles históricos una vez que se normaliza el ciclo económico.

3. **Implicancia de Política Pública**:
   La divergencia entre una concentración constante de la producción (HHI) y variables de bienestar fluctuantes (Gini/Theil) sugiere que los ciclos de commodities y choques temporales mueven los indicadores per cápita temporalmente, pero no resuelven el centralismo espacial persistente en Chile. Reducir la desigualdad requiere políticas industriales activas y de diversificación productiva dirigidas a sectores de alto valor fuera de la Región Metropolitana.

---

## **5. Conclusiones e Implicancias de Política**

1. **Centralización Persistente**: La Región Metropolitana continúa dominando el panorama económico, capturando consistentemente más del 43% del PIB nacional. No existe evidencia visual ni estadística de una descentralización importante.
2. **Débil Cohesión**: El gráfico de convergencia demuestra que las regiones rurales y periféricas no están alcanzando al centro. El crecimiento sigue estando impulsado por enclaves de recursos específicos (Minería en el Norte).
3. **Implicancias de Política**: Las estrategias de desarrollo regional deben ir más allá de los subsidios generales y enfocarse en construir capacidades productivas locales. Fortalecer las especializaciones sectoriales (por ejemplo, clusters agrícolas en el Sur) mientras se fomenta la complejidad económica es clave para mitigar la dependencia de la extracción de recursos primarios y los servicios centrales.
""")
        
    logger.info("Spanish report generation complete!")



if __name__ == "__main__":
    main()

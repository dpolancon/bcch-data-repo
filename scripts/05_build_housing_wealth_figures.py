import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.paths import DATA_DIR, CRSM_RAW_DIR, report_assets_dir

ASSETS_DIR = report_assets_dir(5)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 0.8


def generate_figures():
    anual = pd.read_csv(DATA_DIR / 'panel_housing_wealth_annual.csv')
    resumen = pd.read_csv(DATA_DIR / 'panel_housing_wealth_summary.csv')
    raw_q = pd.read_csv(CRSM_RAW_DIR / 'raw_quarterly.csv', low_memory=False)

    # FIGURA 5.1: Descomposición de Knoll et al. (2017) (% del PIB)
    nac = anual[anual['zone'] == 'Nacional']
    piv_nac = nac.pivot_table(index='anio', columns='indicador', values='valor')

    years = sorted(piv_nac.index.tolist())
    valv_pib = piv_nac['valor_vivienda_pib']
    valt_pib = (piv_nac['valor_terreno'] / piv_nac['valor_vivienda']) * valv_pib
    valc_pib = (piv_nac['valor_construccion'] / piv_nac['valor_vivienda']) * valv_pib

    fig, ax = plt.subplots(figsize=(10.5, 5.8), dpi=300)
    ax.bar(years, valc_pib, label='Valor de Estructuras / Construcción (VALC)', color='#3b82f6', width=0.55, edgecolor='#1e40af', linewidth=0.5)
    ax.bar(years, valt_pib, bottom=valc_pib, label='Valor del Suelo / Terreno (VALT - Renta Espacial)', color='#dc2626', width=0.55, edgecolor='#991b1b', linewidth=0.5)
    ax.plot(years, valv_pib, marker='o', color='#0f172a', linewidth=2.2, label='Patrimonio Residencial Total (VALV / PIB %)')

    ax.set_title('Figura 5.1: Descomposición de Knoll et al. (2017) de la Riqueza Residencial (% del PIB)', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
    ax.set_xlabel('Año', fontsize=10, fontweight='bold', color='#334155')
    ax.set_ylabel('% del PIB Nacional', fontsize=10, fontweight='bold', color='#334155')
    ax.set_xticks(years)
    ax.set_ylim(0, 200)
    ax.grid(True, linestyle=':', alpha=0.5, color='#cbd5e1')
    ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9, loc='upper left')

    for yr, v_val in zip(years, valv_pib):
        if yr in [2012, 2021, 2024]:
            ax.annotate(f'{v_val:.1f}%', xy=(yr, v_val), xytext=(yr, v_val + 6),
                        ha='center', fontsize=8.5, fontweight='bold', color='#0f172a')

    plt.tight_layout()
    fig1_path = ASSETS_DIR / 'fig5_1_riqueza_pib.png'
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print('Generated', fig1_path)

    # FIGURA 5.2: Trayectoria del IPV por Macro-Zonas y Subzonas RM (2002-2026)
    codes = {
        'F034.IPVZ4.FLU.BCCH.2008.0.T': ('RM General (IPVZ4)', '#0f172a', '-', 2.5),
        'F034.IPVZ41.FLU.BCCH.2008.0.T': ('RM - Centro (IPVZ41)', '#059669', '--', 1.6),
        'F034.IPVZ42.FLU.BCCH.2008.0.T': ('RM - Oriente (IPVZ42)', '#dc2626', '--', 1.6),
        'F034.IPVZ43.FLU.BCCH.2008.0.T': ('RM - Poniente (IPVZ43)', '#2563eb', '--', 1.6),
        'F034.IPVZ44.FLU.BCCH.2008.0.T': ('RM - Sur (IPVZ44)', '#d97706', '--', 1.6),
        'F034.IVPZ1.FLU.BCCH.2008.0.T': ('Macro-Zona Norte (IVPZ1)', '#7c3aed', '-.', 1.8),
        'F034.IPVZ2.FLU.BCCH.2008.0.T': ('Macro-Zona Centro (IPVZ2)', '#0891b2', '-.', 1.8),
        'F034.IPVZ3.FLU.BCCH.2008.0.T': ('Macro-Zona Sur (IPVZ3)', '#64748b', '-.', 1.8),
    }

    fig, ax = plt.subplots(figsize=(11.0, 6.2), dpi=300)

    for code, (label, color, ls, lw) in codes.items():
        sub = raw_q[raw_q['series_code'] == code].dropna(subset=['value']).sort_values('date')
        if not sub.empty:
            sub['year'] = sub['date'].str[:4].astype(int)
            ann = sub.groupby('year')['value'].mean()
            ax.plot(ann.index, ann.values, label=label, color=color, linestyle=ls, linewidth=lw)

    ax.axhline(100, color='#94a3b8', linestyle=':', linewidth=1.0)
    ax.set_title('Figura 5.2: Trayectoria del Índice de Precios de Vivienda (IPV Base 2008=100) por Macro-Zonas y Subzonas RM', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
    ax.set_xlabel('Año', fontsize=10, fontweight='bold', color='#334155')
    ax.set_ylabel('Índice Base 2008=100', fontsize=10, fontweight='bold', color='#334155')
    ax.grid(True, linestyle=':', alpha=0.5, color='#cbd5e1')
    ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=8.5, loc='upper left', ncol=2)

    plt.tight_layout()
    fig2_path = ASSETS_DIR / 'fig5_2_ipv_subzonas.png'
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print('Generated', fig2_path)

    # FIGURA 5.3: Densidad de Valor por Metro Cuadrado por Macro-Zona (Full Width)
    piv_24 = anual[anual['anio'] == 2024].pivot_table(index='zone', columns='indicador', values='valor')
    zones_sel = ['Región Metropolitana', 'Zona Norte', 'Zona Centro', 'Zona Sur', 'Nacional']
    sub_24 = piv_24.loc[zones_sel]

    pm2_c = (sub_24['valor_vivienda'] / sub_24['metros_construidos']) / 1e3
    pm2_t = (sub_24['valor_vivienda'] / sub_24['metros_terreno']) / 1e3

    fig, ax = plt.subplots(figsize=(10.5, 5.8), dpi=300)
    x = range(len(zones_sel))

    b1 = ax.bar([i - 0.18 for i in x], pm2_c, width=0.35, label='Valor por m² Construido (VALV / MCC)', color='#1e3a8a', edgecolor='#0f172a', linewidth=0.5)
    b2 = ax.bar([i + 0.18 for i in x], pm2_t, width=0.35, label='Valor por m² de Terreno (VALV / MCT)', color='#dc2626', edgecolor='#991b1b', linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(['Región Metropolitana', 'Macro-Zona Norte', 'Macro-Zona Centro', 'Macro-Zona Sur', 'Nacional General'], fontsize=9.5, fontweight='bold')
    ax.set_ylabel('Miles de pesos por m²', fontsize=10, fontweight='bold', color='#334155')
    ax.set_title('Figura 5.3: Densidad de Valor Residencial por Metro Cuadrado por Macro-Zona (2024)', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
    ax.set_ylim(0, max(pm2_c.max(), pm2_t.max()) * 1.18)
    ax.grid(True, axis='y', linestyle=':', alpha=0.5, color='#cbd5e1')
    ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9, loc='upper right')

    for i in x:
        ax.text(i - 0.18, pm2_c.iloc[i] + 30, f'k', ha='center', fontsize=8.5, fontweight='bold', color='#1e3a8a')
        ax.text(i + 0.18, pm2_t.iloc[i] + 30, f'k', ha='center', fontsize=8.5, fontweight='bold', color='#dc2626')

    plt.tight_layout()
    fig3_path = ASSETS_DIR / 'fig5_3_densidad_valor.png'
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    print('Generated', fig3_path)


if __name__ == '__main__':
    generate_figures()

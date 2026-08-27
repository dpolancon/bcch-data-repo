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

    # FIGURA 5.1
    nac = anual[anual['zone'] == 'Nacional']
    piv_nac = nac.pivot_table(index='anio', columns='indicador', values='valor')

    years = sorted(piv_nac.index.tolist())
    valv_pib = piv_nac['valor_vivienda_pib']
    valt_pib = (piv_nac['valor_terreno'] / piv_nac['valor_vivienda']) * valv_pib
    valc_pib = (piv_nac['valor_construccion'] / piv_nac['valor_vivienda']) * valv_pib

    fig, ax = plt.subplots(figsize=(10, 5.8), dpi=300)
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

    # FIGURA 5.2
    codes = {
        'F034.IPVZ4.FLU.BCCH.2008.0.T': ('RM General', '#0f172a', '-', 2.5),
        'F034.IPVZ41.FLU.BCCH.2008.0.T': ('RM - Oriente', '#dc2626', '-', 2.0),
        'F034.IPVZ42.FLU.BCCH.2008.0.T': ('RM - Norte', '#059669', '--', 1.8),
        'F034.IPVZ43.FLU.BCCH.2008.0.T': ('RM - Poniente', '#2563eb', '--', 1.8),
        'F034.IPVZ44.FLU.BCCH.2008.0.T': ('RM - Sur', '#d97706', '--', 1.8),
    }

    fig, ax = plt.subplots(figsize=(10, 6.0), dpi=300)

    for code, (label, color, ls, lw) in codes.items():
        sub = raw_q[raw_q['series_code'] == code].dropna(subset=['value']).sort_values('date')
        if not sub.empty:
            sub['year'] = sub['date'].str[:4].astype(int)
            ann = sub.groupby('year')['value'].mean()
            ax.plot(ann.index, ann.values, label=label, color=color, linestyle=ls, linewidth=lw)

    ax.axhline(100, color='#94a3b8', linestyle=':', linewidth=1.0)
    ax.set_title('Figura 5.2: Trayectoria del Índice de Precios de Vivienda (IPV Base 2008=100) en la RM', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
    ax.set_xlabel('Año', fontsize=10, fontweight='bold', color='#334155')
    ax.set_ylabel('Índice Base 2008=100', fontsize=10, fontweight='bold', color='#334155')
    ax.grid(True, linestyle=':', alpha=0.5, color='#cbd5e1')
    ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9, loc='upper left')

    plt.tight_layout()
    fig2_path = ASSETS_DIR / 'fig5_2_ipv_subzonas.png'
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print('Generated', fig2_path)

    # FIGURA 5.3
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.2), dpi=300)

    v_rm = float(anual[(anual['anio'] == 2024) & (anual['zone'] == 'Región Metropolitana') & (anual['indicador'] == 'valor_vivienda')]['valor'].iloc[0])
    v_nac = float(anual[(anual['anio'] == 2024) & (anual['zone'] == 'Nacional') & (anual['indicador'] == 'valor_vivienda')]['valor'].iloc[0])
    v_resto = v_nac - v_rm

    shares = [v_rm / 1e12, v_resto / 1e12]
    labels = ['Región Metropolitana\n(,8B / 53,6%)', 'Resto del País\n(,2B / 46,4%)']
    colors = ['#1e3a8a', '#94a3b8']

    ax1.pie(shares, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140, explode=(0.05, 0),
            textprops={'fontsize': 9, 'fontweight': 'bold'})
    ax1.set_title('Concentración Territorial de la Riqueza\nResidencial (2024, Billones $)', fontsize=11, fontweight='bold', pad=12)

    piv_24 = anual[anual['anio'] == 2024].pivot_table(index='zone', columns='indicador', values='valor')
    zones_sel = ['Nacional', 'Región Metropolitana', 'Zona Centro', 'Zona Norte', 'Zona Sur']
    sub_24 = piv_24.loc[zones_sel]

    pm2_t = (sub_24['valor_terreno'] / sub_24['metros_terreno']) / 1e3
    pm2_c = (sub_24['valor_construccion'] / sub_24['metros_construidos']) / 1e3

    x = range(len(zones_sel))
    ax2.bar([i - 0.2 for i in x], pm2_t, width=0.4, label='Suelo ($/m² terreno)', color='#dc2626')
    ax2.bar([i + 0.2 for i in x], pm2_c, width=0.4, label='Construcción ($/m² const.)', color='#3b82f6')
    ax2.set_xticks(x)
    ax2.set_xticklabels(zones_sel, rotation=15, ha='right', fontsize=8.5)
    ax2.set_ylabel('Miles de $ / m²', fontsize=9, fontweight='bold')
    ax2.set_title('Densidad de Valor por Metro Cuadrado (2024)', fontsize=11, fontweight='bold', pad=12)
    ax2.grid(True, axis='y', linestyle=':', alpha=0.5)
    ax2.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=8.5, loc='upper right')

    plt.tight_layout()
    fig3_path = ASSETS_DIR / 'fig5_3_densidad_valor.png'
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    print('Generated', fig3_path)


if __name__ == '__main__':
    generate_figures()

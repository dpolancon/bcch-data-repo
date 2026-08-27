import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.paths import DATA_DIR, report_assets_dir

ASSETS_DIR = report_assets_dir(4)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 0.8


def generate_figures():
    anual = pd.read_csv(DATA_DIR / 'panel_permits_annual.csv', dtype={'region_id': str})
    ejes = pd.read_csv(DATA_DIR / 'panel_two_axes_annual.csv', dtype={'region_code': str})

    nat_piv = anual.pivot_table(index='anio', columns='indicador', values='valor', aggfunc='sum')
    s10 = ejes[ejes['sector_id'] == 10].groupby('year')['share'].mean()

    a0 = 2014
    years = [y for y in range(a0, int(anual['anio'].max()) + 1)]
    idx_sah = (nat_piv.loc[years, 'superficie_habitacional'] / nat_piv.loc[a0, 'superficie_habitacional']) * 100
    idx_nva = (nat_piv.loc[years, 'viviendas_autorizadas'] / nat_piv.loc[a0, 'viviendas_autorizadas']) * 100
    idx_s10 = (s10.loc[years] / s10.loc[a0]) * 100
    idx_ceys = (nat_piv.loc[years, 'empresas_constituidas'] / nat_piv.loc[a0, 'empresas_constituidas']) * 100

    # Fig 1: El Gran Desacople
    fig, ax1 = plt.subplots(figsize=(10, 5.5), dpi=300)
    ax1.plot(years, idx_sah, marker='o', color='#1e3a8a', linewidth=2.5, label='Superficie Habitacional (SAH)')
    ax1.plot(years, idx_nva, marker='s', color='#0284c7', linewidth=2.0, linestyle='--', label='Viviendas Autorizadas (NVA)')
    ax1.plot(years, idx_s10, marker='^', color='#dc2626', linewidth=2.5, label='Renta Espacial en PIB (Sector 10)')
    ax1.plot(years, idx_ceys, marker='d', color='#64748b', linewidth=1.5, linestyle=':', label='Creacion de Empresas (CEYS, control)')

    ax1.axhline(100, color='#94a3b8', linestyle='-', linewidth=0.8, alpha=0.7)
    ax1.set_title('Figura 1: El Gran Desacople - Actividad Fisica vs. Renta Espacial', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
    ax1.set_xlabel('Anio', fontsize=10, fontweight='bold', color='#334155')
    ax1.set_ylabel('Indice (Base 100 = 2014)', fontsize=10, fontweight='bold', color='#334155')
    ax1.set_xticks(years)
    ax1.grid(True, linestyle=':', alpha=0.5, color='#cbd5e1')
    ax1.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9, loc='upper left')

    ax1.annotate(f'{idx_sah.iloc[-1]:.1f}', xy=(years[-1], idx_sah.iloc[-1]), xytext=(years[-1]+0.1, idx_sah.iloc[-1]-5),
                 fontsize=9, fontweight='bold', color='#1e3a8a')
    ax1.annotate(f'{idx_s10.iloc[-1]:.1f}', xy=(years[-1], idx_s10.iloc[-1]), xytext=(years[-1]+0.1, idx_s10.iloc[-1]+3),
                 fontsize=9, fontweight='bold', color='#dc2626')

    plt.tight_layout()
    fig1_path = ASSETS_DIR / 'fig4_1_desacople_macro.png'
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print('Generated', fig1_path)

    # Fig 2: Heterogeneidad Regional
    sah_piv = anual[anual['indicador'] == 'superficie_habitacional'].pivot(index='region_display', columns='anio', values='valor')
    a1 = int(anual['anio'].max())
    var_reg = (((sah_piv[a1] / sah_piv[a0]) - 1) * 100).dropna().sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    colors = ['#ef4444' if v < 0 else '#059669' for v in var_reg.values]
    bars = ax.barh(var_reg.index, var_reg.values, color=colors, height=0.65, edgecolor='#cbd5e1', linewidth=0.5)

    ax.axvline(0, color='#475569', linewidth=1.0)
    ax.set_title(f'Figura 2: Heterogeneidad Territorial - Variacion Superficie Habitacional ({a0} vs. {a1})', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
    ax.set_xlabel('Variacion porcentual acumulada (%)', fontsize=10, fontweight='bold', color='#334155')
    ax.grid(True, axis='x', linestyle=':', alpha=0.5, color='#cbd5e1')

    for bar, val in zip(bars, var_reg.values):
        offset = 3 if val >= 0 else -3
        ha = 'left' if val >= 0 else 'right'
        color = '#047857' if val >= 0 else '#b91c1c'
        ax.text(val + offset, bar.get_y() + bar.get_height()/2, f'{val:+.1f}%',
                va='center', ha=ha, fontsize=8.5, fontweight='bold', color=color)

    ax.set_xlim(var_reg.min() - 15, var_reg.max() + 25)
    plt.tight_layout()
    fig2_path = ASSETS_DIR / 'fig4_2_heterogeneidad_regional.png'
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print('Generated', fig2_path)

    # Fig 3: Composicion y Metraje Medio
    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(10, 7), dpi=300, sharex=True, gridspec_kw={'height_ratios': [1.2, 0.8]})

    sah_m = nat_piv.loc[years, 'superficie_habitacional'] / 1e6
    sanh_m = nat_piv.loc[years, 'superficie_no_habitacional'] / 1e6
    mm = nat_piv.loc[years, 'superficie_habitacional'] / nat_piv.loc[years, 'viviendas_autorizadas']

    ax_top.bar(years, sah_m, label='Superficie Habitacional (SAH)', color='#3b82f6', width=0.55, edgecolor='#1e40af', linewidth=0.5)
    ax_top.bar(years, sanh_m, bottom=sah_m, label='Superficie No Habitacional (SANH)', color='#94a3b8', width=0.55, edgecolor='#475569', linewidth=0.5)
    ax_top.set_title('Figura 3: Composicion de Demanda Fisica y Estabilidad del Metraje Medio', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
    ax_top.set_ylabel('Millones de m2 anuales', fontsize=10, fontweight='bold', color='#334155')
    ax_top.grid(True, linestyle=':', alpha=0.5, color='#cbd5e1')
    ax_top.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9, loc='upper right')

    ax_bot.plot(years, mm, marker='o', color='#d97706', linewidth=2.2, label='Metraje medio por vivienda (m2/viv)')
    ax_bot.axhline(mm.mean(), color='#b45309', linestyle='--', linewidth=1.0, alpha=0.7, label=f'Promedio ({mm.mean():.1f} m2)')
    ax_bot.set_ylabel('m2 / vivienda', fontsize=10, fontweight='bold', color='#334155')
    ax_bot.set_xlabel('Anio', fontsize=10, fontweight='bold', color='#334155')
    ax_bot.set_xticks(years)
    ax_bot.set_ylim(65, 85)
    ax_bot.grid(True, linestyle=':', alpha=0.5, color='#cbd5e1')
    ax_bot.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9, loc='lower left')

    for yr, m_val in zip(years, mm):
        ax_bot.text(yr, m_val + 0.8, f'{m_val:.1f}', ha='center', fontsize=8, fontweight='bold', color='#92400e')

    plt.tight_layout()
    fig3_path = ASSETS_DIR / 'fig4_3_composicion_metraje.png'
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    print('Generated', fig3_path)


if __name__ == '__main__':
    generate_figures()

import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.paths import DATA_DIR, report_assets_dir

ASSETS_DIR = report_assets_dir(8)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 0.8


def generate_figures():
    df_anual = pd.read_csv(DATA_DIR / 'panel_tasas_annual.csv')
    df_sum = pd.read_csv(DATA_DIR / 'panel_tasas_summary.csv')

    piv_anual = df_anual.pivot_table(index='anio', columns='indicador', values='valor')
    years = sorted(piv_anual.index.tolist())

    # =========================================================================
    # FIGURA 8.1: Evolución Histórica de la Tasa de Política Monetaria (1995-2026)
    # =========================================================================
    fig, ax = plt.subplots(figsize=(10.5, 5.8), dpi=300)
    tpm = piv_anual['tpm']

    ax.plot(years, tpm, marker='o', linewidth=2.2, color='#1e3a8a', label='Tasa de Política Monetaria (TPM %)')

    ax.set_title('Figura 8.1: Evolución Histórica de la Tasa de Política Monetaria en Chile (1995–2026)', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
    ax.set_xlabel('Año', fontsize=10, fontweight='bold', color='#334155')
    ax.set_ylabel('Porcentaje Anual (%)', fontsize=10, fontweight='bold', color='#334155')
    ax.set_ylim(0, 15.0)
    ax.grid(True, linestyle=':', alpha=0.5, color='#cbd5e1')
    ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9, loc='upper right')

    # Annotate key shocks
    ax.annotate('Pico 1998\n(12.76%)', xy=(1998, tpm.loc[1998]), xytext=(1998, tpm.loc[1998] + 1.2),
                ha='center', fontsize=8, fontweight='bold', color='#dc2626',
                arrowprops=dict(arrowstyle='->', color='#dc2626', lw=1.0))

    ax.annotate('Piso 2009 & 2020\n(0.50%)', xy=(2020, tpm.loc[2020]), xytext=(2016, tpm.loc[2020] + 3.0),
                ha='center', fontsize=8, fontweight='bold', color='#059669',
                arrowprops=dict(arrowstyle='->', color='#059669', lw=1.0))

    plt.tight_layout()
    fig1_path = ASSETS_DIR / 'fig8_1_ciclo_tpm.png'
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print('Generated', fig1_path)

    # =========================================================================
    # FIGURA 8.2: Estructura de Tasas por Tipo de Colocación (2002-2026)
    # =========================================================================
    fig, ax = plt.subplots(figsize=(10.5, 5.8), dpi=300)

    t_hip = piv_anual.get('tasa_hipotecaria', pd.Series(dtype=float))
    t_con = piv_anual.get('tasa_consumo', pd.Series(dtype=float))
    t_com = piv_anual.get('tasa_comercial', pd.Series(dtype=float))

    if not t_hip.empty:
        ax.plot(years, t_hip, marker='^', linewidth=2.2, color='#059669', label='Tasa Hipotecaria (Vivienda %)')
    if not t_com.empty:
        ax.plot(years, t_com, marker='s', linewidth=2.0, color='#dc2626', linestyle='--', label='Tasa Comercial (%)')
    if not t_con.empty:
        ax.plot(years, t_con, marker='d', linewidth=1.8, color='#d97706', linestyle='-.', label='Tasa Consumo (%)')

    ax.set_title('Figura 8.2: Estructura de Tasas de Interés por Tipo de Colocación Bancaria (2002–2026)', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
    ax.set_xlabel('Año', fontsize=10, fontweight='bold', color='#334155')
    ax.set_ylabel('Porcentaje Anual (%)', fontsize=10, fontweight='bold', color='#334155')
    ax.grid(True, linestyle=':', alpha=0.5, color='#cbd5e1')
    ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9, loc='upper right')

    if not t_hip.empty and 2019 in t_hip.index:
        ax.annotate('Piso Hipotecario 2019\n(1.99%)', xy=(2019, t_hip.loc[2019]), xytext=(2019, t_hip.loc[2019] - 1.5),
                    ha='center', fontsize=8, fontweight='bold', color='#059669',
                    arrowprops=dict(arrowstyle='->', color='#059669', lw=1.0))

    plt.tight_layout()
    fig2_path = ASSETS_DIR / 'fig8_2_estructura_tasas.png'
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print('Generated', fig2_path)

    # =========================================================================
    # FIGURA 8.3: Spread y Transmisión de la TPM a Tasas Hipotecarias y Comerciales
    # =========================================================================
    fig, ax = plt.subplots(figsize=(11.0, 6.2), dpi=300)

    spread_hip = t_hip - tpm
    spread_com = t_com - tpm

    ax.plot(years, spread_hip, marker='o', linewidth=2.0, color='#2563eb', label='Spread Hipotecario (Tasa Hipotecaria - TPM %)')
    ax.plot(years, spread_com, marker='s', linewidth=2.0, color='#d97706', linestyle='--', label='Spread Comercial (Tasa Comercial - TPM %)')
    ax.axhline(0, color='#0f172a', linewidth=1.0)

    ax.set_title('Figura 8.3: Margen de Intermediación y Transmisión Monetaria (Spreads sobre TPM)', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
    ax.set_xlabel('Año', fontsize=10, fontweight='bold', color='#334155')
    ax.set_ylabel('Puntos Porcentuales (pp)', fontsize=10, fontweight='bold', color='#334155')
    ax.grid(True, linestyle=':', alpha=0.5, color='#cbd5e1')
    ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9, loc='upper right')

    plt.tight_layout()
    fig3_path = ASSETS_DIR / 'fig8_3_diferencial_tasas.png'
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    print('Generated', fig3_path)


if __name__ == '__main__':
    generate_figures()

import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.paths import DATA_DIR, report_assets_dir

ASSETS_DIR = report_assets_dir(3)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 0.8


def generate_figures():
    df_trade = pd.read_csv(DATA_DIR / 'panel_interregional_trade_summary.csv')

    aper = df_trade[df_trade['indicador'] == 'apertura'].set_index('region_name')['valor']
    auto = df_trade[df_trade['indicador'] == 'autocontencion'].set_index('region_name')['valor']
    bal = df_trade[df_trade['indicador'] == 'balance_neto'].set_index('region_name')['valor']

    fig, ax = plt.subplots(figsize=(10.5, 6.2), dpi=300)

    regions = aper.index.tolist()
    x_vals = [aper.loc[r] for r in regions]
    y_vals = [auto.loc[r] for r in regions]

    # Color code regions by type
    colors = []
    for r in regions:
        if 'Metropolitana' in r:
            colors.append('#dc2626')  # Red for RM (Spatial rent node)
        elif r in ['Antofagasta', 'Atacama', 'Tarapacá']:
            colors.append('#d97706')  # Amber for Resource rent nodes
        elif r in ['Valparaíso', 'Biobío', 'Los Ríos', 'Los Lagos']:
            colors.append('#1e3a8a')  # Blue for Integrated productives
        else:
            colors.append('#64748b')  # Slate for Periphery

    ax.scatter(x_vals, y_vals, c=colors, s=140, alpha=0.85, edgecolors='#0f172a', linewidth=1.2, zorder=3)

    for r, x, y in zip(regions, x_vals, y_vals):
        short_name = r.replace('Metropolitana de Santiago', 'RM').replace('Arica y Parinacota', 'Arica')
        ax.annotate(short_name, (x, y), xytext=(x + 0.8, y + 0.8), fontsize=8.5, fontweight='bold', color='#0f172a')

    # Quadrant lines
    ax.axvline(50, color='#94a3b8', linestyle='--', linewidth=1.0)
    ax.axhline(50, color='#94a3b8', linestyle='--', linewidth=1.0)

    ax.text(25, 75, 'CUADRANTE I:\nNodo Metropolitano\n(Renta Espacial Dominante)', fontsize=9, fontweight='bold', color='#dc2626', bbox=dict(boxstyle='round,pad=0.4', facecolor='#fee2e2', alpha=0.7))
    ax.text(68, 30, 'CUADRANTE II:\nRegiones de Recursos\n(Renta Primario-Exportadora)', fontsize=9, fontweight='bold', color='#d97706', bbox=dict(boxstyle='round,pad=0.4', facecolor='#fef3c7', alpha=0.7))

    ax.set_title('Figura 3.1: Matriz de los Dos Ejes: Renta Espacial vs. Renta de Recursos (2025)', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
    ax.set_xlabel('Tasa de Apertura Interregional (% Ventas al Resto de Chile)', fontsize=10, fontweight='bold', color='#334155')
    ax.set_ylabel('Tasa de Autocontención Intrarregional (% Ventas Mercado Interno)', fontsize=10, fontweight='bold', color='#334155')
    ax.set_xlim(15, 80)
    ax.set_ylim(15, 85)
    ax.grid(True, linestyle=':', alpha=0.5, color='#cbd5e1')

    plt.tight_layout()
    fig_path = ASSETS_DIR / 'fig3_1_dos_ejes.png'
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print('Generated', fig_path)


if __name__ == '__main__':
    generate_figures()

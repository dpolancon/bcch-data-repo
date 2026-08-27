import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.paths import DATA_DIR, report_assets_dir

ASSETS_DIR = report_assets_dir(7)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 0.8


def generate_figures():
    df_anual = pd.read_csv(DATA_DIR / 'panel_interregional_trade_annual.csv')
    df_sum = pd.read_csv(DATA_DIR / 'panel_interregional_trade_summary.csv')

    sub25 = df_anual[df_anual['anio'] == 2025].pivot_table(index='region_name', columns='indicador', values='valor')

    # =========================================================================
    # FIGURA 7.1: Apertura Comercial Interregional vs Autocontención (2025)
    # =========================================================================
    sub25['v_tot'] = sub25['venta_interregional'] + sub25['venta_intrarregional']
    sub25['apertura_pct'] = 100 * (sub25['venta_interregional'] / sub25['v_tot'])
    sub25['auto_pct'] = 100 * (sub25['venta_intrarregional'] / sub25['v_tot'])

    sub25_sorted = sub25.sort_values('apertura_pct', ascending=True)
    regions = sub25_sorted.index.tolist()

    fig, ax = plt.subplots(figsize=(10.5, 6.2), dpi=300)
    y = range(len(regions))

    ax.barh(y, sub25_sorted['apertura_pct'], height=0.45, label='Apertura Interregional (Ventas a Otras Regiones %)', color='#1e3a8a')
    ax.barh(y, sub25_sorted['auto_pct'], left=sub25_sorted['apertura_pct'], height=0.45, label='Autocontención Intrarregional (%)', color='#94a3b8')

    ax.set_yticks(y)
    ax.set_yticklabels(regions, fontsize=9, fontweight='bold')
    ax.set_xlabel('Porcentaje de Ventas Totales (%)', fontsize=10, fontweight='bold', color='#334155')
    ax.set_title('Figura 7.1: Grado de Apertura Comercial Interregional vs. Autocontención por Región (2025)', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
    ax.set_xlim(0, 100)
    ax.grid(True, axis='x', linestyle=':', alpha=0.5, color='#cbd5e1')
    ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9, loc='lower right')

    for i, (ap, au) in enumerate(zip(sub25_sorted['apertura_pct'], sub25_sorted['auto_pct'])):
        if ap > 25:
            ax.text(ap / 2, i, f'{ap:.1f}%', va='center', ha='center', fontsize=7.5, fontweight='bold', color='#ffffff')

    plt.tight_layout()
    fig1_path = ASSETS_DIR / 'fig7_1_autocontencion_vs_apertura.png'
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print('Generated', fig1_path)

    # =========================================================================
    # FIGURA 7.2: Balance Comercial Neto Interregional (2025, Billones $)
    # =========================================================================
    sub25['balance_neto_b'] = (sub25['venta_interregional'] - sub25['compra_interregional']) / 1e12
    sub25_bal = sub25.sort_values('balance_neto_b', ascending=True)

    fig, ax = plt.subplots(figsize=(10.5, 6.2), dpi=300)
    y_bal = range(len(sub25_bal))
    colors = ['#dc2626' if v < 0 else '#059669' for v in sub25_bal['balance_neto_b']]

    ax.barh(y_bal, sub25_bal['balance_neto_b'], height=0.55, color=colors, edgecolor='#0f172a', linewidth=0.5)
    ax.axvline(0, color='#0f172a', linewidth=1.0)

    ax.set_yticks(y_bal)
    ax.set_yticklabels(sub25_bal.index.tolist(), fontsize=9, fontweight='bold')
    ax.set_xlabel('Balance Neto Interregional (Billones de pesos)', fontsize=10, fontweight='bold', color='#334155')
    ax.set_title('Figura 7.2: Balance Comercial Neto Interregional por Región (Ventas - Compras, 2025)', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
    ax.grid(True, axis='x', linestyle=':', alpha=0.5, color='#cbd5e1')

    for i, v in enumerate(sub25_bal['balance_neto_b']):
        if abs(v) > 0.5:
            offset = 0.3 if v > 0 else -0.3
            ha = 'left' if v > 0 else 'right'
            ax.text(v + offset, i, f'B', va='center', ha=ha, fontsize=8, fontweight='bold', color='#0f172a')

    plt.tight_layout()
    fig2_path = ASSETS_DIR / 'fig7_2_balance_comercial_neto.png'
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print('Generated', fig2_path)

    # =========================================================================
    # FIGURA 7.3: Volumen Total de Comercio Interregional (2025, Billones $)
    # =========================================================================
    sub25['v_inter_b'] = sub25['venta_interregional'] / 1e12
    sub25['v_intra_b'] = sub25['venta_intrarregional'] / 1e12
    sub25_vol = sub25.sort_values('v_tot', ascending=True)

    fig, ax = plt.subplots(figsize=(11.0, 6.4), dpi=300)
    y_vol = range(len(sub25_vol))

    ax.barh(y_vol, sub25_vol['v_intra_b'], height=0.5, label='Ventas Intrarregionales (Mercado Interno)', color='#2563eb')
    ax.barh(y_vol, sub25_vol['v_inter_b'], left=sub25_vol['v_intra_b'], height=0.5, label='Ventas Interregionales (Otras Regiones)', color='#d97706')

    ax.set_yticks(y_vol)
    ax.set_yticklabels(sub25_vol.index.tolist(), fontsize=9, fontweight='bold')
    ax.set_xlabel('Masa Comercial de Ventas (Billones de pesos)', fontsize=10, fontweight='bold', color='#334155')
    ax.set_title('Figura 7.3: Volumen Total de Comercio por Región y Destino (2025, Billones $)', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
    ax.grid(True, axis='x', linestyle=':', alpha=0.5, color='#cbd5e1')
    ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9, loc='lower right')

    plt.tight_layout()
    fig3_path = ASSETS_DIR / 'fig7_3_volumen_comercio.png'
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    print('Generated', fig3_path)


if __name__ == '__main__':
    generate_figures()

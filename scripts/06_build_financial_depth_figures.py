import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.paths import DATA_DIR, report_assets_dir

ASSETS_DIR = report_assets_dir(6)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 0.8


def generate_figures():
    df_anual = pd.read_csv(DATA_DIR / 'panel_financial_depth_annual.csv')
    df_sum = pd.read_csv(DATA_DIR / 'panel_financial_depth_summary.csv')

    piv_sum = df_sum.pivot_table(index='anio', columns='indicador', values='valor')

    # =========================================================================
    # FIGURA 6.1: Ciclo Macro-Temporal de Morosidad Bancaria >90 Días (2009-2025)
    # =========================================================================
    years = sorted(piv_sum.index.tolist())
    m_com = piv_sum['mora_comercial']
    m_con = piv_sum['mora_consumo']
    m_viv = piv_sum['mora_vivienda']

    fig, ax = plt.subplots(figsize=(10.5, 5.8), dpi=300)
    ax.plot(years, m_com, marker='o', linewidth=2.2, color='#dc2626', label='Mora Comercial >90 días (%)')
    ax.plot(years, m_con, marker='s', linewidth=2.0, color='#d97706', linestyle='--', label='Mora Consumo >90 días (%)')
    ax.plot(years, m_viv, marker='^', linewidth=2.2, color='#1e3a8a', label='Mora Vivienda >90 días (%)')

    ax.set_title('Figura 6.1: Evolución Nacional de la Morosidad Bancaria a 90 Días o Más por Tipo de Cartera (2009–2025)', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
    ax.set_xlabel('Año', fontsize=10, fontweight='bold', color='#334155')
    ax.set_ylabel('Porcentaje de Deuda Morosa >90 Días (%)', fontsize=10, fontweight='bold', color='#334155')
    ax.set_xticks(years)
    ax.set_ylim(0, 4.0)
    ax.grid(True, linestyle=':', alpha=0.5, color='#cbd5e1')
    ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9, loc='upper right')

    # Annotations for key inflection points
    ax.annotate('Piso Vivienda 2023\n(0.32%)', xy=(2023, m_viv.loc[2023]), xytext=(2023, m_viv.loc[2023] + 0.5),
                ha='center', fontsize=8, fontweight='bold', color='#1e3a8a',
                arrowprops=dict(arrowstyle='->', color='#1e3a8a', lw=1.0))

    ax.annotate('Rebrote Comercial\n(3.02%)', xy=(2024, m_com.loc[2024]), xytext=(2024 - 1.2, m_com.loc[2024] + 0.4),
                ha='center', fontsize=8, fontweight='bold', color='#dc2626',
                arrowprops=dict(arrowstyle='->', color='#dc2626', lw=1.0))

    plt.tight_layout()
    fig1_path = ASSETS_DIR / 'fig6_1_mora_temporal.png'
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print('Generated', fig1_path)

    # =========================================================================
    # FIGURA 6.2: Centralización Espacial de Liquidez en la RM vs Resto (2009-2025)
    # =========================================================================
    conc_rm = piv_sum['concentracion_rm_cuentas']
    saldo_med = piv_sum['saldo_medio_cuenta'] / 1e6  # en millones $

    fig, ax1 = plt.subplots(figsize=(10.5, 5.8), dpi=300)
    color_conc = '#1e3a8a'
    color_saldo = '#059669'

    ax1.plot(years, conc_rm, marker='o', color=color_conc, linewidth=2.4, label='Participación RM en Cuentas Corrientes (%)')
    ax1.set_xlabel('Año', fontsize=10, fontweight='bold', color='#334155')
    ax1.set_ylabel('% del Total Nacional de Cuentas en RM', fontsize=10, fontweight='bold', color=color_conc)
    ax1.tick_params(axis='y', labelcolor=color_conc)
    ax1.set_xticks(years)
    ax1.set_ylim(50, 90)
    ax1.grid(True, linestyle=':', alpha=0.5, color='#cbd5e1')

    ax2 = ax1.twinx()
    ax2.plot(years, saldo_med, marker='s', color=color_saldo, linewidth=2.0, linestyle='--', label='Saldo Medio por Cuenta (Millones $)')
    ax2.set_ylabel('Saldo Medio por Cuenta (Millones $)', fontsize=10, fontweight='bold', color=color_saldo)
    ax2.tick_params(axis='y', labelcolor=color_saldo)
    ax2.set_ylim(0, 5.0)

    # Annotate peaks
    ax1.annotate('Pico RM 2025\n(80.5%)', xy=(2025, conc_rm.loc[2025]), xytext=(2023.5, conc_rm.loc[2025] - 5),
                 ha='center', fontsize=8.5, fontweight='bold', color=color_conc,
                 arrowprops=dict(arrowstyle='->', color=color_conc, lw=1.0))

    ax2.annotate('Pico Liquidez 2021\n(.98M)', xy=(2021, saldo_med.loc[2021]), xytext=(2021, saldo_med.loc[2021] + 0.5),
                 ha='center', fontsize=8.5, fontweight='bold', color=color_saldo,
                 arrowprops=dict(arrowstyle='->', color=color_saldo, lw=1.0))

    plt.title('Figura 6.2: Centralización Espacial del Crédito y Saldo Medio por Cuenta Corriente (2009–2025)', fontsize=12, fontweight='bold', pad=12, color='#0f172a')

    # Unified legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9, loc='upper left')

    plt.tight_layout()
    fig2_path = ASSETS_DIR / 'fig6_2_concentracion_liquidez.png'
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print('Generated', fig2_path)

    # =========================================================================
    # FIGURA 6.3: Matriz de Heterogeneidad Regional de la Morosidad (2024)
    # =========================================================================
    sub24 = df_anual[df_anual['anio'] == 2024]
    piv24 = sub24.pivot_table(index='region_display', columns='indicador', values='valor')

    # Sort regions by mora_comercial
    piv24_sorted = piv24.sort_values('mora_comercial', ascending=True)

    regions = piv24_sorted.index.tolist()
    m_com_r = piv24_sorted['mora_comercial']
    m_con_r = piv24_sorted['mora_consumo']
    m_viv_r = piv24_sorted['mora_vivienda']

    fig, ax = plt.subplots(figsize=(11.0, 6.5), dpi=300)
    y = range(len(regions))

    ax.barh([i + 0.25 for i in y], m_com_r, height=0.25, label='Mora Comercial (%)', color='#dc2626')
    ax.barh([i for i in y], m_con_r, height=0.25, label='Mora Consumo (%)', color='#d97706')
    ax.barh([i - 0.25 for i in y], m_viv_r, height=0.25, label='Mora Vivienda (%)', color='#1e3a8a')

    ax.set_yticks(y)
    ax.set_yticklabels(regions, fontsize=9, fontweight='bold')
    ax.set_xlabel('Porcentaje de Deuda Morosa >90 Días (%)', fontsize=10, fontweight='bold', color='#334155')
    ax.set_title('Figura 6.3: Heterogeneidad Regional de la Morosidad Bancaria >90 Días por Cartera (2024)', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
    ax.grid(True, axis='x', linestyle=':', alpha=0.5, color='#cbd5e1')
    ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9, loc='lower right')

    for i in y:
        v_c = m_com_r.iloc[i]
        if v_c > 3.5:
            ax.text(v_c + 0.1, i + 0.25, f'{v_c:.1f}%', va='center', fontsize=7.5, fontweight='bold', color='#dc2626')

    plt.tight_layout()
    fig3_path = ASSETS_DIR / 'fig6_3_mora_regional.png'
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    print('Generated', fig3_path)


if __name__ == '__main__':
    generate_figures()

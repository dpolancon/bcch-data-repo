"""
Stage:    14 -- Build the report figures
Purpose:  Draw every PNG exhibit of reports 3 to 8 from its theme panel and
          write it into that report's own assets/ directory. One builder per
          report, sharing a single house style.
Task:     Publication programme -- BCCh regional data
Inputs:   data/panel_two_axes_annual.csv
          data/panel_permits_annual.csv
          data/panel_housing_wealth_annual.csv, ..._summary.csv
          data/raw/regional-spatial-macro-dataset/raw_quarterly.csv
          data/panel_financial_depth_annual.csv, ..._summary.csv
          data/panel_interregional_trade_annual.csv, ..._summary.csv
          data/panel_tasas_annual.csv, ..._summary.csv
Outputs:  bcch-data-repo-vault/report{3..8}_*/assets/fig*.png
Created:  2026-08-28
Updated:  2026-08-28
Owner:    dpolancon
Run:      python scripts/14_build_report_figures.py [--report N ...]
          Runs BEFORE stage 10: that stage copies these PNGs into the site
          worktree and stage 11 compares them byte for byte.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt
import pandas as pd

from lib.paths import CRSM_RAW_DIR, DATA_DIR, report_assets_dir


def _estilo() -> None:
    """The house style, applied once for every builder in this stage."""
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
    plt.rcParams['axes.edgecolor'] = '#cbd5e1'
    plt.rcParams['axes.linewidth'] = 0.8


def _assets(n: int):
    """Assets directory of report `n`, created on demand."""
    d = report_assets_dir(n)
    d.mkdir(parents=True, exist_ok=True)
    return d


def figuras_reporte3():
    """Matriz de los dos ejes, dibujada del panel que el reporte 3 describe.

    Esta figura se dibujaba desde `panel_interregional_trade_summary.csv` —el
    panel del reporte 7— y graficaba apertura contra autocontención bajo un
    título que prometía renta espacial contra renta de recursos. Los cuadrantes
    rotulaban rentas sobre ejes que medían comercio, el epígrafe describía la
    figura real y contradecía a su propio título, y ninguna cifra del cuerpo del
    reporte 3 aparecía en la única figura que lo acompañaba.
    """
    ASSETS_DIR = _assets(3)

    ejes = pd.read_csv(DATA_DIR / 'panel_two_axes_annual.csv', dtype={'region_code': str})
    a1 = int(ejes['year'].max())
    corte = ejes[ejes['year'] == a1]

    esp = corte[corte['sector_id'] == 10].set_index('region_display')['share'] * 100
    rec = corte[corte['sector_id'] == 3].set_index('region_display')['share'] * 100
    regions = [r for r in esp.index if r in rec.index]

    x_vals = [esp.loc[r] for r in regions]
    y_vals = [rec.loc[r] for r in regions]

    # El corte de cada eje es su mediana, no un 50% arbitrario: las dos rentas
    # viven en rangos muy distintos y un umbral fijo dejaría un cuadrante vacío.
    x_med, y_med = float(pd.Series(x_vals).median()), float(pd.Series(y_vals).median())

    colors = [
        '#dc2626' if x >= x_med and y < y_med else
        '#d97706' if y >= y_med and x < x_med else
        '#1e3a8a' if x >= x_med and y >= y_med else
        '#64748b'
        for x, y in zip(x_vals, y_vals)
    ]

    fig, ax = plt.subplots(figsize=(10.5, 6.2), dpi=300)
    ax.scatter(x_vals, y_vals, c=colors, s=140, alpha=0.85, edgecolors='#0f172a', linewidth=1.2, zorder=3)

    # El racimo de baja renta de recursos amontona media docena de etiquetas
    # sobre la misma banda horizontal. Se alternan arriba y abajo del punto.
    orden = sorted(range(len(regions)), key=lambda i: x_vals[i])
    for pos, i in enumerate(orden):
        r, x, y = regions[i], x_vals[i], y_vals[i]
        corto = (r.replace('Metropolitana de Santiago', 'RM')
                  .replace('Arica y Parinacota', 'Arica')
                  .replace('Libertador General Bernardo OHiggins', "O'Higgins"))
        arriba = y > y_med or pos % 2 == 0
        ax.annotate(
            corto, (x, y),
            xytext=(x, y + (2.4 if arriba else -3.2)),
            ha='center', va='bottom' if arriba else 'top',
            fontsize=8.5, fontweight='bold', color='#0f172a',
        )

    ax.axvline(x_med, color='#94a3b8', linestyle='--', linewidth=1.0)
    ax.axhline(y_med, color='#94a3b8', linestyle='--', linewidth=1.0)
    ax.set_ylim(-8, max(y_vals) * 1.12)
    ax.text(
        0.985, 0.97,
        f'Cortes en la mediana de cada eje:\nrenta espacial {x_med:.1f}%  ·  renta de recursos {y_med:.1f}%',
        transform=ax.transAxes, ha='right', va='top', fontsize=8, color='#64748b',
    )

    ax.set_title(
        f'Figura 3.1: Matriz de los dos ejes — renta espacial y renta de recursos por región ({a1})',
        fontsize=12, fontweight='bold', pad=12, color='#0f172a',
    )
    ax.set_xlabel('Renta espacial: sector 10 en el producto regional (%)', fontsize=10, fontweight='bold', color='#334155')
    ax.set_ylabel('Renta de recursos: sector 03 en el producto regional (%)', fontsize=10, fontweight='bold', color='#334155')
    ax.grid(True, linestyle=':', alpha=0.5, color='#cbd5e1')

    plt.tight_layout()
    fig_path = ASSETS_DIR / 'fig3_1_dos_ejes.png'
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print('Generated', fig_path)


def figuras_reporte4():
    ASSETS_DIR = _assets(4)

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


def figuras_reporte5():
    ASSETS_DIR = _assets(5)

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
        ax.text(i - 0.18, pm2_c.iloc[i] + 30, f'{pm2_c.iloc[i]:.0f}k', ha='center', fontsize=8.5, fontweight='bold', color='#1e3a8a')
        ax.text(i + 0.18, pm2_t.iloc[i] + 30, f'{pm2_t.iloc[i]:.0f}k', ha='center', fontsize=8.5, fontweight='bold', color='#dc2626')

    plt.tight_layout()
    fig3_path = ASSETS_DIR / 'fig5_3_densidad_valor.png'
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    print('Generated', fig3_path)


def figuras_reporte6():
    ASSETS_DIR = _assets(6)

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

    # Annotations for key inflection points. The year names the turning point --
    # an editorial choice -- but the figure is read off the panel, never typed.
    ax.annotate(f'Piso Vivienda 2023\n({m_viv.loc[2023]:.2f}%)', xy=(2023, m_viv.loc[2023]), xytext=(2023, m_viv.loc[2023] + 0.5),
                ha='center', fontsize=8, fontweight='bold', color='#1e3a8a',
                arrowprops=dict(arrowstyle='->', color='#1e3a8a', lw=1.0))

    ax.annotate(f'Rebrote Comercial\n({m_com.loc[2024]:.2f}%)', xy=(2024, m_com.loc[2024]), xytext=(2024 - 1.2, m_com.loc[2024] + 0.4),
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
    ax1.annotate(f'Pico RM 2025\n({conc_rm.loc[2025]:.1f}%)', xy=(2025, conc_rm.loc[2025]), xytext=(2023.5, conc_rm.loc[2025] - 5),
                 ha='center', fontsize=8.5, fontweight='bold', color=color_conc,
                 arrowprops=dict(arrowstyle='->', color=color_conc, lw=1.0))

    ax2.annotate(f'Pico Liquidez 2021\n({saldo_med.loc[2021]:.2f}M)', xy=(2021, saldo_med.loc[2021]), xytext=(2021, saldo_med.loc[2021] + 0.5),
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


def figuras_reporte7():
    ASSETS_DIR = _assets(7)

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
            ax.text(v + offset, i, f'{v:.1f}B', va='center', ha=ha, fontsize=8, fontweight='bold', color='#0f172a')

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


def figuras_reporte8():
    ASSETS_DIR = _assets(8)

    df_anual = pd.read_csv(DATA_DIR / 'panel_tasas_annual.csv')
    df_sum = pd.read_csv(DATA_DIR / 'panel_tasas_summary.csv')

    piv_anual = df_anual.pivot_table(index='anio', columns='indicador', values='valor')
    years = sorted(piv_anual.index.tolist())

    # The series plotted here are annual means; the extremes the prose quotes
    # are monthly. Read them from the summary panel and say "mensual" in the
    # label, so the number matches the page and the words match the point the
    # arrow lands on.
    ext = df_sum.set_index('indicador')

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
    a_max, v_max = int(ext.loc['tpm_maximo', 'anio']), ext.loc['tpm_maximo', 'valor']
    a_min, v_min = int(ext.loc['tpm_minimo', 'anio']), ext.loc['tpm_minimo', 'valor']

    ax.annotate(f'Pico mensual {a_max}\n({v_max:.2f}%)', xy=(a_max, tpm.loc[a_max]), xytext=(a_max, tpm.loc[a_max] + 1.2),
                ha='center', fontsize=8, fontweight='bold', color='#dc2626',
                arrowprops=dict(arrowstyle='->', color='#dc2626', lw=1.0))

    ax.annotate(f'Piso mensual {a_min} y 2020\n({v_min:.2f}%)', xy=(2020, tpm.loc[2020]), xytext=(2016, tpm.loc[2020] + 3.0),
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

    a_hip = int(ext.loc['hipotecaria_minima', 'anio'])
    v_hip = ext.loc['hipotecaria_minima', 'valor']
    if not t_hip.empty and a_hip in t_hip.index:
        ax.annotate(f'Piso mensual hipotecario {a_hip}\n({v_hip:.2f}%)', xy=(a_hip, t_hip.loc[a_hip]), xytext=(a_hip, t_hip.loc[a_hip] - 1.5),
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


CONSTRUCTORES = {
    3: figuras_reporte3,
    4: figuras_reporte4,
    5: figuras_reporte5,
    6: figuras_reporte6,
    7: figuras_reporte7,
    8: figuras_reporte8,
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build the PNG exhibits of reports 3-8 from their theme panels. "
            "Run before stage 10, which copies the figures into the site "
            "worktree, and stage 11, which compares them byte for byte."
        )
    )
    parser.add_argument(
        "--report",
        type=int,
        action="append",
        choices=sorted(CONSTRUCTORES),
        help="Report to draw; repeatable. Omit to draw every report.",
    )
    args = parser.parse_args()

    _estilo()
    for n in args.report or sorted(CONSTRUCTORES):
        CONSTRUCTORES[n]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

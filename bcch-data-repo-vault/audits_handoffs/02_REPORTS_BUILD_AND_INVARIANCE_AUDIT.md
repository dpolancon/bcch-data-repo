# Audit & Handoff 02: Full Report Building, Visual Exhibits & Invariance Engine Audit

**Fecha de Ejecución:** 2026-08-27  
**Repositorio Principal:** `c:\ReposGitHub\bcch-data-repo`

---

## 1. Construcción y Extensión de los Reportes 3 a 8

En esta fase de desarrollo se completó la construcción empírica, generación gráfica y redacción analítica de los reportes del programa:

### A. Reporte 3 (*"Los dos ejes: renta espacial y renta de recursos"*)
- **Script Creado:** `scripts/03_build_two_axes_figures.py`
- **Exhibits Visuales:** `fig3_1_dos_ejes.png` (Matriz Bi-Axial de Apertura Comercial Interregional vs. Autocontención Intrarregional a 300 DPI).
- **Inyección Metodológica (`.callout-warning`):** Clarificación explícita de que la participación en el PIB regional (*Sector 10: Servicios de vivienda e inmobiliarios*) no es necesariamente una proxy perfecta de la renta espacial urbana del suelo, sino una primera aproximación empírica admisible con los datos disponibles en la BDE del BCCh.

### B. Reporte 4 (*"El ciclo regional de la construcción"*)
- **Dinámica del Empleo Sectorial:** Se incorporó el análisis sectorial de absorción de mano de obra en el *Sector 06: Construcción*, demostrando cómo la caída del -50% en los permisos de edificación (`SAH`, `NVA`) impacta el empleo directo regional y precariza la actividad física, a diferencia de la revalorización patrimonial del *Sector 10*.
- **Cuadros Metodológicos (`.callout-note`):** Estandarización de contenedores para Figuras 4.1 (*El Gran Desacople*), 4.2 (*Contracción Física Regional*) y 4.3 (*Metraje Medio por Unidad Habitacional*).

### C. Reporte 6 (*"Profundidad financiera y morosidad por región"*)
- **Exhibits Visuales:** `fig6_1_mora_temporal.png`, `fig6_2_concentracion_liquidez.png` y `fig6_3_mora_regional.png`.
- **Hallazgos Empíricos:** Demuestra la extrema concentración de cuentas corrientes personales en la Región Metropolitana (80,5% de las cuentas del país) y la marcada heterogeneidad regional en el riesgo de crédito (>90 días).

### D. Reporte 7 (*"Estancamiento del sector dinámico y comercio interregional"*)
- **Script Creado:** `scripts/07_build_interregional_trade_figures.py`
- **Exhibits Visuales:** `fig7_1_autocontencion_vs_apertura.png`, `fig7_2_balance_comercial_neto.png` y `fig7_3_volumen_comercio.png`.
- **Análisis de Red:** Matriz de flujo comercial de 496 series (`CVRV`, `CVRC`, `NFRV`, `NFRC`), constatando una autocontención comercial metropolitana del 76,4% y una elevada dependencia de demanda externa en regiones extractivas.

### E. Reporte 8 (*"El precio del dinero y condiciones de crédito"*)
- **Script Creado:** `scripts/08_build_tasas_figures.py`
- **Exhibits Visuales:** `fig8_1_ciclo_tpm.png`, `fig8_2_estructura_tasas.png` y `fig8_3_diferencial_tasas.png`.
- **Macro-Finanzas:** Evaluación de la transmisión de la Tasa de Política Monetaria (TPM), el piso histórico de la tasa de crédito hipotecario (2019) y el apalancamiento de los hogares (`DEUBH`), que se multiplicó por 2,7x sobre el ingreso disponible.

---

## 2. El Motor de Auditoría e Invariancia Forense (`11_audit_site.py`)

Para garantizar que el sitio publicado sea **100% fiel y matemáticamente consistente** con los datos crudos del Banco Central, se ejecuta el script de auditoría `scripts/11_audit_site.py`, el cual realiza las siguientes verificaciones automatizadas:

1. **Verificación Byte a Byte de Activos:** Compara el hash SHA-256 de los 61 archivos gráficos y manifiestos entre la bóveda original y la carpeta `assets/` del sitio.
2. **Re-cálculo Dinámico de Cifras:** Recalcula desde los CSVs de `data/` cada una de las cifras destacadas en negrita (`**...**`) en la prosa de los reportes.
3. **Escaneo de Tokens Indefinidos:** Falla inmediatamente si existe cualquier token `@@TOKEN@@` sin resolver.
4. **Verificación de Idioma y Atribución:** Asegura que todas las figuras incluyan su correspondiente macro `site_lib.fuente()` enlazando al CSV de origen.

### Resultado de la Auditoría Ejecutada:
```text
2026-08-27 18:49:57,978 | INFO | Assets verified byte-identical: 61/61
2026-08-27 18:49:58,000 | INFO | Panels verified: 16
2026-08-27 18:49:58,012 | INFO | Pages scanned for unresolved tokens: 23
2026-08-27 18:49:58,016 | INFO | Report 3 headline statistics reproduce from the panel: 8/8
2026-08-27 18:49:58,042 | INFO | Reporte 4: 9 cifras y el conteo de regiones reproducen del panel
2026-08-27 18:49:58,055 | INFO | Reporte 5: 19 cifras reproducen del panel
2026-08-27 18:49:58,065 | INFO | Reporte 6: 9 cifras reproducen del panel
2026-08-27 18:49:58,079 | INFO | Reporte 7: 18 cifras reproducen del panel
2026-08-27 18:49:58,086 | INFO | Reporte 8: 13 cifras reproducen del panel
2026-08-27 18:49:58,136 | INFO | Audit passed: the site is coherent with the repository.
```

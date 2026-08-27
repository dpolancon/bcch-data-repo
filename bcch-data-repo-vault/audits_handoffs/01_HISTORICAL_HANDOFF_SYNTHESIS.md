# Audit & Handoff 01: Historical Session Baseline & Absorption Synthesis

**Fecha de Absorción:** 2026-08-27  
**Repositorios:** `bcch-data-repo` (`main` / `site`), `dpolancon.github.io` (`master`)  
**URL en vivo:** <https://dpolancon.github.io/bcch/>

---

## 1. Contexto Inicial y Mandato del Proyecto

El proyecto se enmarca en la investigación econométrica sobre **determinantes financieras de la inflación del precio del suelo metropolitano en Chile (1983–2024)** (Fondecyt framework). La Base de Datos Estadísticos (BDE) del Banco Central de Chile (BCCh) constituye una de las ocho capas de información del proyecto, coordinada junto con el Boletín del Mercado del Suelo (BMS/IPSS), el Conservador de Bienes Raíces (CBR), el Servicio de Impuestos Internos (SII), el Instituto Nacional de Estadísticas (INE) y el Ministerio de Vivienda y Urbanismo (MINVU).

El entregable central es un **sitio web de investigación empírica modular, reproducible e interactivo**, alojado en GitHub Pages, con paneles de datos limpios en formato CSV transparente (Data, Code & Outputs).

---

## 2. El Hallazgo Estructural Inicial: Asimetría de Escalas

El censo automatizado del catálogo (`scripts/13_census_bde.py`) reveló que la BDE publica 25.369 series únicas con una asimetría geográfica radical:

| Escala Observacional | Series Únicas | Participación (%) | Significado Institucional |
|:---|---:|---:|:---|
| **Nacional** | 21.287 | 83,9% | Mandato exclusivo de política monetaria nacional. |
| **Sectorial-Regional** | 2.331 | 9,2% | Cuentas Nacionales desglosadas por rama de actividad. |
| **Regional** | 1.695 | 6,7% | Totales regionales por actividad y finanzas locales. |
| **Macro-Zona** | 56 | 0,2% | Estadísticas experimentales e índice IPV (7 zonas). |
| **Metropolitana** | **0** | **0,0%** | **Ausencia total en el catálogo del Banco Central.** |

**Conclusión Metodológica:** La BDE mide las escalas que al Banco Central le interesa gobernar. El nivel metropolitano (donde se captura la renta urbana) no existe en la BDE y debe construirse agregando datos regionales o zonales hacia arriba.

---

## 3. Estado Inicial Absorbiendo la Sesión Previa

Al momento del traspaso inicial, el repositorio contaba con la siguiente cobertura:

1. **Reportes 1 a 4:**
   - Reporte 1 (original): Disparidades regionales (PIB regional, Gini vs. HHI).
   - Reporte 2 (original): Cobertura de datos y censo BDE.
   - Reporte 3: Los dos ejes (renta espacial Sector 10 vs. renta de recursos Sector 03).
   - Reporte 4: Ciclo de la construcción (permisos de edificación SAH/NVA vs. valor agregado).
2. **Reportes Pendientes por Construir:**
   - Reporte 5 (`housing_wealth`): Inmueble como reserva de valor (VALT vs. VALC e IPV).
   - Reporte 6 (`financial_depth`): Profundidad financiera y morosidad por región.
   - Reporte 7 (`interregional_trade`): Comercio interregional y sector dinámico.
   - Reporte 8 (`tasas`): El precio del dinero, TPM y apalancamiento de hogares.

---

## 4. Convenciones No Negociables del Repositorio

- **Invariancia y No-Sintetización:** Prohibido el uso de `np.random` o datos sintéticos en `scripts/`. Toda cifra se calcula dinámicamente desde el Banco Central.
- **CSV Exclusivo y Cero Parquet:** Todos los paneles analíticos se guardan y leen en CSV con `dtype={"region_id": str, "sector_id": str}` para preservar los ceros a la izquierda (`"01"` vs. `1`).
- **Inyección Implícita de Cifras (`@@TOKEN@@`):** Ninguna cifra de prosa se escribe a mano; se interpola dinámicamente desde los paneles CSV resueltos.
- **Compromiso de Autenticidad Narrativa:** Eliminación de muletillas de IA (*"Furthermore"*, *"Moreover"*) y adopción del registro académico directo (estilo López, Meza & Gasic, 2014).

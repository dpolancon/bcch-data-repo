# Bóveda de Traspasos y Auditorías del Proyecto BDE BCCh (`audits_handoffs`)

**Repositorios Relacionados:** `bcch-data-repo` (`main`), `bcch-site` (`site`), `dpolancon.github.io` (`master`)  
**Sitio Público en Vivo:** <https://dpolancon.github.io/bcch/>

---

## Estructura Interrelacionada de Documentos de Traspaso y Auditoría

Esta carpeta contiene el compendio interrelacionado de auditorías y documentos de traspaso de sesión que documentan el desarrollo, la arquitectura y el despliegue del sitio de investigación empírica sobre los datos del Banco Central de Chile:

1. **[`01_HISTORICAL_HANDOFF_SYNTHESIS.md`](01_HISTORICAL_HANDOFF_SYNTHESIS.md)**  
   - *Síntesis Histórica de Absorción:* Absorbe y sintetiza el estado base de la sesión previa (`HANDOFF_SESION.md`), el hallazgo estructural de asimetría de escalas (25.369 series del BCCh), las convenciones no negociables del repositorio y la justificación metodológica.

2. **[`02_REPORTS_BUILD_AND_INVARIANCE_AUDIT.md`](02_REPORTS_BUILD_AND_INVARIANCE_AUDIT.md)**  
   - *Construcción de Reportes y Motor de Auditoría:* Documenta la construcción completa de los Reportes 3 a 8, los scripts generadores de figuras (`fig3_1_dos_ejes.png`, `fig6_*`, `fig7_*`, `fig8_*`), la dinámica del empleo en la construcción (Reporte 4), la clarificación de proxy de renta espacial (Reporte 3) y el motor de auditoría forense (`11_audit_site.py`).

3. **[`03_NARRATIVE_REORDERING_AND_IMPLICIT_HYPOTHESIS_AUDIT.md`](03_NARRATIVE_REORDERING_AND_IMPLICIT_HYPOTHESIS_AUDIT.md)**  
   - *Reordenamiento Lógico y Prosa Implícita:* Registra la reestructuración secuencial del sitio (elevando Cobertura de Datos a Reporte 1), la purga total de códigos de hipótesis explícitos (`H1`, `Objetivo 1-4`, `formulación Fondecyt`) a prosa autónoma y la integración del benchmark Heterodata.org (Data, Code & Outputs).

4. **[`04_TRI_REPOSITORY_DEPLOYMENT_HANDOFF.md`](04_TRI_REPOSITORY_DEPLOYMENT_HANDOFF.md)**  
   - *Arquitectura Tri-Repositorio y Despliegue en Vivo:* Explica el flujo de trabajo entre `bcch-data-repo` (`main`), `bcch-site` (`site`) y `dpolancon.github.io/bcch` (`master`), la secuencia del pipeline de comandos, la verificación de commits y los resultados de respuesta HTTP 200 OK en vivo.

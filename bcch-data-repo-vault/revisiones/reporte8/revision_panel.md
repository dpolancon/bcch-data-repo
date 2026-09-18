# Revisión por pares — Reporte 8, «El precio del dinero»

**Fecha:** 2026-08-29 · **Modo:** `full`
**Material:** `reportes/report8-tasas.qmd`, `briefings/briefing_tasas.md`,
`data/panel_tasas_annual.csv`, `..._summary.csv`, `..._monthly.csv`

---

## Revisor 1 — Metodología y medición

**Recomendación: revisión mayor.**

**M1 · Las cifras publicadas no están en el CSV que la página enlaza. [CRÍTICO]**
La línea de fuente remite a `panel_tasas_annual.csv`. Las cifras del cuerpo salen de
`panel_tasas_summary.csv`, que registra extremos **sub-anuales**. No coinciden ni en
valor ni en año:

| Serie | Publicado (summary) | En el CSV enlazado (anual) |
|---|---|---|
| Deuda/ingreso, mínimo | 17,8% en 2004 | 17,87% en **2003** |
| Deuda/ingreso, máximo | **47,8%** en 2022 | **45,94%** en **2023** |

Un lector del equipo que descargue el archivo enlazado para verificar el 47,8% no lo
encontrará, y hallará el máximo en otro año. Lo mismo ocurre con la TPM: el máximo
publicado, 12,76% en 1998, es un extremo mensual; el promedio anual de 1998 es 9,01%.

El problema es sistémico y no de este reporte: **el sitio mezcla series de promedio anual
con extremos sub-anuales sin rotular cuál es cuál**. La misma confusión produjo las
anotaciones incorrectas de las figuras 8.1 y 8.2 que se corrigieron el 2026-08-28. La
regla de «una copia de cada artefacto» tiene aquí su equivalente pendiente: una
agregación declarada por cada cifra.

**M2 · «Multiplicándose por 2,7 veces» es una razón entre mínimo y máximo. [MAYOR]**
No es el crecimiento del período: es el cociente entre el punto más bajo (2004) y el más
alto (2022), dos años elegidos por ser extremos. Del inicio al presente el factor es
2,47. La tabla rotula las columnas como mínimo y máximo históricos, así que el dato es
honesto; la entradilla, que dice «se multiplicó por 2,7 veces», no lo aclara.

**M3 · La cobertura desigual se declara pero no se aplica. [MENOR]**
La nota metodológica dice que captación y colocación inician en 1983, la TPM en 1995 y
las hipotecarias en 2002. La Tabla 1 se titula «(1995–2026)» y mezcla ambas filas, de
modo que el «mínimo histórico» de cada serie corresponde a ventanas distintas.

---

## Revisor 2 — Dominio

**Recomendación: revisión mayor.**

**D1 · La entradilla afirma causalidad en un programa que se declara descriptivo.
[CRÍTICO]**
«El desplome de la tasa de créditos hipotecarios … **constituyó el principal estímulo
financiero a la valorización del suelo**.» Es una atribución causal con jerarquía —«el
principal»— sobre un reporte que no estima nada, en un sitio cuya página de metodología
declara que «donde el texto dice "acompaña", "corre contra" o "coincide con", debe leerse
literalmente y no como una afirmación de causalidad».

R8 es el reporte que mejor conecta con H1 de todo el programa, y lo hace pasándose al
otro extremo: donde los demás no dicen nada, este da la hipótesis por establecida. H1 es
lo que el proyecto va a **contrastar**; el reporte de datos no puede darlo por resuelto
en la primera línea.

**D2 · El reporte anuncia regresores que el panel no contiene. [MAYOR]**
«La BDE concentra a escala nacional el conjunto completo de regresores financieros
requeridos … las expectativas de mercado, las tasas de colocación bancaria a largo plazo
(`VIV`), la curva soberana en UF (`BCU`) y los ratios de apalancamiento (`DEUBH`).» El
panel ingerido tiene siete indicadores: TPM, tasa hipotecaria, tres expectativas de TPM y
dos ratios de deuda. **No hay `BCU`, ni captación y colocación, ni IPSA.** La nota
metodológica refuerza la impresión al decir «bonos BCU en 2002», como si estuvieran.

La afirmación sobre el catálogo es correcta; la que el lector infiere sobre el reporte no
lo es. Conviene separar lo que la BDE publica de lo que este panel ingirió.

---

## Revisor 3 — Perspectiva

**Recomendación: aceptar con revisión menor.**

**P1 · La advertencia de escala es el mejor párrafo del sitio. [ELOGIO]**
El recuadro que explica que las tasas son un precio único de la economía, y que por eso
la escala nacional no es una carencia sino la escala correcta del objeto, resuelve en
cuatro líneas la tensión que arrastra todo el programa. Es el modelo para el resto.

**P2 · Un reporte nacional en un programa de asimetría de escalas. [MENOR]**
El sitio se organiza sobre el hallazgo de que la BDE mide lo que al Banco Central le
interesa gobernar. R8 es el único reporte que vive enteramente en la escala dominante y
no comenta esa coincidencia: las tasas son abundantes en el catálogo por la misma razón
por la que la escala metropolitana está ausente. Es una observación que el programa ya
tiene y este reporte podría cerrar.

---

## Abogado del diablo

**El reporte confunde disponibilidad con evidencia.** Documenta que las tasas cayeron y
que la deuda subió. Eso no distingue H1 de H2: en un modelo con fundamentos reales
—crecimiento del ingreso, urbanización, restricción de oferta— también se esperaría más
deuda y precios más altos, y las tasas habrían caído igual por razones globales. El
reporte presenta el co-movimiento como si sólo fuera compatible con H1.

**Prueba del «¿y qué?».** La pasa: es la capa de regresores del proyecto. Pero el reporte
se atribuye una conclusión —«el principal estímulo»— que sólo el trabajo econométrico
posterior puede entregar. Su función es dejar la serie lista y declarar sus límites, no
adelantar el resultado.

**Contraargumento más fuerte.** Si la caída de tasas fuese la causa principal, la
valorización debería ser mayor donde el crédito hipotecario es más profundo. R6 muestra
que la mora hipotecaria es baja en todas partes y R5 que la RM **pierde** participación en
la riqueza inmobiliaria. Ninguno de esos hechos entra en R8.

---

## Editor del programa (EIC)

R8 es el reporte mejor escrito del programa y el que más se excede. Su párrafo de escala
es ejemplar, su conexión con la formulación es explícita y su nota metodológica declara
las ventanas. A cambio, afirma causalidad en la primera línea, cita cifras que no están
en el archivo que enlaza, y anuncia un conjunto de regresores más amplio que el que
ingirió.

1. **¿H1/H2?** Es el único que lo dice, y lo dice de más (D1).
2. **¿Robusto?** La trayectoria de la TPM y de la tasa hipotecaria, y los ratios de deuda.
   **No robusto:** nada que dependa de comparar extremos sub-anuales con la serie anual
   (M1), y la jerarquía causal de la entradilla.
3. **¿Sin respaldo?** «El principal estímulo» (D1); el conjunto completo de regresores
   (D2); y los extremos citados frente al CSV enlazado (M1).

---

## Decisión editorial

**REVISIÓN MAYOR.** Dos hallazgos CRÍTICOS.

### Consenso
Los cinco coinciden en que el reporte tiene el mejor oficio del programa y que sus
defectos son de exceso, no de omisión: es el único que dice de más.

### Desacuerdo
R1 quiere que las cifras se tomen del panel anual para que coincidan con el CSV enlazado;
R2 sostiene que el extremo mensual es la cifra sustantiva —la TPM tocó 0,50%, y eso es un
hecho— y que lo que falta es el rótulo. **Arbitraje:** a favor de R2. Cambiar a promedios
anuales empobrecería el reporte. La corrección es declarar la agregación en cada cifra y
enlazar el CSV que efectivamente la contiene.

### Hoja de ruta priorizada

| # | Acción | Clase | Origen |
|---|---|---|---|
| 1 | Rotular la agregación de cada extremo —mensual o promedio anual— y enlazar `panel_tasas_summary.csv` donde las cifras provienen de él | Mayor | M1 |
| 2 | Reescribir la entradilla sin atribución causal jerárquica: describir el co-movimiento y remitir el contraste al trabajo econométrico | Mayor | D1 |
| 3 | Separar lo que la BDE publica de lo que este panel ingirió; nombrar `BCU`, captación y colocación e IPSA como pendientes | Mayor | D2 |
| 4 | Aclarar que el factor 2,7 es la razón entre mínimo y máximo históricos, no el crecimiento del período | Menor | M2 |
| 5 | Declarar que las filas de la Tabla 1 tienen ventanas de cobertura distintas | Menor | M3 |
| 6 | Cerrar la observación sobre por qué esta capa es abundante y la metropolitana no existe | Menor | P2 |

### Grado de evidencia sugerido

**Cobertura completa** para TPM y tasa hipotecaria en su ventana declarada, con la
salvedad de que las series del conjunto de regresores no están todas ingeridas. El grado
no aplica a la afirmación causal de la entradilla, que debe retirarse.

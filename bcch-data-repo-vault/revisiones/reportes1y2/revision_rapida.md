# Revisión rápida — Reportes 1 y 2

**Fecha:** 2026-08-29 · **Modo:** `quick` (sólo editor; sin panel de cinco)
**Razón del modo:** ambos provienen de la cadena LaTeX antigua y son inventario y
descriptiva regional; no cargan el argumento del proyecto.

---

# Reporte 1 — «Reporte de cobertura de datos regionales»

**Evaluación: aceptar con revisión menor.** Es el reporte metodológicamente más sólido
del programa.

## Lo que hace bien, y conviene no tocar

La **reconciliación entre el capítulo y el universo del pipeline** es el mejor párrafo
técnico del sitio. Distingue 3 881 filas de catálogo de 2 306 códigos únicos, explica por
qué el catálogo repite un código bajo varios cuadros con un ejemplo concreto, y remata
con la cifra que importa: **1 785 series regionales viven fuera del capítulo
*Regionales***, de modo que un inventario construido sobre el capítulo las omitiría. Ese
razonamiento —el capítulo es metadato editorial, no filtro— es el que justifica toda la
arquitectura de selección del repositorio, y está donde debe estar.

Es también el único reporte del programa que **anticipa la objeción del lector y la
responde con datos** en vez de declararla como límite.

## Problemas

**Q1 · Los números no usan formato español. [MENOR]**
«2306 series», «3881 filas», «1785 series». El resto del sitio escribe 25.369 y 12,04
mediante `site_lib.es()`. R1 imprime enteros crudos. Es visible al cambiar de página.

**Q2 · El badge de escala no corresponde. [MENOR]**
Dice «SECTORIAL-REGIONAL · 16 regiones × 13 sectores». R1 no es un reporte
sectorial-regional: es el censo de cobertura del catálogo regional, y su propia tabla de
reconciliación abarca cuatro capítulos y cuatro frecuencias. El badge le impone la
geometría de R3.

**Q3 · Restos de su vida anterior como documento LaTeX. [MENOR]**
«Esta versión expandida pone especial énfasis en el Desarrollo Sectorial Integrado» no
significa nada para quien llega por el sitio: no hay una versión no expandida. Los
encabezados llevan negrita dentro del propio encabezado (`## **1. Resumen…**`), que el
resto del sitio no usa.

**Q4 · Falta el cierre. [MENOR]** Como todos salvo R8, no dice qué implica el hallazgo
—la asimetría de escalas— para H1 o H2. Aquí la respuesta es de programa más que de
hipótesis, y por eso mismo vale la pena escribirla.

---

# Reporte 2 — «Disparidades económicas regionales en Chile»

**Evaluación: revisión mayor.**

## Q5 · El reporte hace exactamente lo que la página de metodología prohíbe. [CRÍTICO]

R2 declara usar cifras «medidas en volumen encadenado, año de referencia 2018» y con
ellas construye la columna **«Participación en el PIB Nacional (%)»**: Metropolitana
45,92%, Antofagasta 9,39%, y así hasta sumar 100%.

La página de metodología del mismo sitio dice:

> Las participaciones sectoriales se calculan sobre precios corrientes. Los volúmenes
> encadenados **no son aditivos**: la suma de los sectores no reproduce el total
> regional, de modo que una participación construida sobre volúmenes no sería una
> proporción del producto regional sino un cociente sin denominador interpretable.

La no aditividad del encadenamiento opera igual entre regiones que entre sectores. La
columna de participación de R2 es precisamente el cociente que la metodología declara
ininterpretable, y la nota de familia de `two_axes` repite la misma advertencia.

**Consecuencia visible:** R2 publica que la RM es el **45,92%** del producto nacional. El
panel de R3, en precios corrientes, da **41,7%** para 2025. Dos páginas del mismo sitio
afirman participaciones distintas para la misma región sin reconciliarlas. R1 demuestra
que este programa sabe hacer una reconciliación cuando decide hacerla; acá falta.

## Q6 · La unidad de la Tabla 1 está equivocada por mil. [CRÍTICO]

La columna se rotula «PIB Promedio (**Miles de Millones de CLP**)» y asigna **78,49** a
la Región Metropolitana. Setenta y ocho mil millones de pesos son del orden de ochenta
millones de dólares: el producto de una empresa mediana, no de una región que concentra
la mitad de la economía chilena. La magnitud corresponde a **billones** de pesos —millones
de millones—, consistente con los 128 mil millones de miles que registra el panel de R3.
Toda la columna está mal rotulada.

## Q7 · Formato numérico en convención inglesa. [MAYOR]

«78.49», «45.92%», «2.04%», «4.79»: punto decimal en todas las tablas y epígrafes de R2,
mientras el resto del sitio usa coma. En español «78.49» se lee como setenta y ocho mil
cuarenta y nueve. Sumado a Q6, un lector no puede saber qué magnitud tiene delante.

## Q8 · «Estructuralmente fijada» sobre doce años. [MENOR]

La entradilla afirma que «la geografía productiva de Chile está estructuralmente fijada».
El panel cubre 2013–2025. Doce años sostienen «no cambió en el período»; «estructuralmente
fijada» es una afirmación sobre el largo plazo que requiere el empalme hacia atrás que el
propio programa declara no haber hecho.

## Q9 · Falta el cierre H1/H2. [MENOR]

---

## Decisión

| Reporte | Decisión |
|---|---|
| R1 | **Aceptar con revisión menor** — cuatro correcciones cosméticas |
| R2 | **Revisión mayor** — dos hallazgos CRÍTICOS |

### Hoja de ruta priorizada

| # | Reporte | Acción | Clase |
|---|---|---|---|
| 1 | R2 | Recalcular las participaciones sobre precios corrientes, o declarar en el cuerpo que la columna no es una proporción interpretable | Mayor |
| 2 | R2 | Reconciliar el 45,92% de la RM con el 41,7% de R3, siguiendo el modelo de reconciliación de R1 | Mayor |
| 3 | R2 | Corregir la unidad de la Tabla 1: billones, no miles de millones | Mayor |
| 4 | R2 | Pasar todo el formato numérico a convención española vía `site_lib.es()` | Mayor |
| 5 | R2 | Acotar «estructuralmente fijada» al período que el panel cubre | Menor |
| 6 | R1 | Formato numérico español | Menor |
| 7 | R1 | Corregir el badge de escala | Menor |
| 8 | R1 | Eliminar los restos de «versión expandida» y la negrita dentro de encabezados | Menor |
| 9 | R1, R2 | Párrafo de cierre H1/H2 | Menor |

**Nota de implementación.** La prosa de R1 y R2 no vive en `10_generate_site.py` sino en
`scripts/03_report_coverage.py:305` y `scripts/04_analyze_regional.py:723`, que escriben
los markdown del vault. Las correcciones se aplican allí y requieren volver a correr esas
etapas antes de la 10.

### Grado de evidencia sugerido

| Reporte | Grado |
|---|---|
| R1 | **Cobertura completa** — es un censo del catálogo, no una inferencia |
| R2 | **Cobertura parcial** — 2013–2025 sin empalme hacia atrás, y la métrica de participación en disputa |

# Revisión por pares — Reporte 4, «El ciclo regional de la construcción»

**Fecha:** 2026-08-29 · **Modo:** `full`
**Material:** `reportes/report4-construccion.qmd`, `briefings/briefing_permits.md`,
`data/panel_permits_annual.csv`, `data/panel_two_axes_annual.csv`

---

## Revisor 1 — Metodología y medición

**Recomendación: revisión mayor.**

**M1 · La columna «Δ Sector 10 (pp)» publica fracciones rotuladas como puntos
porcentuales. Error de cien veces. [CRÍTICO]**
`10_generate_site.py:444` calcula `delta_s10 = s10_1 - s10_0` sobre `share`, que en
`panel_two_axes_annual.csv` es una **fracción** (0,0904), y lo imprime con el sufijo
« pp» sin multiplicar por 100. Los valores reales:

| Región | Publicado | Real |
|---|---:|---:|
| Metropolitana | +0,01 pp | **+0,71 pp** |
| Biobío | +0,02 pp | **+1,54 pp** |

El daño va contra el propio argumento del reporte. La tesis es que la renta espacial
creció mientras la cantidad construida se reducía a la mitad, y la columna que debía
mostrar ese crecimiento muestra dieciséis valores entre −0,00 y +0,02, es decir, nada.
La tabla desmiente en silencio a su propia entradilla. Corregir las unidades **refuerza**
el reporte.

La auditoría no lo detectó porque `audit_report4` verifica un conjunto declarado de
cifras esperadas y esta columna no está en él. Es el mismo hueco que dejó pasar
«7 655 059,97 billones de pesos» en R6: una unidad mal escalada que ninguna prueba mira.

**M2 · Biobío pierde territorio en 2018 y el reporte compara 2014 con 2025 como si
nada. [CRÍTICO]**
Ñuble se separa de Biobío en 2018. La Tabla 1 muestra Ñuble con «—» en 2014 y 435 mil m²
en 2025, y a Biobío cayendo de 1 532 a 480 mil m² —un **−68,6%** que es el segundo peor
del país—. Sumando el territorio que se le quitó, la caída de la unidad geográfica
comparable es **1 532 → 915, es decir −40,3%**, prácticamente el promedio nacional. La
cifra publicada mezcla un cambio administrativo con un ciclo económico y convierte a
Biobío en un caso extremo que no lo es. Toda comparación regional que cruce 2018 tiene
el mismo problema; el agregado nacional no lo tiene.

**M3 · El año base 2014 no es el máximo y no se justifica. [MAYOR]**
La serie nacional alcanza su máximo en **2015 con 15,47 millones de m²**, y 2019 llega a
14,09. Tomando 2014 (13,32) como base, la contracción publicada es −46,1%; desde el
máximo real de 2015 es **−53,6%**. La elección de base no se explica en ninguna parte y
altera la cifra titular en siete puntos.

**M4 · «Índice 109,9 frente a 53,9» compara dos cosas incomparables. [MENOR]**
Un índice de participación sectorial contra un índice de metros cuadrados. Ambos con
base 100 en 2014, pero el primero es un cociente acotado y el segundo una cantidad sin
techo. La divergencia es real; la forma de presentarla sugiere una razón entre
magnitudes homogéneas que no existe.

---

## Revisor 2 — Dominio

**Recomendación: revisión menor.**

**D1 · El reporte no discute su propio control, y el control es espectacular. [MAYOR]**
`CEYS` —constitución de empresas— pasa de **51 547 en 2014 a 202 406 en 2025**, casi
cuadruplicándose, mientras la edificación se reduce a la mitad. Entra en la Figura 4.1
como «control de dinamismo empresarial» y el texto no lo menciona una sola vez. Un
control que se mueve cuatro veces en la dirección opuesta a la variable de interés no
es un control: es un hallazgo, o bien es un indicador que mide otra cosa —constitución
formal de sociedades, no actividad—. Cualquiera de las dos lecturas merece un párrafo.

**D2 · La cadena causal del cierre excede lo que el dato sostiene. [MAYOR]**
El epígrafe de la Figura 4.3 afirma que la contracción de permisos «frena la generación
de puestos de trabajo regionales, acelerando la precarización laboral y la contracción
de la demanda agregada en las economías regionales». El panel no contiene una sola
serie de empleo, salarios ni demanda agregada. Es una cadena de tres eslabones sobre
datos que el programa no ha ingerido —y que existen en el catálogo, sin tocar, en el
capítulo Regionales—. En un sitio que declara alcance descriptivo, es la afirmación más
fuerte de todo el reporte y la peor sostenida.

**D3 · El argumento de discriminación precio/cantidad es el mejor del programa. [ELOGIO]**
Contrastar el sector 10 con metros cuadrados autorizados para separar valorización de
formación de capital está bien planteado y es exactamente lo que la nota de familia de
`two_axes` dejaba pendiente. Conviene decir explícitamente en el cierre que este es el
reporte donde el supuesto de alquiler imputado se pone a prueba, no sólo se declara.

---

## Revisor 3 — Perspectiva

**Recomendación: revisión menor.**

**P1 · Permisos no son construcción, y el título dice construcción. [MAYOR]**
La nota de familia lo advierte —«son permisos: intención de construir, no construcción
ejecutada»— y la página no lo repite. El título del reporte es «El ciclo regional de la
construcción». En un ciclo de tasas al alza la brecha entre permiso y obra ejecutada se
ensancha, justo en el tramo final de la serie. La advertencia pertenece al cuerpo.

**P2 · Arica y Parinacota +85,3% sobre una base de 81 mil m². [MENOR]**
El mayor crecimiento de la tabla ocurre en la región más pequeña, sobre una base
diminuta. Sin una nota, el ordenamiento por variación porcentual premia el ruido.

---

## Abogado del diablo

**[CRÍTICO] Con las unidades corregidas, la tabla podría no decir lo que el reporte
quiere.** El argumento es «la renta espacial creció mientras la cantidad cayó». Con la
corrección de M1, Biobío sube +1,54 pp de renta espacial y cae −68,6% (o −40,3%) en
superficie: el desacople existe. Pero conviene verificar región por región antes de
reafirmar la tesis, porque parte del alza del sector 10 puede ser puramente aritmética:
si el resto del producto regional se contrae, la participación de vivienda sube sin que
nada se valorice. El reporte no distingue numerador de denominador, igual que R3.

**Prueba del «¿y qué?».** Esta sí la pasa: si permisos y renta espacial se movieran
juntos, H2 ganaría y H1 perdería. El reporte tiene contenido discriminante y no lo
enuncia como tal.

**Selección de extremos.** 2014 y 2025 otra vez, con el máximo real en 2015 (M3).

---

## Editor del programa (EIC)

R4 es el reporte con el mejor diseño argumental del programa y la ejecución numérica más
descuidada. La idea —separar precio de cantidad para poner a prueba el supuesto que R3
sólo declara— es exactamente lo que el encargo necesita. Pero publica una columna con
un error de escala de cien veces, compara regiones a través de un cambio de fronteras
administrativas y cierra con una cadena causal sobre empleo y demanda agregada que no
tiene ningún dato detrás.

1. **¿Qué implica para H1/H2?** Está implícito y bien planteado, pero no escrito. Es el
   reporte que más fácil lo tiene: el desacople precio-cantidad es evidencia a favor de
   H1 sobre H2.
2. **¿Qué es robusto?** La contracción nacional de la edificación, que no depende de
   fronteras regionales ni de la columna defectuosa. **No robusto:** toda comparación
   regional que cruce 2018, y la magnitud exacta de la caída, sensible al año base.
3. **¿Afirmaciones sin respaldo?** La cadena empleo-precarización-demanda agregada (D2),
   y la columna de puntos porcentuales (M1), que es directamente falsa.

---

## Decisión editorial

**REVISIÓN MAYOR.** Dos hallazgos CRÍTICOS.

### Consenso
Los cinco coinciden en que el argumento central es sólido y en que los defectos son de
ejecución, no de diseño. R1 y DA convergen en que la corrección de unidades cambia lo
que la tabla dice.

### Desacuerdo
R2 quiere borrar la cadena causal del cierre; R3 sostiene que la intuición es correcta y
que el problema es que los datos que la sostendrían están en el catálogo sin ingerir.
**Arbitraje:** se borra del reporte y se convierte en pregunta abierta que nombra la
familia que la respondería —`empleo`, capítulo Regionales, 78 series regionales—.

### Hoja de ruta priorizada

| # | Acción | Clase | Origen |
|---|---|---|---|
| 1 | Corregir la escala de «Δ Sector 10 (pp)»: multiplicar por 100 en `10_generate_site.py:444` | Mayor | M1 |
| 2 | Añadir a `audit_report4` la verificación de esa columna, para que el hueco se cierre | Mayor | M1 |
| 3 | Declarar la creación de Ñuble en 2018 y marcar Biobío como no comparable, o publicar la serie Biobío+Ñuble | Mayor | M2 |
| 4 | Justificar el año base o desplazarlo al máximo de 2015, declarando el efecto sobre la cifra titular | Mayor | M3 |
| 5 | Eliminar la cadena empleo-precarización-demanda y sustituirla por la pregunta abierta | Mayor | D2 |
| 6 | Discutir CEYS: cuadruplicarse mientras la edificación cae exige lectura | Mayor | D1 |
| 7 | Trasladar al cuerpo la advertencia de que son permisos, no obra ejecutada | Menor | P1 |
| 8 | Párrafo de cierre H1/H2 | Menor | EIC |
| 9 | Nota sobre las variaciones porcentuales de base pequeña | Menor | P2 |
| 10 | Renumerar las figuras a 4.1 / 4.2 / 4.3 como el resto del programa | Editorial | — |

### Grado de evidencia sugerido

**Cobertura parcial.** Dieciséis regiones y serie mensual completa 2014–2025, pero la
comparación regional está rota por el cambio de fronteras de 2018 y el agregado depende
del año base elegido.

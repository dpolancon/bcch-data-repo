# Revisión por pares — Reporte 3, «Los dos ejes: renta espacial y renta de recursos»

**Fecha:** 2026-08-29 · **Modo:** `full` (cinco revisores independientes + síntesis editorial)
**Material revisado:** `reportes/report3-dos-ejes.qmd`, `briefings/briefing_two_axes.md`,
`metodologia.qmd`, `data/panel_two_axes_annual.csv`, `data/panel_two_axes_summary.csv`
**Encuadre declarado al panel:** reporte interno de revisión de datos para el equipo de
un Fondecyt; programa descriptivo por decisión; no se evalúa identificación causal.

---

## Fase 0 — Configuración del panel

| Revisor | Identidad | Foco |
|---|---|---|
| EIC | Editor del programa de revisión | Cumplimiento del encargo y utilidad para el investigador responsable |
| R1 | Cuentas nacionales y estadística regional | Validez de constructo y de medición |
| R2 | Economía política urbana heterodoxa | Operacionalización del marco de dos rentas |
| R3 | Geografía económica y crítica de la estadística oficial | Qué esconde la escala regional |
| DA | Abogado del diablo | La tesis central y la prueba del «¿y qué?» |

---

## Revisor 1 — Metodología y medición

**Recomendación: revisión mayor.**

**M1 · El ranking de renta espacial mide tamaño, no renta. [CRÍTICO]**
La participación sectorial es un cociente, y su dispersión entre regiones confunde
numerador y denominador. La lista de 2025 —La Araucanía 12,3%, Ñuble 11,8%,
Valparaíso 11,5%— no ordena regiones por intensidad de renta espacial: ordena por
ausencia de todo lo demás. La Araucanía pesa 3,0% del PIB nacional y Ñuble 1,5%. La
Región Metropolitana, con **41,7% del producto nacional**, aparece novena con 9,04%.
El reporte presenta el ranking sin esta advertencia y el lector lo leerá como un mapa
de dónde se captura renta espacial. No lo es.

**M2 · El Gini no está ponderado. [MAYOR]**
Un Gini sobre dieciséis participaciones trata a Aysén (0,65% del PIB) igual que a la
RM (41,7%). Para un programa que estudia la captura metropolitana de renta, el índice
sin ponderar describe la estructura del mapa regional, no dónde está la masa de renta.
`lib/stats.py` ofrece Gini ponderado y el reporte no declara cuál usa. Debe declararlo,
y justificar la elección o publicar ambos.

**M3 · El Gini de recursos está inflado por ceros estructurales. [MAYOR]**
En 2025 la minería es menos del 1% del producto regional en **seis de dieciséis
regiones**. Un Gini sobre una variable con ceros estructurales es mecánicamente alto:
0,6956 mide en buena parte que no hay minería en medio país. El propio reporte lo dice
en «Por qué importa» —«la geología no se redistribuye»— pero antes presenta el
contraste 0,1798 contra 0,6956 como si fuera un hallazgo económico. Es en gran medida
un hecho geológico expresado en notación de desigualdad.

**M4 · Comparación de extremos sobre una variable cíclica. [MAYOR]**
«La renta de recursos pasó de 14,08% a 14,13% —es decir, se mantuvo prácticamente
donde estaba.» En el intervalo la serie recorre de **10,76% (2016) a 15,48% (2021)**.
La participación minera en precios corrientes está dominada por el ciclo del cobre;
que 2013 y 2025 coincidan no es estabilidad, es coincidencia de fase. La afirmación
de estabilidad no sobrevive a mover un año cualquiera de los dos extremos.

**M5 · Dos decimales sobre una diferencia de 0,05 pp.** Invita a leer como señal lo que
es ruido de redondeo. Reportar la variación con la precisión que el dato sostiene.

---

## Revisor 2 — Dominio (economía política urbana)

**Recomendación: revisión mayor.**

**D1 · «Difusa» y el Gini dicen cosas opuestas. [CRÍTICO]**
La entradilla afirma que «la renta espacial es difusa y creciente». Su Gini pasó de
**0,1498 a 0,1798**, un aumento de 20% y el valor **más alto de toda la serie
justamente en el último año**. El nivel es bajo y el texto tiene razón en decir que la
renta espacial existe en todas partes; pero la dirección es hacia la concentración, no
hacia la difusión. Ambos ejes se concentraron en el período. La lectura honesta —y más
interesante— es que los dos se concentraron, uno desde base baja y otro desde base
alta, no que uno se difunde mientras el otro se endurece.

**D2 · «Creciente» es un artefacto de los extremos elegidos. [CRÍTICO]**
La participación media de renta espacial no crece de forma sostenida: sube hasta
**9,18% en 2022** y **cae tres años consecutivos** hasta 8,66% en 2025. El reporte
compara sólo 2013 con 2025 y el descenso desaparece. Para este proyecto en particular
esa omisión es costosa: una caída de la renta espacial que arranca en 2022 coincide con
el ciclo de alza de tasas, y es el hecho más directamente relevante para H1 que
contiene el panel. El reporte lo tiene en los datos y no lo dice.

**D3 · El reporte no dice qué implica para H1 ni para H2. [MAYOR]**
Es la pregunta que el encargo pone primero y el texto no la responde. Peor: la
respuesta obvia es contraintuitiva y merece discusión. El sector 10 es alquiler
imputado, es decir una **valorización**, no un flujo real: se mueve con el precio de la
vivienda. Una participación creciente del sector 10 puede ser evidencia *a favor de H1*
—capitalización por caída de la tasa de descuento— antes que evidencia sobre
fundamentos reales. El reporte usa el eje espacial como si fuera H2 sin discutirlo.

**D4 · El sector 03 no es el análogo de renta que el marco postula. [MENOR]**
El marco de crecimiento desbalanceado opone captura de renta a producción. El valor
agregado minero incluye salarios, depreciación y retorno normal al capital, no sólo
renta de recursos. Llamarlo «renta de recursos» sin matizar sobreestima el eje. La
advertencia que el reporte sí hace para el sector 10 no tiene equivalente para el 03.

---

## Revisor 3 — Perspectiva (geografía económica)

**Recomendación: revisión menor.**

**P1 · La conclusión se contradice con su propia tabla. [MAYOR]**
«La renta espacial acompaña a la población: donde hay gente hay vivienda.» Las tres
regiones que el reporte nombra en cabeza no son donde está la gente, y la región más
poblada del país queda novena. Como está escrita, la frase es refutada por el dato que
la precede tres párrafos antes.

**P2 · La región es la unidad equivocada para la tesis, y conviene decirlo acá. [MAYOR]**
La renta espacial se captura en submercados urbanos; la región promedia Santiago con
las comunas rurales de la RM. El sitio declara esta limitación en la página de
metodología y en el índice, pero R3 es el reporte que *opera* el eje espacial y no la
repite. La advertencia debe estar donde se usa el constructo.

**P3 · La ventana 2013–2025 excluye el tramo que al proyecto le importa. [MENOR]**
La nota de familia explica que antes de 2013 hay que empalmar bases de referencia y que
el reporte no cruza ese límite. La consecuencia —el panel no cubre la fase de tasas
bajas previa— no aparece en la página. Es la misma limitación que R7 sí declara.

---

## Abogado del diablo

**Cuestión central.** La tesis es «son dos geografías distintas dentro del mismo país».
El contraargumento más fuerte: los datos sostienen algo más débil y más banal —que la
minería está concentrada donde hay yacimientos y la vivienda está en todas partes
porque en todas partes vive gente—. Eso no es un hallazgo sobre dos regímenes de renta
en competencia; es una descripción de la geología y de la demografía. Para que la tesis
de los dos ejes tenga contenido, el reporte tendría que mostrar que compiten por el
mismo excedente, y no muestra ninguna relación entre ambos.

**Prueba del «¿y qué?».** Si el resultado se invirtiera —si la renta espacial estuviera
concentrada y la minera difusa— ¿cambiaría alguna decisión del proyecto? El reporte no
lo dice, y esa es la señal de que le falta el párrafo de cierre.

**Selección de casos.** Se nombran tres regiones por eje, elegidas por ser los extremos,
sobre dieciséis. El lector no puede ver si hay estructura o sólo colas.

**[CRÍTICO] · La Figura 3.1 no grafica lo que su título afirma.**
El título dice «Matriz de los Dos Ejes: Renta Espacial vs. Renta de Recursos (2025)».
Sus ejes son apertura interregional y autocontención intrarregional, y se dibuja desde
`panel_interregional_trade_summary.csv` —el panel del Reporte 7—, mientras la línea de
fuente de la página enlaza `panel_two_axes_annual.csv`. Los cuadrantes rotulan «Renta
Espacial Dominante» y «Renta Primario-Exportadora» sobre ejes que miden comercio. El
epígrafe describe correctamente la figura real y por lo tanto contradice al título que
tiene encima. Ninguna cifra del cuerpo del reporte aparece en la única figura que lo
acompaña.

---

## Editor del programa (EIC)

R3 cumple su función de puesta en marcha: es la familia que no requiere llamadas a la
API y prueba la cadena completa. La prosa es densa y sin relleno, las cifras se
interpolan del panel y el supuesto del alquiler imputado se declara en el cuerpo, como
corresponde. El problema no es el oficio sino que **el reporte cuenta una historia más
simple que la que sus propios datos contienen**, y la simplificación va en la dirección
de confirmar el marco en vez de tensionarlo.

Sobre las tres preguntas del encargo:

1. **¿Qué implica para H1 o H2?** No lo dice, y tiene material para decirlo (D2, D3).
2. **¿Qué es robusto?** El nivel y el orden de magnitud del contraste entre ejes. **No
   es robusto** nada que dependa de comparar 2013 con 2025: ni «creciente», ni «se
   mantuvo donde estaba» (M4, D2). El ranking de 2025 es un corte único y además
   confundido por el denominador (M1).
3. **¿Hay afirmaciones que el dato no sostiene?** Tres: «difusa» contra su propio Gini
   (D1), «creciente» contra la caída 2022–2025 (D2), y «acompaña a la población» contra
   su propia lista (P1).

---

## Decisión editorial

**REVISIÓN MAYOR.** El abogado del diablo levantó un hallazgo CRÍTICO —la figura
equivocada—, de modo que la regla del skill impide una decisión de aceptación.

### Consenso de los cinco

- La comparación 2013 contra 2025 sostiene dos afirmaciones que la serie completa
  desmiente. Es el problema de fondo y lo levantan R1, R2 y el EIC por vías distintas.
- Falta el párrafo de cierre sobre H1/H2. Lo piden R2, DA y el EIC.

### Desacuerdo

R1 quiere ponderar el Gini; R3 sostiene que ponderar no arregla nada porque la región
es la unidad equivocada de todas formas. **Arbitraje:** ambas cosas son ciertas y no se
excluyen. Declarar que el Gini es sin ponderar y qué significa eso es barato y honesto;
sustituir la escala regional no está disponible en este catálogo.

### Hoja de ruta priorizada

| # | Acción | Clase | Origen |
|---|---|---|---|
| 1 | Reparar la Figura 3.1: o se dibuja la matriz de los dos ejes desde `panel_two_axes_annual.csv`, o se retitula y se traslada a R7 | Mayor | DA |
| 2 | Sustituir «difusa y creciente» por la lectura que el Gini y la serie sostienen: ambos ejes se concentraron; la renta espacial cayó tres años desde su pico de 2022 | Mayor | D1, D2 |
| 3 | Advertir que el ranking de participación mide también el tamaño del denominador, y nombrar el caso de la RM: novena en participación, 41,7% del producto | Mayor | M1, P1 |
| 4 | Añadir el párrafo de cierre H1/H2, incluida la ambigüedad de que el sector 10 es una valorización y puede ser evidencia de H1 y no de H2 | Mayor | D3 |
| 5 | Declarar si el Gini es ponderado y qué implica; declarar los ceros estructurales de minería | Menor | M2, M3 |
| 6 | Reescribir «acompaña a la población» o respaldarla con el dato que aún no existe en el programa | Menor | P1 |
| 7 | Declarar en la página que la ventana arranca en 2013 por el empalme de bases y qué deja fuera | Menor | P3 |
| 8 | Matizar que el valor agregado minero no es sólo renta de recursos | Menor | D4 |
| 9 | Bajar la precisión donde el dato no la sostiene | Editorial | M5 |

### Grado de evidencia sugerido para este reporte

**Cobertura parcial.** Dieciséis de dieciséis regiones, pero la ventana 2013–2025 no
cruza el empalme de bases y por tanto no cubre el tramo de tasas bajas anterior. El
ranking regional es un corte único.

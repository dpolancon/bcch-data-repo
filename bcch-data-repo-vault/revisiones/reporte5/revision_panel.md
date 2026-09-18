# Revisión por pares — Reporte 5, «El inmueble como reserva de valor»

**Fecha:** 2026-08-29 · **Modo:** `full`
**Material:** `reportes/report5-reserva-valor.qmd`, `briefings/briefing_housing_wealth.md`,
`data/panel_housing_wealth_annual.csv`

---

## Revisor 1 — Metodología y medición

**Recomendación: revisión mayor.**

**M1 · El año del techo histórico es falso. [CRÍTICO]**
La página afirma «alcanzando un techo histórico de **174,3%** del PIB en 2021». El valor
está interpolado del panel y es correcto; **el año está escrito a mano y es incorrecto**.
El máximo de `valor_vivienda_pib` ocurre en **2020**, y 2021 es el único año de caída de
toda la serie (164,1%). El reporte adjudica el techo precisamente al año del retroceso.

Es el mismo patrón que esta sesión corrigió en las figuras y en la prosa de R6, R7 y R8:
la cifra se deriva y el año no. Aquí ya produjo una afirmación falsa publicada.

**M2 · «+-0,4 pp». [MAYOR]**
La fila «Participación RM en Riqueza Nacional» de la Tabla 1 imprime `+-0,4 pp`. El
generador antepone «+» de forma incondicional en vez de condicionarlo al signo, como sí
hace R4 en su tabla equivalente. Es un defecto visible en la página en vivo.

**M3 · Los pesos son nominales y no se declara. [MAYOR]**
«+269,2%», «multiplicándose por 3,7 veces», «el valor del suelo creció 3,8 veces»: todo
en pesos corrientes de 2012 a 2024, sin deflactar. La razón sobre PIB (111,9% → 172,3%)
sí controla el nivel de precios y es la cifra defendible; las magnitudes en pesos, que
ocupan la entradilla, no. Conviene o deflactar, o marcar explícitamente que son
nominales y remitir a la razón sobre producto como la medida sustantiva.

**M4 · Doce años y un solo par de extremos. [MENOR]**
Mismo patrón que R3 y R4: 2012 contra 2024. Acá el sesgo es menor porque la serie es
casi monótona, pero conviene decirlo.

---

## Revisor 2 — Dominio

**Recomendación: revisión mayor.**

**D1 · Los datos chilenos no respaldan la premisa de Knoll et al., y el reporte no lo
dice. [CRÍTICO]**
El argumento declarado es que el encarecimiento secular responde «primordialmente a la
absorción de rentas de localización por parte del suelo urbano (`VALT`), y no al costo
físico de los materiales ni al reemplazo de estructuras construidas (`VALC`)». El
reporte anuncia que la BDE «permite evaluar esta premisa de manera directa». Los
resultados:

| | 2012 → 2024 |
|---|---|
| Terreno (`VALT`) | +282,4% |
| Construcción (`VALC`) | +260,7% |
| Participación del suelo | 39,1% → 40,5%, **+1,4 pp en doce años** |

Suelo y estructuras crecieron casi al mismo ritmo. En el caso chileno, y a escala
nacional, **la premisa de absorción por el suelo apenas se distingue de la nula**. El
reporte presenta ambas cifras, no las contrasta, y pasa al párrafo siguiente.

Esto es lo más importante que R5 tiene para decir, y es un resultado negativo. Las
convenciones de escritura del programa establecen que «el resultado nulo es hallazgo».
Aquí el hallazgo está en la tabla y no en la prosa.

**D2 · «La RM concentrando el 53,6%» describe una desconcentración. [MAYOR]**
La entradilla presenta la participación metropolitana como concentración. La serie va de
**54,0% a 53,6%**: la RM perdió participación. Es un movimiento pequeño y probablemente
sin significado, pero la palabra elegida apunta en la dirección contraria al signo. Es
la misma inclinación retórica que R3 tiene con «difusa».

**D3 · Falta el vínculo con H1, que aquí es directo. [MAYOR]**
Si el suelo no absorbe más que las estructuras, la vía por la que H1 opera no es la
recomposición del valor entre terreno y construcción sino la **capitalización del
conjunto**: todo el stock se revaloriza cuando cae la tasa de descuento. El reporte
tiene los datos para decirlo y no lo dice.

---

## Revisor 3 — Perspectiva

**Recomendación: revisión menor.**

**P1 · La descomposición es nacional y el reporte es de macro-zona. [MAYOR]**
El badge dice «MACRO-ZONA · 7 zonas» y el hallazgo central —la descomposición de Knoll—
sólo existe a escala nacional; la nota de familia lo advierte. La página lo dice de
pasada («a escala nacional») en un subtítulo. Debe ser una advertencia en el cuerpo: el
reporte de mayor promesa territorial del programa entrega su resultado principal sin
territorio.

**P2 · Siete «zonas» que no son siete zonas comparables. [MENOR]**
El panel mezcla `Nacional`, `Nacional -- casas`, `Nacional -- departamentos`, `Región
Metropolitana`, `Zona Norte`, `Zona Centro` y `Zona Sur`. Tres son cortes nacionales y
cuatro son territorios. El badge las cuenta como si fueran siete unidades geográficas.

---

## Abogado del diablo

**El reporte reproduce una figura de la formulación en vez de ponerla a prueba.** Se
declara que replica la Figura 4 de la formulación y se presenta como evaluación directa
de la premisa de Knoll. Pero cuando el dato no la confirma (D1), el texto no lo registra.
Un lector del equipo saldrá de la página creyendo que la absorción por el suelo quedó
documentada en Chile, y no es lo que muestra la tabla que acaba de leer.

**Prueba del «¿y qué?».** La pasa holgadamente en potencia y no en acto: el resultado
—que suelo y estructura se valorizan juntos— es más informativo para el proyecto que la
confirmación que se esperaba, porque redirige el mecanismo de H1 desde la recomposición
hacia la capitalización general.

**Contraargumento más fuerte.** `VALC` es valor **de mercado** de las estructuras, no
costo de reposición. Si se valoriza con el mismo factor de capitalización que el suelo,
la descomposición chilena no es comparable con la de Knoll et al., que usa costo de
construcción. En ese caso el resultado nulo no refuta la tesis: indica que la
descomposición publicada por la BDE no es la que la tesis requiere. **Esta distinción
decide cómo se lee todo el reporte y no aparece en ninguna parte.**

---

## Editor del programa (EIC)

R5 es el reporte con más peso teórico del programa y el que menos concluye. Reproduce
correctamente las magnitudes, respeta la restricción de escala y declara sus fuentes,
pero publica un año falso, un signo mal formateado, y —lo decisivo— deja sin enunciar el
único resultado que el lector no podía anticipar.

1. **¿H1/H2?** No lo dice, y es el reporte donde la respuesta es más consecuente (D3).
2. **¿Robusto?** La razón riqueza/PIB y su trayectoria. **No robusto:** las magnitudes en
   pesos sin deflactar (M3) y toda lectura de la participación del suelo mientras no se
   aclare si `VALC` es mercado o reposición (DA).
3. **¿Sin respaldo?** El techo en 2021 (M1) es directamente falso; «concentrando» (D2)
   contradice el signo.

---

## Decisión editorial

**REVISIÓN MAYOR.** Dos hallazgos CRÍTICOS, uno de ellos una afirmación falsa en vivo.

### Consenso
Los cinco convergen en que el resultado nulo de D1 es el hallazgo del reporte y está sin
escribir.

### Desacuerdo
R2 lee el resultado como refutación parcial de Knoll en Chile; el DA sostiene que puede
ser un artefacto de que `VALC` sea valor de mercado y no costo de reposición.
**Arbitraje:** el DA tiene razón en que la pregunta es previa. La corrección es enunciar
el resultado *y* la ambigüedad de constructo que impide interpretarlo, no elegir una de
las dos lecturas.

### Hoja de ruta priorizada

| # | Acción | Clase | Origen |
|---|---|---|---|
| 1 | Interpolar el año del techo desde `idxmax` del panel; hoy dice 2021 y es 2020 | Mayor | M1 |
| 2 | Enunciar el resultado: suelo y estructuras crecen casi igual, la participación del suelo sube 1,4 pp en doce años | Mayor | D1 |
| 3 | Aclarar si `VALC` es valor de mercado o costo de reposición, y qué implica para la comparabilidad con Knoll et al. | Mayor | DA |
| 4 | Condicionar el signo en la fila de participación RM: hoy imprime `+-0,4 pp` | Mayor | M2 |
| 5 | Declarar que las magnitudes en pesos son nominales; remitir a la razón sobre PIB | Mayor | M3 |
| 6 | Párrafo H1/H2: si el suelo no absorbe diferencialmente, el mecanismo es capitalización del conjunto | Mayor | D3 |
| 7 | Reemplazar «concentrando» por el signo real de la serie | Menor | D2 |
| 8 | Advertencia en el cuerpo: la descomposición sólo existe a escala nacional | Menor | P1 |
| 9 | Distinguir cortes nacionales de territorios en el recuento de zonas | Menor | P2 |

### Grado de evidencia sugerido

**Cobertura parcial.** Serie anual completa 2012–2024, pero el hallazgo central existe
sólo a escala nacional, nunca por zona, y su interpretación depende de una ambigüedad de
constructo aún sin resolver.

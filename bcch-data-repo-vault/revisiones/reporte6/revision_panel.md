# Revisión por pares — Reporte 6, «Profundidad financiera y morosidad por región»

**Fecha:** 2026-08-29 · **Modo:** `full`
**Material:** `reportes/report6-financiera.qmd`, `briefings/briefing_financial_depth.md`,
`data/panel_financial_depth_annual.csv`, `..._summary.csv`

---

## Revisor 1 — Metodología y medición

**Recomendación: revisión mayor.**

**M1 · La concentración metropolitana mide dónde se registra la cuenta, no dónde vive el
titular. [CRÍTICO]**
El hallazgo titular —la RM pasa de 57,6% a 80,5% de las cuentas corrientes de personas—
tiene un problema de validez de constructo que la propia Tabla 1 delata. La RM registra
**9 698 002 cuentas** sobre 12,04 millones nacionales, en una región que concentra
alrededor del 40% de la población del país. Y su **saldo medio por cuenta es 895,64 mil
pesos, frente a ~2,0–2,5 millones en las quince regiones restantes**: un tercio del
resto, sin excepción.

Ese patrón es exactamente el que produce la banca digital. Una cuenta abierta por
internet se adscribe a la casilla del banco, no al domicilio del titular, y el período
2009–2025 es el de la masificación de las cuentas digitales de bajo saldo. La serie
puede estar midiendo una práctica de registro bancario y no una geografía económica.

El reporte titula «centralización espacial de la liquidez» y lo lee como estructura
territorial. Con el saldo medio anómalo en la misma tabla, esa lectura no se sostiene
sin antes descartar el artefacto.

**M2 · Ñuble aparece con «0» cuentas en 2009. [MAYOR]**
Ñuble se crea en 2018. Publicar `0` afirma que existían cero cuentas corrientes en ese
territorio, cuando lo cierto es que el territorio no era una región y sus cuentas están
dentro de Biobío. R4 usa «—» para el mismo caso; R6 usa cero. Además, la cifra de Biobío
en 2009 no es comparable con la de 2025 por la misma razón.

**M3 · Los montos son nominales. [MENOR]**
462,64 miles de millones en 2009 contra 7,66 billones en 2025, sin deflactar y sin
declararlo.

---

## Revisor 2 — Dominio

**Recomendación: revisión menor.**

**D1 · La caída de la mora hipotecaria se atribuye a liquidez y probablemente sea
diferimiento. [MAYOR]**
El texto atribuye la caída de 2,22% a 0,32% al «período de liquidez extraordinaria
(2020–2021)». En esos años operaron programas masivos de postergación de dividendos
hipotecarios, que **suprimen mecánicamente la mora registrada** sin que mejore la
capacidad de pago. Sumado a los retiros de fondos previsionales, la explicación por
liquidez es plausible pero no es la única ni la más simple. Una mora que cae 86% en dos
años y repunta después es el perfil típico de una moratoria que termina.

**D2 · Nada conecta con H1, y la conexión existe. [MAYOR]**
La mora hipotecaria es el indicador de tensión del canal de crédito que H1 postula. Su
mínimo histórico coincide con el piso de tasas que documenta R8, y su repunte con el
alza. El reporte tiene los dos extremos y no traza la línea.

---

## Revisor 3 — Perspectiva

**Recomendación: revisión menor.**

**P1 · «Profundidad financiera» se mide sólo con cuentas a la vista. [MAYOR]**
El título promete profundidad financiera regional; el contenido son cuentas corrientes,
depósitos a la vista y mora por cartera. Falta todo el activo: colocaciones, crédito
hipotecario vigente, plazos. El reporte mide **liquidez transaccional**, que es una parte
estrecha de lo que el término nombra.

**P2 · La mora se presenta como riesgo y también es composición. [MENOR]**
Una región con poca cartera hipotecaria y mucha de consumo tendrá otra mora agregada sin
que su riesgo subyacente difiera. Sin el tamaño de cada cartera por región, la Tabla 2
ordena regiones por una mezcla de riesgo y composición.

---

## Abogado del diablo

**El hallazgo central puede no ser un hallazgo.** Si M1 es correcto, la afirmación más
citable del reporte —la liquidez se centraliza en Santiago— es un cambio en la práctica
de registro bancario. El reporte no ofrece ninguna prueba que distinga ambas hipótesis, y
el dato que la ofrecería —saldo medio por cuenta— está en la tabla apuntando en contra.

**Prueba del «¿y qué?».** Si la mora hipotecaria es la más baja del sistema y se mantiene
baja, el canal de crédito **no** muestra tensión, lo que es un resultado negativo
interesante para H1 y el reporte no lo enuncia como tal.

**Contraargumento.** El saldo medio bajo en la RM también sería consistente con una
población más bancarizada y de menores saldos individuales. Es una hipótesis rival
legítima, y precisamente por eso hay que discriminarlas en vez de no mencionar el asunto.

---

## Editor del programa (EIC)

R6 tiene la mejor cobertura temporal del programa y el peor problema de constructo. La
ejecución numérica es correcta —esta familia es la que enseñó al repositorio a declarar
unidades canónicas— pero el reporte lee una serie administrativa como si fuera geografía
económica.

1. **¿H1/H2?** No lo dice; la mora hipotecaria es el puente natural (D2).
2. **¿Robusto?** Las series de mora por cartera a escala nacional. **No robusto:** la
   concentración metropolitana mientras no se descarte el artefacto de registro (M1), y
   toda comparación regional que cruce 2018 (M2).
3. **¿Sin respaldo?** «Centralización espacial de la liquidez» como afirmación
   territorial (M1) y la atribución exclusiva a liquidez de la caída de la mora (D1).

---

## Decisión editorial

**REVISIÓN MAYOR.** Un hallazgo CRÍTICO de validez de constructo.

### Consenso
Los cinco coinciden en que la cifra de 80,5% no puede publicarse como geografía sin antes
descartar el registro bancario.

### Desacuerdo
R1 propone bajar la afirmación a descriptiva; el DA quiere retirarla hasta poder
discriminar. **Arbitraje:** se conserva la serie —es un dato real— y se reescribe la
interpretación, declarando explícitamente las dos lecturas rivales y que el dato
disponible no las separa. Retirar una serie oficial porque su interpretación es ambigua
sería peor que declarar la ambigüedad.

### Hoja de ruta priorizada

| # | Acción | Clase | Origen |
|---|---|---|---|
| 1 | Reescribir la interpretación de la concentración: declarar la hipótesis de registro bancario y el saldo medio anómalo de la RM como evidencia a su favor | Mayor | M1, DA |
| 2 | Sustituir el `0` de Ñuble 2009 por «—» y marcar Biobío como no comparable | Mayor | M2 |
| 3 | Añadir la moratoria hipotecaria 2020–2021 como explicación rival de la caída de la mora | Mayor | D1 |
| 4 | Párrafo H1/H2 usando la mora hipotecaria como indicador de tensión del canal de crédito | Mayor | D2 |
| 5 | Acotar el título o ampliar el contenido: hoy dice profundidad financiera y mide liquidez transaccional | Menor | P1 |
| 6 | Declarar que los montos son nominales | Menor | M3 |
| 7 | Advertir que la mora agregada mezcla riesgo y composición de cartera | Menor | P2 |

### Grado de evidencia sugerido

**Cobertura parcial.** Dieciséis regiones y serie mensual 2009–2025, pero el indicador
titular tiene validez de constructo en disputa y la comparación regional cruza el cambio
de fronteras de 2018.

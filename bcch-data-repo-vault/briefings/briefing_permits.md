# Nota de familia — `permits` (Reporte 4)

**Tier:** B (16 regiones) · **Frecuencia:** mensual
**Fuente:** `data/raw/regional-spatial-macro-dataset/raw_monthly.csv`
**Universo:** `universe_permits.csv` (64 series) · **Manifiesto:** `manifest_permits.csv`

Esta nota existe para que la próxima persona no tenga que reconstruir lo que ya
se aprendió aquí. No resume el reporte: describe los datos.

## Qué contiene la familia

Cuatro indicadores mensuales, cada uno para las 16 regiones. **64 series, cero
errores de descarga.**

| Mnemónico | Qué mide | Unidad | Fuente original |
|-----------|----------|--------|-----------------|
| `SAH` | Superficie autorizada habitacional | m² | INE |
| `SANH` | Superficie autorizada **no** habitacional | m² | INE |
| `NVA` | Número de viviendas autorizadas | unidades | INE |
| `CEYS` | Constitución de empresas y sociedades | unidades | — |

Las tres primeras son permisos de edificación: **intención de construir, no
construcción**. Un permiso autorizado puede no ejecutarse nunca. Es un
indicador adelantado del ciclo, no una medida de stock ni de producto.

## Por qué esta familia importa en el programa

El Reporte 3 dejó una pregunta abierta que el sector 10 no puede responder. La
renta espacial se mide ahí como *Servicios de vivienda e inmobiliarios*, que en
cuentas nacionales es en buena parte **arriendo imputado**: sube cuando suben
los precios de la vivienda, aunque no se construya un solo metro cuadrado
nuevo. Con sector 10 solo, precio y cantidad son indistinguibles.

`SAH` y `NVA` son cantidad pura, en metros y en unidades, sin precio de por
medio. Cruzarlos con el sector 10 y con el sector 06 (Construcción) separa las
dos historias: si la renta espacial crece mientras los permisos caen, lo que
crece es la valorización del stock existente, no la formación de capital.

## Cómo se leen los códigos

El código lleva la región **pegada al mnemónico**, no en un token posicional:

```
F034 . SAH AP . FLU . INE . Z . 0 . M
  0      1↑      2      3    4   5   6
         └── mnemónico + sufijo de región de dos letras
```

Los 16 sufijos, de norte a sur: `AP TA AN AT CO VA RM LI ML NB BI AR LR LL AI MA`.

Nunca escribir un parser nuevo para esto. `lib.regions.parse_region` ya resuelve
las cuatro codificaciones del catálogo y tiene la lista blanca de raíces
(`GLUED_FAMILY_STEMS`) que evita los falsos positivos de esta forma pegada.

### La trampa del subtoken: `NVA` dentro de `CCPNVA`

Encontrada al descargar esta familia. La selección por familia buscaba el token
en **cualquier posición del código**, y `F022.CCPNVA` —cuentas corrientes de
Valparaíso, que pertenece a `financial_depth` (Reporte 6)— contiene `NVA`.
Resultado: 66 series en vez de 64, con dos intrusas de otra familia y de otro
tier temático.

La corrección está en `SeriesFamily.matches()`: el token se ancla al
**mnemónico** (el segundo token del código), como prefijo y no como subcadena.
Es prefijo y no igualdad porque el sufijo de región va pegado. `SANH` y `SAH`
siguen siendo distintos bajo esta regla: `"SANHAP"` no empieza con `"SAH"`.

**Regla general:** un mnemónico de dos o tres letras aparecerá tarde o temprano
dentro de otro. Cualquier familia nueva se declara con `tokens` y se verifica
contando: si el total no es un múltiplo limpio de 16, hay una intrusa.

## Cobertura real

| Mnemónico | Series | Observaciones | Inicio | Fin |
|-----------|--------|---------------|--------|-----|
| `CEYS` | 16 | 2.464 | 2013-05 | 2026-06 |
| `NVA` | 16 | 2.328 | 2014-01 | 2026-05 |
| `SAH` | 16 | 2.328 | 2014-01 | 2026-05 |
| `SANH` | 16 | 2.328 | 2014-01 | 2026-05 |

Las tres series INE empiezan en **enero de 2014** y terminan un mes antes que
`CEYS`. Cualquier panel que las combine debe recortar al rango común, no
rellenar: `lib.transform` no interpola y no debe hacerlo.

Ninguna región falta. Ninguna serie viene vacía.

## Advertencias al construir el panel

1. **Son flujos mensuales, no stocks.** No acumular sin decirlo. Para comparar
   con el PIB sectorial anual hay que sumar los doce meses, y 2026 está
   incompleto —termina en mayo—, así que el último año es parcial y no debe
   graficarse junto a años completos sin marcarlo.
2. **Fuerte estacionalidad.** Los permisos caen en invierno austral y en enero.
   Cualquier lectura mes contra mes es ruido; usar variación doce meses o
   promedios móviles de doce meses.
3. **Las series no están desestacionalizadas ni deflactadas.** `SAH` y `SANH`
   están en metros cuadrados, así que no hay problema de precios; `CEYS` es un
   conteo. No hay nada que deflactar, y por eso mismo no hay excusa para
   mezclarlas con series en pesos sin normalizar.
4. **`CEYS` no es un indicador inmobiliario.** Es constitución de empresas de
   todo tipo. Entra en esta familia como control de dinamismo empresarial
   regional, no como parte del eje espacial. No sumarlo a los otros tres.
5. **Escala:** la Región Metropolitana domina en niveles por población. Para
   comparar regiones hay que normalizar —per cápita o como índice base 100— y
   la población regional **no existe como serie del BCCh**: viene embebida como
   denominador en las tablas per cápita, o hay que traerla del INE.

## Relacionado

- [[briefing_two_axes]] — los sectores 10, 03 y 06, y la trampa del token 7
- `lib/families.py` — declaración de la familia y `matches()`
- `lib/regions.py` — el parser de las cuatro codificaciones

# Nota de familia — `tasas` (Reporte 8)

**Escala:** nacional (una economía) · **Frecuencia:** diaria, mensual, trimestral
**Fuente:** `raw_daily.csv`, `raw_monthly.csv`, `raw_quarterly.csv`
**Universo:** `universe_tasas.csv` (531 series) · **Manifiesto:** `manifest_tasas.csv`

Esta nota existe para que la próxima persona no tenga que reconstruir lo que ya
se aprendió acá. No resume el reporte: describe los datos.

## Qué contiene la familia

La familia reúne el conjunto completo de regresores financieros de la hipótesis
H1 del proyecto Fondecyt (la caída de la tasa de descuento como determinante
financiero de la valorización del suelo metropolitano, Tabla 1 de la formulación):

1. **Tasa de Política Monetaria (TPM):**
   - Tasa diaria y promedios mensuales/anuales (`F022.TPM.TIN.D001.NO.Z.D` y series de operaciones).
   - Cobertura desde 1995 nominalizada en agosto de 2001.
2. **Expectativas de TPM y condiciones crediticias (`ECB` / `TPM`):**
   - Encuesta de Expectativas Económicas (EEE) y Encuesta de Crédito Bancario (`ECB`).
   - Expectativas de TPM a horizonte de 11, 23, 35 meses y parámetros estructurales de largo plazo (`LP`).
3. **Tasas de interés del sistema financiero (`TIP` / `COL` / `VIV`):**
   - Tasas de captación y colocación nominales y reales a distintos plazos (30–89 días, 90–365 días, 1–3 años).
   - Tasa promedio de colocación para créditos de vivienda / hipotecarios (`VIV` / `TCOVIV`).
4. **Bonos del Banco Central en UF (`BCU`):**
   - Licitación y tasas de bonos BCU a 2, 5 y 10 años.
5. **Apalancamiento de hogares (`DEUBH`):**
   - Deuda hipotecaria bancaria de los hogares como % del PIB (`PPB2`) y como % del ingreso disponible (`PIND`).

## Por qué esta familia importa en el programa

Es la **mitad macro-financiera del modelo de valorización de activos**. La renta
del suelo es el flujo de servicios futuros descontados a una tasa de descuento:
cuando la tasa real cae, el valor presente de un activo que no se deprecia (el
suelo urbano) sube mecánicamente.

Esta familia provee el precio del dinero y las condiciones crediticias que
operaron durante las cuatro décadas de estudio (1983–2024), conectando la
política monetaria, la estructura de plazos de la curva soberana (BCU), las
tasas de colocación hipotecaria bancaria y el consiguiente apalancamiento de los
hogares (`DEUBH`).

## Escala de observación: puramente nacional

A diferencia de las demás familias del programa (R1 a R7), `tasas` **no tiene ni
necesita desagregación regional**:
- La tasa de política monetaria, la curva de bonos soberanos y las tasas de
  referencia del sistema bancario constituyen un **precio único de la economía**.
- Los hogares y las instituciones financieras operan bajo un mercado financiero
  integrado a escala nacional.
- Por tanto, la unidad de observación es **una economía nacional**.

## Advertencias metodológicas

1. **Coberturas temporales heterogéneas:**
   - Captación y colocación desde 1983; TPM desde 1995; bonos BCU y tasas
     hipotecarias desagregadas desde 2002; deuda de hogares `DEUBH` desde
     2003/2008.
   - Cualquier cruce simultáneo multivariado (como la Tabla 1 de la formulación)
     debe trabajar con ventanas comunes o empalmes explícitos.
2. **Nominal vs Real:**
   - La TPM operaba en UF (tasa real) hasta agosto de 2001, fecha en que se
     nominalizó. Las comparaciones de largo plazo deben usar tasas reales
     consistentes (restando inflación o expectativas de inflación).
3. **Deuda `DEUBH` es un ratio macroeconómico trimestral:**
   - Mide el saldo de deuda bancaria hipotecaria como proporción del PIB
     anualizado o del ingreso disponible de los hogares, no montos per cápita.

## Relacionado

- [[briefing_financial_depth]] — la huella regional sobre el deudor (mora por cartera)
- [[briefing_housing_wealth]] — la contraparte real: valor del stock habitacional
- `lib/families.py` — declaración de la familia `tasas` y escala nacional

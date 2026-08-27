# Traspaso de sesión — revisión multiescalar de la BDE

**Fecha:** 2026-08-27 · **Motivo:** límite de sesión
**Repos:** `bcch-data-repo` (main + rama `site`), `dpolancon.github.io` (master)
**Sitio en vivo:** <https://dpolancon.github.io/bcch/>

Este documento existe para que otra sesión retome sin reconstruir contexto. No
resume el proyecto: dice dónde está el trabajo, qué falta y qué trampas ya
costaron tiempo.

---

## 1. Qué es esto

El investigador responsable encargó **revisar exhaustivamente los datos del
Banco Central que servirán al proyecto, a nivel sectorial-regional, regional,
macro-zonas y nacional**. El entregable **es el sitio**, presentado de forma
modular e interactiva y con descargas de las bases procesadas. No es un informe
aparte.

El proyecto marco es el Fondecyt sobre **determinantes financieras de la
inflación del precio del suelo metropolitano en Chile, 1983–2024** (H1: la
caída de la tasa de descuento; H2: fundamentos reales). La BDE del Banco
Central es **una capa** de un ensamblaje de ocho, y las otras siete vienen de
BMS/IPSS, Conservadores de Bienes Raíces, SII, INE y MINVU.

### El hallazgo que organiza la revisión

La BDE publica 25.369 series únicas con una geografía radicalmente asimétrica:

| Escala | Series | % |
|---|---:|---:|
| Nacional | 21.287 | 83,9 |
| Sectorial-regional | 2.331 | 9,2 |
| Regional | 1.695 | 6,7 |
| **Macro-zona** | **56** | **0,2** |

**La BDE mide las escalas que al Banco Central le interesa gobernar.** El grueso
es nacional porque el mandato es la política monetaria nacional; la región
aparece por vía de Cuentas Nacionales; la macro-zona aparece como estadística
*experimental*; y el área metropolitana —donde ocurre la captura de renta que el
proyecto estudia— **no aparece en ninguna escala**. La asimetría no es una
limitación técnica del catálogo: es una propiedad de la institución que lo
produce.

---

## 2. Estado por reporte

| | Reporte | Escala | Descarga | Nota | Panel | Página | Auditado | En vivo |
|---|---|---|---|---|---|---|---|---|
| R1 | Disparidades regionales | sectorial-regional | — | — | ✓ | ✓ | ✓ | ✓ |
| R2 | Cobertura de datos | — | — | — | censo | ✓ | ✓ | ✓ |
| R3 | Los dos ejes | sectorial-regional | en disco | ✓ | ✓ | ✓ | ✓ | ✓ |
| R4 | Ciclo de la construcción | regional | ✓ 64 | ✓ | ✓ | ✓ | ✓ | ✓ |
| R6 | Profundidad financiera | regional | ✓ 96 | ✓ | ✓ | ✓ | ✓ | ✓ |
| **R7** | Estancamiento del sector dinámico | regional | ✓ 496 | ✓ | ✓ | **falta** | **falta** | — |
| R5 | Inmueble como reserva de valor | macro-zona | — | — | — | — | — | — |
| R8 | Precio del dinero (tasas) | nacional | — | — | — | — | — | — |

**Cinco páginas en vivo.** `405 passed, 3 skipped`.

---

## 3. Lo siguiente, en orden

### 3.1 R7 está a una página de distancia

Ya tiene descarga (496 series), nota de familia, y los tres paneles construidos
—`panel_interregional_trade_{monthly,annual,summary}.csv`— con indicadores
`apertura`, `autocontencion` y `balance_neto`. **Falta sólo la página.** El
patrón está en `build_report4()` y `build_report6()` de `scripts/10_generate_site.py`:

1. `build_report7(anual, resumen)` en la etapa 10, con toda cifra interpolada
   del panel y ninguna escrita a mano.
2. Registrarlo en `published` con slug, `nav_label` y `family`.
3. `audit_report7()` en `scripts/11_audit_site.py`, copiando `audit_report6()`:
   recalcula las cifras y falla si la prosa deja de seguir del panel.

**Ojo:** el resumen actual cubre sólo 2025. Las compraventas arrancan en **2018**
—la serie regional más corta del programa— y las exportaciones en 2013, con
frecuencias distintas. Cruzarlas obliga a agregar a anual y recortar al rango
común, y ese rango **no cubre el tramo de tasas bajas** que más le interesa al
proyecto. Conviene decirlo en la página en vez de dejarlo implícito.

### 3.2 R8 (`tasas`) es lo más consecuente que queda

Es la **Tabla 1 de la formulación**: el conjunto completo de regresores de H1
—TPM, expectativa de TPM, captación y colocación, bonos BCCh en UF, tasa de
créditos hipotecarios, IPSA— más `DEUBH` (deuda hipotecaria de hogares). Está
declarada en `lib/families.py` y **no tiene un solo dato en disco**.

Es la única capa nacional que el proyecto necesita y aún no se ingiere. Secuencia:
`--family tasas` → nota de familia → panel → página.

Arrastra una decisión de diseño pendiente: es **nacional y no necesita
desagregación** —la tasa de descuento que discute H1 es un precio único de la
economía—. O el programa admite un reporte puramente nacional, o `tasas` se
adhiere a R5 como su mitad financiera.

### 3.3 R5 (`housing_wealth`) es el más delicado

77 series en 13 zonas. Reproduce la **Figura 4 de la formulación** y contiene
`VALT`/`VALC`, la descomposición terreno/construcción de Knoll et al. Dos
advertencias: esa descomposición **sólo existe a escala nacional** (NAC, CAS,
DEP), nunca por zona; y la correspondencia zona↔región es de uno a muchos salvo
en la RM, de modo que **la única dirección de agregación honesta es subir el
dato regional hasta la zona**.

---

## 4. Reglas del repositorio que no se negocian

- **Nunca fabricar datos.** No hay modo sintético en ninguna etapa. Si un dato
  falta, se reporta la ausencia. `tests/test_conventions.py` falla ante
  cualquier uso de `np.random` en `scripts/`.
- **Derivar, nunca repetir.** Toda cifra de prosa se interpola de la tabla que
  describe. Las etapas fallan ante un `@@TOKEN@@` sin resolver.
- **Una copia de cada artefacto.** Cada reporte es dueño de su `assets/`.
- **CSV en todas partes, nunca Parquet.** Leer siempre con
  `dtype={"region_id": str, "sector_id": str}`: los códigos van con relleno de
  ceros y como entero `"01"` se vuelve `1`, rompiendo todo cruce en silencio.
- **`codes/` es R, `scripts/` es Python.** Verificado mecánicamente.
- **Números de etapa únicos.** Ya hubo una colisión en `09`.

---

## 5. Trampas que ya costaron tiempo

Cada una llegó lejos porque nada la detectaba. Todas tienen test ahora.

**El merge parcial destruía la capa cruda.** `write_outputs` escribía lo que la
corrida hubiera descargado encima de `raw_*.csv`. Una corrida `--family` habría
recortado `raw_monthly.csv` de 110.637 filas a 9.448 y **vaciado los otros tres
archivos**. Las corridas acotadas ahora fusionan; sólo una corrida completa
reemplaza.

**El relleno de ceros se perdía en la fusión.** Leer con
`dtype={"region_code": str}` cuando la columna se llama `region_id` hizo que
pandas infiriera entero y escribiera `"1"` por `"01"` en los cuatro archivos. La
fusión ahora lee todo como texto: nombrar columnas sueltas es cómo se equivocó
la primera vez.

**La fecha quedaba en dos formatos.** Las filas nuevas llegaban como datetime y
se serializaban con hora; las preservadas conservaban la forma corta. 29.956
filas en `YYYY-MM-DD` y 3.840 con hora en el mismo archivo. No falla al
escribir: falla mucho después, en cualquier consumidor que use `.dt`.

**Un token hacía match dentro de otro mnemónico.** `NVA` coincidía dentro de
`CCPNVA` —cuentas corrientes de Valparaíso, de R6— y contaminaba la familia de
R4. El conteo era 66 donde 16 × 4 = 64, y la discrepancia se dejó pasar.
`SeriesFamily.matches()` ancla cada token al mnemónico como prefijo.

**Se sumaron los doce meses de un stock.** `CCPN` lleva token `STO`. Daba 144,5
millones de cuentas en vez de 12,04. El campo `medida` lo hace visible.

**Se sumó entre regiones un saldo que es un promedio.** `SCCPN` es un stock *y*
un saldo promedio por cuenta. `lib/unidades.py` declara la agregación de cada
unidad y el resumen la respeta.

**Dos unidades monetarias con tres órdenes de magnitud de diferencia.** `SCCPN`
en pesos y `SDV` en millones de pesos, etiquetadas igual. `lib/unidades.py` fija
una unidad canónica por dimensión y **falla ante una unidad no declarada** en
vez de suponer factor 1.

**Un divisor calibrado a la unidad vieja.** Al pasar la unidad canónica a pesos,
la página de R6 publicó «7 655 059,97 billones de pesos». Usar
`site.es_dinero()`, que escala y elige la palabra.

**Inglés filtrado a un sitio en español.** El campo `notes` del registro se
volcaba literal a la página de metodología. Lo que se publica es `notas_es`.

**Dos páginas afirmando conteos distintos.** R2 decía doce sectores y R1 trece.
La base 2018 no tiene un `07` combinado: comercio se separa de restaurantes y
hoteles, y el desglose tiene **trece** actividades. El número sale de
`len(SECTOR_BREAKDOWN_IDS)`.

**Una afirmación falsa en el propio registro.** La nota de `interregional_trade`
decía que las compraventas necesitaban un parser nuevo por su token numérico. Es
falso: es la posicional de F035, que `f035_positional` resuelve desde el primer
día. Corregida, con constancia del error.

---

## 6. La cadena

```bash
python scripts/13_census_bde.py                          # censo del catálogo
python scripts/01_fetch_crsm_raw.py --family <familia>   # descarga acotada
python scripts/09_build_theme_panels.py --family <fam>   # panel analítico
python scripts/10_generate_site.py                       # .qmd al worktree
cd C:\ReposGitHub\bcch-site && quarto render             # HTML
python scripts/11_audit_site.py                          # coherencia
python scripts/12_deploy_site.py                         # a dpolancon.github.io
```

Quarto **no está en el PATH**: anteponer `C:\Program Files\Quarto\bin`. El
servidor local de pruebas bloquea `docs/` y hace fallar el render; hay que
detenerlo antes.

La **compuerta de absorción** es un test: una familia con manifiesto de descarga
y sin nota de familia deja la suite en rojo. Es deliberado —el ritmo lo fija la
comprensión, no el calendario— y no se salta.

La auditoría (etapa 11) verifica: activos byte a byte, paneles idénticos a
`data/`, ningún token sin resolver, las cifras de R3/R4/R6 recalculadas desde su
panel, ningún exhibit sin línea de fuente ni dato descargable, ninguna página en
inglés, y ningún conteo que contradiga su propia tabla.

---

## 7. Convenciones de escritura

Calibradas contra **López, Meza y Gasic (2014)**, *Norte Grande* 58 —Gasic
figura en la formulación, así que es la voz del equipo—:

- La hipótesis va en prosa densa, no en notación.
- El supuesto se declara corto y **en el cuerpo**, nunca en nota al pie.
- La magnitud se traduce a un referente social.
- Primera persona plural para el acto de investigación, impersonal para el
  procedimiento.
- Número, mecanismo y consecuencia en el mismo párrafo.
- El resultado nulo es hallazgo.
- La agencia se atribuye.

De `econ-write` sobrevive lo concreto antes que lo abstracto, el resultado antes
que el método y la prohibición de carraspeo. Se sustituye la identificación
causal por **validez de constructo y escala de observación**. **No** se usa
registro de auditoría editorial: el texto habla de los datos, nunca de cómo está
escrito el texto.

El destinatario es el equipo, que conoce la formulación. No se le explica lo que
ya sabe.

### Autoría, en tres capas

El dato es del Banco Central; la elaboración es del proyecto; las herramientas
de apoyo —censo automatizado, crosswalk, explorador, rutinas de auditoría— se
construyeron con asistencia de IA. Está declarado en la página *Diseño* bajo
«Nota: herramientas de apoyo creadas con IA», y **toda figura y tabla lleva línea
de fuente y enlaza el CSV que la produce** (`site.fuente()`).

---

## 8. Pendientes administrativos

1. **Sin commitear** en `main`: los tres paneles de R7, `tests/test_trade.py`,
   la baja de `scripts/09_analyze_trade_network.py`, y modificaciones a
   `09_build_theme_panels.py` y `lib/unidades.py`. Todo trabajo del
   investigador; conviene que lo commitee él, con su propio mensaje.
2. **`scripts/lib/trade.py` quedó trackeado dentro del commit `4a7a7f1`**, que
   trata de unidades canónicas y no tiene relación. Fue un `git add -A scripts/`
   demasiado amplio de la sesión anterior. Si molesta, sacarlo a un commit
   propio.
3. **Migración futura** a una cuenta de GitHub del proyecto: ya es
   configuración y no código. `BCCH_SITE_HOST`, `BCCH_SITE_HOST_NOMBRE` y
   `BCCH_PERSONAL_SITE` en `lib/paths.py`. Verificado apuntando el generador a
   otro host.
4. **`editorial_decision.md` y `report_structure_REG_ECON_DEV.md`** aparecen
   modificados pero **no tienen cambios de contenido**, sólo de fin de línea. No
   commitearlos.

---

## 9. Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Registro de familias, escalas, objetivos, trampas | `scripts/lib/families.py` |
| Unidades canónicas y agregación | `scripts/lib/unidades.py` |
| Páginas de escala | `scripts/lib/escalas.py` |
| Andamiaje del sitio, fuente, nota de IA | `scripts/lib/site.py` |
| Notas de familia | `bcch-data-repo-vault/briefings/` |
| Fuente Quarto | rama `site`, worktree en `C:\ReposGitHub\bcch-site` |
| Sitio publicado | `C:\ReposGitHub\dpolancon.github.io\bcch\` |
| Formulación del proyecto | Google Doc `1GsjxE3pxuPDp7gstHcrsDkt3H0h-SBhC` |

> # ⇒ EMPIEZA AQUÍ
>
> **Este es el documento que hay que leer para abrir la sesión del 2026-08-30.**
> No leas primero `audits_handoffs/`: esos cuatro documentos son historia absorbida
> y describen un estado anterior. Este es el vigente.
>
> **La sesión abre con una decisión, no con código.** Está en §2.

---

# Traspaso de sesión — revisión multiescalar de la BDE

**Cierre:** 2026-08-29 · **Próxima sesión:** 2026-08-30
**Repos:** `bcch-data-repo` (main + rama `site`), `dpolancon.github.io` (master)
**Sitio en vivo:** <https://dpolancon.github.io/bcch/>

Este documento existe para que otra sesión retome sin reconstruir contexto. No
resume el proyecto: dice dónde está el trabajo, qué falta y qué trampas ya
costaron tiempo.

---

## 1. Qué cambió esta sesión

Dos cosas, y la segunda cambia el orden de todo lo que venía planificado.

**Se reparó la colisión de etapas.** Seis scripts de figuras numerados 03–08
chocaban con seis etapas vivas de la cadena LaTeX. Se fusionaron en
`scripts/14_build_report_figures.py` con `--report N`. La suite pasó de 25 fallos
a **415 passed, 1 skipped**. De paso se interpolaron los años escritos a mano en
la prosa de R6, R7 y R8, y se corrigieron cuatro etiquetas de figura.

**Se sometieron los ocho reportes a revisión por pares** con el plugin
`academic-research-skills`: modo `full` —cinco revisores independientes más
síntesis editorial— en R3–R8, modo `quick` en R1 y R2. Los informes están en
`bcch-data-repo-vault/revisiones/`.

El resultado obliga a reordenar el programa. **Siete de los ocho reportes
recibieron revisión mayor**, y la revisión encontró ocho cifras falsas o
engañosas publicadas en vivo. El plan que traía esta sesión —revisar, luego
pulir prosa, luego publicar cartas de respuesta— sigue siendo correcto, pero
ahora tiene por delante una capa de reparación factual que no estaba prevista.

| | Reporte | Decisión | Críticos |
|---|---|---|---|
| R1 | Cobertura de datos | aceptar con revisión menor | — |
| R2 | Disparidades regionales | **revisión mayor** | 2 |
| R3 | Los dos ejes | **revisión mayor** | 2 |
| R4 | El ciclo de la construcción | **revisión mayor** | 2 |
| R5 | El inmueble como reserva de valor | **revisión mayor** | 2 |
| R6 | Profundidad financiera | **revisión mayor** | 1 |
| R7 | Estancamiento del sector dinámico | **revisión mayor** | 2 |
| R8 | El precio del dinero | **revisión mayor** | 2 |

---

## 2. La decisión que abre la sesión

**Ninguna corrección debe aplicarse antes de triar la hoja de ruta.** Las
revisiones se hicieron con un panel simulado que no conoce las restricciones del
repositorio ni las decisiones ya tomadas por el programa. Cada ítem tiene que
quedar marcado como una de tres cosas, y la marca la pone el investigador
responsable:

- **acoger** — la crítica tiene razón y la corrección cabe;
- **acoger parcial** — se corrige el texto pero no el alcance;
- **declinar con razón** — el revisor pide algo que el catálogo no permite o que
  el programa decidió no hacer. **No es un fracaso**: es el contenido más valioso
  de la futura carta de respuesta, porque deja por escrito por qué el reporte es
  como es.

Las ocho cifras falsas de §3 **no entraban en el triaje**: son errores de hecho y
ya se corrigieron el 2026-08-29. El triaje es para todo lo demás — con una
excepción anotada allí mismo: recalcular las participaciones de R2 sobre precios
corrientes sí es una decisión, no una reparación.

---

## 3. Ocho cifras falsas o engañosas — **corregidas el 2026-08-29**

Ninguna la detectó la suite ni la etapa 11; las ocho pasaban los 415 tests. Se
dejan documentadas porque el **bloque 2 de §6 sigue pendiente**: las compuertas
que impedirían que vuelvan a ocurrir no existen todavía, y sin ellas la próxima
corrección introduce el próximo error en silencio.

Están ordenadas por gravedad. Cada una lleva el arreglo que se aplicó.

**R4 · La columna «Δ Sector 10 (pp)» está mal por cien veces.**
`10_generate_site.py:444` resta dos `share`, que son **fracciones**, y les pone
el sufijo « pp» sin multiplicar por 100. La RM publica «+0,01 pp» y son
**+0,71 pp**; Biobío publica «+0,02 pp» y son **+1,54 pp**. El daño iba contra el
propio reporte: la columna que debía mostrar el alza de la renta espacial mostraba
dieciséis valores cercanos a cero, y la tabla desmentía en silencio a su
entradilla. *Arreglo: factor 100 en `10_generate_site.py`; corregirla reforzó el
argumento del reporte.*

**R2 · La Tabla 1 está mal por mil veces.** Rotula «PIB Promedio (Miles de
Millones de CLP)» y asigna 78,49 a la Región Metropolitana. Son **billones**.
Setenta y ocho mil millones de pesos son unos ochenta millones de dólares.
*Arreglo: encabezado corregido en `04_analyze_regional.py`, y todo el informe
español pasa ahora por `site_lib.es()` — publicaba «45.9%» con punto decimal.*

**R2 · Las participaciones se construyen sobre volumen encadenado.** La página de
metodología del mismo sitio declara que los volúmenes encadenados no son
aditivos y que una participación construida sobre ellos «no sería una proporción
del producto regional sino un cociente sin denominador interpretable». R2 hace
exactamente eso y publica RM = **45,92%**, donde el panel de R3 en precios
corrientes da **41,7%**. Dos páginas del sitio, dos cifras, sin reconciliar.
*Arreglo parcial: se declara en el cuerpo que el cociente encadenado no es una
proporción y por qué difiere de R3. **Recalcular sobre precios corrientes sigue
siendo decisión de triaje**, porque cambia todas las cifras del reporte.*

**R5 · El año del techo histórico es falso.** «Techo histórico de 174,3% del PIB
**en 2021**». El máximo está en **2020**; 2021 es el único año de caída de toda
la serie. El valor se interpola del panel y el año estaba escrito a mano —y no
sólo en el reporte: `09_build_theme_panels.py` lo fijaba a 2021 en el propio
panel resumen—. *Arreglo: el año sale de `idxmax` en la etapa 09, y la prosa lo
interpola. Los tres años del IPV se derivaron también, aunque eran correctos.*

**R8 · Las cifras citadas no están en el CSV que la página enlaza.** La línea de
fuente remite a `panel_tasas_annual.csv` y los números salen de
`panel_tasas_summary.csv`, que registra extremos **sub-anuales**. Quien descargue
el archivo enlazado para verificar el 47,8% hallará 45,94%, y en otro año (2023,
no 2022). *Arreglo: `site_lib.fuente()` acepta varios CSV y R8 enlaza los dos, más
un párrafo que declara qué cifras son promedio anual y cuáles extremo mensual.*

**R4 y R6 · La creación de Ñuble en 2018 rompe las comparaciones regionales.**
R4 publica Biobío **−68,6%** comparando 2014 con 2025 a través del cambio de
fronteras; la unidad geográfica comparable cae **−40,3%**, el promedio nacional.
R6 publica «0» cuentas corrientes para Ñuble en 2009, afirmando que había cero
donde no había región. Ningún reporte lo declara. *Arreglo:
`site_lib.aviso_nuble()`, compartido por R4 y R6; el cero pasa a «—»; y R4 publica
la cifra comparable, **−40,2%** calculada del panel, junto a la fila de Biobío.*

**R3 · La Figura 3.1 es la figura de otro reporte.** Su título dice «Renta
Espacial vs. Renta de Recursos»; sus ejes son apertura interregional y
autocontención, dibujados desde `panel_interregional_trade_summary.csv` —el panel
de R7—. Los cuadrantes rotulan «Renta Espacial Dominante» sobre ejes que miden
comercio, y el epígrafe describe la figura real, contradiciendo al título que
tiene encima. **Ninguna cifra del cuerpo de R3 aparece en la única figura que lo
acompaña.** *Arreglo: la figura se redibujó desde `panel_two_axes_annual.csv`
—sector 10 contra sector 03, cortes en la mediana de cada eje— y el epígrafe se
reescribió. La nube resultante muestra el hallazgo real: banda estrecha en el eje
espacial, tres extremos en el de recursos.*

**R5 · Imprime `+-0,4 pp`.** El generador antepone «+» sin condicionarlo al
signo. R4 sí lo condiciona en su tabla equivalente. *Arreglo:
`site_lib.es_delta()`, que antepone el signo sólo cuando corresponde, aplicado a
las siete filas de la tabla.*

---

## 4. Tres causas sistémicas, y cómo se cierran

Las ocho cifras de arriba no son ocho descuidos independientes. Son tres huecos.

### 4.1 El sitio mezcla promedio anual con extremo sub-anual sin rotular

Es la causa del año falso de R5, del desajuste de R8, y de las anotaciones de
figura que se corrigieron el 2026-08-28 —donde la flecha apuntaba al promedio
anual y la etiqueta citaba el extremo mensual—.

**El primer intento de arreglo fue peor que el error:** interpolar del panel
anual habría puesto 9,01% en la figura 8.1 contra el 12,76% que la prosa cita
tres párrafos más arriba. **Interpolar no basta: hay que interpolar de la tabla
que la prosa cita, y rotular la agregación.**

*Cierre:* una convención declarada —cada cifra dice si es promedio anual o
extremo sub-anual— y la línea de fuente enlazando el CSV que efectivamente la
contiene.

### 4.2 La auditoría verifica cifras en negrita, y nada más

`audit_report3` … `audit_report8` recalculan un conjunto de cifras desde el panel
y comprueban que aparezcan dentro de un bloque `**negrita**`. **No miran años, ni
unidades, ni rótulos de columna, ni de qué panel salió una figura.** Los ocho
errores pasaron los 415 tests y la etapa 11 sin una advertencia.

*Cierre, en tres piezas:*
1. Verificar los años igual que las cifras, comparándolos con el `idxmax`/`idxmin`
   del panel.
2. Que la etapa 14 emita, junto a cada PNG, un CSV con las etiquetas que dibujó, y
   que la etapa 11 lo verifique contra el panel. Es el mecanismo del `@@TOKEN@@`
   aplicado a las figuras.
3. Que cada figura declare de qué panel proviene y que la auditoría compruebe que
   coincide con la línea de fuente de su página. Esto sólo habría bastado para
   atrapar la Figura 3.1.

### 4.3 Ñuble, 2018

Toda comparación regional que cruce 2018 mezcla un cambio administrativo con un
ciclo económico. Afecta a R4 y R6 hoy, y afectará a cualquier reporte regional
futuro con ventana larga.

*Cierre:* una constante en `lib/regions.py` con el año de la partición y la
pareja Biobío–Ñuble, y una comprobación en la etapa 11 que falle si una tabla
regional compara extremos que la cruzan sin declararlo.

---

## 5. Lo que la revisión encontró y nadie esperaba

Esto no son defectos: son hallazgos que los reportes tienen en sus tablas y no
enuncian. Las convenciones de escritura del programa dicen que **el resultado
nulo es hallazgo**; estos tres están enterrados.

**R5 — La premisa de Knoll et al. apenas se sostiene en Chile.** El reporte
declara que la BDE «permite evaluar esta premisa de manera directa» y luego no la
evalúa. Los números: terreno **+282,4%**, construcción **+260,7%**, participación
del suelo de 39,1% a 40,5%, **+1,4 pp en doce años**. Suelo y estructuras se
valorizaron casi al mismo ritmo. Es lo más importante que R5 tiene para decir.

*Con una salvedad que decide cómo se lee todo:* `VALC` es valor **de mercado** de
las estructuras, no costo de reposición. Si se capitaliza con el mismo factor que
el suelo, la descomposición chilena no es la que la tesis de Knoll requiere, y el
resultado nulo no la refuta: indica que la BDE no publica la descomposición
necesaria. **Hay que resolver esto antes de escribir el hallazgo.**

**R3 — La renta espacial se está concentrando, y lleva tres años cayendo.** La
entradilla dice «difusa y creciente». Su Gini pasó de **0,1498 a 0,1798**, el
valor más alto de la serie justamente en el último año. Y la participación media
sube hasta **9,18% en 2022** y **cae tres años consecutivos** hasta 8,66%. Una
caída de la renta espacial que arranca en 2022 coincide con el ciclo de alza de
tasas: es el hecho más directamente relevante para H1 que contiene ese panel, y
el reporte lo tiene en los datos y no lo dice.

**R6 — El canal de crédito hipotecario no muestra tensión en ninguna región.**
Resultado negativo, relevante para H1, sin enunciar.

### Dos impugnaciones de constructo

Valen más que cualquier corrección de estilo, y ninguna se resuelve reescribiendo.

**R6 · El 80,5% puede medir dónde el banco registra la cuenta, no dónde vive el
titular.** La RM registra 9,7 de 12,04 millones de cuentas en una región con
~40% de la población, y su **saldo medio es un tercio del de las otras quince**,
sin excepción. Ese patrón es la huella de la banca digital: la cuenta abierta por
internet se adscribe a la casilla del banco. El reporte lo titula «centralización
espacial de la liquidez». La serie es real; la interpretación territorial no se
sostiene sin descartar el artefacto, y el dato que lo delata está en la misma
tabla.

**R7 · El 76,4% de autocontención de la RM es lo que predice el tamaño.** Una
región que es 41,7% de la economía vende una fracción alta dentro de sí misma por
pura aritmética. Sin normalizar por tamaño, la cifra no distingue «nodo
metropolitano autocontenido» de «región grande», y el reporte la interpreta como
lo primero.

### Y el patrón transversal

**Siete de los ocho reportes no dicen qué implican para H1 o H2.** El octavo, R8,
se pasa al otro extremo: su entradilla afirma que la caída de la tasa hipotecaria
«constituyó **el principal estímulo** a la valorización del suelo» —una
atribución causal con jerarquía, en un sitio cuya metodología declara alcance
descriptivo y en un reporte que no estima nada—. H1 es lo que el proyecto va a
contrastar; el reporte de datos no puede darlo por resuelto en la primera línea.

---

## 6. El trabajo, en orden

**Bloque 0 · Triaje.** §2. Bloquea todo lo demás salvo el bloque 1, que ya se hizo.

**Bloque 1 · Reparación factual. ✅ HECHO el 2026-08-29.** Las ocho cifras de §3.
Se añadieron de paso `site_lib.es_delta()` —variación con signo condicionado— y
`site_lib.aviso_nuble()` —la advertencia de la partición de 2018, compartida por
R4 y R6—, y `site_lib.fuente()` ahora acepta varios CSV, porque una página que
cita dos paneles tiene que enlazar los dos.

**Bloque 2 · Compuertas. ← EMPEZAR AQUÍ.** Las tres piezas de §4.2 y la de §4.3. Van antes de
reescribir prosa: sin ellas, la siguiente corrección introduce el siguiente error
sin que nada lo detecte.

**Bloque 3 · Los hallazgos enterrados.** §5. Requiere resolver antes la ambigüedad
`VALC` mercado/reposición.

**Bloque 4 · Cierre de hipótesis y gradación de evidencia.** Un párrafo final por
reporte —qué predice la hipótesis, qué muestra el dato, y si lo sostiene, lo
tensiona o **no lo discrimina**, que tiene que estar disponible como respuesta—.
La gradación en tres niveles vive como campo en `lib/families.py` y se renderiza
como distintivo en `lib/site.py`, igual que `escala_badge()`. Grados sugeridos por
la revisión: R1 completa; R2, R3, R4, R5, R6 parcial; R7 corte único; R8 completa
en su ventana declarada.

**Bloque 5 · Cartas de respuesta.** `ars-revision-coach` sobre las revisiones de
`revisiones/`, y publicación como el tercer artefacto que el índice promete y que
no existe. Cañería: `RESPUESTAS_DIR` en `lib/paths.py`, bucle en la etapa 10
copiando el de las notas de familia, `site_lib.respuesta()` siguiendo a
`site_lib.fuente()`, y **`audit_respuestas()`** para que la promesa no se vuelva a
abrir. Deliberadamente **no** se construyó esta sesión: publicar la cañería sin
cartas deja la auditoría en rojo y sin forma de verificarla de punta a punta.

**Bloque 6 · Despliegue.** `quarto render` y etapa 12. **No corre hasta el bloque
2**: desplegar ahora publicaría las correcciones de figura de ayer junto con las
ocho cifras falsas intactas.

---

## 7. Reglas del repositorio que no se negocian

- **Nunca fabricar datos.** No hay modo sintético en ninguna etapa. Si un dato
  falta, se reporta la ausencia. `tests/test_conventions.py` falla ante
  cualquier uso de `np.random` en `scripts/`.
- **Derivar, nunca repetir.** Toda cifra de prosa se interpola de la tabla que
  describe. Las etapas fallan ante un `@@TOKEN@@` sin resolver. **Extensión
  aprendida esta sesión: los años, las unidades y los rótulos de columna también
  son cifras.**
- **Una copia de cada artefacto.** Cada reporte es dueño de su `assets/`. Aplica
  también a este traspaso: no se crea un segundo, se reescribe éste.
- **CSV en todas partes, nunca Parquet.** Leer siempre con
  `dtype={"region_id": str, "sector_id": str}`.
- **`codes/` es R, `scripts/` es Python.** Verificado mecánicamente.
- **Números de etapa únicos.** Ya hubo dos colisiones: en `09` y, esta sesión,
  seis simultáneas en `03`–`08`.

---

## 8. Trampas que ya costaron tiempo

**El merge parcial destruía la capa cruda.** `write_outputs` escribía lo que la
corrida hubiera descargado encima de `raw_*.csv`. Una corrida `--family` habría
recortado `raw_monthly.csv` de 110.637 filas a 9.448 y vaciado los otros tres.
Las corridas acotadas ahora fusionan; sólo una completa reemplaza.

**El relleno de ceros se perdía en la fusión.** Leer con
`dtype={"region_code": str}` cuando la columna se llama `region_id` hizo que
pandas infiriera entero y escribiera `"1"` por `"01"`. La fusión lee todo como
texto: nombrar columnas sueltas es cómo se equivocó la primera vez.

**La fecha quedaba en dos formatos.** 29.956 filas en `YYYY-MM-DD` y 3.840 con
hora en el mismo archivo. No falla al escribir: falla en cualquier consumidor que
use `.dt`.

**Un token hacía match dentro de otro mnemónico.** `NVA` coincidía dentro de
`CCPNVA` y contaminaba la familia de R4. `SeriesFamily.matches()` ancla cada
token al mnemónico como prefijo.

**Se sumaron los doce meses de un stock.** `CCPN` lleva token `STO`. Daba 144,5
millones de cuentas en vez de 12,04.

**Se sumó entre regiones un saldo que es un promedio.** `SCCPN` es stock *y*
saldo medio. `lib/unidades.py` declara la agregación de cada unidad.

**Dos unidades monetarias con tres órdenes de diferencia.** `lib/unidades.py`
fija una unidad canónica por dimensión y falla ante una unidad no declarada.

**Un divisor calibrado a la unidad vieja.** R6 publicó «7 655 059,97 billones de
pesos». Usar `site.es_dinero()`.

**Inglés filtrado a un sitio en español.** Lo que se publica es `notas_es`.

**Dos páginas afirmando conteos distintos.** El desglose de la base 2018 tiene
**trece** actividades. El número sale de `len(SECTOR_BREAKDOWN_IDS)`.

**Una afirmación falsa en el propio registro.** La nota de `interregional_trade`
decía que las compraventas necesitaban un parser nuevo. Es la posicional de F035,
que `f035_positional` resuelve desde el primer día.

**Seis scripts de figuras chocaron con seis etapas vivas.** La cadena LaTeX
03–08 **no se puede retirar**: produce los dos markdown que `VAULT_REPORTS`
convierte en R1 y R2. Fusionados en la etapa 14.

**Una f-string sin campo es Python válido.** `f'k'` sobre cada barra de la figura
5.3, `f'B'` en la 7.2, `'(.98M)'` en la 6.2 donde el valor es 3,98M. Nada falla.

**La auditoría no lee dentro de los PNG, ni los años, ni las unidades.** Es la
trampa que sigue abierta y la que más costó esta sesión. Ver §4.2.

---

## 9. La cadena

```bash
python scripts/13_census_bde.py                          # censo del catálogo
python scripts/01_fetch_crsm_raw.py --family <familia>   # descarga acotada
python scripts/09_build_theme_panels.py --family <fam>   # panel analítico
python scripts/14_build_report_figures.py [--report N]   # figuras de R3-R8
python scripts/10_generate_site.py                       # .qmd al worktree
cd C:\ReposGitHub\bcch-site && quarto render             # HTML
python scripts/11_audit_site.py                          # coherencia
python scripts/12_deploy_site.py                         # a dpolancon.github.io
```

La etapa 14 va **antes** de la 10: la 10 copia los PNG al worktree y la 11 los
compara byte a byte.

La prosa de R1 y R2 **no** vive en la etapa 10 sino en
`scripts/03_report_coverage.py:305` y `scripts/04_analyze_regional.py:723`, que
escriben los markdown del vault. Corregirlos exige volver a correr esas etapas
antes de la 10.

Quarto **no está en el PATH**: anteponer `C:\Program Files\Quarto\bin`. El
servidor local de pruebas bloquea `docs/` y hace fallar el render.

La **compuerta de absorción** es un test: una familia con manifiesto de descarga y
sin nota de familia deja la suite en rojo. Es deliberado y no se salta.

---

## 10. Convenciones de escritura

Calibradas contra **López, Meza y Gasic (2014)**, *Norte Grande* 58:

- La hipótesis va en prosa densa, no en notación.
- El supuesto se declara corto y **en el cuerpo**, nunca en nota al pie.
- La magnitud se traduce a un referente social.
- Primera persona plural para el acto de investigación, impersonal para el
  procedimiento.
- Número, mecanismo y consecuencia en el mismo párrafo.
- **El resultado nulo es hallazgo.** Tres están enterrados ahora mismo (§5).
- La agencia se atribuye.

De `econ-write` sobrevive lo concreto antes que lo abstracto y la prohibición de
carraspeo. Se sustituye la identificación causal por **validez de constructo y
escala de observación** —y la revisión de esta sesión mostró que ahí es donde
están los problemas de fondo, no en la redacción—. **No** se usa registro de
auditoría editorial: el texto habla de los datos, nunca de cómo está escrito.

El destinatario es el equipo, que conoce la formulación. No se le explica lo que
ya sabe. **Pero conocer la formulación no es poder derivar, de una participación
sectorial, si la hipótesis queda mejor o peor parada:** por eso el párrafo de
cierre del bloque 4 no es redundante.

### Autoría, en tres capas

El dato es del Banco Central; la elaboración es del proyecto; las herramientas de
apoyo se construyeron con asistencia de IA. Declarado en la página *Diseño*, y
toda figura y tabla lleva línea de fuente y enlaza el CSV que la produce
(`site.fuente()`) — con la salvedad de R3 y R8, donde ese enlace apunta a un CSV
que no contiene la cifra (§3).

---

## 11. Estado y pendientes administrativos

**Suite:** `415 passed, 1 skipped`. **Etapa 11:** pasa —61 activos byte a byte,
16 paneles, 23 páginas sin token sin resolver, 76 cifras de prosa recalculadas—.
Que pase con ocho cifras falsas publicadas es exactamente el punto de §4.2.

1. **Sin commitear** en `main`, y ya es bastante: la alta de
   `scripts/14_build_report_figures.py`, la baja de los seis
   `0N_build_*_figures.py`, la reparación de las ocho cifras de §3 —que toca las
   etapas 04, 09, 10 y 14 y `lib/site.py`—, las figuras regeneradas, los dos
   markdown de R1 y R2 con sus PDF, el directorio nuevo
   `bcch-data-repo-vault/revisiones/`, y los cambios a `CLAUDE.md`, a
   `audits_handoffs/INDEX.md` y a este traspaso. Conviene que lo commitee el
   investigador, y conviene hacerlo antes de seguir.
2. **Sin desplegar**, y **no debe desplegarse todavía** (bloque 6 de §6).
3. **Plugin `academic-research-skills`** instalado en scope de usuario, marketplace
   apuntando a `C:\ReposGitHub\academic-research-skills`. La copia local es
   **v3.12.0** contra **3.21.1** upstream; como el marketplace es local,
   `claude plugin update` no trae nada: hay que hacer `git pull` en ese repo y
   reiniciar. **Sus skills sólo se registran al iniciar sesión.**
4. **Migración futura** a una cuenta de GitHub del proyecto: ya es configuración.
   `BCCH_SITE_HOST`, `BCCH_SITE_HOST_NOMBRE` y `BCCH_PERSONAL_SITE` en
   `lib/paths.py`.

---

## 12. Dónde está cada cosa

| Qué | Dónde |
|---|---|
| **Las ocho revisiones por pares** | `bcch-data-repo-vault/revisiones/` |
| Plan de la revisión, aprobado | `~/.claude/plans/lee-este-session-handoff-quirky-dawn.md` |
| Registro de familias, escalas, objetivos, trampas | `scripts/lib/families.py` |
| Unidades canónicas y agregación | `scripts/lib/unidades.py` |
| Páginas de escala | `scripts/lib/escalas.py` |
| Andamiaje del sitio, fuente, nota de IA | `scripts/lib/site.py` |
| Figuras de R3 a R8 | `scripts/14_build_report_figures.py` |
| Prosa de R3 a R8 | `scripts/10_generate_site.py`, `build_report3..8()` |
| Prosa de R1 y R2 | `scripts/03_report_coverage.py:305`, `scripts/04_analyze_regional.py:723` |
| Notas de familia | `bcch-data-repo-vault/briefings/` |
| Historia absorbida (no vigente) | `bcch-data-repo-vault/audits_handoffs/` |
| Fuente Quarto | rama `site`, worktree en `C:\ReposGitHub\bcch-site` |
| Sitio publicado | `C:\ReposGitHub\dpolancon.github.io\bcch\` |
| Formulación del proyecto | Google Doc `1GsjxE3pxuPDp7gstHcrsDkt3H0h-SBhC` |

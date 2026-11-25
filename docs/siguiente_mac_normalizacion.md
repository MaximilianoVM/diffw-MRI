# Siguiente paso (Mac): normalización de Ricardo y modelo, evaluados contra Hausdorff

Para el Claude de la Mac y para Ricardo. Haz `git pull` antes de empezar (trae `out/hausdorff/hausdorff.csv` y el paso 10).
Contexto: `docs/junta_17nov.md`, `docs/evaluacion_filtrado.md`, `docs/hausdorff_eficiencia.md`.

## 1. Lo que ya medimos (Hausdorff < 5 mm = verdadero; 33 349 de 100 000 hilos; tasa base 33.3 %)
AUC del peso como clasificador de la etiqueta (0.5 = azar). Se calculó con numpy en la laptop de desarrollo.

| | AUC global | corr(peso, longitud) | AUC peso×longitud | AUC percentil por decil de longitud | AUC **dentro** de cada decil de longitud |
|---|---|---|---|---|---|
| SIFT2 | 0.426 | **−0.41** | 0.620 | 0.505 | 0.508 |
| COMMIT | 0.449 | −0.20 | 0.482 | 0.498 | 0.485 |
| LiFE | 0.601 | +0.27 | 0.620 | 0.517 | 0.529 |
| COMMIT2 | 0.634 | +0.27 | 0.633 | 0.561 | 0.576 |
| longitud sola | 0.652 | | | | |

Combinaciones al estilo Ricardo (promedio de percentiles):
| Percentil | Promedio SIFT2+COMMIT+LiFE | + COMMIT2 | LiFE+COMMIT2 |
|---|---|---|---|
| global (especificación) | AUC 0.485 | 0.541 | 0.649 |
| por decil de longitud | AUC 0.509 | 0.555 | 0.610 |

Regla «≥ 2 de 3» (percentil > 0.5 en al menos 2 métodos): con SIFT2+COMMIT+LiFE conserva 33 719 hilos con precisión 30.2 % (peor que
la tasa base 33.3 %); con LiFE+COMMIT2 conserva 10 637 con 54.4 %.

## 2. Qué dicen estos números
1. **SIFT2 y COMMIT salen por debajo del azar por la longitud.** SIFT2 da pesos altos a hilos cortos (correlación −0.41) y los
   hilos cortos casi nunca son verdaderos. Al comparar solo hilos de longitud parecida (último bloque de la tabla), SIFT2 ≈ 0.51 y COMMIT ≈ 0.49: **sus
   pesos no aportan información propia sobre la etiqueta**, no están al revés.
2. **La normalización percentil global de Ricardo no cambia el AUC de ningún método** (es una transformación monótona; SIFT2 sigue en 0.426).
   Resuelve otra cosa: pone los tres métodos en la misma escala para poder promediarlos. Esa es su utilidad.
3. **Percentil por decil de longitud** quita el efecto de la longitud y lleva a SIFT2 a 0.505: confirma el punto 1. No «mejora» SIFT2: muestra que sin longitud no hay señal.
4. **Multiplicar por longitud (peso×L)** sube SIFT2 a 0.62, pero es longitud, no SIFT2.
5. **Promediar con SIFT2 y COMMIT empeora** el resultado (0.485 vs 0.649 sin ellos): arrastran al promedio.
6. **LiFE y COMMIT2 sí tienen algo propio**, pequeño (0.53 y 0.58 dentro de deciles de longitud).
7. Un modelo supervisado puede usar un coeficiente **negativo** para SIFT2 y la longitud como entrada: ese ajuste es justo lo que la regla fija «promediar» no puede hacer.

## 3. Qué hacer en la Mac (en este orden)

### 3.1 Evaluar lo de Ricardo con la etiqueta de Hausdorff (no con MDF)
`scripts/normalizacion_ricardo.py` hoy evalúa con MDF (`--etiqueta mdf|mascara`). Añade `--etiqueta hausdorff`, que lea
`out/hausdorff/hausdorff.csv` (columna `hd_min`; verdadero = `hd_min < --eps-hd`, por omisión 5; vacío = falso). No cambies el comportamiento de las opciones existentes.
Corre, con COMMIT, SIFT2, LiFE y COMMIT2:
- percentil global; `--por-longitud 10`; `--x-longitud`; `--corte` (SIFT2 sin ceros).
- combinaciones: promedio de los 4; de LiFE+COMMIT2; voto «≥ 2 de 3» y «≥ 2 de 4».
Reporta, para cada una: AUC, precisión/recall/lift al conservar los n = 10 000, 25 000 y 50 000 hilos de mayor puntaje, y compara
**siempre** con (a) la longitud sola y (b) COMMIT2 solo. Se puede reutilizar `scripts/evaluar_filtrado.py` (funciones `auc` y `metr`).

### 3.2 Modelo (paso 11) con separación entrenamiento/prueba
- Entradas: percentil global de cada método (o log del peso) + longitud (`out/longitudes.txt`). Salida: etiqueta Hausdorff < 5 mm.
- Regresión logística (sklearn). **Separar** 50/50 con semilla fija y estratificado por etiqueta; ajustar solo con entrenamiento, reportar solo en prueba.
- Variantes: (i) con y sin longitud; (ii) solo los 3 métodos pedidos (SIFT2, LiFE, COMMIT); (iii) con COMMIT2.
- Imprimir los **coeficientes** (esperable: SIFT2 negativo). Comparar en prueba contra longitud sola, COMMIT2 solo y el promedio de Ricardo.
- Ojo: un modelo con longitud puede estar aprendiendo «hilo largo = verdadero». Mostrar siempre el resultado **sin** longitud para saber cuánto aportan los pesos.

### 3.3 Dónde dejar resultados
`docs/resultados/modelo_y_normalizacion_hausdorff.md` (tablas + una lectura de 5 líneas). Scripts nuevos con número libre (`11_modelo.sh` + `.py`).
Sube solo código, `.md` y tablas pequeñas (CSV < 5 MB). Se puede actualizar cualquier documento o script existente, sea de quien sea, para que todo quede al día. Avisa con el hash del commit.

### 3.4 Comparar el tractograma filtrado por el modelo contra el GT (último tramo del paso D) — **TAREA PENDIENTE PARA LA MAC**
Hasta aquí todo se midió **hilo por hilo** (precisión, AUC). La junta pide además comparar **el tractograma filtrado como un todo** contra el GT:
¿qué haces (de 21) se recuperan, con qué solape (Dice por haz) y cuántos hilos falsos quedan? Es el resultado más fácil de mostrar al doctor.
Se intentó en la laptop de desarrollo (4 núcleos, ≈ 3 GB de RAM libres) y se **detuvo a los ~4 min**, todavía en la asignación de hilos a haces; **no hay ningún resultado**. Se prepararon dos piezas, descritas abajo.

**Estado de las piezas (léelo antes de usarlas):**
- `scripts/puntajes_candidatos.py` — **probado, funciona (≈ 1 min).** Genera en `out/modelo/puntaje_<nombre>.txt` un puntaje por hilo para: `MODELO_3metodos`
  (SIFT2+LiFE+COMMIT, percentil, sin longitud), `MODELO_4metodos` y `MODELO_4metodos_mas_longitud` (log del peso), `MIN_percentil_LiFE_COMMIT2`, `PROMEDIO_percentil_LiFE_COMMIT2`.
  Los modelos se puntúan con validación cruzada de 2 pliegues (cada hilo lo puntúa un modelo que no lo vio; misma separación 50/50, semilla 0 que `modelo.py`).
- `scripts/normalizacion_ricardo.py --mismos-n N1 N2 …` — **opción nueva SIN PROBAR de punta a punta** (solo se comprobó que el archivo compila). Cada «método» pasado en `--pesos`
  conserva sus N hilos de mayor valor y se evalúa contra el GT (hilos conservados, haces detectados, % falsos, cobertura, desborde, Dice por haz) más la fila «sin filtrar».
  No combina los puntajes entre sí. Salidas: `<salida>/comparacion_mismos_n.csv` y `comparacion_mismos_n_por_conducto.csv`. Si falla o parece incorrecta, corrígela o reescríbela.

**Qué hacer, en orden:**
1. `git pull`; `python scripts/puntajes_candidatos.py 5` (genera los 5 puntajes).
2. Correr (la asignación MDF a los 21 haces se hace una vez y queda en caché en `out/normalizacion/asignacion_mdf_*.npz`):
   ```
   python scripts/normalizacion_ricardo.py --etiqueta hausdorff --eps-hd 5 --mismos-n 10000 25000 50000 \
     --salida out/normalizacion/tractograma_hausdorff --pesos \
     MODELO_3metodos=out/modelo/puntaje_MODELO_3metodos.txt MODELO_4metodos=out/modelo/puntaje_MODELO_4metodos.txt \
     MODELO_4metodos_mas_longitud=out/modelo/puntaje_MODELO_4metodos_mas_longitud.txt \
     MIN_LiFE_COMMIT2=out/modelo/puntaje_MIN_percentil_LiFE_COMMIT2.txt PROM_LiFE_COMMIT2=out/modelo/puntaje_PROMEDIO_percentil_LiFE_COMMIT2.txt \
     SIFT2=out/pesos_sift2.txt COMMIT=out/commit/pesos_commit.txt LiFE=out/life/pesos_life.txt COMMIT2=out/commit2/pesos_commit2.txt LONGITUD=out/longitudes.txt
   ```
   (`LONGITUD` = «me quedo con los hilos largos», referencia obligatoria; `sin filtrar` sale solo.)
3. **Verificar la herramienta antes de fiarse:** la fila `sin filtrar` debe dar los 100 000 hilos y los mismos haces detectados / % de falsos que el tractograma completo ya reportado
   en `docs/resultados/modelo_y_normalizacion_hausdorff.md` (66.7 % de falsos con MDF; con Hausdorff 5 mm debe ser 66.7 %: 1 − 0.333).
4. **Reportar** en `docs/resultados/tractograma_modelo_vs_gt.md`: una tabla por n (10 000 / 25 000 / 50 000) con todas las filas, el Dice por haz de las 3 mejores
   (qué haces se pierden), y una lectura de 5 líneas que diga **si esta evaluación contradice a la de por hilo** (p. ej. un puntaje con buena precisión pero que pierde haces enteros).
5. Mismas reglas de la sección 3.3 (se puede actualizar cualquier archivo existente; solo código, `.md` y tablas < 5 MB; avisar con el hash del commit).

### 3.5 COMMIT2 con otros λ en la comparación del tractograma — **TAREA PENDIENTE PARA LA MAC**
La sección 3.4 mostró que COMMIT2 con λ = 1e-2 apaga por completo BPS, Fornix e ICP, y que todo puntaje que dependa de él pierde esos haces.
Pero el barrido de λ anterior (`docs/resultados/commit2.md`, etiqueta MDF) decía que con **λ = 1e-3 se conservan los 21 haces** (31 % de falsos) y con λ = 1e-4 también (42 %).
Esa comparación usó otra etiqueta y no fue a igual número de hilos. Hay que repetirla con Hausdorff y `--mismos-n`.
1. Los pesos están en `out/commit2_lam1e-3/pesos_commit2.txt`, `out/commit2_lam1e-4/…` y `out/commit2_lam5e-3/…` (solo en la Mac; verifica que existan y que tengan 100 000 valores).
2. Corre `scripts/normalizacion_ricardo.py --etiqueta hausdorff --eps-hd 5 --mismos-n 10000 25000 50000` con, además de las referencias de 3.4, los puntajes `COMMIT2_1e-3`, `COMMIT2_1e-4`, `COMMIT2_5e-3`
   **y** los mínimos de percentiles de LiFE con cada uno (ver cómo lo hace `scripts/puntajes_candidatos.py` para λ = 1e-2). Opcional: el modelo de 4 métodos reentrenado con COMMIT2 de λ = 1e-3.
3. Reportar en `docs/resultados/tractograma_modelo_vs_gt.md` (nueva sección) la misma tabla por n, con el **Dice por haz de BPS, Fornix e ICP**: ¿los recupera con λ menor, y a qué costo en % de falsos?
4. Decir si cambia la recomendación del resumen (`docs/resumen_para_la_junta.md`, secciones 9–10) y actualizarlo tú mismo.
5. Nota: la diferencia con la corrida original de COMMIT2 (62 779 contra 36 928 hilos con peso > 0) ya está documentada en `commit2.md`; no hace falta preguntarle a nadie.

### 3.6 Modelos del grupo de modelos (boosting y bosque) en la comparación del tractograma — **TAREA PENDIENTE PARA LA MAC**
El grupo de modelos entregó dos modelos no lineales, ya integrados y verificados por hilo (ver `docs/resultados/modelo_boosting_ajustado.md` y `modelo_bosque_ajustado.md`):

| Puntaje | AUC (prueba) | Precisión 10 000 / 25 000 / 50 000 | Verdaderos con COMMIT2 = 0 que quedan en los 25 000 mejores |
|---|---|---|---|
| boosting, sin longitud | 0.727 | 63.8 / 56.5 / 47.5 % | 1.8 % |
| boosting, con longitud | 0.798 | 70.5 / 62.4 / 52.7 % | 24.2 % |
| bosque, sin longitud | 0.725 | 63.8 / 56.6 / 47.4 % | 4.1 % |
| bosque, con longitud | 0.799 | 71.5 / 62.8 / 53.0 % | 25.0 % |
| *(referencia) logística 4 métodos* | *0.683* | *45 / 50 / 46 %* | *0.5 %* |

**Falta lo que solo podemos medir nosotros: si filtrar con estos puntajes conserva los haces** (BPS, Fornix, ICP, CA), es decir, el tractograma completo contra el GT.

1. `git pull`. Regenera los 4 puntajes (no están en Git; ≈ 1–3 min cada uno):
   ```
   python scripts/modelo_boosting_ajustado.py --longitud ; python scripts/modelo_boosting_ajustado.py
   python scripts/modelo_bosque_ajustado.py --longitud   ; python scripts/modelo_bosque_ajustado.py
   ```
   **Verifica** que el AUC impreso coincida con la tabla (±0.002). Si no coincide, detente y avisa (se pueden pedir los puntajes originales del grupo).
2. Regenera también las referencias: `python scripts/puntajes_candidatos.py 5`.
3. Corre la comparación (puedes hacerla en la misma corrida que la sección 3.5, añadiendo los COMMIT2 de otros λ):
   ```
   python scripts/normalizacion_ricardo.py --etiqueta hausdorff --eps-hd 5 --mismos-n 10000 25000 50000 \
     --salida out/normalizacion/tractograma_modelos_grupo --pesos \
     BOOSTING_long=out/modelos/puntaje_boosting_ajustado_long.txt BOOSTING=out/modelos/puntaje_boosting_ajustado.txt \
     BOSQUE_long=out/modelos/puntaje_bosque_ajustado_long.txt BOSQUE=out/modelos/puntaje_bosque_ajustado.txt \
     LOGISTICA_4m=out/modelo/puntaje_MODELO_4metodos.txt LOGISTICA_4m_long=out/modelo/puntaje_MODELO_4metodos_mas_longitud.txt \
     MIN_LiFE_COMMIT2=out/modelo/puntaje_MIN_percentil_LiFE_COMMIT2.txt COMMIT2=out/commit2/pesos_commit2.txt \
     LiFE=out/life/pesos_life.txt COMMIT=out/commit/pesos_commit.txt LONGITUD=out/longitudes.txt
   ```
4. **Reporta** en `docs/resultados/tractograma_modelo_vs_gt.md` (sección nueva «Modelos del grupo»): la tabla por n (haces con Dice ≥ 0.3, % falsos, Dice) y el **Dice por haz de BPS, Fornix, ICP y CA**. La pregunta central: **¿el salto de AUC (0.68 → 0.80) se traduce en recuperar haces, o solo en menos falsos?** Y si los recupera, ¿es por los pesos o por la longitud (comparar con y sin longitud)?
5. **Entrega al grupo de modelos la asignación de haces** que pidieron (la necesitan para medir haces recuperados por su cuenta): a partir de `out/normalizacion/etiqueta_hausdorff.csv`, escribe `out/modelos/haz_por_hilo.csv` con columnas `hilo,haz` (100 000 filas, `haz` = nombre del haz o `falso`; usa el haz solo si `etiqueta_5mm = 1`). El `.gitignore` ya permite subir ese archivo. Añade una línea en `docs/para_continuar_modelos.md` (sección 2) diciendo que existe y que, igual que la etiqueta, **no es entrada** del modelo.
6. Actualiza `docs/resumen_para_la_junta.md` (secciones 1, 8 y 9) con lo que salga.
7. Mismas reglas de la sección 3.3.

### 3.7 Actualizar el reporte LaTeX (`Proyecto2_Laboratorio/main.tex`) — **TAREA PENDIENTE PARA LA MAC**
El reporte se escribió **antes de tener la etiqueta de Hausdorff**: sus resultados por hilo y de tractograma usan la etiqueta MDF, y dice que el paso C está «en curso» y el D «pendiente». Hoy C y D están hechos. **Haz primero 3.5 y 3.6** (sus resultados entran aquí) y luego esto.

**Regla general.** La etiqueta oficial es **Hausdorff < 5 mm** (lo pidió el doctor). Los resultados con MDF **no se borran**: pasan a ser secundarios (una tabla o párrafo «comparación con la etiqueta MDF»). **Nunca mezclar en una misma tabla cifras de las dos etiquetas** (sin filtrar: MDF da 45.2 % de falsos; Hausdorff, 66.7 %). Fuentes de las cifras: `docs/resumen_para_la_junta.md` (todo resumido), `docs/evaluacion_filtrado.md`, `docs/resultados/modelo_y_normalizacion_hausdorff.md`, `tractograma_modelo_vs_gt.md`, `modelo_bosque_ajustado.md`, `modelo_boosting_ajustado.md`.

Cambios, por sección (los números de línea son aproximados):
1. **Resumen (≈ l. 120–140).** Reescribirlo con los resultados de Hausdorff: 33.3 % de los hilos corresponden al GT a 5 mm; AUC por hilo SIFT2 0.426, COMMIT 0.449, LiFE 0.601, COMMIT2 0.634, longitud 0.652; logística 3 métodos 0.623 y 4 métodos + longitud 0.70; **boosting / bosque 0.73 sin longitud y 0.80 con longitud** (71 % de verdaderos con 10 000 hilos); el compromiso precisión–haces (lo más preciso pierde BPS, Fornix e ICP por COMMIT2 con λ = 1e-2). Quitar «el entrenamiento de un modelo queda como trabajo pendiente». Conservar la frase de la poda de Hausdorff (22 s → 0.12 s).
2. **Introducción (≈ l. 190–200).** Borrar los comentarios `% NOTA: Falta agregar…` y el párrafo comentado viejo de estado. En «Contribuciones» añadir: (v) la evaluación del tractograma filtrado por haces, y (vi) modelos supervisados (logística, bosque, boosting) entrenados con la etiqueta de Hausdorff.
3. **Figura de flujo (`fig:flujo`).** La caja D ya no está pendiente: quitar el estilo `todo` (borde punteado) y ajustar el pie («Las cajas con borde punteado están pendientes» ya no aplica). Si cabe, cambiar «(7 bloques)» por «(7 computadoras)» y añadir «evaluación por hilo y por haz».
4. **Metodología.**
   - `Etiqueta por hilo`: decir que la **etiqueta principal es Hausdorff < 5 mm** (33 349 verdaderos) y la MDF se usa solo para comparar. Quitar «es la etiqueta con que se obtuvieron los resultados… mientras se calcula la de Hausdorff».
   - `Métricas`: borrar el comentario `% Faltan los métodos de aprendizaje`; añadir precisión al conservar n hilos (10 000 / 25 000 / 50 000), recall, lift y la comparación «a igual número de hilos»; para tractogramas, «haces con Dice ≥ 0.3» y la advertencia de que el Dice solo cuenta hilos verdaderos.
   - **Subsección nueva «Modelos»**: logística (entradas estandarizadas), bosque aleatorio y gradient boosting (fórmulas de las notas del grupo), separación 50/50 estratificada con semilla 0, **intercambio de mitades** (cada hilo lo puntúa un modelo que no lo vio), búsqueda de hiperparámetros dentro de la mitad de entrenamiento, variantes con y sin longitud.
5. **Resultados.**
   - `Nivel de hilo`: rehacer la figura `fig:auc` con los AUC de Hausdorff (0.426 / 0.449 / 0.601 / 0.634 / 0.652) y el texto (verdaderos vs. falsos por longitud, correlaciones peso–longitud: −0.41 SIFT2, −0.20 COMMIT, +0.27 LiFE y COMMIT2; AUC dentro de deciles de longitud ≈ 0.51 / 0.49 / 0.53 / 0.58). Añadir la tabla de precisión «mismo n» de `docs/evaluacion_filtrado.md`.
   - `Combinación de métodos`: las tablas `tab:combo` y `tab:mismon` son de MDF; pasarlas a «comparación con MDF» o reemplazarlas por las de Hausdorff (promedio de Ricardo 3 métodos 0.485, LiFE+COMMIT2 0.649; voto 2 de 3: 30.2 %).
   - `COMMIT2 y λ`: la tabla `tab:lambda` es de MDF; señalarlo en el pie y, con lo de 3.5, añadir los valores con Hausdorff. El párrafo sobre la corrida previa (62 779 contra 36 928) puede quedarse como nota, sin atribuirlo a nadie.
   - `Cálculo de la etiqueta de Hausdorff`: actualizar el cierre — ya se corrió en 7 computadoras; distribución 2 / 3 / 5 / 7 / 10 mm = 2.6 / 13.0 / 33.3 / 46.0 / 58.6 %; los 7 bloques dan 33 ± 0.5 % a 5 mm. Quitar «en una prueba con 300 hilos…» si estorba.
   - **Subsección nueva «Modelos»**: tabla de AUC y precisión (logística, bosque, boosting, con y sin longitud; referencias longitud sola y COMMIT2), coeficientes de la logística (SIFT2 negativo), y el rescate de hilos con COMMIT2 = 0 (24–25 % solo con longitud).
   - **Subsección nueva «Tractograma filtrado contra el GT»**: tabla a 25 000 hilos (% falsos, haces con Dice ≥ 0.3, Dice) y Dice por haz de BPS, Fornix, ICP y CA; con lo de 3.6, las filas de bosque y boosting.
6. **Discusión.** El párrafo sobre la etiqueta («el orden depende de la etiqueta… conviene reportar ambas») ya se puede contestar: con Hausdorff el orden se mantiene (SIFT2 y COMMIT siguen por debajo del azar). Añadir: contradicción entre evaluación por hilo y por haz; no linealidad + longitud explican el salto a 0.80; la longitud domina (reportar siempre sin ella).
7. **Estado (`tab:estado`).** B: hecho (falta ε definitivo); C: hecho; D: hecho (falta decidir qué priorizar con el doctor). Reescribir los párrafos «Paso B/C/D» como **siguientes pasos** reales: decidir prioridad (limpieza vs. haces), COMMIT2 con λ menor, modelo genético (lo mencionó el doctor), validar en otro tractograma o fantoma.
8. **Conclusiones.** Reescribirlas con Hausdorff (quitar «se midieron con la MDF; su confirmación con Hausdorff y el entrenamiento del modelo son los pasos que faltan»).
9. **Apéndice (`tab:scripts`).** Añadir `10_evaluar.sh`, `11_modelo.sh`, `puntajes_candidatos.py`, `modelo_bosque_ajustado.py`, `modelo_boosting_ajustado.py`, `crear_tabla_modelos.py`, y en «Números de control» la tasa base 33.3 % (33 349 hilos) a 5 mm.
10. **Comentarios sueltos** (`% Pendientes, el tiempo de cómputo, parfor…` tras el resumen): resolverlos o borrarlos; los tiempos están en `docs/hausdorff_eficiencia.md`.

**Cómo entregarlo.**
- Compila (`pdflatex main.tex` dos veces) y revisa que no haya referencias rotas (`??`). Si no tienes LaTeX en la Mac, dilo y deja el `.tex` sin compilar.
- Crea `Proyecto2_Laboratorio/.gitignore` con `*.aux *.log *.out *.toc *.synctex.gz *.fls *.fdb_latexmk` (no toques el `.gitignore` de la raíz). El PDF no se sube (lo ignora la raíz).
- No cambies autores, título ni formato; solo contenido. Si una cifra no está en los documentos, no la inventes: marca `\textbf{[FALTA]}` y avísame.
- Commit aparte, solo con el reporte: «reporte: resultados con Hausdorff, modelos y haces».

### 3.8 Compilar y revisar el reporte después de las correcciones — **TAREA PENDIENTE PARA LA MAC**
Después de tu commit `b9d8db1`, en la laptop de desarrollo se corrigió `Proyecto2_Laboratorio/main.tex` (haz `git pull` antes de tocarlo):
- **Resumen** sin mezclar etiquetas (todo con Hausdorff); **las dos logísticas distinguidas** («mismas entradas que los árboles», 0.688/0.699, y «del paso 11», 0.683/0.701) en metodología y tablas.
- **Nivel de hilo** pasado a Hausdorff: figura `fig:auc` con dos series (Hausdorff y MDF), AUC por deciles de longitud y tabla nueva `tab:mismon-haus`.
- Secciones de **λ** y **combinación por percentiles** rotuladas «(etiqueta MDF)», con etiquetas `sec:res-mdf-ini` / `sec:res-mdf-fin`; resultados de Hausdorff en la sección de la etiqueta; discusión, estado (B = hecho), pendientes y conclusiones actualizados; comentarios pendientes borrados; `.gitignore` propio en la carpeta.
- **Apéndice de reproducibilidad reescrito**: enlace al repo, MD5, «el tractograma no se regenera», dos niveles de reproducción, tabla de scripts con 17 filas y columna de tiempo, semillas y números de control.
- En el repo: `environment.yml` ahora incluye `dipy==1.12.1` y `matplotlib==3.11.2`; `requirements.txt` ya no apunta a un script inexistente.

Antes del apéndice, el documento se compiló limpio (15 páginas, sin referencias rotas). **El apéndice nuevo no se ha compilado.** Pide:
1. Compilar (`pdflatex main.tex` dos veces, dentro de `Proyecto2_Laboratorio/`) y confirmar que no hay errores ni `??` (referencias o citas rotas).
2. Revisar en el PDF, sobre todo:
   - la tabla `tab:scripts` (4 columnas, descripciones largas): que quepa en el ancho; si se desborda, acorta descripciones, usa `\footnotesize` o quita la columna «Objetivo», sin perder filas;
   - que `-{}-mismos-n` se vea como dos guiones y no como una raya;
   - la figura `fig:auc`: que la leyenda no tape barras ni etiquetas;
   - las líneas demasiado anchas («Overfull \hbox» en el `.log`): ya había una de 56 pt en la portada (líneas ≈ 85–86) y una de 6 pt en la figura de flujo; corrige las que se vean en el PDF.
3. Si puedes, mide los tiempos que faltan en `tab:scripts` (preproceso, tractografía, matrices, LiFE): ahora dicen «minutos» o «---». Si no los mides, déjalos así; no los inventes.
4. Opcional: comprobar que `conda env create -f environment.yml` funciona con las dos librerías nuevas.
5. No cambies contenido, autores ni título; solo forma. No subas el PDF ni los auxiliares. Commit aparte: «reporte: compilado y ajustes de formato».

## 4. Advertencias
- Los vectores de COMMIT y COMMIT2 se asumen en el orden de `tracks_100k.tck` (solo se verificó el tamaño). Si el AUC de COMMIT sale ≈ 0.5 exacto, sospechar orden.
- ε de Hausdorff = 5 mm es propuesta; repetir con 3 y 7 mm para ver si las conclusiones cambian.
- Las cifras de la sección 1 las generó un script efímero de la laptop de desarrollo; el paso 3.1 debe reproducirlas dentro del repo.

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

## 4. Advertencias
- Los vectores de COMMIT y COMMIT2 se asumen en el orden de `tracks_100k.tck` (solo se verificó el tamaño). Si el AUC de COMMIT sale ≈ 0.5 exacto, sospechar orden.
- ε de Hausdorff = 5 mm es propuesta; repetir con 3 y 7 mm para ver si las conclusiones cambian.
- Las cifras de la sección 1 las generó un script efímero de la laptop de desarrollo; el paso 3.1 debe reproducirlas dentro del repo.

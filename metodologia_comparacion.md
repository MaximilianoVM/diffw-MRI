# Cómo se comparan COMMIT, SIFT2 y LiFE

Explica exactamente qué calculan `scripts/comparar_matrices.py`, `scripts/comparar_pesos.py` y `scripts/evaluar_pesos.py`, y por qué.

**Resumen:** no se usó MDF ni se normalizaron los pesos. Todas las métricas son **invariantes a la escala**: dependen de proporciones o del orden (ranking) de los pesos, no de sus valores absolutos. Por eso dan lo mismo si un método multiplica todos sus pesos por una constante.

---

## 0. El problema de escala

Cada método mide algo distinto y en otras unidades:

| Método | Qué es el peso | Mediana por hilo | Suma de la matriz (triángulo superior) |
|---|---|---|---|
| COMMIT | fracción de volumen intra-axonal por unidad de longitud | 0.00019 (45 % en 0) | ≈ 125 |
| SIFT2 | factor multiplicativo alrededor de 1 (densidad de fibra) | 0.82 (ningún 0) | ≈ 6.2 × 10⁴ |
| LiFE | β de NNLS sobre la señal | ≈ 0.0006 (≈ 39 % en 0, según el equipo) | — |
| GT | conteo de hilos del ground truth | — | ≈ 1.5 × 10⁵ |

Comparar valores directos ("COMMIT da 0.002 y SIFT2 da 0.8") no tiene sentido. Hay dos salidas: **normalizar** (z-score, min-max, cuantiles, dividir por la suma) o **usar métricas que no dependan de la escala**. Aquí se eligió la segunda: es más simple, no obliga a decidir una normalización y no cambia los resultados según cuál se elija.

---

## 1. Matrices contra el GT (`scripts/comparar_matrices.py`)

### Qué se compara

- Cada matriz 84 × 84 sale de `tck2connectome` con `-symmetric -zero_diagonal`: la celda $(i,j)$ es la **suma de los pesos** de los hilos cuyos extremos caen en las regiones $i$ y $j$.
- La matriz GT sale igual, con `data/GT/all_tracks.tck` y sin pesos: **conteo** de hilos reales por par.
- Como las matrices son simétricas y la diagonal es 0, solo se usa el **triángulo superior**: $84 \cdot 83 / 2 = 3486$ pares de regiones. Cada par es una "conexión".
- **Conexión real:** un par con al menos un hilo del GT. Son 529 de los 3486.

### Las cinco métricas

Sea $m_k$ el peso de la conexión $k$ en la matriz del método, $g_k$ su conteo en el GT y $G = \{k : g_k > 0\}$ las conexiones reales.

| Métrica | Fórmula | ¿Depende de la escala? | Qué dice |
|---|---|---|---|
| Conexiones > 0 | $\#\{k : m_k > 0\}$ | no | cuántos pares conecta el método. COMMIT y LiFE pueden apagar conexiones (todos sus hilos con peso 0); SIFT2 nunca |
| En el GT | $\#\{k \in G : m_k > 0\}$ | no | conexiones reales que sobreviven (de 529) |
| % del peso en el GT | $\dfrac{\sum_{k \in G} m_k}{\sum_k m_k}$ | **no**: al multiplicar todo por $c$, la $c$ se cancela | qué fracción del peso total cae en conexiones reales. Es la métrica más directa de "limpieza" del conectoma |
| AUC por conexión | área bajo la curva ROC usando $m_k$ como puntaje para predecir $k \in G$ | **no**: solo usa el orden de los $m_k$ | probabilidad de que una conexión real elegida al azar tenga más peso que una falsa elegida al azar. 0.5 = azar, 1 = separación perfecta |
| Pearson con el GT | $r(m, g)$ sobre los 3486 pares | invariante a $m \to a\,m + b$ con $a > 0$, pero **no** a cambios no lineales | si el peso de cada conexión es **proporcional** a cuántos hilos reales tiene. Pide más que el AUC: no basta con ordenar bien, también hay que acertar en las proporciones |

### Detalles a tener en cuenta

- **Pearson es sensible a las colas.** Unas pocas conexiones con mucho peso dominan el resultado, y el GT es un conteo. Por eso COMMIT, cuyo peso es por unidad de longitud y favorece conexiones cortas, sale bajo (0.73) y sube al multiplicarlo por la longitud (0.88). Spearman entre $m$ y $g$ sería una alternativa por rangos; no está calculada.
- **Empates en el AUC.** Las conexiones con peso 0 empatan entre sí, y el AUC las cuenta como medio acierto. Afecta igual a todos los métodos.
- **La región 15 no existe** en `Parcels_free.nii`. Sus 83 pares están en 0 en todas las matrices y en el GT, y entran al AUC como empates falsos-falsos. El efecto es pequeño e igual para todos.
- **Asignación de extremos.** `tck2connectome` usa por omisión una búsqueda radial de hasta 4 mm desde cada extremo para encontrar la región. Los hilos que no llegan a ninguna región (27 %) no entran a ninguna matriz, sin importar su peso. Pasa igual en los tres métodos porque comparten tractograma.
- **"Sin pesos" es el control:** la misma matriz contando hilos (peso 1 para todos). Si un método no supera al control, sus pesos no mejoran el conectoma respecto a contar.

---

## 2. Pesos de los métodos entre sí (`scripts/comparar_pesos.py`)

Aquí no interviene el GT: solo cuánto se parecen los métodos. Esto solo es posible porque los tres pesan **los mismos hilos en el mismo orden** (`data/tracks_100k.tck`).

| Métrica | Cómo se calcula | Por qué así |
|---|---|---|
| **Spearman por hilo** | correlación de Pearson entre los **rangos** de $w^{A}$ y $w^{B}$ sobre los 100 000 hilos | solo usa el orden: no hace falta normalizar y no la dominan los valores extremos. Responde: ¿los hilos que un método valora más son los mismos que valora el otro? |
| **Spearman por conexión** | se arma la matriz 84 × 84 de cada método (suma de pesos por par, con `out/asignaciones.txt`) y se calcula Spearman entre los dos triángulos superiores | lo mismo, al nivel del conectoma |
| **Coincidencia en lo que descartan** | cada método "descarta" la misma fracción $f$ de hilos, los de **menor peso** (cuantil $f$ de sus propios pesos). Se reporta $\lvert D_A \cap D_B\rvert / \lvert D_A\rvert$ y el índice de Jaccard $\lvert D_A \cap D_B\rvert / \lvert D_A \cup D_B\rvert$ | es una **normalización por cuantiles**: no se compara "peso < 0.001", que significa cosas distintas en cada método, sino "el 45 % más bajo de cada uno". Así los dos descartan la misma cantidad y la comparación es justa |
| Línea base | si los descartes fueran al azar, la coincidencia esperada sería $f$ | para saber si 63 % es mucho o poco |
| Spearman con la longitud | rangos de $w$ contra rangos de la longitud del hilo | detecta el sesgo por longitud de cada método |

**¿Por qué $f = 45\%$?** Es la fracción de hilos que COMMIT pone exactamente en 0. Es su descarte "natural", así que se le pide a SIFT2 (y a LiFE) descartar la misma cantidad. En COMMIT, el cuantil 45 % cae justo en el bloque de ceros, así que sus descartados son exactamente sus hilos con peso 0.

**Resultado actual, COMMIT vs SIFT2:** Spearman por hilo +0.49, por conexión +0.96, coincidencia en descartes 63 % (azar 45 %), Jaccard 0.46. Coinciden mucho en qué conexiones importan y bastante menos en qué hilos individuales sobran.

---

## 3. Pesos contra el GT, hilo por hilo (`scripts/evaluar_pesos.py`)

Para evaluar hilo por hilo hace falta saber si cada hilo es "bueno". **No se usó MDF.** La etiqueta actual es **por extremos**:

| Etiqueta | Regla | Hilos |
|---|---|---|
| bueno | sus dos extremos caen en regiones que el GT conecta | 55 108 |
| malo | sus dos extremos caen en regiones, pero el GT no las conecta | 18 179 |
| sin región | algún extremo no cae en ninguna región (se cuenta como malo) | 26 713 |

Con esa etiqueta se calcula el **AUC por hilo**: el peso como puntaje para predecir "bueno". También es invariante a la escala.

**Por qué esta etiqueta es débil:** un hilo puede unir dos regiones conectadas en el GT siguiendo un camino falso, o terminar fuera de las regiones siguiendo bien un haz real; el 21 % de los hilos del propio GT no termina en ninguna región. Con ella, los métodos salen alrededor del azar (COMMIT 0.458, SIFT2 0.430), mientras que por conexión salen bien (0.83–0.85). Es la razón para cambiarla por la MDF.

### Qué cambiaría con MDF (pendiente)

La distancia MDF (ver `docs/dwaveone_metodologia.md`) compara la **forma** del hilo con los haces del GT, no solo sus extremos:

1. Remuestrear cada hilo y cada haz del GT a 20 puntos.
2. Centroides de cada uno de los 21 haces de `data/GT/` con QuickBundles.
3. $\mathrm{MDF}(s,t) = \min\big(\tfrac{1}{20}\sum_i \lVert s_i - t_i\rVert,\ \tfrac{1}{20}\sum_i \lVert s_i - t_{21-i}\rVert\big)$; para cada hilo, la menor MDF a algún centroide.
4. Bueno si esa MDF es menor que un umbral (p. ej. 10 mm).

Solo cambiaría la sección 3, la evaluación contra el GT por hilo. Las secciones 1 y 2 no dependen de la etiqueta.

---

## 4. Lo que no se hizo y por qué

| | Por qué no |
|---|---|
| Normalizar los pesos (z-score, min-max, dividir por la suma) | las métricas elegidas no la necesitan. Hará falta en la regla de decisión si se combinan los pesos en una sola fórmula (p. ej. promedio de rangos o de cuantiles) |
| Comparar valores absolutos de las matrices (diferencia celda a celda, norma de Frobenius) | dependen de la escala; solo tendrían sentido después de normalizar |
| MDF | es la siguiente etiqueta por hilo; aún no está escrita |
| Spearman entre la matriz y el GT | sería un buen complemento de Pearson (menos sensible a las colas); se puede agregar en una línea |
| Comparar con la matriz LiFE del equipo hilo por hilo | sale de otro tractograma: los hilos no se corresponden |

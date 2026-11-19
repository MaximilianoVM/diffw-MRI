# Integración de COMMIT, SIFT2 y LiFE (2026-11-13)

**Objetivo de este paso intermedio:** que los tres métodos den una matriz 84 × 84 **comparable** y que sus pesos se puedan comparar hilo por hilo. Es el paso 3 de la idea del proyecto (`docs/equipos/Introduccion-desafio.pptx`, diap. 22): aplicar LiFE, COMMIT y SIFT2 al **mismo** tractograma para obtener un peso por streamline. La regla de decisión (paso 4) va después.

## Estado

| Método | Quién | Pesos sobre `data/tracks_100k.tck` | Matriz comparable | Estado |
|---|---|---|---|---|
| COMMIT | nosotros | `out/commit/pesos_commit.txt` | `out/matriz_peso_commit_84x84_corregida.xlsx` | ✅ |
| SIFT2 | equipo SIFT2 / nosotros | `out/pesos_sift2.txt` | `out/matriz_sift2.xlsx` (la del equipo, con la diagonal corregida: `out/equipos/matriz_sift2_equipo_84x84_diag0.xlsx`) | ✅ |
| LiFE | equipo LiFE | `out/life/pesos_life.txt` (su `life_weights.txt`, 14 nov) | `out/matriz_peso_life_84x84.xlsx` | ✅ |

## Qué hace comparables las matrices

Las tres deben cumplir lo mismo, si no la diferencia no es del método:

1. **Mismo tractograma:** `data/tracks_100k.tck` (100 000 hilos, media 92 mm, eje *y* corregido, `-mask`).
2. **Un peso por hilo, en el orden del `.tck`.**
3. **Misma matriz:** `tck2connectome ... data/Parcels_free.nii ... -tck_weights_in <pesos> -symmetric -zero_diagonal`.
4. **Mismo formato:** `.xlsx` 84 × 84 con encabezados R1–R84 (`scripts/exportar_matriz84.py`).
5. **Comparación sin depender de la escala:** las sumas no se parecen (COMMIT ≈ 125, SIFT2 ≈ 6 × 10⁴), así que se usan el % del peso en conexiones del GT, el AUC por conexión y el Pearson con el GT (`scripts/comparar_matrices.py`).

## Lo que mandaron los equipos y en qué diferimos

Material en `docs/`: `Comandos SIFT2.txt`, `life_comandos_matriz.txt`, `life_metodo.md` y sus matrices `.numbers`, convertidas a CSV en `out/equipos/`.

### SIFT2 (`docs/equipos/Comandos SIFT2.txt`, `Connectome_SIFT2_100k.numbers`)

Su matriz **sí sale de nuestro `tracks_100k.tck`**: las mismas 1322 conexiones, y r = 0.99994 con la nuestra. La reproduje con sus comandos exactos (`out/equipos/sift2_repro/`): diferencia máxima de 0.05.

| Diferencia | Ellos | Nosotros | Efecto | Qué se hizo |
|---|---|---|---|---|
| `-zero_diagonal` | no | sí | 5968 de peso en la diagonal (8.8 % del total), autoconexiones que inflan la matriz | **Corregido:** `out/equipos/Connectome_SIFT2_100k_diag0.csv` y `.xlsx` |
| FOD | `-fslgrad` con el `.bvec` crudo (sin invertir *y*) y la máscara `ISMRM_2023_b3000_mask.nii` | `out/fod.mif` con *y* invertido y `dwi2mask` | pequeño (abajo) | se reporta; usamos la nuestra |
| `-out_mu` | sí | no | ninguno en los pesos | agregado a `scripts/02_tractography.sh` |
| `tcksift2` sobre… | el `.txt` dice `all_tracks.tck` (el GT) | `tracks_100k.tck` | la matriz que entregaron sí usa `tracks_100k.tck`: el `.txt` está desactualizado | avisarles |

**¿Qué tan grave es la FOD sin corregir?** Poco:

| | Su FOD vs la nuestra |
|---|---|
| Pesos por hilo: Pearson / Spearman | 0.989 / 0.986 |
| Cambio relativo por hilo: mediana / p90 | 1.4 % / 10.9 % (3 % de los hilos cambian más de 20 %) |
| Cambio relativo por conexión: mediana / p90 | 1.3 % / 7.7 % |
| AUC por hilo (etiqueta por extremos) | 0.433 / 0.430 |
| AUC por conexión, % peso en GT, Pearson con GT | 0.850 / 74.7 % / 0.793 contra 0.850 / 74.6 % / 0.795 |
| Coinciden en el 10 % de hilos con menor peso | 93 % |

SIFT2 reparte peso sobre un tractograma que ya estaba bien trazado, así que una FOD con *y* invertido apenas lo mueve. No hace falta recalcular nada: la versión con la FOD corregida es la nuestra (`out/pesos_sift2.txt`, 12 s). Para la regla de decisión conviene usar la nuestra, porque ≈ 7 % de los hilos que se descartarían por umbral cambian.

### LiFE (`docs/equipos/life_comandos_matriz.txt`, `docs/equipos/life_metodo.md`, `conn_life_full.numbers`)

**Su matriz no se puede usar para comparar.**

| Diferencia | Ellos | Nosotros | Efecto |
|---|---|---|---|
| Tractograma | su propio `tracks.tck`, generado con la FOD sin invertir *y* y sin `-mask` | `tracks_100k.tck` | **grave**: son otros hilos, no se pueden comparar ni combinar hilo por hilo |
| Longitud de los hilos | `tracks.tck` de 44 MB (≈ 40 mm de media) | 109 MB (92 mm) | sus hilos salen cortados, como en el Excel inicial |
| `-zero_diagonal` | no | sí | 14.8 de peso en la diagonal |
| Gradientes en DIPY | `.bvec` crudo | — | **correcto**: el `.bvec` crudo es idéntico a nuestra tabla corregida; la inversión de *y* solo hace falta al importarlo a MRtrix con `-fslgrad` |
| `np.linalg.inv(img.affine)` | sí | sí (mismo script) | correcto |

Su matriz recupera **120 de 529** conexiones del GT, con AUC 0.535 (azar) y Pearson 0.05 con el GT. Es casi igual que el Excel inicial con el mismo error (125). El problema es el tractograma, no su código de LiFE.

**Qué se hizo:** `scripts/correr_life.py` es su mismo script (`FiberModel(gtab).fit(data, hilos, inv(affine))`, `.bvec` crudo), solo con `data/tracks_100k.tck` como entrada. Aquí no se pudo correr completo: con nuestros hilos de 92 mm pide ≈ 20 GB y la Mac tiene 16. Una prueba con 20 000 hilos tardó 21 s y usó 4.7 GB; con 100 000 se quedó esperando a la swap y la detuve. **Se les pidió correrlo con `tracks_100k.tck`.** Cuando manden `life_weights.txt`:

```bash
mkdir -p out/life && cp life_weights.txt out/life/pesos_life.txt   # 100 000 líneas, orden del .tck
bash scripts/05_life.sh                                              # salta el ajuste si el archivo ya existe
```

Eso genera `out/matriz_peso_life_84x84.xlsx`, `out/evaluacion_life.txt`, `out/comparacion_matrices.csv` y `out/comparacion_pesos.txt`.

**Actualización (13 nov, noche): llegó LiFE sobre `tracks_100k.tck`** (`conn_life_full.csv`, `conn_raw_full.csv`; copias en `out/equipos/life_100k/`).

- `conn_raw_full.csv` es idéntico a nuestro conteo sin pesos fuera de la diagonal (68 418 hilos, 1322 conexiones): **usaron nuestro tractograma**.
- Siguen sin `-zero_diagonal`: 4869 hilos en la diagonal del conteo y 1.3 % del peso LiFE. Se puso en 0 → `*_diag0.csv`.
- Mandaron solo las matrices, no `life_weights.txt` (100 000 pesos por hilo). Con la matriz basta para comparar conexiones; **para la normalización y la comparación hilo por hilo hacen falta los pesos por hilo**.

**Actualización (14 nov): llegaron los pesos por hilo** (`life_weights.txt`, `life_weights.csv`, `life_summary.csv`; en `out/equipos/life_100k/`, copia en `out/life/pesos_life.txt`).

- Cumplen el contrato de `docs/guia_equipo.md`: 100 000 pesos ≥ 0, sin NaN; 74 612 > 0 (25.4 % en 0).
- Están en el orden de `data/tracks_100k.tck`: la columna `length_mm` coincide con `out/longitudes.txt` (diferencia máxima 0.001 mm).
- Nuestra matriz con sus pesos (`tck2connectome -tck_weights_in`) da exactamente lo mismo que la suya: 1168 conexiones, 90.7 % de peso en el GT, Pearson 0.923.
- Contra la prueba local con 20 000 hilos: Spearman 0.96 en esos hilos.
- Hilo por hilo (etiqueta por extremos): AUC 0.707, el único método por encima de la longitud sola (0.635). Los que pone en 0 son malos en un 67 % (al azar 45 %). Con la etiqueta MDF del paso 7: AUC 0.655 (COMMIT2 0.684, COMMIT 0.420, SIFT2 0.345).
- Hilo por hilo casi no se parece a COMMIT ni a SIFT2 (Spearman −0.02 y −0.10), pero sí a COMMIT2 (+0.33). Por conexión coincide con todos (0.89–0.93).

## Resultados de la comparación

### Matrices contra el GT (`scripts/comparar_matrices.py`)

GT: 529 conexiones reales de 3486 pares posibles.

| Matriz | Conexiones > 0 | En el GT | % peso en GT | AUC conexión | Pearson con GT |
|---|---|---|---|---|---|
| sin pesos (control) | 1322 | 460 | 80.5 | 0.857 | 0.894 |
| SIFT2 | 1322 | 460 | 74.6 | 0.850 | 0.795 |
| COMMIT | 1203 | 446 | 63.8 | 0.829 | 0.731 |
| COMMIT × longitud | 1203 | 446 | 79.0 | 0.846 | 0.881 |
| equipo SIFT2 (diagonal en 0) | 1322 | 460 | 74.7 | 0.850 | 0.793 |
| COMMIT2 (λ = 1e-2) | 86 | 70 | 91.9 | 0.564 | 0.788 |
| equipo LiFE (su tractograma) | 595 | 120 | 34.7 | 0.535 | 0.051 |
| **equipo LiFE sobre `tracks_100k.tck` (diagonal en 0)** | 1168 | 442 | **90.7** | 0.851 | **0.923** |

**LiFE es el único método que supera al conteo sin pesos** en % de peso en el GT (90.7 contra 80.5) y en Pearson (0.923 contra 0.894), y casi lo iguala en AUC (0.851 contra 0.857). Descarta 154 de las 1322 conexiones (las pone en 0) y solo pierde 18 reales. COMMIT2 tiene más % de peso en el GT, pero se queda con solo 86 conexiones.

### Pesos entre sí, hilo por hilo (`scripts/comparar_pesos.py`)

| | COMMIT | SIFT2 |
|---|---|---|
| Peso = 0 | 44.8 % | 0 % |
| Spearman con la longitud | −0.20 | −0.41 |

**COMMIT vs SIFT2:** Spearman por hilo +0.49 y por conexión +0.96. Si cada uno descartara el 45 % de hilos con menor peso, coincidirían en el 63 % de los descartados (al azar sería 45 %; Jaccard 0.46). A nivel de conexión casi coinciden, pero hilo por hilo descartan cosas distintas. Eso es lo que hace interesante combinarlos.

## Pendiente

1. ~~Matriz y pesos por hilo de LiFE sobre `tracks_100k.tck`~~ (llegaron; 05 y 07 corridos el 14 nov). Que la próxima vez usen `-zero_diagonal`.
2. Avisar al equipo SIFT2: falta `-zero_diagonal`, la FOD va sin invertir *y* (efecto pequeño) y el `.txt` dice `all_tracks.tck`.
3. **Etiqueta por haz contra el GT**, para evaluar hilo por hilo: la de extremos da AUC ≈ 0.43–0.46 en todos los métodos. La distancia MDF que usó DWaveOne sirve para esto (`docs/equipos/dwaveone_metodologia.md`). Corresponde al paso 2 de la diap. 22 ("seleccionar los streamlines que más se parezcan al GT").
4. Regla de decisión que combine los tres pesos (paso 4).

## Archivos nuevos

| Archivo | Qué es |
|---|---|
| `scripts/correr_life.py` | el script de LiFE del equipo, con `tracks_100k.tck` como entrada |
| `scripts/05_life.sh` | matriz, Excel y evaluación de LiFE + las dos comparaciones |
| `scripts/comparar_matrices.py` | matrices de todos los métodos contra el GT → `out/comparacion_matrices.csv` |
| `scripts/comparar_pesos.py` | pesos de los métodos entre sí → `out/pesos_por_hilo.csv` |
| `out/equipos/` | matrices de los equipos en CSV, la de SIFT2 con la diagonal en 0, y la reproducción de sus comandos |

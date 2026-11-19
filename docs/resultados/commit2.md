# COMMIT2: corrida, arreglos y barrido de λ (2026-11-13)

Registro de todo lo hecho con COMMIT2 en esta sesión: bajar el script del repo, corregirlo, correrlo con cuatro valores de λ y evaluarlo solo, en las matrices y dentro de la normalización Ricardo.

## 1. Qué es COMMIT2

Es COMMIT (mismo modelo Stick-Zeppelin-Ball y mismo diccionario) con una penalización **group lasso**. Los hilos que unen el mismo par de regiones forman un grupo, y el ajuste prefiere apagar grupos completos, es decir, conexiones poco respaldadas por la señal. Cada hilo que no une dos regiones forma su propio grupo. λ controla la fuerza de esa penalización: con λ más grande se apagan más conexiones.

## 2. Origen

- Commit `42022b6` de Maximiliano ("COMMIT2: script de ajuste con group lasso y paso 6"): `scripts/correr_commit2.py` y `scripts/06_commit2.sh`.
- El repo trae el **script**, no los pesos, porque `out/` no se sube. Se corrió aquí, en la Mac (16 GB, 10 núcleos), reutilizando el diccionario de nuestro COMMIT (`out/commit/COMMIT/`).
- Grupos: 32 904, de los cuales 1322 son conexiones entre dos regiones y el resto hilos sueltos.
- Configuración: `group_weights_cardinality=True` y `group_weights_adaptive=True` (como en Schiavi et al. 2020).

## 3. Arreglos al script

| Problema | Síntoma | Arreglo |
|---|---|---|
| Faltaba el ajuste sin regularizar | `ERROR Group weights cannot be computed if the fit without regularisation has not been performed before` | `mit.fit()` antes de `set_regularisation`: los pesos de grupo adaptativos se calculan a partir del COMMIT normal |
| `save_results()` escribía en la carpeta del diccionario de COMMIT | **Pisó `out/commit/COMMIT/Results_StickZeppelinBall/`** (mapas de NRMSE y compartimentos de COMMIT) y el script no encontraba los pesos (`max() iterable argument is empty`) | `save_results(path_suffix="_COMMIT2")` y mover el resultado a la carpeta de salida de COMMIT2 |
| Una sola carpeta de salida | Cada λ pisaba al anterior | Opción `--salida=` (p. ej. `--salida=out/commit2_lam5e-3`) |

**Daño de la primera corrida:** los pesos de COMMIT (`out/commit/pesos_commit.txt`, del 10 de noviembre, 44 780 ceros) **no se tocaron**. Se perdieron los mapas detallados de COMMIT (`fit_NRMSE.nii.gz`, `compartment_*.nii.gz`, `results.pickle`). Esa carpeta, que en realidad tenía los resultados de COMMIT2 con λ = 1e-2, se movió a `out/commit2/Results_StickZeppelinBall/`. Para regenerar los mapas de COMMIT: `bash scripts/03_commit.sh` (≈ 75 s). **Pendiente.**

## 4. Qué se corrió

```bash
bash scripts/06_commit2.sh                                  # λ = 1e-2 -> out/commit2/ (pesos, matriz, evaluación)
bash scripts/barrido_lambda_commit2.sh 5e-3 1e-3 1e-4      # cada λ -> out/commit2_lam<λ>/ y out/normalizacion/umbrales_lam<λ>/
bash scripts/07_normalizacion.sh                            # normalización con COMMIT + SIFT2 + COMMIT2 (λ = 1e-2)
python scripts/comparar_matrices.py; python scripts/comparar_pesos.py
```

`scripts/barrido_lambda_commit2.sh` (nuevo) hace, para cada λ: pesos con `correr_commit2.py --lambda=λ --salida=out/commit2_lam<λ>`, matriz con `tck2connectome -symmetric -zero_diagonal`, `.xlsx`, `evaluar_pesos.py` y la normalización Ricardo (umbrales 0.1–0.5) con COMMIT + SIFT2 + COMMIT2(λ).

Tiempo: ≈ 1 min 6 s por λ para el ajuste (dos ajustes seguidos: sin regularizar y con group lasso), ≈ 1 min 40 s con la evaluación y la normalización.

| Carpeta | λ | Archivos |
|---|---|---|
| `out/commit2/` | 1e-2 | `pesos_commit2.txt`, `Results_StickZeppelinBall/`; matriz en `out/connectome_commit2.csv`, `out/matriz_commit2.xlsx`, `out/evaluacion_commit2.txt` |
| `out/commit2_lam5e-3/` | 5e-3 | `pesos_commit2.txt`, `connectome_commit2.csv`, `matriz_commit2.xlsx`, `evaluacion.txt`, `normalizacion.txt`, `Results_StickZeppelinBall/` |
| `out/commit2_lam1e-3/` | 1e-3 | ídem |
| `out/commit2_lam1e-4/` | 1e-4 | ídem |
| `out/normalizacion/umbrales*/` | cada λ | `resumen_umbrales.csv`, `comparacion_mismo_n.csv`, `resultados_por_conducto.csv`, `.tck` y `keep_u*.txt` por umbral |

## 5. Resultados: COMMIT2 solo, según λ

Referencias en el mismo tractograma: COMMIT (λ = 0, sin group lasso) y "sin filtrar".

### Hilos y matriz 84 × 84

| | COMMIT | λ = 1e-4 | λ = 1e-3 | λ = 5e-3 | λ = 1e-2 |
|---|---|---|---|---|---|
| Hilos con peso > 0 | 55 220 | 49 470 | 49 003 | 41 746 | 36 928 |
| Peso = 0 | 44.8 % | 50.5 % | 51.0 % | 58.3 % | 63.1 % |
| Conexiones > 0 | 1203 | 800 | 298 | 134 | 86 |
| Conexiones del GT recuperadas (de 529) | **446** | 337 | 172 | 99 | 70 |
| % de la matriz que existe en el GT | 37 % | 42 % | 58 % | 74 % | **81 %** |
| % del peso en conexiones del GT | 64 % | 67 % | 79 % | 87 % | **92 %** |
| AUC por conexión | **0.829** | 0.756 | 0.644 | 0.588 | 0.564 |
| Pearson con el GT | 0.731 | 0.751 | 0.773 | 0.791 | **0.788** |
| Spearman con la longitud | −0.20 | −0.06 | +0.09 | +0.20 | +0.27 |
| Spearman por hilo con COMMIT | 1 | +0.71 | +0.25 | +0.07 | +0.01 |

### Hilo por hilo y por haz (contra el GT)

| | COMMIT | λ = 1e-4 | λ = 1e-3 | λ = 5e-3 | λ = 1e-2 | sin filtrar |
|---|---|---|---|---|---|---|
| AUC por hilo, etiqueta MDF | 0.420 | 0.508 | 0.622 | 0.666 | **0.684** | — |
| AUC por hilo, etiqueta por extremos* | 0.458 | 0.623 | 0.785 | **0.809** | 0.804 | — |
| Haces detectados (de 21) | 21 | 21 | 21 | 20 | 17 | 21 |
| % fibras falsas ↓ | 48.7 | 41.7 | 31.2 | 25.0 | **21.2** | 45.2 |
| Cobertura ↑ | 0.776 | 0.756 | 0.702 | 0.615 | 0.540 | **0.818** |
| Desborde ↓ | 0.253 | 0.237 | 0.219 | 0.175 | **0.160** | 0.332 |
| Dice ↑ | **0.750** | 0.740 | 0.704 | 0.633 | 0.545 | **0.750** |
| MDF simétrico (mm) ↓ | **2.58** | 2.63 | 2.74 | 2.92 | 2.89 | 2.47 |

\* La etiqueta por extremos favorece a COMMIT2: sus grupos se definen con los mismos pares de regiones que esa etiqueta. La de MDF es la más honesta.

**Lectura:**
- **λ es una perilla entre precisión y cobertura.** Al subirlo bajan las fibras falsas (48.7 → 21.2 %) y sube la limpieza de la matriz (81 % de sus conexiones existen en el GT), pero se pierden conexiones reales (446 → 70) y haces (21 → 17).
- **COMMIT2 es el único método que separa hilos buenos de malos** (AUC MDF 0.62–0.68 con λ ≥ 1e-3). Además corrige el sesgo hacia los hilos cortos de COMMIT y SIFT2: la correlación con la longitud pasa de −0.20 a positiva.
- **λ = 1e-4** es casi COMMIT (Spearman 0.71 con COMMIT), pero con menos falsas (41.7 % contra 48.7 %) y casi el mismo Dice (0.740 contra 0.750). Es el **único filtro de todos los probados que baja las fibras falsas respecto a "sin filtrar" (45.2 %) sin perder haces ni Dice apreciable**.
- **λ = 1e-3** es el punto medio: conserva los 21 haces y deja 31 % de falsas, a cambio de cobertura 0.70 y Dice 0.70.

## 6. Normalización Ricardo con COMMIT + SIFT2 + COMMIT2(λ)

Umbrales 0.1–0.5 sobre el promedio de percentiles, cada versión contra el GT (etiqueta MDF). Fila del umbral ganador en cada caso:

| COMMIT2 con λ | Ganador | Hilos | % falsas | Cobertura | Dice | % falsas con u = 0.5 |
|---|---|---|---|---|---|---|
| (sin COMMIT2) | u = 0.1 | 84 278 | 47.1 | 0.804 | 0.749 | 59.5 |
| 1e-2 | u = 0.1 | 82 873 | 46.5 | 0.797 | 0.743 | 52.0 |
| 5e-3 | u = 0.1 | 82 492 | 46.7 | 0.797 | 0.743 | 52.9 |
| 1e-3 | u = 0.1 | 82 189 | 47.0 | 0.797 | 0.743 | 53.6 |
| 1e-4 | u = 0.1 | 79 029 | 48.0 | 0.794 | 0.743 | 55.3 |

- Con cualquier λ, el ganador es **u = 0.1**, el que menos filtra, y ninguna versión combinada baja de 45.2 % de falsas (sin filtrar).
- Agregar COMMIT2 hace que el combinado empeore menos al subir el umbral (59.5 → 52–55 % de falsas con u = 0.5), pero **promediar con SIFT2 y COMMIT diluye la ventaja de COMMIT2**: su AUC MDF de 0.62–0.68 baja a 0.40–0.46 en el score combinado. COMMIT2 solo (21–42 % de falsas) es mejor filtro que cualquier combinado.

## 7. Diferencia con la corrida de la compañera

Ella reportaba **62 779 hilos con peso > 0** con λ = 1e-2. Aquí quedan **36 928**, y ningún λ probado llega a 62 779: el máximo fue 49 470, con λ = 1e-4. Causas posibles, por preguntarle:
1. Si usó pesos de grupo adaptativos (`group_weights_adaptive`) y por cardinalidad.
2. Cómo armó los grupos: su matriz era 85 × 85, con el nodo 0 de "sin región". Si juntó todos los hilos sin región en un solo grupo, el resultado cambia mucho.
3. Si usó el tractograma oficial (md5 `66ba3e6efe1fadf5b534d3947b2b138f`).
4. Su `d_isos` y los demás parámetros del modelo.

## 8. Conclusión y recomendación

| Si se prioriza… | Usar | Por qué |
|---|---|---|
| Matriz 84 × 84 (conectoma) | **COMMIT** (o COMMIT × longitud) | recupera 446 de 529 conexiones, AUC por conexión 0.83; COMMIT2 apaga conexiones reales |
| Tractograma limpio sin perder haces | **COMMIT2 con λ = 1e-3** | 21 haces, 31 % de falsas (contra 45 %), Dice 0.70 |
| Mejora casi gratis sobre COMMIT | **COMMIT2 con λ = 1e-4** | 21 haces, 42 % de falsas, Dice 0.74 |
| Máxima precisión | COMMIT2 con λ = 1e-2 | 21 % de falsas, pero pierde 4 haces |

Para la normalización: con estos métodos, **combinar empeora a COMMIT2**. Si se mantiene la combinación, conviene darle más peso a COMMIT2 o usar solo COMMIT2 y LiFE cuando llegue, en lugar de un promedio simple con SIFT2.

## 9. Pendientes

1. Regenerar los mapas de COMMIT: `bash scripts/03_commit.sh` (≈ 75 s).
2. Preguntar a la compañera su configuración de COMMIT2 (sección 7).
3. Decidir con el equipo qué λ usar y si COMMIT2 entra a la normalización como método aparte o reemplaza a COMMIT.
4. Repetir todo con LiFE cuando llegue `out/life/pesos_life.txt` (`instrucciones_life.md`).

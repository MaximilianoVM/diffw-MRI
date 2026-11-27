# Selección de *streamlines* con pesos SIFT2, LiFE y COMMIT

Código y resultados del proyecto *Selección de streamlines en tractografía mediante pesos SIFT2, LiFE y COMMIT: normalización, filtrado y evaluación contra el ground truth del fantoma ISMRM* (Laboratorio de Resolución de Problemas I, Maestría en Modelación y Optimización de Procesos, CIMAT Unidad Aguascalientes, 2026).

## Resumen

Un mismo tractograma de 100 000 *streamlines* (hilos) del fantoma ISMRM 2015 (versión revisada de 2023) se pesa con **SIFT2, LiFE, COMMIT y COMMIT2**. Los pesos se comparan contra el *ground truth* (GT; 189 985 hilos en 21 haces) en tres niveles:

1. **Conexión:** matrices de conectividad de 84 × 84 regiones.
2. **Hilo:** cada hilo se etiqueta como verdadero si su distancia de Hausdorff al GT es menor que 5 mm.
3. **Tractograma filtrado:** Dice por haz, al conservar el mismo número de hilos.

Después se entrenan modelos supervisados (regresión logística, bosque aleatorio, *gradient boosting* y MLP) que combinan los pesos con la longitud del hilo.

**Resultado principal.** Por sí solos, los pesos no bastan para seleccionar hilos: SIFT2 y COMMIT ordenan por debajo del azar (AUC 0.43 y 0.45), y LiFE y COMMIT2 separan moderadamente (0.60 y 0.63). Combinados con la longitud mediante un modelo no lineal llegan a un AUC de 0.80. Al conservar 25 000 hilos, el bosque aleatorio reduce los hilos falsos de 66.7 % a 37.2 % y conserva 19 de los 21 haces con un Dice de al menos 0.3.

El reporte completo está en [`reporte/main.tex`](reporte/main.tex).

## Requisitos

- **MRtrix3 3.0.8**, para el preprocesamiento, la tractografía, SIFT2 y las matrices.
- **Python 3.13**, con las versiones fijadas en `environment.yml` / `requirements.txt`: COMMIT 2.4.2, AMICO 2.1.1, DIPY 1.12.1, scikit-learn 1.9.1, numpy, pandas y nibabel. PyTorch solo hace falta para el MLP.

Hay dos formas de instalar el entorno:

```bash
# Linux / WSL (conda; incluye MRtrix3)
conda env create -f environment.yml
conda activate dwmri

# macOS (venv; MRtrix3 3.0.8 se instala aparte y debe estar en el PATH)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
source .venv/bin/activate
```

Todos los scripts se corren **desde la raíz del repositorio**. COMMIT falla si la ruta del proyecto tiene acentos o espacios.

## Datos

Los datos de entrada **no están en el repositorio** y van en `data/` (lista completa en [`data/README.md`](data/README.md)):

| Archivo | Contenido | Origen |
|---|---|---|
| `ISMRM_2023_b3000.{nii.gz,bval,bvec}` | Imagen de difusión (b = 3000 s/mm², 64 direcciones + 1 b0) | Fantoma ISMRM 2015, versión revisada (Renauld *et al.*, 2023) |
| `Parcels_free.nii` | Parcelación en 84 regiones | Mismo conjunto |
| `GT/` | 21 haces del GT (`.tck`) y `all_tracks.tck` | Mismo conjunto |
| `tracks_100k.tck` | Tractograma de trabajo (100 000 hilos, 114 MB) | Generado por este proyecto; ver abajo |

**El tractograma no se regenera.** `tckgen` es aleatorio: correrlo de nuevo produce otros 100 000 hilos, y ningún peso, etiqueta ni resultado coincidiría. Toda reproducción parte del mismo archivo, verificable por MD5:

```
tracks_100k.tck          66ba3e6efe1fadf5b534d3947b2b138f
GT/all_tracks.tck        4cf4a8d5a268e06a7fdeb5aa388cdfdf
```

## Reproducción

Hay dos niveles de reproducción.

### A. Rápida, desde los productos intermedios (minutos, sin MRtrix ni datos de difusión)

El repositorio ya incluye los productos intermedios:

- los cuatro vectores de pesos: `out/pesos_sift2.txt`, `out/commit/pesos_commit.txt`, `out/equipos/life_100k/life_weights.txt` y `out/commit2/pesos_commit2.txt`;
- las longitudes de los hilos: `out/longitudes.txt`;
- la distancia de Hausdorff de cada hilo al GT: `out/hausdorff/hausdorff.csv`;
- la tabla por hilo que usan los modelos: `out/modelos/tabla_hilos.csv`.

Con ellos se rehacen todos los resultados por hilo y de los modelos:

```bash
python scripts/crear_tabla_modelos.py                 # (opcional) regenera out/modelos/tabla_hilos.csv
bash scripts/10_evaluar.sh                            # AUC y precisión de cada método
bash scripts/11_modelo.sh                             # normalización por percentiles y regresión logística
python scripts/modelo_bosque_ajustado.py --longitud   # bosque aleatorio (sin --longitud: variante sin longitud)
python scripts/modelo_boosting_ajustado.py --longitud # gradient boosting
python scripts/modelo_mlp_ajustado.py --longitud      # MLP (requiere PyTorch)
python scripts/puntajes_candidatos.py                 # puntajes de referencia para comparar tractogramas
```

La comparación del tractograma filtrado contra el GT, haz por haz, necesita además `data/GT/` y DIPY. Los comandos están en [`docs/resultados/tractograma_modelo_vs_gt.md`](docs/resultados/tractograma_modelo_vs_gt.md).

### B. Completa, desde los datos de difusión (varias horas)

Con `data/` completo:

| Paso | Script | Qué hace | Tiempo aprox. |
|---|---|---|---|
| 1 | `scripts/01_preprocess.sh` | Gradientes (con el eje *y* invertido), máscara, respuesta y FOD | minutos |
| 2 | `scripts/02_tractography.sh` | Usa el tractograma existente (solo lo genera si falta), longitudes y pesos SIFT2 | minutos |
| 3 | `scripts/03_commit.sh` | Pesos COMMIT | ≈ 1 min |
| 4 | `scripts/04_matrices.sh` | Matrices 84 × 84 y su comparación con el GT | minutos |
| 5 | `scripts/05_life.sh` | Pesos LiFE | — |
| 6 | `scripts/06_commit2.sh` | Pesos COMMIT2 (λ = 10⁻²) | ≈ 1 min |
| 8 | `scripts/08_hausdorff.sh <k> <N>` | Distancia de Hausdorff al GT, en bloques independientes | ≈ 35 min por bloque (N = 7) |
| 8b | `scripts/08_hausdorff.sh unir` | Junta los bloques en `out/hausdorff/hausdorff.csv` | segundos |

Después se continúa con los comandos de la reproducción rápida. Los pasos intermedios (7 y 9) son exploratorios. Cada comando, uno por uno, está en [`pipeline.md`](pipeline.md).

**Cálculo de la etiqueta.** Por fuerza bruta, la distancia de Hausdorff contra los 189 985 hilos del GT tomaría ≈ 22 s por hilo (≈ 25 días en total). `scripts/hausdorff_bloque.py` usa una poda espacial exacta con un árbol KD y baja a ≈ 0.12 s por hilo. `scripts/validar_hausdorff_rapido.py` la compara con la fuerza bruta en 40 hilos al azar. Explicación en [`docs/hausdorff_fragmento_basico.md`](docs/hausdorff_fragmento_basico.md).

### Aleatoriedad

La partición entrenamiento/prueba es 50/50, estratificada por la etiqueta, con semilla 0 (columna `conjunto` de `tabla_hilos.csv`). Los modelos usan `random_state=0`. Cada hilo se puntúa con un modelo entrenado en la otra mitad (intercambio de mitades).

### Números de control

| Verificación | Valor esperado |
|---|---|
| `tckstats data/tracks_100k.tck` | 100 000 hilos, media 92.13 mm, mediana 95.21 mm |
| Pesos en cero | COMMIT 44 780; LiFE 25 388; SIFT2 ninguno; COMMIT2 con 36 928 positivos |
| Conexiones de la matriz del GT | 529 |
| Hilos con Hausdorff < 5 mm | 33 349 (33.3 %) |
| AUC por hilo | SIFT2 0.426 · COMMIT 0.449 · LiFE 0.601 · COMMIT2 0.634 · longitud 0.652 |
| AUC del bosque aleatorio con longitud | 0.799 |

Si se olvida invertir el eje *y* de los gradientes, se nota de inmediato: los hilos miden ≈ 42 mm en promedio y solo ≈ 21 % de las conexiones de la matriz son reales.

## Estructura

```
data/        datos de entrada (no se suben; ver data/README.md)
scripts/     pipeline numerado (01–11) y scripts de apoyo en Python
out/         resultados generados; solo se suben los productos intermedios listados arriba
docs/        documentación técnica: métodos, métricas y resultados detallados (docs/resultados/)
reporte/     reporte en LaTeX (main.tex) y presentación (presentacion/)
```

## Autores

Sarai Hernández, Andrea Martínez, Jaqueline Barajas, Mario Cruz, Maximiliano Vaca, Ricardo Carranza y Pablo Alvarado. CIMAT, Unidad Aguascalientes.

## Referencias principales

- Renauld *et al.* Validate your white matter tractography algorithms with a reappraised ISMRM 2015 Tractography Challenge scoring system. *Scientific Reports* 13:2347, 2023.
- Smith *et al.* SIFT2. *NeuroImage* 119:338–351, 2015.
- Pestilli *et al.* LiFE. *Nature Methods* 11:1058–1063, 2014.
- Daducci *et al.* COMMIT. *IEEE Trans. Med. Imaging* 34(1):246–257, 2015.
- Schiavi *et al.* COMMIT2. *Science Advances* 6(31):eaba8245, 2020.

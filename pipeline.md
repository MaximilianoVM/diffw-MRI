# Pipeline: del DWI a la matriz 84 × 84 ponderada por COMMIT

Todo se corre desde la raíz del proyecto. Las entradas están en `data/` y todo lo generado va a `out/`.
Cada paso es un script (`bash scripts/0N_*.sh`). Abajo están los mismos comandos, uno por uno, para escribirlos a mano.

## Antes de empezar

Entorno, opción A — conda (WSL/Linux; trae MRtrix 3.0.8, Python 3.13, COMMIT 2.4.2 y AMICO 2.1.1):

```bash
conda env create -f environment.yml   # una sola vez
conda activate dwmri                  # en cada terminal nueva
```

Opción B — venv (macOS; MRtrix3 3.0.8 instalado aparte y en el `PATH`, `mrconvert -version`):

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # una sola vez
source .venv/bin/activate                                            # en cada terminal nueva
```

Las dos opciones fijan las mismas versiones de COMMIT, AMICO, numpy, etc. Luego:

```bash
mkdir -p out
```

Entradas en `data/` (ver `data/README.md`): `ISMRM_2023_b3000.{nii.gz,bval,bvec}`, `Parcels_free.nii`, `T1.nii.gz`, `GT/` (21 haces + `all_tracks.tck`).

> **Rutas con acentos o espacios:** COMMIT falla con ellas. Si la ruta del proyecto las tiene, `correr_commit.py` crea el acceso directo `~/Proyecto_2_cerebro` y lo avisa en pantalla. La alternativa es mover el proyecto a una ruta sin acentos ni espacios.

---

## Paso 1. Gradientes, máscara y FOD — `scripts/01_preprocess.sh`

```bash
mrconvert data/ISMRM_2023_b3000.nii.gz out/dwi_original.mif \
  -fslgrad data/ISMRM_2023_b3000.bvec data/ISMRM_2023_b3000.bval
```
Junta la imagen y sus gradientes originales en un solo archivo. → `out/dwi_original.mif`

```bash
mrinfo out/dwi_original.mif -dwgrad | awk '{print $1, -$2, $3, $4}' > out/gradientes_y.b
```
Imprime la tabla de gradientes, le cambia el signo a la columna *y* y la guarda. → `out/gradientes_y.b`

```bash
mrconvert out/dwi_original.mif out/dwi.mif -grad out/gradientes_y.b
```
Crea la DWI con los gradientes corregidos. Desde aquí no se vuelve a usar `-fslgrad`. → `out/dwi.mif`

```bash
dwi2mask out/dwi.mif out/mask.mif
```
Calcula la máscara del cerebro. → `out/mask.mif`

```bash
dwi2response tournier out/dwi.mif out/respuesta.txt -mask out/mask.mif
```
Estima la señal de una sola fibra. → `out/respuesta.txt`

```bash
dwi2fod csd out/dwi.mif out/respuesta.txt out/fod.mif -mask out/mask.mif
```
Calcula la FOD (orientaciones de fibras en cada vóxel) por deconvolución esférica. → `out/fod.mif`

## Paso 2. Tractograma y SIFT2 — `scripts/02_tractography.sh`

```bash
tckgen out/fod.mif out/tracks_100k.tck -algorithm iFOD2 \
  -seed_image out/mask.mif -mask out/mask.mif -select 100000
```
Genera 100 000 hilos sin salir de la máscara. Es aleatorio: para obtener los mismos números, usen el `tracks_100k.tck` compartido y salten este comando (`bash scripts/02_tractography.sh --sin-tckgen`). → `out/tracks_100k.tck`

```bash
tckstats out/tracks_100k.tck -dump out/longitudes.txt
```
Imprime estadísticas de longitud y guarda la longitud de cada hilo en mm. → `out/longitudes.txt`

```bash
tcksift2 out/tracks_100k.tck out/fod.mif out/pesos_sift2.txt
```
Calcula un peso SIFT2 por hilo. → `out/pesos_sift2.txt`

## Paso 3. COMMIT — `scripts/03_commit.sh`

```bash
python scripts/correr_commit.py out/tracks_100k.tck --salida=out/commit
```
Calcula un peso COMMIT por hilo, en el mismo orden que el `.tck` (≈ 75 s en una Mac de 16 GB). → `out/commit/pesos_commit.txt`

Por dentro, el script hace esto:
1. Pasa `dwi.mif` y `mask.mif` a NIfTI.
2. Saca hasta 3 picos por vóxel de la FOD (`sh2peaks`), que necesita el compartimento extra-axonal.
3. Escribe los gradientes ya corregidos en el formato de AMICO.
4. Construye el diccionario con `fiber_shift=0.5`, porque MRtrix pone el centro del vóxel en 0 y COMMIT en 0.5.
5. Ajusta el modelo Stick-Zeppelin-Ball con `d_par=1.7e-3`, `d_perps_zep=[0.51e-3]` y `d_isos=[1.7e-3, 3.0e-3]`.

## Paso 4. Matrices, Excel y evaluación — `scripts/04_matrices.sh`

Los cuatro `tck2connectome` usan `data/Parcels_free.nii` y las opciones `-symmetric -zero_diagonal`.

```bash
tck2connectome data/GT/all_tracks.tck data/Parcels_free.nii out/gt.csv -symmetric -zero_diagonal
```
Calcula el conectoma del ground truth, que sirve de referencia. → `out/gt.csv`

```bash
tck2connectome out/tracks_100k.tck data/Parcels_free.nii out/connectome_commit.csv \
  -tck_weights_in out/commit/pesos_commit.txt -symmetric -zero_diagonal
```
Calcula la matriz sumando los pesos COMMIT de los hilos de cada par de regiones. Es la matriz que se entrega. → `out/connectome_commit.csv`

```bash
tck2connectome out/tracks_100k.tck data/Parcels_free.nii out/connectome_sin_pesos.csv \
  -out_assignments out/asignaciones.txt -symmetric -zero_diagonal
```
Calcula la matriz contando hilos y guarda en qué par de regiones termina cada hilo. → `out/connectome_sin_pesos.csv`, `out/asignaciones.txt`

```bash
tck2connectome out/tracks_100k.tck data/Parcels_free.nii out/connectome_sift2.csv \
  -tck_weights_in out/pesos_sift2.txt -symmetric -zero_diagonal
```
Calcula la matriz ponderada por SIFT2. → `out/connectome_sift2.csv`

```bash
paste -d' ' out/commit/pesos_commit.txt out/longitudes.txt | awk '{print $1*$2}' > out/pesos_commit_x_long.txt
tck2connectome out/tracks_100k.tck data/Parcels_free.nii out/connectome_commit_x_long.csv \
  -tck_weights_in out/pesos_commit_x_long.txt -symmetric -zero_diagonal
```
Multiplica cada peso COMMIT por la longitud de su hilo y calcula la matriz con eso. → `out/connectome_commit_x_long.csv`

```bash
python scripts/exportar_matriz84.py out/connectome_commit.csv out/gt.csv out/matriz_peso_commit_84x84_corregida.xlsx
```
Comprueba que la matriz es 84 × 84, simétrica y con diagonal en cero, imprime su parecido con el GT y la guarda en Excel (R1–R84). El script repite lo mismo para `sin_pesos`, `sift2` y `commit_x_long`. → `out/matriz_*.xlsx`

```bash
python scripts/evaluar_pesos.py COMMIT out/commit/pesos_commit.txt
```
Etiqueta cada hilo contra el GT y mide qué tan bien lo separa COMMIT. → `out/hilos_commit.csv`, `out/evaluacion_commit.txt`

El aviso `nodes are missing from the parcellation image: 15` es esperable: la región 15 no existe en `Parcels_free.nii`, así que su fila y su columna quedan en cero.

---

## Números de control

| Qué | Valor esperado |
|---|---|
| `tckstats out/tracks_100k.tck` | mean 92.13, median 95.21, count 100000 |
| COMMIT: log | `100000 streamlines kept` |
| COMMIT: NRMSE | 0.106 ± 0.039 |
| COMMIT: pesos = 0 | 44 780 (45 %) |
| `out/gt.csv` | 529 conexiones |

| Matriz | Conexiones > 0 | Del GT recuperadas (de 529) | Peso en conexiones del GT | AUC por conexión |
|---|---|---|---|---|
| sin_pesos | 1322 | 460 | 81 % | — |
| sift2 | 1322 | 460 | 75 % | — |
| **commit** | **1203** | **446** | **64 %** | **0.829** |
| commit_x_long | 1203 | 446 | 79 % | 0.846 |

Por hilo, con la etiqueta por extremos de `evaluar_pesos.py`, COMMIT da AUC 0.458, igual que el azar.

Si olvidaron invertir *y*, se nota: hilos de ≈ 42 mm de media y solo ≈ 21 % de conexiones reales en la matriz.

---

## Pendiente

- **LiFE** (DIPY): sin correr.
- **Etiqueta por haz contra el GT,** común a los tres métodos. La de extremos es débil: el 21 % de los hilos del propio GT no termina en ninguna región.
- **Regla de decisión** que combine COMMIT, SIFT2 y LiFE.
- **COMMIT a secas o × longitud:** por decidir.
- **`d_isos`:** `[1.7e-3, 3.0e-3]` (versión anterior: `[2.0e-3]`).
- Hipótesis sin comprobar: peso 0 en COMMIT significaría "redundante", no "falso".

## Bitácora

| Fecha | Qué |
|---|---|
| 2026-11-06 | Datos de los zips organizados en `data/`. |
| 2026-11-10 | Scripts 01–04 y evaluación tomados del otro equipo (corrección del eje y incluida). |
| 2026-11-10 | Pasos 1–4 corridos en macOS con el `tracks_100k.tck` compartido: COMMIT en 1 min 15 s, 44 780 pesos en 0, AUC 0.829 por conexión. Coincide con los números de control. |
| 2026-11-13 | Fusión con el repo `MaximilianoVM/diffw-MRI`: conda (`environment.yml`) y venv (`requirements.txt`) documentados como alternativas. |

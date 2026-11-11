# Pipeline: del DWI a la matriz de peso 84 × 84 (COMMIT)

Todo se corre desde la raíz del proyecto. Entrada en `data/`, todo lo generado en `out/`.
Cada paso tiene un script que junta sus comandos (`bash scripts/0N_*.sh`). Abajo está cada comando explicado, para que puedas escribirlo a mano.

Archivos de entrada (en `data/`): `ISMRM_2023_b3000.{nii.gz,bval,bvec}`, `Parcels_free.nii`, `T1.nii.gz`, `GT/` (21 haces + `all_tracks.tck`).

Entorno (una sola vez):

```bash
conda env create -f environment.yml
conda activate dwmri
```
Trae MRtrix 3.0.8, Python 3.13, COMMIT 2.4.2 y AMICO 2.1.1 (las mismas versiones del otro equipo).

| Paso | Script | Sale |
|---|---|---|
| 1. Preprocesamiento | `scripts/01_preprocess.sh` | `out/dwi.mif`, `mask.mif`, `fod.mif` |
| 2. Tractograma y SIFT2 | `scripts/02_tractography.sh` | `out/tracks_100k.tck`, `pesos_sift2.txt` |
| 3. COMMIT | `scripts/03_commit.sh` | `out/commit/pesos_commit.txt` |
| 4. Matrices 84 × 84 | `scripts/04_matrices.sh` | `out/matriz_peso_commit_84x84_corregida.xlsx` |

---

## 1. Preprocesamiento (MRtrix)

```bash
mkdir -p out
```
Crea la carpeta `out/`.

**1.1 Juntar la imagen con sus gradientes**
```bash
mrconvert data/ISMRM_2023_b3000.nii.gz out/dwi_original.mif \
  -fslgrad data/ISMRM_2023_b3000.bvec data/ISMRM_2023_b3000.bval
```
Convierte la imagen al formato `.mif` de MRtrix y le mete adentro las direcciones (`.bvec`) y los valores b (`.bval`).

**1.2 Invertir el eje y de los gradientes (corrección importante)**
```bash
mrinfo out/dwi_original.mif -dwgrad | awk '{print $1, -$2, $3, $4}' > out/gradientes_y.b
mrconvert out/dwi_original.mif out/dwi.mif -grad out/gradientes_y.b
```
El `.bvec` viene con el eje `y` al revés respecto a lo que espera MRtrix. Si no se corrige, los hilos salen cortados (≈ 42 mm de media en vez de ≈ 92 mm).
- `mrinfo -dwgrad` imprime la tabla de gradientes (4 columnas: x, y, z, b).
- `awk '{print $1, -$2, $3, $4}'` le cambia el signo a la segunda columna (y).
- `mrconvert -grad` vuelve a guardar la imagen con esa tabla corregida: `out/dwi.mif`.

**A partir de aquí no se usa más `-fslgrad`.** Siempre `out/dwi.mif`, que ya lleva los gradientes corregidos.

Cómo se comprobó que hacía falta (opcional): `dwigradcheck out/dwi_original.mif -mask out/mask.mif`.

**1.3 Máscara del cerebro**
```bash
dwi2mask out/dwi.mif out/mask.mif
```
Marca qué vóxeles son cerebro (1) y cuáles aire (0).

**1.4 Función de respuesta**
```bash
dwi2response tournier out/dwi.mif out/respuesta.txt -mask out/mask.mif
```
Estima cómo se ve la señal de **una sola fibra**.

**1.5 FOD (hacia dónde apuntan las fibras en cada vóxel)**
```bash
dwi2fod csd out/dwi.mif out/respuesta.txt out/fod.mif -mask out/mask.mif
```
Con la señal de una fibra, separa las fibras de cada vóxel. Es lo que usa el tractograma.

Revisar: `mrview out/mask.mif -odf.load_sh out/fod.mif` (los lóbulos deben seguir la materia blanca).

### Revisar el `.bvec` (opcional)
3 filas (x, y, z) × 65 columnas. Cada columna debe medir 1; la del b0 mide 0.
```bash
awk '{for(i=1;i<=NF;i++) v[NR,i]=$i; n=NF}
     END{for(i=1;i<=n;i++){s=sqrt(v[1,i]^2+v[2,i]^2+v[3,i]^2); if(i==1||s<m)m=s; if(i==1||s>M)M=s}
         print "norma mínima",m,"máxima",M}' data/ISMRM_2023_b3000.bvec
```
Debe dar mínima ≈ 0 y máxima ≈ 1.

---

## 2. Tractograma y SIFT2 (MRtrix)

**2.1 Tractograma de 100 000 hilos**
```bash
tckgen out/fod.mif out/tracks_100k.tck -algorithm iFOD2 \
  -seed_image out/mask.mif -mask out/mask.mif -select 100000
tckstats out/tracks_100k.tck
```
- `tckgen -algorithm iFOD2` genera hilos siguiendo la FOD (método probabilístico).
- `-seed_image`: los hilos empiezan en puntos al azar del cerebro. `-mask`: no pueden salir del cerebro.
- `-select 100000`: se detiene al tener 100 000 hilos.
- `tckstats` muestra el resumen. Se espera media ≈ 92 mm y `count 100000`.

`tckgen` es aleatorio: cada corrida da un tractograma distinto. Para tener los mismos números que el otro equipo, usen su `tracks_100k.tck` (109 MB, por Drive) y corran `bash scripts/02_tractography.sh --sin-tckgen`.

**2.2 Longitud de cada hilo**
```bash
tckstats out/tracks_100k.tck -dump out/longitudes.txt
```
Guarda la longitud en mm de cada hilo, una por línea (se usa después).

**2.3 SIFT2 (para comparar)**
```bash
tcksift2 out/tracks_100k.tck out/fod.mif out/pesos_sift2.txt
```
Da un peso a cada hilo según qué tanto aporta a la FOD.

---

## 3. COMMIT (Python)

```bash
python scripts/correr_commit.py out/tracks_100k.tck --salida=out/commit
```
Tarda ≈ 75 s y usa unos pocos GB de RAM. Hace lo siguiente:
1. Convierte `dwi.mif` y `mask.mif` a NIfTI (el formato que lee COMMIT).
2. Saca hasta 3 picos de fibra por vóxel con `sh2peaks` (los pide el modelo para el agua alrededor de los axones).
3. Escribe los gradientes desde `dwi.mif`, o sea ya con `y` corregido.
4. Construye el diccionario (qué vóxeles cruza cada hilo) con `trk2dictionary`, usando `fiber_shift=0.5`: MRtrix pone el centro del vóxel en 0 y COMMIT en 0.5.
5. Ajusta el modelo Stick-Zeppelin-Ball. Stick = agua dentro del axón; Zeppelin = agua alrededor; Ball = agua libre.
6. Guarda un peso por hilo en `out/commit/pesos_commit.txt`, en el mismo orden que el `.tck`.

Se espera: NRMSE 0.106 ± 0.039 y 44 780 pesos en 0 (45 %).

Cuidado: COMMIT falla si la ruta del proyecto tiene acentos o espacios.
Si da `Killed` es falta de RAM: usa un subconjunto (`tckedit out/tracks_100k.tck -number 20000 out/tracks_20k.tck`) y corre todos los métodos sobre ese mismo archivo.

---

## 4. Matrices 84 × 84 (MRtrix + Python)

```bash
bash scripts/04_matrices.sh
```

Lo que hace, comando por comando:

```bash
# conectoma del ground truth: qué pares de regiones están realmente conectados (529)
tck2connectome data/GT/all_tracks.tck data/Parcels_free.nii out/gt.csv -symmetric -zero_diagonal

# la matriz que se entrega: cada hilo cuenta con su peso de COMMIT
tck2connectome out/tracks_100k.tck data/Parcels_free.nii out/connectome_commit.csv \
  -tck_weights_in out/commit/pesos_commit.txt -symmetric -zero_diagonal
```
`tck2connectome` cuenta cuántos hilos unen cada par de las 84 regiones de `Parcels_free.nii`. `-tck_weights_in` hace que cada hilo valga su peso en vez de 1. `-symmetric` llena la matriz por los dos lados y `-zero_diagonal` pone 0 en la diagonal.

El aviso `nodes are missing from the parcellation image: 15` es normal: la región 15 no existe en la imagen, su fila y columna quedan en 0.

Además el script saca matrices para comparar (sin pesos, SIFT2 y COMMIT × longitud) y las exporta a Excel:
```bash
python scripts/exportar_matriz84.py out/connectome_commit.csv out/gt.csv out/matriz_peso_commit_84x84_corregida.xlsx
```
Comprueba que la matriz es 84 × 84, simétrica y con diagonal 0, imprime cuánto se parece al GT y guarda el `.xlsx` (filas y columnas R1–R84).

Por último evalúa los pesos de COMMIT contra el GT, hilo por hilo:
```bash
python scripts/evaluar_pesos.py COMMIT out/commit/pesos_commit.txt
```

### Resultados esperados (con el `tracks_100k.tck` del otro equipo)

| Matriz | Conexiones > 0 | GT recuperadas (de 529) | Peso en conexiones del GT |
|---|---|---|---|
| sin pesos | 1322 | 460 | 81 % |
| SIFT2 | 1322 | 460 | 75 % |
| **COMMIT** (entregada) | **1203** | **446** | **64 %** |
| COMMIT × longitud | 1203 | 446 | 79 % |

- COMMIT da un peso por unidad de longitud, así que la matriz "a secas" favorece las conexiones cortas. Multiplicar por la longitud sube el peso en conexiones reales de 64 % a 79 %.
- Con un `.tck` propio estos números cambian un poco.

---

## Pendiente

- **LiFE** (DIPY): no se ha corrido.
- **Etiqueta por hilo contra el GT.** `evaluar_pesos.py` usa una aproximación por extremos y es débil (AUC 0.46 por hilo, 0.83 por conexión). Hace falta una etiqueta por haz, la misma para los tres métodos.
- **Regla de decisión** que combine COMMIT, SIFT2 y LiFE: sin empezar.
- **Decidir:** COMMIT a secas o × longitud, y `d_isos=[1.7e-3, 3.0e-3]` (versión anterior: `[2.0e-3]`).
- Hipótesis sin comprobar: peso 0 en COMMIT significaría "redundante", no "falso".

## Bitácora

| Fecha | Qué |
|---|---|
| 2026-11-06 | Datos de los zips organizados en `data/`. |
| 2026-11-10 | Scripts 01–04 y evaluación tomados del otro equipo (corrección del eje y incluida). Sin correr todavía en este repo. |

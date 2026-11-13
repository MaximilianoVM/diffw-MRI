#!/usr/bin/env bash
# Paso 5: pesos de LiFE (DIPY), su matriz 84 x 84, evaluación y comparación de los tres métodos.
# Uso (desde la raíz del proyecto, después de 01-04):  bash scripts/05_life.sh
# Memoria: con los 100 000 hilos de data/tracks_100k.tck, LiFE pide ~20 GB (en una Mac de 16 GB no cabe).
# Si el equipo de LiFE ya lo corrió con su script sobre data/tracks_100k.tck, pongan su
# life_weights.txt como out/life/pesos_life.txt y este paso se salta el ajuste.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python}
[ -x .venv/bin/python ] && PY=.venv/bin/python
T=data/tracks_100k.tck
P=data/Parcels_free.nii
opc="-symmetric -zero_diagonal -force"

# data/ISMRM_2023_b3000.{nii.gz,bval,bvec} + data/tracks_100k.tck -> out/life/pesos_life.txt
if [ ! -s out/life/pesos_life.txt ]; then
  $PY scripts/correr_life.py $T 2>&1 | tee out/life_log.txt
fi
n=$(grep -cv '^#' out/life/pesos_life.txt)
[ "$n" -eq 100000 ] || { echo "ERROR: out/life/pesos_life.txt tiene $n pesos; deben ser 100000 (uno por hilo de $T)"; exit 1; }

# tractograma + pesos LiFE -> out/connectome_life.csv
tck2connectome $T $P out/connectome_life.csv -tck_weights_in out/life/pesos_life.txt $opc

# pesos LiFE x longitud -> out/connectome_life_x_long.csv
paste -d' ' out/life/pesos_life.txt out/longitudes.txt | awk '{print $1*$2}' > out/pesos_life_x_long.txt
tck2connectome $T $P out/connectome_life_x_long.csv -tck_weights_in out/pesos_life_x_long.txt $opc

# .csv -> .xlsx (mismo formato que la de COMMIT: R1-R84)
$PY scripts/exportar_matriz84.py out/connectome_life.csv out/gt.csv out/matriz_peso_life_84x84.xlsx

# evaluación hilo por hilo de LiFE y SIFT2 (COMMIT ya se evaluó en el paso 4)
$PY scripts/evaluar_pesos.py LiFE out/life/pesos_life.txt | tee out/evaluacion_life.txt
$PY scripts/evaluar_pesos.py SIFT2 out/pesos_sift2.txt | tee out/evaluacion_sift2.txt

# las matrices de los tres métodos lado a lado -> out/comparacion_matrices.csv
$PY scripts/comparar_matrices.py

# los pesos de los tres métodos entre sí, hilo por hilo -> out/comparacion_pesos.txt, out/pesos_por_hilo.csv
$PY scripts/comparar_pesos.py | tee out/comparacion_pesos.txt

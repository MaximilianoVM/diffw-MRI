#!/usr/bin/env bash
# Paso 4: conectoma del GT, matrices 84 x 84, Excel y evaluación de COMMIT.
# Uso (desde la raíz del proyecto):  bash scripts/04_matrices.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python}
[ -x .venv/bin/python ] && PY=.venv/bin/python
T=data/tracks_100k.tck
P=data/Parcels_free.nii
opc="-symmetric -zero_diagonal -force"

# data/GT/all_tracks.tck + parcelación -> out/gt.csv
tck2connectome data/GT/all_tracks.tck $P out/gt.csv $opc

# tractograma + pesos COMMIT -> out/connectome_commit.csv (la que se entrega)
tck2connectome $T $P out/connectome_commit.csv -tck_weights_in out/commit/pesos_commit.txt $opc

# tractograma -> out/connectome_sin_pesos.csv (cuenta de hilos); + región de cada hilo -> out/asignaciones.txt
tck2connectome $T $P out/connectome_sin_pesos.csv -out_assignments out/asignaciones.txt $opc

# tractograma + pesos SIFT2 -> out/connectome_sift2.csv
tck2connectome $T $P out/connectome_sift2.csv -tck_weights_in out/pesos_sift2.txt $opc

# pesos COMMIT x longitud -> out/pesos_commit_x_long.txt -> out/connectome_commit_x_long.csv
paste -d' ' out/commit/pesos_commit.txt out/longitudes.txt | awk '{print $1*$2}' > out/pesos_commit_x_long.txt
tck2connectome $T $P out/connectome_commit_x_long.csv -tck_weights_in out/pesos_commit_x_long.txt $opc

# .csv + out/gt.csv -> .xlsx (verifica 84 x 84, simetría, diagonal; imprime el parecido con el GT)
$PY scripts/exportar_matriz84.py out/connectome_commit.csv out/gt.csv out/matriz_peso_commit_84x84_corregida.xlsx
for f in sin_pesos sift2 commit_x_long; do
  $PY scripts/exportar_matriz84.py out/connectome_$f.csv out/gt.csv out/matriz_$f.xlsx
done

# pesos + asignaciones + longitudes + gt -> out/hilos_commit.csv, out/evaluacion_commit.txt
$PY scripts/evaluar_pesos.py COMMIT out/commit/pesos_commit.txt | tee out/evaluacion_commit.txt

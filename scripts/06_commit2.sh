#!/usr/bin/env bash
# Paso 6: matriz 84 x 84 y evaluación de COMMIT2 (variante de COMMIT, lambda = 1e-2).
# Uso (desde la raíz del proyecto, después de 02 y 04):  bash scripts/06_commit2.sh
# Si no existe out/commit2/pesos_commit2.txt, lo calcula con scripts/correr_commit2.py (necesita el paso 3 hecho
# y la máquina grande). Si ya hay pesos (por ejemplo commit2_lam1e-2_weights.txt de otra corrida), los usa tal cual.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python}
[ -x .venv/bin/python ] && PY=.venv/bin/python
T=data/tracks_100k.tck
P=data/Parcels_free.nii
W=out/commit2/pesos_commit2.txt
opc="-symmetric -zero_diagonal -force"

# out/commit/ + data/tracks_100k.tck -> out/commit2/pesos_commit2.txt
[ -s "$W" ] || $PY scripts/correr_commit2.py 2>&1 | tee out/commit2_log.txt
echo "md5 del tractograma (debe ser 66ba3e6efe1fadf5b534d3947b2b138f): $(md5sum $T | cut -d' ' -f1)"
$PY - <<'PY'
import numpy as np
w = np.loadtxt("out/commit2/pesos_commit2.txt", comments="#").ravel()
print("pesos", w.size, "| negativos", (w < 0).sum(), "| NaN", np.isnan(w).sum(), "| >0:", (w > 0).sum(), "| =0:", (w == 0).sum())
assert w.size == 100000 and (w >= 0).all() and not np.isnan(w).any(), "no cumple el contrato: 100 000 pesos >= 0, sin NaN"
PY

# tractograma + pesos COMMIT2 -> out/connectome_commit2.csv (84 x 84, simétrica, diagonal 0)
tck2connectome $T $P out/connectome_commit2.csv -tck_weights_in $W $opc

# .csv + out/gt.csv -> .xlsx
$PY scripts/exportar_matriz84.py out/connectome_commit2.csv out/gt.csv out/matriz_commit2.xlsx

# evaluación hilo por hilo y por conexión -> out/evaluacion_commit2.txt
$PY scripts/evaluar_pesos.py COMMIT2 $W | tee out/evaluacion_commit2.txt

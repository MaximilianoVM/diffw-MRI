#!/usr/bin/env bash
# Barrido de lambda en COMMIT2: pesos, matriz 84 x 84, evaluación y normalización Ricardo con cada lambda.
# Uso (desde la raíz del proyecto, después de 03 y 04):  bash scripts/barrido_lambda_commit2.sh 5e-3 1e-3
# Cada lambda queda en out/commit2_lam<λ>/ y out/normalizacion/umbrales_lam<λ>/ (no pisa out/commit2/).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python}
[ -x .venv/bin/python ] && PY=.venv/bin/python
T=data/tracks_100k.tck
P=data/Parcels_free.nii

for lam in "$@"; do
  D=out/commit2_lam$lam
  echo "################ lambda = $lam -> $D"
  # 1) pesos
  [ -s $D/pesos_commit2.txt ] || $PY scripts/correr_commit2.py --lambda=$lam --salida=$D > $D.log 2>&1
  tail -2 $D.log
  # 2) matriz 84 x 84 + Excel
  tck2connectome $T $P $D/connectome_commit2.csv -tck_weights_in $D/pesos_commit2.txt -symmetric -zero_diagonal -force -quiet
  $PY scripts/exportar_matriz84.py $D/connectome_commit2.csv out/gt.csv $D/matriz_commit2.xlsx
  # 3) evaluación hilo por hilo (etiqueta por extremos) y por conexión
  $PY scripts/evaluar_pesos.py COMMIT2_lam$lam $D/pesos_commit2.txt > $D/evaluacion.txt
  grep -E "peso = 0|AUC \(peso como|\[peso\]" $D/evaluacion.txt
  # 4) normalización Ricardo con COMMIT + SIFT2 + COMMIT2(lambda), umbrales 0.1-0.5, contra el GT por haz
  $PY scripts/normalizacion_ricardo.py \
    --pesos COMMIT=out/commit/pesos_commit.txt SIFT2=out/pesos_sift2.txt COMMIT2=$D/pesos_commit2.txt \
    --umbrales 0.1 0.2 0.3 0.4 0.5 --salida out/normalizacion/umbrales_lam$lam > $D/normalizacion.txt 2>&1
  grep -E "hilo por hilo|MÁS SE ACERCA" $D/normalizacion.txt
done

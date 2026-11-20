#!/usr/bin/env bash
# Paso 11: normalización de Ricardo y modelo (regresión logística), evaluados contra la etiqueta de Hausdorff.
# Uso: bash scripts/11_modelo.sh [E_mm=5]       Resultados: docs/resultados/modelo_y_normalizacion_hausdorff.md
# Repite con 3 y 7 mm para ver si las conclusiones cambian con ε.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python3}; [ -x .venv/bin/python ] && PY=.venv/bin/python
[ -f out/hausdorff/hausdorff.csv ] || { echo "ERROR: falta out/hausdorff/hausdorff.csv (paso 8)"; exit 1; }
E=${1:-5}
mkdir -p out/evaluacion out/modelo
# 3.1: cada normalización y combinación -> out/evaluacion/normalizacion_hausdorff_E<E>.csv, auc_normalizacion_por_eps.csv
$PY scripts/evaluar_normalizacion_hausdorff.py "$E" 3 7 | tee out/evaluacion/normalizacion_hausdorff_log.txt
# 3.2: regresión logística 50/50 -> out/modelo/resultados_E<E>.csv, coeficientes_E<E>.csv, auc_por_eps.csv
$PY scripts/modelo.py "$E" 3 7 | tee out/modelo/log.txt

#!/usr/bin/env bash
# Paso 10: evalúa cada método filtrado contra la etiqueta de Hausdorff (out/hausdorff/hausdorff.csv).
# Uso: bash scripts/10_evaluar.sh [E_mm=5]      Documentación: docs/evaluacion_filtrado.md
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python3}; [ -x .venv/bin/python ] && PY=.venv/bin/python
[ -f out/hausdorff/hausdorff.csv ] || { echo "ERROR: falta out/hausdorff/hausdorff.csv (corre: bash scripts/08_hausdorff.sh unir)"; exit 1; }
$PY scripts/evaluar_filtrado.py "${1:-5}"

#!/usr/bin/env bash
# Paso 9: normaliza el vector de pesos de un método a (0,1) (entre su máximo) y lo filtra con epsilon.
# Uso: bash scripts/09_filtrar_pesos.sh <pesos.txt> <metodo> [epsilon=0.1] [carpeta_salida=out/filtrado]
# Ej.: bash scripts/09_filtrar_pesos.sh out/pesos_sift2.txt sift2 0.1
# Documentación: docs/filtrado_pesos.md
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python3}; [ -x .venv/bin/python ] && PY=.venv/bin/python
[ $# -ge 2 ] || { sed -n 2,5p "$0"; exit 1; }
[ -f "$1" ] || { echo "ERROR: no existe $1"; exit 1; }
$PY scripts/filtrar_pesos.py "$1" "$2" "${3:-0.1}" "${4:-out/filtrado}"

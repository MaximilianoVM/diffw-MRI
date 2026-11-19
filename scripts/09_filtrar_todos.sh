#!/usr/bin/env bash
# Corre el paso 9 sobre los métodos cuyo vector de pesos exista en esta computadora.
# Uso: bash scripts/09_filtrar_todos.sh [epsilon=0.1]
set -uo pipefail
cd "$(dirname "$0")/.."
E=${1:-0.1}
for par in sift2:out/pesos_sift2.txt commit:out/commit/pesos_commit.txt life:out/equipos/life_100k/life_weights.txt commit2:out/commit2/pesos_commit2.txt; do
  m=${par%%:*}; f=${par#*:}
  if [ -f "$f" ]; then bash scripts/09_filtrar_pesos.sh "$f" "$m" "$E"; else echo "(omitido $m: no existe $f)"; fi
done

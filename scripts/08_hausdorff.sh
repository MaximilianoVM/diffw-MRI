#!/usr/bin/env bash
# Paso 8: etiqueta por Hausdorff (distancia de cada hilo al ground truth), repartida en bloques.
# Uso (desde la raíz del proyecto, con el entorno activado):
#   bash scripts/08_hausdorff.sh 3 7      # esta computadora hace el bloque 3 de 7 (hilos 28 572-42 857)
#   bash scripts/08_hausdorff.sh unir     # junta los bloques -> out/hausdorff/hausdorff.csv (en la máquina central)
# Instrucciones completas: docs/hausdorff_instrucciones.md
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python}
[ -x .venv/bin/python ] && PY=.venv/bin/python

if [ "${1:-}" = "unir" ]; then
  $PY scripts/hausdorff_bloque.py --unir
  exit 0
fi
[ $# -eq 2 ] || { echo "Uso: bash scripts/08_hausdorff.sh <bloque> <n_bloques>   (ej. 3 7)   o   bash scripts/08_hausdorff.sh unir"; exit 1; }

# el tractograma debe ser el oficial: si no, los índices de los hilos no coinciden entre computadoras
esperado=66ba3e6efe1fadf5b534d3947b2b138f
real=$( (md5sum data/tracks_100k.tck 2>/dev/null || md5 -r data/tracks_100k.tck) | cut -d' ' -f1)
[ "$real" = "$esperado" ] || { echo "ERROR: data/tracks_100k.tck tiene md5 $real; debe ser $esperado"; exit 1; }
[ -s data/GT/all_tracks.tck ] || { echo "ERROR: falta data/GT/all_tracks.tck"; exit 1; }

# data/tracks_100k.tck + data/GT/all_tracks.tck -> out/hausdorff/bloque_<k>_de_<N>.csv
$PY scripts/hausdorff_bloque.py "$1" "$2"

#!/usr/bin/env bash
# Paso 2: tractograma de 100 000 hilos y pesos SIFT2.
# Uso (desde la raíz del proyecto):  bash scripts/02_tractography.sh
# tckgen es aleatorio: para reproducir los números exactos, usa el tracks_100k.tck compartido
# y salta el tckgen (bash scripts/02_tractography.sh --sin-tckgen).
set -euo pipefail
cd "$(dirname "$0")/.."

if [ "${1:-}" != "--sin-tckgen" ]; then
  # out/fod.mif + out/mask.mif -> out/tracks_100k.tck
  tckgen -force out/fod.mif out/tracks_100k.tck -algorithm iFOD2 \
    -seed_image out/mask.mif -mask out/mask.mif -select 100000
fi
tckstats out/tracks_100k.tck

# out/tracks_100k.tck -> out/longitudes.txt (mm, una por hilo)
tckstats -force out/tracks_100k.tck -dump out/longitudes.txt > /dev/null

# out/tracks_100k.tck + out/fod.mif -> out/pesos_sift2.txt
tcksift2 -force out/tracks_100k.tck out/fod.mif out/pesos_sift2.txt

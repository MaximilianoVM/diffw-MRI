#!/usr/bin/env bash
# Paso 2: tractograma de 100 000 hilos y pesos SIFT2.
# Uso (desde la raíz del proyecto):  bash scripts/02_tractography.sh
# El tractograma oficial es data/tracks_100k.tck (compartido, no se regenera).
# Solo se genera uno nuevo si ese archivo NO existe. tckgen es aleatorio: los números cambian.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -e data/tracks_100k.tck ]; then
  # out/fod.mif + out/mask.mif -> data/tracks_100k.tck
  tckgen out/fod.mif data/tracks_100k.tck -algorithm iFOD2 \
    -seed_image out/mask.mif -mask out/mask.mif -select 100000
fi
tckstats data/tracks_100k.tck

# data/tracks_100k.tck -> out/longitudes.txt (mm, una por hilo)
tckstats -force data/tracks_100k.tck -dump out/longitudes.txt > /dev/null

# data/tracks_100k.tck + out/fod.mif -> out/pesos_sift2.txt (+ mu)
tcksift2 -force data/tracks_100k.tck out/fod.mif out/pesos_sift2.txt -out_mu out/mu_sift2.txt

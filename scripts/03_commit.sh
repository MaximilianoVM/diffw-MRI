#!/usr/bin/env bash
# Paso 3: pesos de COMMIT (un valor por hilo).
# Uso (desde la raíz del proyecto, con el Python que tiene COMMIT):  bash scripts/03_commit.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python}
[ -x .venv/bin/python ] && PY=.venv/bin/python

# out/dwi.mif + out/mask.mif + out/fod.mif + data/tracks_100k.tck -> out/commit/pesos_commit.txt
$PY scripts/correr_commit.py data/tracks_100k.tck --salida=out/commit 2>&1 | tee out/commit_log.txt

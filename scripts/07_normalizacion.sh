#!/usr/bin/env bash
# Paso 7: normalización Ricardo (rango percentil), combinación de métodos y evaluación por haz contra el GT.
# Uso (desde la raíz del proyecto, después de 02-04):  bash scripts/07_normalizacion.sh
# Usa COMMIT + SIFT2, y COMMIT2 y LiFE si existen sus pesos (out/commit2/pesos_commit2.txt, out/life/pesos_life.txt).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python}
[ -x .venv/bin/python ] && PY=.venv/bin/python

# test obligatorio del ejemplo de docs/Normalizacion Ricardo.md (sección 4)
$PY scripts/test_normalizacion.py

pesos="COMMIT=out/commit/pesos_commit.txt SIFT2=out/pesos_sift2.txt"
[ -s out/commit2/pesos_commit2.txt ] && pesos="$pesos COMMIT2=out/commit2/pesos_commit2.txt"
[ -s out/life/pesos_life.txt ] && pesos="$pesos LiFE=out/life/pesos_life.txt"

# pesos + data/tracks_100k.tck + data/GT/*.tck -> out/normalizacion/umbrales/
# una versión del tractograma por umbral (eliminar promedio < u), cada una contra el GT con todas las métricas
$PY scripts/normalizacion_ricardo.py --pesos $pesos --umbrales 0.1 0.2 0.3 0.4 0.5 \
  --salida out/normalizacion/umbrales | tee out/normalizacion_log.txt

# lo mismo con el percentil por rango de longitud (deciles) -> out/normalizacion/umbrales_longitud/
$PY scripts/normalizacion_ricardo.py --pesos $pesos --umbrales 0.1 0.2 0.3 0.4 0.5 --por-longitud 10 \
  --salida out/normalizacion/umbrales_longitud | tee out/normalizacion_longitud_log.txt

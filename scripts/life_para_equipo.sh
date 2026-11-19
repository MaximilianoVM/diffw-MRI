#!/usr/bin/env bash
# =============================================================================
# LiFE sobre el tractograma oficial tracks_100k.tck  ->  lo que necesita el equipo de COMMIT
#
# Es el mismo método de docs/equipos/life_metodo.md (DIPY: FiberModel(gtab).fit(data, hilos, inv(affine)),
# .bvec original). Lo único que cambia es el tractograma: tracks_100k.tck en vez de tracks.tck.
#
# Uso:
#   bash life_para_equipo.sh --prueba    # 1-2 min: revisa archivos y entornos, LiFE con 2 000 hilos
#   bash life_para_equipo.sh             # corrida completa (100 000 hilos, ~20 GB de RAM+swap)
#
# Ajusten estas rutas si sus archivos están en otro lado:
# =============================================================================
BASE="${BASE:-$HOME/desafio/datos/dataset/DWIs}"
TCK="${TCK:-$BASE/tracks_100k.tck}"                  # el que les compartimos por Drive
DWI="${DWI:-$BASE/ISMRM_2023_b3000.nii.gz}"
BVAL="${BVAL:-$BASE/ISMRM_2023_b3000.bval}"
BVEC="${BVEC:-$BASE/ISMRM_2023_b3000.bvec}"           # el .bvec ORIGINAL (DIPY lo lee bien así)
PARC="${PARC:-$BASE/../Parcels_free.nii}"
ENV_MRTRIX="${ENV_MRTRIX:-dmri}"                      # entorno conda con tck2connectome
ENV_PY="${ENV_PY:-pydmri}"                            # entorno conda con DIPY
SALIDA="${SALIDA:-$HOME/desafio/entrega_life_100k}"
# =============================================================================

set -euo pipefail
MD5_OFICIAL="66ba3e6efe1fadf5b534d3947b2b138f"
RAM_NECESARIA_GB=22
PRUEBA=0; [ "${1:-}" = "--prueba" ] && PRUEBA=1

ok()    { echo "  [OK]    $*"; }
falla() { echo "  [ERROR] $*"; echo; echo "Detenido. Manden este mensaje al equipo de COMMIT si no saben cómo resolverlo."; exit 1; }
paso()  { echo; echo "== $*"; }

activar() {  # activa un entorno conda si conda existe; si no, usa lo que haya en el PATH
  if command -v conda >/dev/null 2>&1; then
    # shellcheck disable=SC1091
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate "$1" || falla "no existe el entorno conda '$1' (ajusten ENV_MRTRIX / ENV_PY arriba)"
  fi
}

mkdir -p "$SALIDA"
RES="$SALIDA/resumen.txt"
exec > >(tee "$SALIDA/log_completo.txt") 2>&1
echo "LiFE sobre tracks_100k.tck — $(date)  —  modo: $([ $PRUEBA = 1 ] && echo PRUEBA || echo COMPLETO)"

# ---------------------------------------------------------------------------
paso "1. Archivos de entrada"
for f in "$TCK" "$DWI" "$BVAL" "$BVEC" "$PARC"; do
  [ -s "$f" ] && ok "$f" || falla "no encuentro $f"
done

md5=$(md5sum "$TCK" | cut -d' ' -f1)
[ "$md5" = "$MD5_OFICIAL" ] && ok "md5 de tracks_100k.tck = $md5 (es el oficial)" \
  || falla "md5 de $TCK = $md5, debe ser $MD5_OFICIAL. No es el tractograma oficial: bájenlo otra vez del Drive"

# ---------------------------------------------------------------------------
paso "2. MRtrix (entorno $ENV_MRTRIX)"
activar "$ENV_MRTRIX"
command -v tck2connectome >/dev/null || falla "no encuentro tck2connectome en el entorno $ENV_MRTRIX"
media=$(tckstats "$TCK" -output mean -quiet | tr -d ' \t\r')
cuenta=$(tckstats "$TCK" -output count -quiet | tr -d ' \t\r')
echo "  tckstats: count $cuenta, media $media mm"
[ "$cuenta" = "100000" ] || falla "el tractograma tiene $cuenta hilos, deben ser 100000"
awk -v m="$media" 'BEGIN{exit !(m > 91.5 && m < 92.8)}' && ok "media ≈ 92.13 mm (eje y bien)" \
  || falla "la media es $media mm, debe ser ≈ 92.13"

# ---------------------------------------------------------------------------
paso "3. Memoria"
disp_kb=$(awk '/MemAvailable/{a=$2} /SwapFree/{s=$2} END{print a+s}' /proc/meminfo 2>/dev/null || echo 0)
[ -n "$disp_kb" ] || disp_kb=0
disp_gb=$((disp_kb / 1024 / 1024))
echo "  RAM disponible + swap libre: ${disp_gb} GB (la corrida completa pide ~${RAM_NECESARIA_GB} GB)"
if [ $PRUEBA = 0 ] && [ "$disp_gb" -lt "$RAM_NECESARIA_GB" ] && [ "${FORZAR:-0}" != 1 ]; then
  falla "no alcanza la memoria. Suban la memoria/swap de WSL (ver docs/equipos/instrucciones_life.md, sección 'Memoria') o corran con FORZAR=1 bajo su riesgo"
fi
ok "memoria suficiente (o modo prueba)"

# ---------------------------------------------------------------------------
paso "4. LiFE con DIPY (entorno $ENV_PY)"
activar "$ENV_PY"
python -c "import dipy, nibabel, numpy; print('  DIPY', dipy.__version__, '| nibabel', nibabel.__version__, '| numpy', numpy.__version__)" \
  || falla "falta DIPY/nibabel/numpy en el entorno $ENV_PY"

N_HILOS=$([ $PRUEBA = 1 ] && echo 2000 || echo 0)
PESOS="$SALIDA/life_weights.txt"; [ $PRUEBA = 1 ] && PESOS="$SALIDA/prueba_life_weights_2000.txt"
rm -f "$PESOS"
TIEMPO=""; /usr/bin/time -v true >/dev/null 2>&1 && TIEMPO="/usr/bin/time -v"

DWI="$DWI" BVAL="$BVAL" BVEC="$BVEC" TCK="$TCK" PESOS="$PESOS" N_HILOS="$N_HILOS" \
$TIEMPO python - <<'PY' 2>&1 | grep -v -E "^\s+(Page size|Socket|Signals|Swaps|File system|Average|Exit status|Voluntary|Involuntary|Minor|Major|Percent|Command being)" || true
import os, time
import numpy as np
import nibabel as nib
from nibabel.streamlines import load as load_tck
from dipy.io.gradients import read_bvals_bvecs
from dipy.core.gradients import gradient_table
from dipy.tracking.life import FiberModel

img  = nib.load(os.environ["DWI"])
data = img.get_fdata(dtype=np.float32)
bvals, bvecs = read_bvals_bvecs(os.environ["BVAL"], os.environ["BVEC"])
gtab = gradient_table(bvals, bvecs=bvecs)
print("  DWI:", data.shape, "| b0:", int(gtab.b0s_mask.sum()), "| direcciones:", int((~gtab.b0s_mask).sum()))

sl = list(load_tck(os.environ["TCK"]).streamlines)
n = int(os.environ["N_HILOS"])
if n:
    sl = sl[:n]   # prueba: los primeros n hilos
print("  hilos a ajustar:", len(sl))

t0 = time.time()
fit  = FiberModel(gtab).fit(data, sl, np.linalg.inv(img.affine))   # affine INVERTIDO, como en su script
beta = np.asarray(fit.beta).ravel()
print(f"  ajuste: {time.time() - t0:.0f} s")

np.savetxt(os.environ["PESOS"], beta)
print(f"  beta min/mediana/media/max: {beta.min():.4g} {np.median(beta):.4g} {beta.mean():.4g} {beta.max():.4g}")
print(f"  beta == 0: {(beta == 0).sum()} ({(beta == 0).mean():.2%})")
PY
[ -s "$PESOS" ] || falla "LiFE no terminó (no se escribió $PESOS). Si dice 'Killed', es falta de memoria"

# ---------------------------------------------------------------------------
paso "5. Revisión de los pesos"
esperado=$([ $PRUEBA = 1 ] && echo 2000 || echo 100000)
python - "$PESOS" "$esperado" <<'PY' || falla "los pesos no cumplen el contrato"
import sys, numpy as np
w = np.loadtxt(sys.argv[1]).ravel(); n = int(sys.argv[2])
print(f"  pesos: {w.size} | negativos: {(w < 0).sum()} | NaN: {np.isnan(w).sum()}")
assert w.size == n, f"hay {w.size} pesos, deben ser {n}"
assert (w >= 0).all() and not np.isnan(w).any(), "hay pesos negativos o NaN"
print("  [OK]    un peso >= 0 por hilo, en el orden del .tck")
PY

if [ $PRUEBA = 1 ]; then
  echo; echo "PRUEBA TERMINADA: todo funciona. Ahora corran sin --prueba:  bash $0"
  exit 0
fi

# ---------------------------------------------------------------------------
paso "6. Matrices 84 x 84 (entorno $ENV_MRTRIX), con -symmetric -zero_diagonal como las nuestras"
activar "$ENV_MRTRIX"
tck2connectome "$TCK" "$PARC" "$SALIDA/conn_life_100k.csv" -tck_weights_in "$PESOS" -symmetric -zero_diagonal -force -quiet
tck2connectome "$TCK" "$PARC" "$SALIDA/conn_raw_100k.csv" -symmetric -zero_diagonal -force -quiet
activar "$ENV_PY"
python - "$SALIDA" <<'PY' || falla "las matrices no cuadran con el tractograma oficial"
import sys, numpy as np
d = sys.argv[1]; iu = np.triu_indices(84, 1)
R = np.loadtxt(f"{d}/conn_raw_100k.csv", delimiter=","); L = np.loadtxt(f"{d}/conn_life_100k.csv", delimiter=",")
print(f"  conteo crudo: conexiones > 0 = {(R[iu] > 0).sum()} (debe ser 1322) | hilos asignados = {int(R[iu].sum())} (debe ser 68418)")
assert (R[iu] > 0).sum() == 1322 and int(R[iu].sum()) == 68418, "el conteo no coincide: no es el tractograma oficial"
print(f"  LiFE: conexiones > 0 = {(L[iu] > 0).sum()} | peso total = {L[iu].sum():.4g} | simétrica {np.allclose(L, L.T)} | diagonal 0 {not np.diag(L).any()}")
PY

# ---------------------------------------------------------------------------
paso "7. Paquete para mandar"
{
  echo "LiFE sobre tracks_100k.tck — $(date)"
  echo "md5 tracks_100k.tck: $md5"
  echo "tckstats: count $cuenta, media $media mm"
  grep -E "DIPY|ajuste:|beta|pesos:|conteo crudo|LiFE:|Maximum resident|Elapsed" "$SALIDA/log_completo.txt" || true
} > "$RES"
cd "$(dirname "$SALIDA")"
tar -czf entrega_life_100k.tar.gz "$(basename "$SALIDA")/life_weights.txt" "$(basename "$SALIDA")/conn_life_100k.csv" \
  "$(basename "$SALIDA")/conn_raw_100k.csv" "$(basename "$SALIDA")/resumen.txt" "$(basename "$SALIDA")/log_completo.txt"
echo
echo "LISTO. Manden este archivo al equipo de COMMIT:"
echo "   $(pwd)/entrega_life_100k.tar.gz"
echo "(en Windows: cp $(pwd)/entrega_life_100k.tar.gz /mnt/c/Users/\$USER/Downloads/)"

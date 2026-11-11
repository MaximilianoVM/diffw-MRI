#!/usr/bin/env bash
# Paso 1: gradientes con el eje y invertido, máscara, respuesta y FOD.
# Uso (desde la raíz del proyecto):  bash scripts/01_preprocess.sh
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p out

# data/ISMRM_2023_b3000.{nii.gz,bvec,bval} -> out/dwi_original.mif (gradientes tal cual)
mrconvert -force data/ISMRM_2023_b3000.nii.gz out/dwi_original.mif \
  -fslgrad data/ISMRM_2023_b3000.bvec data/ISMRM_2023_b3000.bval

# out/dwi_original.mif -> out/gradientes_y.b (tabla x y z b con y invertido)
mrinfo out/dwi_original.mif -dwgrad | awk '{print $1, -$2, $3, $4}' > out/gradientes_y.b

# out/dwi_original.mif + out/gradientes_y.b -> out/dwi.mif (DWI con gradientes corregidos)
mrconvert -force out/dwi_original.mif out/dwi.mif -grad out/gradientes_y.b

# out/dwi.mif -> out/mask.mif
dwi2mask -force out/dwi.mif out/mask.mif

# out/dwi.mif + out/mask.mif -> out/respuesta.txt (respuesta de una fibra)
dwi2response tournier -force out/dwi.mif out/respuesta.txt -mask out/mask.mif

# out/dwi.mif + out/respuesta.txt + out/mask.mif -> out/fod.mif (CSD)
dwi2fod csd -force out/dwi.mif out/respuesta.txt out/fod.mif -mask out/mask.mif

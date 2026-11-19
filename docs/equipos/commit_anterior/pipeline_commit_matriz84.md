# Pipeline: del DWI a la matriz de peso 84 × 84 (COMMIT)

Carpeta de trabajo: `~/desafio/datos/dataset/DWIs`

Entornos conda:

- `dmri`: MRtrix (`dwi2response`, `dwi2fod`, `tckgen`, `sh2peaks`, `tcksift2`, `tck2connectome`). No tiene numpy.
- `pydmri`: COMMIT 2.4.2, AMICO, numpy, pandas. No tiene MRtrix.

Regla práctica: mira el prompt antes de ejecutar. Debe decir `(dmri)` o `(pydmri)` según el paso.

---

## 0. Ubicar los datos

```bash
cd ~/desafio
ls -la ~/desafio/datos
cd ~/desafio/datos/dataset/DWIs
ls
```

Archivos de entrada: `ISMRM_2023_b3000.nii.gz`, `.bval`, `.bvec`.
La parcelación está en `~/desafio/datos/dataset/Parcels_free.nii`.

---

## 1. Preprocesamiento y tractograma con MRtrix (entorno `dmri`)

> Estos comandos los reconstruí a partir de las salidas que pegaste (`response.txt`, `ODF.nii`,
> `tracks.tck`, máscara, FA y DT). Los parámetros exactos están en `datos/comandos.txt`;
> si difieren, usa los de ese archivo.

```bash
conda activate dmri
cd ~/desafio/datos/dataset/DWIs

# máscara, tensor y FA
dwi2mask ISMRM_2023_b3000.nii.gz ISMRM_2023_b3000_mask.nii \
  -fslgrad ISMRM_2023_b3000.bvec ISMRM_2023_b3000.bval
dwi2tensor ISMRM_2023_b3000.nii.gz ISMRM_2023_b3000_DT.nii.gz \
  -fslgrad ISMRM_2023_b3000.bvec ISMRM_2023_b3000.bval
tensor2metric ISMRM_2023_b3000_DT.nii.gz -fa ISMRM_2023_b3000_FA.nii

# función de respuesta (salida: response.txt)
dwi2response tournier ISMRM_2023_b3000.nii.gz response.txt \
  -fslgrad ISMRM_2023_b3000.bvec ISMRM_2023_b3000.bval

# deconvolución esférica restringida (salida: ODF.nii)
dwi2fod csd ISMRM_2023_b3000.nii.gz response.txt ODF.nii \
  -mask ISMRM_2023_b3000_mask.nii \
  -fslgrad ISMRM_2023_b3000.bvec ISMRM_2023_b3000.bval

# tractografía (salida: tracks.tck con 100000 streamlines)
tckgen ODF.nii tracks.tck -algorithm iFOD2 \
  -seed_image ISMRM_2023_b3000_mask.nii -select 100000
```

Comprobar:

```bash
ls -lh ODF.nii tracks.tck
tckinfo tracks.tck | grep -i count
```

---

## 2. Picos de fibra para COMMIT (entorno `dmri`)

COMMIT con el modelo Stick-Zeppelin-Ball necesita las direcciones de los picos (compartimento extra-axonal). Sin ellos da el error `The selected model has EC compartments, but no peaks have been provided`.

```bash
sh2peaks ODF.nii peaks.nii.gz -num 3 -mask ISMRM_2023_b3000_mask.nii
ls -lh peaks.nii.gz
```

Alternativa si `sh2peaks` falla con `.nii`:

```bash
mrconvert ODF.nii ODF.mif
sh2peaks ODF.mif peaks.nii.gz -num 3 -mask ISMRM_2023_b3000_mask.nii
```

---

## 3. COMMIT (entorno `pydmri`)

Instalación (solo si falta):

```bash
conda activate pydmri
python -c "import commit; print(commit.__version__)"   # debe dar 2.4.2
python -c "import amico; print('amico ok')"
# si falta: pip install dmri-commit dmri-amico
```

Script `run_commit.py`:

```bash
cat > run_commit.py << 'EOF'
import commit
commit.setup()
from commit import trk2dictionary
import amico

amico.util.fsl2scheme("ISMRM_2023_b3000.bval", "ISMRM_2023_b3000.bvec",
                      schemeFilename="dwi.scheme")

trk2dictionary.run(
    filename_tractogram="tracks.tck",
    filename_mask="ISMRM_2023_b3000_mask.nii",
    filename_peaks="peaks.nii.gz",
    peaks_use_affine=True,
    path_out="COMMIT",          # debe coincidir con el dictionary_path por defecto de Evaluation
)

mit = commit.Evaluation(".", ".")
mit.load_data("ISMRM_2023_b3000.nii.gz", "dwi.scheme")
mit.set_model("StickZeppelinBall")
mit.model.set(1.7E-3, [0.6E-3], [2.0E-3])
mit.generate_kernels(regenerate=True)
mit.load_kernels()
mit.load_dictionary("COMMIT")
mit.set_threads()
mit.build_operator()
mit.fit(tol_fun=1e-3, max_iter=1000)
mit.save_results()
EOF

rm -rf COMMIT
python run_commit.py
```

Notas de los errores que aparecieron:

- `No module named 'commit'`: estabas en `dmri`; COMMIT vive en `pydmri`.
- `Dictionary is outdated or not found`: `path_out` y la carpeta que busca `Evaluation` (por defecto `COMMIT`) deben coincidir.
- `no peaks have been provided`: faltaba `filename_peaks` (paso 2).
- `Killed`: falta de RAM; usar un subconjunto con `tckedit tracks.tck -number 20000 tracks_20k.tck` (en `dmri`).

Resultado: 100000 pesos, de los cuales 36940 son mayores que 0.

---

## 4. Guardar los pesos de COMMIT (entorno `pydmri`)

Los pesos quedan en `COMMIT/Results_StickZeppelinBall/streamline_weights.txt`.

```bash
find . -name "streamline_weights.txt"
cp COMMIT/Results_StickZeppelinBall/streamline_weights.txt commit_weights.txt

python - << 'EOF'
import numpy as np
w = np.loadtxt("commit_weights.txt")
print("total:", w.size)
print("peso > 0:", (w > 0).sum())
print("peso = 0:", (w == 0).sum())
EOF
```

---

## 5. (Opcional) Tractograma filtrado, solo streamlines con peso > 0

```bash
python - << 'EOF'
import numpy as np
from nibabel.streamlines import load, save, Tractogram

w = np.loadtxt("commit_weights.txt")
tck = load("tracks.tck")
sl = tck.streamlines
assert len(w) == len(sl), (len(w), len(sl))

keep = np.where(w > 0)[0]
out = Tractogram(sl[keep], affine_to_rasmm=np.eye(4))
save(out, "tracks_commit.tck", header=tck.header)
np.savetxt("commit_keep_idx.txt", keep, fmt="%d")
print("guardados:", len(keep))
EOF
```

---

## 6. (Opcional) SIFT2 para comparar (entorno `dmri`)

```bash
conda activate dmri
tcksift2 tracks.tck ODF.nii sift2_weights.txt
```

---

## 7. Matriz de conectividad 84 × 84 ponderada por COMMIT (entorno `dmri`)

```bash
conda activate dmri
cd ~/desafio/datos/dataset/DWIs

find ~/desafio -iname "*parcel*"
mrstats ~/desafio/datos/dataset/Parcels_free.nii -output max      # debe dar 84

tck2connectome tracks.tck ~/desafio/datos/dataset/Parcels_free.nii connectome_commit.csv \
  -tck_weights_in commit_weights.txt -symmetric -zero_diagonal
```

El aviso `The following nodes are missing from the parcellation image: 15` es esperable: la región 15 no aparece en la imagen, por lo que su fila y columna quedan en cero. La matriz sigue siendo 84 × 84.

Versiones de comparación (opcionales):

```bash
tck2connectome tracks.tck ~/desafio/datos/dataset/Parcels_free.nii connectome_sin_pesos.csv \
  -symmetric -zero_diagonal
tck2connectome tracks.tck ~/desafio/datos/dataset/Parcels_free.nii connectome_sift2.csv \
  -tck_weights_in sift2_weights.txt -symmetric -zero_diagonal
```

---

## 8. Verificar y exportar a Excel (entorno `pydmri`, usa numpy y pandas)

```bash
conda activate pydmri
cd ~/desafio/datos/dataset/DWIs

python -c "
import numpy as np
M = np.loadtxt('connectome_commit.csv', delimiter=',')
print(M.shape)
print('fila 15 suma:', M[14].sum())
print('conexiones > 0:', (M > 0).sum() // 2)
"

# si falta: pip install pandas openpyxl
python - << 'EOF'
import numpy as np, pandas as pd

M = np.loadtxt("connectome_commit.csv", delimiter=",")
assert M.shape == (84, 84), M.shape

etiquetas = [f"R{i}" for i in range(1, 85)]
pd.DataFrame(M, index=etiquetas, columns=etiquetas).to_excel(
    "/mnt/c/Users/sarai/Downloads/matriz_peso_commit_84x84.xlsx")
print("Guardado en Descargas")
EOF
```

Resultado: `matriz_peso_commit_84x84.xlsx` en la carpeta Descargas de Windows.

---

## Pendiente (no ejecutado todavía)

- LIFE con Dipy.
- Etiquetar los streamlines contra el ground truth (`datos/Fibers/tck/all_tracks.tck`).
- Regla de decisión que combine los pesos de COMMIT, SIFT2 y LIFE.

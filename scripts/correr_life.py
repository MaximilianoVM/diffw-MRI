"""Calcula los pesos de LiFE (un beta por hilo) con DIPY para un tractograma .tck.

Sigue el script del equipo de LiFE (docs/life_metodo.md): FiberModel(gtab).fit(data, hilos, inv(affine)).
La única diferencia es la entrada: el tractograma común data/tracks_100k.tck en vez de uno propio.

Uso (desde la raíz del proyecto, con el entorno activado):
    python scripts/correr_life.py                         # usa data/tracks_100k.tck
    python scripts/correr_life.py --n=20000               # prueba con una submuestra (semilla 0)

Gradientes: se leen directo del .bvec, como hace el equipo. Ese .bvec ya está en las
coordenadas que espera DIPY (es idéntico a la tabla corregida que usa COMMIT); la inversión
del eje y solo hace falta cuando MRtrix lo importa con -fslgrad.

Resultado: out/life/pesos_life.txt (una línea por hilo, mismo orden que el .tck)
           y, con --n, out/life/indices_life.txt (qué hilos del .tck se usaron).
"""
import os
import sys
import time

import nibabel as nib
import numpy as np
from dipy.core.gradients import gradient_table
from dipy.io.gradients import read_bvals_bvecs
from dipy.tracking.life import FiberModel

args = [a for a in sys.argv[1:] if not a.startswith("--")]
n_sub = [int(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith("--n=")]
os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

D = "data/ISMRM_2023_b3000"
tck = args[0] if args else "data/tracks_100k.tck"
OUT = "out/life"
os.makedirs(OUT, exist_ok=True)

img = nib.load(f"{D}.nii.gz")
data = img.get_fdata(dtype=np.float32)
bvals, bvecs = read_bvals_bvecs(f"{D}.bval", f"{D}.bvec")
gtab = gradient_table(bvals, bvecs=bvecs)
print("DWI:", data.shape, "| b0:", int(gtab.b0s_mask.sum()), "| direcciones:", int((~gtab.b0s_mask).sum()))

hilos = list(nib.streamlines.load(tck).streamlines)
print("hilos en", tck, ":", len(hilos))
if n_sub:
    idx = np.sort(np.random.default_rng(0).choice(len(hilos), size=n_sub[0], replace=False))
    hilos = [hilos[i] for i in idx]
    np.savetxt(f"{OUT}/indices_life.txt", idx, fmt="%d")
    print("submuestra:", len(hilos))

# El affine va invertido: DIPY aplica esta matriz a los puntos (en mm) y redondea para
# obtener el índice de vóxel. Con img.affine sin invertir da IndexError.
t0 = time.time()
fit = FiberModel(gtab).fit(data, hilos, np.linalg.inv(img.affine))
beta = np.asarray(fit.beta).ravel()
print(f"ajuste LiFE: {time.time() - t0:.0f} s")

nombre = "pesos_life.txt" if not n_sub else f"pesos_life_{n_sub[0]}.txt"
np.savetxt(f"{OUT}/{nombre}", beta)
print(f"beta min/mediana/media/max: {beta.min():.4g} {np.median(beta):.4g} {beta.mean():.4g} {beta.max():.4g}")
print(f"beta == 0: {(beta == 0).sum()} ({(beta == 0).mean():.2%})")
print(f"guardado en {OUT}/{nombre}")

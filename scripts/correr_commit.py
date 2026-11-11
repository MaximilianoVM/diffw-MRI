"""Calcula los pesos de COMMIT (un número por hilo) para un tractograma .tck.

Uso (desde la raíz del proyecto):
    python scripts/correr_commit.py                                   # usa out/tracks_100k.tck
    python scripts/correr_commit.py out/otro.tck
    python scripts/correr_commit.py --sin-corregir-y                  # prueba de control
    python scripts/correr_commit.py otro.tck --salida=out/otra_carpeta

Antes hay que haber corrido scripts/01_preprocess.sh y 02_tractography.sh (crean out/dwi.mif, mask.mif, fod.mif, tracks_100k.tck).
Resultado: out/commit/pesos_commit.txt  (una línea por hilo, mismo orden que el .tck)
"""
import glob
import os
import subprocess
import sys

import numpy as np

args = [a for a in sys.argv[1:] if not a.startswith("--")]
corregir_y = "--sin-corregir-y" not in sys.argv

# COMMIT (código en C) falla con rutas que llevan acentos o espacios.
# Si la ruta de este proyecto los tiene, muévelo a una ruta sin ellos.
PROY = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
REAL = PROY
os.chdir(PROY)

OUT = "out"
tck_rel = args[0] if args else f"{OUT}/tracks_100k.tck"
tck = os.path.join(PROY, os.path.relpath(os.path.realpath(tck_rel), REAL))
salida = [a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--salida=")]
C = os.path.join(PROY, salida[0] if salida else
                 "out/commit" + ("" if corregir_y else "_sin_y"))
os.makedirs(C, exist_ok=True)


def corre(*cmd):
    subprocess.run(list(cmd), check=True)


# 1) Datos en NIfTI con ejes "normales" (strides 1,2,3): así las coordenadas de vóxel
#    apuntan igual que las del escáner y los gradientes/picos no necesitan reorientarse.
dwi_mif = f"{OUT}/dwi.mif" if corregir_y else f"{OUT}/dwi_original.mif"
corre("mrconvert", "-quiet", "-force", dwi_mif, f"{C}/dwi.nii.gz", "-strides", "1,2,3,4")
corre("mrconvert", "-quiet", "-force", f"{OUT}/mask.mif", f"{C}/mask.nii.gz", "-strides", "1,2,3")
# Picos de la FOD (hasta 3 direcciones por vóxel): COMMIT los usa para el compartimento
# extra-axonal (Zeppelin) en los vóxeles por donde no pasa ningún hilo.
corre("sh2peaks", "-quiet", "-force", f"{OUT}/fod.mif", f"{C}/picos_tmp.mif", "-num", "3",
      "-mask", f"{OUT}/mask.mif")
corre("mrcalc", "-quiet", "-force", f"{C}/picos_tmp.mif", "-finite", f"{C}/picos_tmp.mif", "0",
      "-if", f"{C}/picos_tmp2.mif")  # sh2peaks pone NaN donde no hay pico
corre("mrconvert", "-quiet", "-force", f"{C}/picos_tmp2.mif", f"{C}/picos.nii.gz", "-strides", "1,2,3,4")
os.remove(f"{C}/picos_tmp.mif"); os.remove(f"{C}/picos_tmp2.mif")

# Gradientes: la tabla de MRtrix (x y z b, en coordenadas del escáner) ya trae la corrección
# del eje y; con strides 1,2,3 esas coordenadas coinciden con las de vóxel que usa AMICO.
tabla = subprocess.run(["mrinfo", dwi_mif, "-dwgrad"], capture_output=True, text=True,
                       check=True).stdout
grad = np.array([l.split() for l in tabla.splitlines() if l.strip()], dtype=float)
np.savetxt(f"{C}/dwi.bvec", grad[:, :3].T, fmt="%.8f")
np.savetxt(f"{C}/dwi.bval", grad[:, 3][None], fmt="%g")

import amico
import commit
from commit import trk2dictionary

amico.util.fsl2scheme(f"{C}/dwi.bval", f"{C}/dwi.bvec", f"{C}/dwi.scheme")

# 2) Diccionario: qué vóxeles cruza cada hilo y en qué dirección
trk2dictionary.run(
    filename_tractogram=tck,
    path_out=f"{C}/COMMIT",
    filename_mask=f"{C}/mask.nii.gz",
    filename_peaks=f"{C}/picos.nii.gz",
    TCK_ref_image=f"{C}/mask.nii.gz",
    fiber_shift=0.5,   # MRtrix pone el centro del vóxel en 0; COMMIT, en 0.5
)

# 3) Modelo Stick-Zeppelin-Ball y ajuste (mínimos cuadrados no negativos)
commit.core.setup()
mit = commit.Evaluation(C, ".", dictionary_path=f"{C}/COMMIT")
mit.load_data(f"{C}/dwi.nii.gz", f"{C}/dwi.scheme")
mit.set_model("StickZeppelinBall")
# Stick: agua dentro del axón (solo se mueve a lo largo). Zeppelin: agua alrededor de los
# axones (d_perp = d_par·(1 − 0.7): 70 % de volumen intra-axonal). Ball: agua libre (GM, LCR).
mit.model.set(d_par=1.7e-3, d_perp=0.0, d_par_zep=1.7e-3, d_perps_zep=[0.51e-3],
              d_isos=[1.7e-3, 3.0e-3])
mit.generate_kernels(regenerate=True)
mit.load_kernels()
mit.load_dictionary()
mit.set_threads()
mit.build_operator()
mit.fit(tol_fun=1e-3, max_iter=1000)
mit.save_results()

# 4) Un peso por hilo, en el mismo orden que el .tck
archivo = max(glob.glob(f"{C}/**/streamline_weights.txt", recursive=True), key=os.path.getmtime)
pesos = np.loadtxt(archivo)
np.savetxt(f"{C}/pesos_commit.txt", pesos)
print(f"\nhilos: {len(pesos)} | pesos = 0: {(pesos == 0).sum()} ({(pesos == 0).mean():.0%})"
      f" | mediana de los no cero: {np.median(pesos[pesos > 0]):.3g}")
print(f"guardado en {C}/pesos_commit.txt")

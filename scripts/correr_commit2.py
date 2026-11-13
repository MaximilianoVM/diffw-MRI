"""Calcula los pesos de COMMIT2 (un número por hilo): COMMIT con penalización por conexión.

COMMIT2 (Schiavi et al. 2020) usa el mismo modelo y el mismo diccionario que COMMIT, pero agrega una
penalización "group lasso": los hilos que unen el mismo par de regiones forman un grupo, y el ajuste
prefiere apagar grupos completos (conexiones poco respaldadas por la señal). Cada hilo que no une
dos regiones forma su propio grupo.

Uso (desde la raíz del proyecto, con el entorno activado):
    python scripts/correr_commit2.py                  # lambda = 1e-2 (el que se probó)
    python scripts/correr_commit2.py --lambda=5e-3

Antes hay que haber corrido el paso 3 (scripts/03_commit.sh): se reutilizan out/commit/dwi.nii.gz,
dwi.scheme, mask.nii.gz y el diccionario out/commit/COMMIT, así no se repite el trabajo pesado.
Resultado: out/commit2/pesos_commit2.txt  (una línea por hilo, mismo orden que el .tck)
Memoria: igual que COMMIT (necesita la máquina grande, no la laptop de 11 GB).
"""
import os
import subprocess
import sys

import numpy as np

lam = 1e-2
salida = "out/commit2"
for a in sys.argv[1:]:
    if a.startswith("--lambda="):
        lam = float(a.split("=", 1)[1])
    if a.startswith("--salida="):          # p. ej. --salida=out/commit2_lam5e-3 para no pisar la corrida principal
        salida = a.split("=", 1)[1]

# COMMIT (código en C) falla con rutas con acentos o espacios; misma solución que correr_commit.py.
REAL = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if REAL.isascii() and " " not in REAL:
    PROY = REAL
else:
    PROY = os.path.expanduser("~/Proyecto_2_cerebro")
    if not os.path.lexists(PROY):
        os.symlink(REAL, PROY)
    elif not os.path.samefile(PROY, REAL):
        sys.exit(f"ERROR: {PROY} ya existe y no apunta a este proyecto ({REAL}).")
os.chdir(PROY)

TCK, P = "data/tracks_100k.tck", "data/Parcels_free.nii"
C1, C2 = "out/commit", salida
for f in (f"{C1}/dwi.nii.gz", f"{C1}/dwi.scheme", f"{C1}/mask.nii.gz", f"{C1}/COMMIT"):
    if not os.path.exists(f):
        sys.exit(f"ERROR: falta {f}. Corran antes el paso 3: bash scripts/03_commit.sh")
os.makedirs(C2, exist_ok=True)
for f in ("dwi.nii.gz", "dwi.scheme", "mask.nii.gz"):  # accesos directos a lo ya preparado
    destino = f"{C2}/{f}"
    if not os.path.lexists(destino):
        os.symlink(os.path.abspath(f"{C1}/{f}"), destino)

# 1) Grupos: hilos que unen el mismo par de regiones (región de cada extremo con tck2connectome)
asig = f"{C2}/asignaciones.txt"
subprocess.run(["tck2connectome", "-force", "-quiet", TCK, P, f"{C2}/tmp.csv", "-out_assignments", asig,
                "-symmetric", "-zero_diagonal"], check=True)
os.remove(f"{C2}/tmp.csv")
A = np.loadtxt(asig, dtype=int)
n = len(A)
grupos, por_par = [], {}
for i, (a, b) in enumerate(A):
    if a > 0 and b > 0 and a != b:          # une dos regiones distintas
        por_par.setdefault((min(a, b), max(a, b)), []).append(i)
    else:                                    # sin región o autoconexión: grupo propio
        grupos.append(np.array([i], dtype=np.int32))
grupos += [np.array(v, dtype=np.int32) for v in por_par.values()]
group_idx = np.empty(len(grupos), dtype=object)
for k, g in enumerate(grupos):
    group_idx[k] = g
print(f"hilos {n} | grupos {len(grupos)} (conexiones entre regiones: {len(por_par)})")

# 2) Mismo modelo que COMMIT, con el diccionario ya calculado
import commit

commit.core.setup()
mit = commit.Evaluation(os.path.abspath(C2), ".", dictionary_path=os.path.abspath(f"{C1}/COMMIT"))
mit.load_data("dwi.nii.gz", "dwi.scheme")
mit.set_model("StickZeppelinBall")
mit.model.set(d_par=1.7e-3, d_perp=0.0, d_par_zep=1.7e-3, d_perps_zep=[0.51e-3],
              d_isos=[1.7e-3, 3.0e-3])
mit.generate_kernels(regenerate=True)
mit.load_kernels()
mit.load_dictionary()
mit.set_threads()
mit.build_operator()

# 3) Ajuste sin regularizar (= COMMIT): los pesos de grupo "adaptativos" se calculan a partir de él.
#    Sin este paso COMMIT da: "Group weights cannot be computed if the fit without regularisation
#    has not been performed before".
mit.fit(tol_fun=1e-3, max_iter=1000)

# 4) Penalización por grupos (pesos de grupo como en el artículo: cardinalidad + adaptativo)
mit.set_regularisation(
    regularisers=("group_lasso", None, None),
    lambdas=(lam, None, None),
    is_nonnegative=(True, True, True),
    params=({"group_idx": group_idx, "group_weights_cardinality": True,
             "group_weights_adaptive": True}, None, None),
)
mit.fit(tol_fun=1e-3, max_iter=1000)
# COMMIT guarda los resultados junto al diccionario (out/commit/COMMIT/): con un sufijo propio no pisa
# los de COMMIT, y luego se mueven a out/commit2/.
mit.save_results(path_suffix="_COMMIT2")
import shutil

origen = f"{C1}/COMMIT/Results_StickZeppelinBall_COMMIT2"
destino = f"{C2}/Results_StickZeppelinBall"
if os.path.exists(destino):
    shutil.rmtree(destino)
shutil.move(origen, destino)

# 5) Un peso por hilo, en el mismo orden que el .tck
w = np.loadtxt(f"{destino}/streamline_weights.txt")
assert len(w) == n, (len(w), n)
np.savetxt(f"{C2}/pesos_commit2.txt", w)
print(f"\nlambda {lam} | hilos {len(w)} | pesos > 0: {(w > 0).sum()} | = 0: {(w == 0).sum()} ({(w == 0).mean():.0%})")
print(f"guardado en {C2}/pesos_commit2.txt")

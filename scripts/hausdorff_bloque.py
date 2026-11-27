"""Distancia de Hausdorff de cada hilo del tractograma al ground truth (etiqueta de la junta del 17 nov).

Para cada hilo y_i de data/tracks_100k.tck calcula, contra los 189 985 hilos del GT (data/GT/all_tracks.tck):
    hd_min      min_j  d_H(y_i, GT_j)          Hausdorff simétrico (el de las notas de la junta)
    hd_dir_min  min_j  max_p d(p, GT_j), p en y_i   Hausdorff dirigido: "¿y_i está dentro de algún hilo del GT?"
    gt_hilo     índice del hilo del GT más cercano según hd_min
Se guardan las DISTANCIAS (mm), no el 0/1: el umbral ε se elige después (hilo "corresponde al GT" si hd_min < ε).
Si ningún hilo del GT está a menos de --eps-max (10 mm por omisión) el valor queda vacío (= "más de eps-max").

Es exacto salvo por el muestreo: los hilos se remuestrean cada --paso mm (2 por omisión; el error es < paso/2).
No es la comparación de fuerza bruta de las notas (≈ 3 días por 10 000 hilos): se descartan primero los hilos del GT
que no tienen un punto a menos de eps-max de tres puntos de y_i (inicio, medio y fin), y solo se mide a los candidatos.

Uso (desde la raíz del proyecto, con el entorno activado):
    python scripts/hausdorff_bloque.py 1 7          # bloque 1 de 7 (los 100 000 hilos se reparten en 7 partes)
    python scripts/hausdorff_bloque.py 3 10         # bloque 3 de 10 (hilos 20 000-29 999)
    python scripts/hausdorff_bloque.py 1 7 --n=200  # prueba rápida: solo los primeros 200 hilos del bloque
    python scripts/hausdorff_bloque.py --unir       # junta out/hausdorff/bloque_*.csv -> out/hausdorff/hausdorff.csv
Salida: out/hausdorff/bloque_<k>_de_<N>.csv  (hilo, hd_min, hd_dir_min, gt_hilo)
Memoria: ≈ 1.5 GB (el GT completo remuestreado a 2 mm). Cabe en una laptop.
"""
import glob
import os
import sys
import time

import nibabel as nib
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist

# rutas y opciones
os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
TCK, GT, SAL = "data/tracks_100k.tck", "data/GT/all_tracks.tck", "out/hausdorff"
opc = {a.split("=")[0]: a.split("=")[1] for a in sys.argv[1:] if a.startswith("--") and "=" in a}
pos = [a for a in sys.argv[1:] if not a.startswith("--")]
EPS_MAX, PASO = float(opc.get("--eps-max", 10)), float(opc.get("--paso", 2))
GT = opc.get("--gt", GT)  # en el paquete: --gt=all_tracks.tck --tck=bloque.tck --offset=<primer hilo>

# unir las partes
if "--unir" in sys.argv:
    fs = sorted(glob.glob(f"{SAL}/bloque_*.csv"))
    T = pd.concat([pd.read_csv(f) for f in fs]).sort_values("hilo").drop_duplicates("hilo")
    print(f"{len(fs)} bloques, {len(T)} hilos distintos, rango {T.hilo.min()}-{T.hilo.max()}")
    if len(T) != 100000 or T.hilo.max() != 99999:
        print("AVISO: faltan hilos (deben ser 100 000, 0-99 999)")
    T.to_csv(f"{SAL}/hausdorff.csv", index=False)
    for e in (2, 3, 5, 7, 10):
        print(f"  hd_min < {e:>2} mm: {(T.hd_min < e).mean():.1%} de los hilos")
    sys.exit()

# redistribuir los puntos de cada hilo para que queden cada 2 mm
# lo prepara para KDtree
k, N = int(pos[0]), int(pos[1])
assert 1 <= k <= N, "el bloque k va de 1 a N"
tam = -(-100000 // N)
ini, fin = (k - 1) * tam, min(k * tam, 100000)
if "--n" in opc:
    fin = min(fin, ini + int(opc["--n"]))

# lo usa la de arriba
def remuestrea(S, paso):
    """Cada hilo -> puntos cada `paso` mm (≥ 2 puntos). Devuelve (puntos float32 concatenados, offsets)."""
    out, off = [], [0]
    for s in S:
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(s, axis=0), axis=1))]
        n = max(2, int(round(d[-1] / paso)) + 1)
        t = np.linspace(0, d[-1], n)
        out.append(np.stack([np.interp(t, d, s[:, c]) for c in range(3)], 1).astype(np.float32))
        off.append(off[-1] + n)
    return np.concatenate(out), np.array(off)

# cargar el GT y preparar el KDtree
t0 = time.time()
print(f"bloque {k}/{N}: hilos {ini}-{fin - 1} | eps-max {EPS_MAX} mm | paso {PASO} mm")
G = nib.streamlines.load(GT).streamlines
GP, GO = remuestrea(G, PASO)
del G
gt_de_punto = np.repeat(np.arange(len(GO) - 1, dtype=np.int32), np.diff(GO))
arbol = cKDTree(GP)
print(f"GT: {len(GO) - 1} hilos, {len(GP)} puntos, listo en {time.time() - t0:.0f} s")

# cargar el tractograma y calcular la distancia de Hausdorff de cada hilo al GT
if "--tck" in opc:  # modo "paquete": el tractograma ya es solo el bloque; --offset = índice global de su primer hilo
    Y = nib.streamlines.load(opc["--tck"]).streamlines[:int(opc.get("--n", 10**9))]
    ini = int(opc.get("--offset", 0))
    fin = ini + len(Y)
else:
    Y = nib.streamlines.load(TCK).streamlines[ini:fin]
YP, YO = remuestrea(Y, PASO)
filas = []

# calcular la distancia de Hausdorff de cada hilo del tractograma al GT
for i in range(fin - ini):
    y = YP[YO[i]:YO[i + 1]]
    tres = y[[0, len(y) // 2, -1]]
    cand = None
    for lista in arbol.query_ball_point(tres, EPS_MAX):  # hilos del GT con un punto cerca de cada una de las 3 puntas
        ids = np.unique(gt_de_punto[lista])
        cand = ids if cand is None else np.intersect1d(cand, ids, assume_unique=True)
        if len(cand) == 0:
            break
    hd, dr, mejor = np.inf, np.inf, -1
    for j in cand:
        D = cdist(y, GP[GO[j]:GO[j + 1]])
        a, b = D.min(1).max(), D.min(0).max()  # y -> GT_j  y  GT_j -> y
        if max(a, b) < hd:
            hd, mejor = max(a, b), int(j)
        dr = min(dr, a)
    if hd > EPS_MAX:
        hd, mejor = np.nan, -1
    if dr > EPS_MAX:
        dr = np.nan
    filas.append((ini + i, hd, dr, mejor))
    if (i + 1) % 1000 == 0:
        print(f"  {i + 1}/{fin - ini} hilos, {time.time() - t0:.0f} s", flush=True)

os.makedirs(SAL, exist_ok=True)
sal = f"{SAL}/bloque_{k}_de_{N}.csv" if "--n" not in opc else f"{SAL}/prueba_{k}_de_{N}.csv"
T = pd.DataFrame(filas, columns=["hilo", "hd_min", "hd_dir_min", "gt_hilo"])
T.to_csv(sal, index=False)
print(f"guardado {sal} | con correspondencia < {EPS_MAX:g} mm: {T.hd_min.notna().mean():.1%} | {time.time() - t0:.0f} s en total")

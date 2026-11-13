"""Compara los pesos por hilo de COMMIT, SIFT2 y LiFE entre sí (mismo tractograma, mismo orden).

Uso (desde la raíz del proyecto, con el entorno activado):
    python scripts/comparar_pesos.py

Lee los pesos que existan de:
    COMMIT  out/commit/pesos_commit.txt
    SIFT2   out/pesos_sift2.txt
    LiFE    out/life/pesos_life.txt   (lo corre el equipo de LiFE sobre out/tracks_100k.tck)

Imprime:
    - resumen de cada método (ceros, mediana)
    - correlación de Spearman entre cada par (por hilo y por conexión de la matriz 84 x 84)
    - cuánto coinciden en lo que descartarían: el 45 % de hilos con menor peso de cada método
      (el % que COMMIT pone en 0), para que los tres descarten la misma cantidad
Salida: out/comparacion_pesos.txt (vía tee en 05_life.sh) y out/pesos_por_hilo.csv
"""
import itertools
import os

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
archivos = {"COMMIT": "out/commit/pesos_commit.txt", "SIFT2": "out/pesos_sift2.txt",
            "LiFE": "out/life/pesos_life.txt"}
W = {m: np.loadtxt(f, comments="#").ravel() for m, f in archivos.items() if os.path.exists(f)}
for m in archivos:
    if m not in W:
        print(f"(falta {archivos[m]}: {m} no entra en la comparación)")
n = {len(w) for w in W.values()}
assert len(n) == 1, f"los pesos no tienen el mismo número de hilos: { {m: len(w) for m, w in W.items()} }"

A = np.loadtxt("out/asignaciones.txt", comments="#", dtype=int)
L = np.loadtxt("out/longitudes.txt", comments="#").ravel()
con = (A[:, 0] > 0) & (A[:, 1] > 0)
iu = np.triu_indices(84, 1)


def matriz(w):
    C = np.zeros((84, 84))
    np.add.at(C, (A[con, 0] - 1, A[con, 1] - 1), w[con])
    C = C + C.T
    np.fill_diagonal(C, 0)
    return C[iu]


print("-- Cada método")
for m, w in W.items():
    print(f"{m:7s} hilos {len(w)} | peso = 0: {(w == 0).mean():.1%} | mediana {np.median(w):.3g}"
          f" | Spearman con la longitud {spearmanr(w, L)[0]:+.2f}")

frac = (W["COMMIT"] == 0).mean() if "COMMIT" in W else 0.45
descarta = {m: w <= np.quantile(w, frac) for m, w in W.items()}

print(f"\n-- Por pares (descartar = el {frac:.0%} con menor peso de cada método)")
for a, b in itertools.combinations(W, 2):
    ra = spearmanr(W[a], W[b])[0]
    rc = spearmanr(matriz(W[a]), matriz(W[b]))[0]
    da, db = descarta[a], descarta[b]
    print(f"{a} vs {b}: Spearman por hilo {ra:+.3f} | por conexión {rc:+.3f}"
          f" | descartan los mismos: {(da & db).sum() / da.sum():.0%}"
          f" (al azar {frac:.0%}) | Jaccard {(da & db).sum() / (da | db).sum():.2f}")

if len(W) == 3:
    todos = np.logical_and.reduce(list(descarta.values()))
    alguno = np.logical_or.reduce(list(descarta.values()))
    print(f"\nlos tres descartan: {todos.mean():.1%} de los hilos | al menos uno: {alguno.mean():.1%}")

pd.DataFrame({"hilo": np.arange(len(L)), "longitud_mm": L, "region_a": A[:, 0], "region_b": A[:, 1],
              **{f"peso_{m.lower()}": w for m, w in W.items()}}).to_csv("out/pesos_por_hilo.csv", index=False)
print("\nguardado en out/pesos_por_hilo.csv")

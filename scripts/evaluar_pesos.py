"""Evalúa un método de filtrado (COMMIT, SIFT2 o LiFE) contra el ground truth, hilo por hilo y por conexión.

Uso (desde la raíz del proyecto, con el entorno activado):
    python scripts/evaluar_pesos.py COMMIT out/commit/pesos_commit.txt

Necesita en out/ (ver pipeline.md):
    asignaciones.txt  par de regiones de cada hilo (tck2connectome -out_assignments)
    longitudes.txt    longitud de cada hilo en mm (tckstats -dump)
    gt.csv            conectoma 84 x 84 del ground truth

Etiqueta de cada hilo:
    bueno       sus dos extremos caen en regiones que el GT conecta
    malo        sus dos extremos caen en regiones, pero el GT no las conecta
    sin_region  algún extremo no cae en ninguna región (se cuenta como malo en el AUC)

Salida: imprime las métricas y guarda out/hilos_<metodo>.csv
(hilo, longitud_mm, region_a, region_b, etiqueta, peso).
"""
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

metodo, archivo = sys.argv[1], sys.argv[2]
M = "out"

w = np.loadtxt(archivo, comments="#").ravel()
L = np.loadtxt(f"{M}/longitudes.txt", comments="#").ravel()
A = np.loadtxt(f"{M}/asignaciones.txt", comments="#", dtype=int)
G = np.loadtxt(f"{M}/gt.csv", delimiter=",") > 0
assert len(w) == len(L) == len(A), (len(w), len(L), len(A))

a, b = A[:, 0], A[:, 1]
con_region = (a > 0) & (b > 0)
bueno = np.zeros(len(w), bool)
bueno[con_region] = G[a[con_region] - 1, b[con_region] - 1]
etiqueta = np.where(bueno, "bueno", np.where(con_region, "malo", "sin_region"))

pd.DataFrame({"hilo": np.arange(len(w)), "longitud_mm": L, "region_a": a, "region_b": b,
              "etiqueta": etiqueta, "peso": w}).to_csv(f"{M}/hilos_{metodo.lower()}.csv", index=False)


def pct(x):
    return f"{x:.0%}"


n = len(w)
cero = w == 0
print(f"== {metodo}: {n} hilos")
print(f"etiquetas: bueno {bueno.sum()} ({pct(bueno.mean())}) | malo {(etiqueta == 'malo').sum()}"
      f" | sin_region {(~con_region).sum()}")
print(f"peso = 0: {cero.sum()} ({pct(cero.mean())})")

print("\n-- Por hilo")
print(f"AUC (peso como puntaje de 'bueno'):            {roc_auc_score(bueno, w):.3f}")
print(f"AUC (peso x longitud):                         {roc_auc_score(bueno, w * L):.3f}")
print(f"AUC solo con la longitud (referencia):         {roc_auc_score(bueno, L):.3f}")
if cero.any():
    print(f"Descartar los de peso 0:")
    print(f"  de los descartados, malos:                   {pct((~bueno[cero]).mean())}"
          f"   (al azar sería {pct((~bueno).mean())})")
    print(f"  malos eliminados:                            {pct(cero[~bueno].mean())}")
    print(f"  buenos perdidos:                             {pct(cero[bueno].mean())}")
print(f"Peso medio buenos / malos:                     {w[bueno].mean():.3g} / {w[~bueno].mean():.3g}")

print("\n-- Por conexión (matriz 84 x 84)")
iu = np.triu_indices(84, 1)
Gu = G[iu]
for nombre, peso in [("peso", w), ("peso x longitud", w * L)]:
    C = np.zeros((84, 84))
    np.add.at(C, (a[con_region] - 1, b[con_region] - 1), peso[con_region])
    C = C + C.T
    np.fill_diagonal(C, 0)
    c = C[iu]
    p = c > 0
    print(f"[{nombre}] conexiones > 0: {p.sum()} | en GT {(p & Gu).sum()} ({pct((p & Gu).sum() / p.sum())})"
          f" | GT recuperadas {(p & Gu).sum()}/{Gu.sum()} | peso en GT {pct(c[Gu].sum() / c.sum())}"
          f" | AUC {roc_auc_score(Gu, c):.3f}")
print(f"\nguardado en {M}/hilos_{metodo.lower()}.csv")

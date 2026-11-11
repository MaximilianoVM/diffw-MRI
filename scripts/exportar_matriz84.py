"""Verifica la matriz 84 x 84 de tck2connectome, la compara con el ground truth y la guarda en Excel.

Uso (desde la raíz del proyecto):
    python scripts/exportar_matriz84.py out/connectome_commit.csv \
        out/gt.csv out/matriz_peso_commit_84x84_corregida.xlsx
"""
import sys

import numpy as np
import pandas as pd

csv, gt_csv, xlsx = sys.argv[1:4]
M = np.loadtxt(csv, delimiter=",")
assert M.shape == (84, 84), M.shape
assert np.allclose(M, M.T) and not np.diag(M).any()

iu = np.triu_indices(84, 1)
G = np.loadtxt(gt_csv, delimiter=",")[iu] > 0
w = M[iu]
p = w > 0
print(f"forma: {M.shape} | región 15 vacía: {M[14].sum() == 0}")
print(f"conexiones con peso > 0: {p.sum()}")
print(f"  que existen en el GT: {(p & G).sum()} ({(p & G).sum() / p.sum():.0%})")
print(f"  conexiones del GT recuperadas: {(p & G).sum()} de {G.sum()}")
print(f"  peso total en conexiones del GT: {w[G].sum() / w.sum():.0%}")

etiquetas = [f"R{i}" for i in range(1, 85)]
pd.DataFrame(M, index=etiquetas, columns=etiquetas).to_excel(xlsx)
print(f"guardado en {xlsx}")

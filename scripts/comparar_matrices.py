"""Compara las matrices 84 x 84 de los tres métodos (y las de los equipos) contra el ground truth.

Uso (desde la raíz del proyecto, con el entorno activado):
    python scripts/comparar_matrices.py

Todas se comparan con el mismo criterio, sobre el triángulo superior (sin diagonal):
    conexiones > 0, cuántas existen en el GT, % del peso en conexiones del GT,
    AUC por conexión (peso como puntaje de "conexión real") y Pearson con el GT
    (la comparación conectoma filtrado vs GT de comandos.txt).
Salida: imprime la tabla y la guarda en out/comparacion_matrices.csv
"""
import os

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
iu = np.triu_indices(84, 1)
G = np.loadtxt("out/gt.csv", delimiter=",")
g = G[iu] > 0

matrices = {
    "sin pesos (control)": "out/connectome_sin_pesos.csv",
    "SIFT2": "out/connectome_sift2.csv",
    "COMMIT": "out/connectome_commit.csv",
    "LiFE": "out/connectome_life.csv",
    "COMMIT2": "out/connectome_commit2.csv",
    "COMMIT x longitud": "out/connectome_commit_x_long.csv",
    "LiFE x longitud": "out/connectome_life_x_long.csv",
    "equipo SIFT2 (diagonal en 0)": "out/equipos/Connectome_SIFT2_100k_diag0.csv",
    "equipo LiFE (tracks_100k, diagonal en 0)": "out/equipos/life_100k/conn_life_full_diag0.csv",
    "equipo LiFE (su tractograma)": "docs/equipos/life_antiguo/conn_life_full.csv",
}

filas = []
for nombre, f in matrices.items():
    if not os.path.exists(f):
        print(f"(falta {f})")
        continue
    M = np.loadtxt(f, delimiter=",")
    m = M[iu]
    p = m > 0
    filas.append({
        "matriz": nombre,
        "simétrica": bool(np.allclose(M, M.T)),
        "diagonal 0": bool(not np.diag(M).any()),
        "conexiones > 0": int(p.sum()),
        "en el GT": int((p & g).sum()),
        "% en GT": round(100 * (p & g).sum() / p.sum(), 1),
        "% peso en GT": round(100 * m[g].sum() / m.sum(), 1),
        "AUC conexión": round(roc_auc_score(g, m), 3),
        "Pearson con GT": round(np.corrcoef(m, G[iu])[0, 1], 3),
    })

T = pd.DataFrame(filas)
print(f"GT: {g.sum()} conexiones reales de {len(g)} pares posibles\n")
print(T.to_string(index=False))
T.to_csv("out/comparacion_matrices.csv", index=False)
print("\nguardado en out/comparacion_matrices.csv")

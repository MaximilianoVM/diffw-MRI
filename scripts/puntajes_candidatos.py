"""Puntajes de los 100 000 hilos para comparar TRACTOGRAMAS filtrados contra el GT (último tramo del paso D).
Uso: python scripts/puntajes_candidatos.py [E_mm=5]  ->  out/modelo/puntaje_<nombre>.txt (un valor por hilo, >= 0)
Los modelos (regresión logística, entradas estandarizadas, como scripts/modelo.py) se puntúan con validación cruzada de
2 pliegues: cada hilo recibe el puntaje de un modelo que NO lo vio al entrenar (misma separación 50/50, semilla 0).
Además guarda referencias que no son modelos: mínimo y promedio de percentiles de LiFE + COMMIT2.
"""
import os, sys
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from normalizacion_ricardo import a_percentil

E = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
SAL = "out/modelo"; os.makedirs(SAL, exist_ok=True)
H = pd.read_csv("out/hausdorff/hausdorff.csv").sort_values("hilo")
y = H.hd_min.values < E; N = len(H)
MET = {"SIFT2": "out/pesos_sift2.txt", "COMMIT": "out/commit/pesos_commit.txt",
       "LiFE": "out/life/pesos_life.txt", "COMMIT2": "out/commit2/pesos_commit2.txt"}
W = {m: np.loadtxt(f, comments="#").ravel() for m, f in MET.items()}
L = np.loadtxt("out/longitudes.txt", comments="#").ravel()
PCT = {m: a_percentil(w) for m, w in W.items()}
LOG = {m: np.log(np.where(w > 0, w, w[w > 0].min() / 2)) for m, w in W.items()}
LOG["longitud"] = np.log(L)

def cruzado(cols, ent):
    X = np.column_stack([ent[c] for c in cols])
    A, B = train_test_split(np.arange(N), test_size=0.5, stratify=y, random_state=0)
    s = np.zeros(N)
    for tr, te in ((A, B), (B, A)):
        m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X[tr], y[tr])
        s[te] = m.predict_proba(X[te])[:, 1]
    return s

P = {
 "MODELO_3metodos": cruzado(["SIFT2", "LiFE", "COMMIT"], PCT),                         # los 3 pedidos, sin longitud
 "MODELO_4metodos": cruzado(["SIFT2", "LiFE", "COMMIT", "COMMIT2"], LOG),
 "MODELO_4metodos_mas_longitud": cruzado(["SIFT2", "LiFE", "COMMIT", "COMMIT2", "longitud"], LOG),
 "MIN_percentil_LiFE_COMMIT2": np.minimum(PCT["LiFE"], PCT["COMMIT2"]),
 "PROMEDIO_percentil_LiFE_COMMIT2": (PCT["LiFE"] + PCT["COMMIT2"]) / 2,
}
for n, s in P.items():
    np.savetxt(f"{SAL}/puntaje_{n}.txt", s, fmt="%.8g")
    print(n, "->", f"{SAL}/puntaje_{n}.txt", "| min %.4f max %.4f" % (s.min(), s.max()))

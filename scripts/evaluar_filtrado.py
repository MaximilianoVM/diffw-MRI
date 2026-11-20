"""Paso 10: evalúa cada método filtrado contra la etiqueta de Hausdorff.
Uso:  python scripts/evaluar_filtrado.py [E_mm=5]
Entradas: out/hausdorff/hausdorff.csv (paso 8) y los vectores de pesos de cada método que existan.
Etiqueta: verdadero = hd_min < E mm (vacío = más de 10 mm = falso).
Salidas (out/evaluacion/): barrido_eps.csv, mismo_n.csv, auc.csv, y un resumen en pantalla. Solo numpy y pandas.
"""
import os, sys
import numpy as np, pandas as pd

E = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
SAL = "out/evaluacion"
METODOS = {"SIFT2": "out/pesos_sift2.txt", "COMMIT": "out/commit/pesos_commit.txt",
           "LiFE": "out/equipos/life_100k/life_weights.txt", "COMMIT2": "out/commit2/pesos_commit2.txt"}

H = pd.read_csv("out/hausdorff/hausdorff.csv").sort_values("hilo")
assert len(H) == 100000 and (H.hilo.values == np.arange(100000)).all(), "hausdorff.csv incompleto"
y = (H.hd_min.values < E)                       # NaN < E es False
base = y.mean()
print(f"Etiqueta: hd_min < {E:g} mm -> {y.sum()} hilos verdaderos de 100 000 (tasa base {base:.1%})\n")

W = {}
for m, f in METODOS.items():
    if os.path.exists(f):
        w = np.loadtxt(f, comments="#").ravel()
        assert w.size == 100000 and np.isfinite(w).all() and (w >= 0).all(), f"{f}: vector inválido"
        W[m] = w
    else:
        print(f"(omitido {m}: no existe {f})")
if os.path.exists("out/longitudes.txt"):                      # referencia: la longitud sola
    L = np.loadtxt("out/longitudes.txt", comments="#").ravel()
    if L.size == 100000: W["longitud (ref.)"] = L


def auc(score, lab):
    """Probabilidad de que un hilo verdadero tenga más score que uno falso (rangos promedio en empates)."""
    u, inv, cnt = np.unique(score, return_inverse=True, return_counts=True)
    rango = (np.cumsum(cnt) - (cnt - 1) / 2.0)[inv]
    n1, n0 = lab.sum(), (~lab).sum()
    return (rango[lab].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def metr(keep):
    k = int(keep.sum()); tp = int((keep & y).sum())
    prec = tp / k if k else np.nan; rec = tp / y.sum()
    f1 = 2 * prec * rec / (prec + rec) if k and tp else 0.0
    return k, prec, rec, f1, prec / base if k else np.nan


os.makedirs(SAL, exist_ok=True)
# 1) barrido de epsilon sobre pesos normalizados entre el máximo (paso 9)
filas = []
for m, w in W.items():
    wn = w / w.max()
    for eps in (0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7):
        k, p, r, f1, lift = metr(wn >= eps)
        filas.append((m, eps, k, p, r, f1, lift))
B = pd.DataFrame(filas, columns=["metodo", "eps", "conservados", "precision", "recall", "F1", "lift"])
B.to_csv(f"{SAL}/barrido_eps.csv", index=False)

# 2) mismo número de hilos conservados (los n de mayor peso): comparable entre métodos
filas = []
for m, w in W.items():
    orden = np.argsort(-w, kind="stable")
    for n in (5000, 10000, 25000, 50000, 75000):
        keep = np.zeros(100000, bool); keep[orden[:n]] = True
        _, p, r, f1, lift = metr(keep)
        filas.append((m, n, p, r, f1, lift))
N = pd.DataFrame(filas, columns=["metodo", "n", "precision", "recall", "F1", "lift"])
N.to_csv(f"{SAL}/mismo_n.csv", index=False)

# 3) AUC del peso como clasificador de la etiqueta (0.5 = azar)
A = pd.DataFrame([(m, auc(w, y)) for m, w in W.items()], columns=["metodo", "AUC"])
A.to_csv(f"{SAL}/auc.csv", index=False)

pd.options.display.float_format = "{:.3f}".format
print("AUC del peso vs etiqueta (0.5 = azar; <0.5 = los pesos altos son más falsos):\n", A.to_string(index=False))
print("\nMismo número de hilos conservados (los n de mayor peso). precision = % verdaderos entre los conservados:")
print(N.pivot(index="n", columns="metodo", values="precision").to_string())
print("\nBarrido de epsilon (peso/máx >= eps): conservados | precision | recall")
for m in W:
    print(f"\n{m}"); print(B[B.metodo == m].drop(columns="metodo").to_string(index=False))
print(f"\nTasa base (conservar todo) = {base:.3f}. Un método sirve si su precision supera claramente la tasa base.")

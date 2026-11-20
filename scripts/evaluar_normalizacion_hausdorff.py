"""Paso 3.1 de docs/siguiente_mac_normalizacion.md: normalización de Ricardo evaluada contra la etiqueta de Hausdorff.

Uso (desde la raíz del proyecto):  python scripts/evaluar_normalizacion_hausdorff.py [E_mm=5 ...]
    p. ej.  python scripts/evaluar_normalizacion_hausdorff.py 5 3 7      (el primero es el principal)

Etiqueta: verdadero = hd_min < E mm en out/hausdorff/hausdorff.csv (vacío = más de 10 mm = falso).
Métodos: SIFT2, COMMIT, LiFE y COMMIT2 (contrato del repo: 100 000 pesos >= 0, orden de data/tracks_100k.tck).
Normalizaciones (las de scripts/normalizacion_ricardo.py, mismas funciones):
    global          percentil contra todos los hilos (especificación de Ricardo)
    por longitud    percentil dentro de 10 deciles de longitud (--por-longitud 10)
    x longitud      percentil de peso × longitud (--x-longitud)
    corte           SIFT2 (sin ceros) pone en 0 la misma fracción de menor peso que COMMIT (--corte)
Para cada normalización: cada método solo, promedio de los 4, promedio de los 3 pedidos (SIFT2+COMMIT+LiFE),
promedio LiFE+COMMIT2, y votos «≥ 2 de 3» / «≥ 2 de 4» (percentil > 0.5 en al menos 2 métodos).
Referencias en todas las tablas: longitud sola y COMMIT2 solo (peso crudo).
Métricas: AUC (0.5 = azar) y, conservando los n = 10 000, 25 000, 50 000 hilos de mayor puntaje,
precisión (% verdaderos entre los conservados), recall y lift (precisión / tasa base).
Los votos son 0/1: se reporta su propio n conservado en lugar de los tres n.
Salidas: out/evaluacion/normalizacion_hausdorff_E<E>.csv (todas las filas) y auc_normalizacion_por_eps.csv.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from normalizacion_ricardo import a_percentil, a_percentil_por_longitud  # noqa: E402

EPS = [float(x) for x in sys.argv[1:]] or [5.0]
SAL = "out/evaluacion"
NS = (10000, 25000, 50000)
METODOS = {"SIFT2": "out/pesos_sift2.txt", "COMMIT": "out/commit/pesos_commit.txt",
           "LiFE": "out/life/pesos_life.txt", "COMMIT2": "out/commit2/pesos_commit2.txt"}
COMBOS = {"promedio 4": ["SIFT2", "COMMIT", "LiFE", "COMMIT2"],
          "promedio SIFT2+COMMIT+LiFE": ["SIFT2", "COMMIT", "LiFE"],
          "promedio LiFE+COMMIT2": ["LiFE", "COMMIT2"]}
VOTOS = {"voto ≥2 de 3 (S+C+L)": ["SIFT2", "COMMIT", "LiFE"], "voto ≥2 de 4": ["SIFT2", "COMMIT", "LiFE", "COMMIT2"]}

H = pd.read_csv("out/hausdorff/hausdorff.csv").sort_values("hilo")
assert len(H) == 100000 and (H.hilo.values == np.arange(100000)).all(), "hausdorff.csv incompleto"
N = len(H)
W = {}
for m, f in METODOS.items():
    w = np.loadtxt(f, comments="#").ravel()
    assert w.size == N and np.isfinite(w).all() and (w >= 0).all(), f"{f}: vector inválido"
    W[m] = w
L = np.loadtxt("out/longitudes.txt", comments="#").ravel()
assert L.size == N
desempate = np.random.default_rng(0).random(N)      # empates (p. ej. los ceros) en orden aleatorio fijo


def auc(score, lab):
    """Probabilidad de que un hilo verdadero tenga más puntaje que uno falso (rangos promedio en empates)."""
    _, inv, cnt = np.unique(score, return_inverse=True, return_counts=True)
    rango = (np.cumsum(cnt) - (cnt - 1) / 2.0)[inv]
    n1, n0 = lab.sum(), (~lab).sum()
    return (rango[lab].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def metr(keep, y):
    k, tp = int(keep.sum()), int((keep & y).sum())
    p = tp / k if k else np.nan
    return k, p, tp / y.sum(), p / y.mean()


def corte(pesos):
    frac = (pesos["COMMIT"] == 0).mean()
    out = {}
    for m, w in pesos.items():
        if not (w == 0).any():
            w = w.copy()
            w[w <= np.quantile(w, frac)] = 0
        out[m] = w
    return out


NORMS = {
    "global": {m: a_percentil(w) for m, w in W.items()},
    "por longitud": {m: a_percentil_por_longitud(w, L, 10) for m, w in W.items()},
    "x longitud": {m: a_percentil(w * L) for m, w in W.items()},
    "corte": {m: a_percentil(w) for m, w in corte(W).items()},
}


def puntajes():
    """(normalización, nombre, puntaje, es_binario) para todas las variantes."""
    yield "referencia", "longitud sola", L, False
    yield "referencia", "COMMIT2 solo (peso crudo)", W["COMMIT2"], False
    for norm, P in NORMS.items():
        for m in W:
            if norm == "corte" and (W[m] == 0).any():
                continue                                    # el corte solo cambia a SIFT2
            yield norm, m, P[m], False
        for c, ms in COMBOS.items():
            yield norm, c, np.mean([P[m] for m in ms], axis=0), False
        for v, ms in VOTOS.items():
            yield norm, v, (np.vstack([P[m] > 0.5 for m in ms]).sum(axis=0) >= 2).astype(float), True
    # otras formas de juntar LiFE y COMMIT2 (percentil global)
    a, b = NORMS["global"]["LiFE"], NORMS["global"]["COMMIT2"]
    yield "LiFE+COMMIT2", "mínimo de percentiles (los dos altos)", np.minimum(a, b), False
    yield "LiFE+COMMIT2", "máximo de percentiles (alguno alto)", np.maximum(a, b), False
    yield "LiFE+COMMIT2", "producto de percentiles", a * b, False
    yield "LiFE+COMMIT2", "producto de pesos crudos", W["LiFE"] * W["COMMIT2"], False
    yield "LiFE+COMMIT2", "voto intersección (peso > 0 en los dos)", ((W["LiFE"] > 0) & (W["COMMIT2"] > 0)) * 1.0, True
    yield "LiFE+COMMIT2", "voto unión (peso > 0 en alguno)", ((W["LiFE"] > 0) | (W["COMMIT2"] > 0)) * 1.0, True
    yield "LiFE+COMMIT2", "voto los dos percentiles > 0.5", ((a > 0.5) & (b > 0.5)) * 1.0, True


def evaluar(E):
    y = H.hd_min.values < E
    filas = []
    for norm, nombre, s, binario in puntajes():
        fila = {"normalizacion": norm, "puntaje": nombre, "AUC": auc(s, y)}
        if binario:
            k, p, r, lift = metr(s > 0, y)
            fila.update({"n_voto": k, "precision_voto": p, "recall_voto": r, "lift_voto": lift})
        else:
            orden = np.lexsort((desempate, -s))
            for n in NS:
                keep = np.zeros(N, bool)
                keep[orden[:n]] = True
                _, p, r, lift = metr(keep, y)
                fila.update({f"precision_{n // 1000}k": p, f"recall_{n // 1000}k": r, f"lift_{n // 1000}k": lift})
        filas.append(fila)
    return pd.DataFrame(filas), y


os.makedirs(SAL, exist_ok=True)
pd.set_option("display.width", 250)
pd.options.display.float_format = "{:.3f}".format
aucs = []
for i, E in enumerate(EPS):
    T, y = evaluar(E)
    T.to_csv(f"{SAL}/normalizacion_hausdorff_E{E:g}.csv", index=False)
    aucs.append(T[["normalizacion", "puntaje", "AUC"]].rename(columns={"AUC": f"AUC_{E:g}mm"}))
    if i == 0:
        print(f"Etiqueta: hd_min < {E:g} mm -> {y.sum()} verdaderos de {N} (tasa base {y.mean():.1%})\n")
        cols = ["normalizacion", "puntaje", "AUC"] + [f"{c}_{n // 1000}k" for n in NS for c in ("precision", "lift")]
        print(T[~T.puntaje.str.startswith("voto")][cols].to_string(index=False))
        print("\nVotos (percentil > 0.5 en al menos 2 métodos):")
        print(T[T.puntaje.str.startswith("voto")][["normalizacion", "puntaje", "AUC", "n_voto", "precision_voto",
                                                    "recall_voto", "lift_voto"]].to_string(index=False))
A = aucs[0]
for x in aucs[1:]:
    A = A.merge(x, on=["normalizacion", "puntaje"])
A.to_csv(f"{SAL}/auc_normalizacion_por_eps.csv", index=False)
if len(EPS) > 1:
    print("\nAUC con distintos ε de Hausdorff:")
    print(A[~A.puntaje.str.startswith("voto")].to_string(index=False))
print(f"\nguardado en {SAL}/")

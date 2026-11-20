"""Paso 11 (docs/siguiente_mac_normalizacion.md, 3.2): modelo (pesos de los métodos [+ longitud]) -> etiqueta Hausdorff.

Uso (desde la raíz del proyecto):  python scripts/modelo.py [E_mm=5 ...]      p. ej.  python scripts/modelo.py 5 3 7

Etiqueta: verdadero = hd_min < E mm en out/hausdorff/hausdorff.csv (vacío = falso).
Modelo: regresión logística (sklearn) con las entradas estandarizadas, así los coeficientes se comparan entre sí
(coeficiente = cambio en el log-momio por una desviación estándar de la entrada).
Separación: 50 % entrenamiento / 50 % prueba, estratificada por etiqueta, semilla 0. Se ajusta SOLO con entrenamiento;
todas las métricas son de la mitad de prueba (50 000 hilos).
Entradas: percentil global de cada método (normalización de Ricardo) o log del peso (ceros -> la mitad del mínimo > 0).
Variantes: los 3 métodos pedidos (SIFT2, LiFE, COMMIT), + COMMIT2, solo LiFE + COMMIT2; cada una con y sin longitud.
Referencias, evaluadas en la misma mitad de prueba: longitud sola, COMMIT2 solo, LiFE solo, y los promedios de Ricardo
(percentil global) de los 4 métodos, de los 3 pedidos y de LiFE + COMMIT2.
Métricas: AUC y precisión / lift al conservar el 10 %, 25 % y 50 % de mayor puntaje (5 000, 12 500 y 25 000 hilos de
prueba; equivalen a 10 000, 25 000 y 50 000 de los 100 000).
Salidas en out/modelo/: resultados_E<E>.csv, coeficientes_E<E>.csv, auc_por_eps.csv.
"""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from normalizacion_ricardo import a_percentil  # noqa: E402

EPS = [float(x) for x in sys.argv[1:]] or [5.0]
SAL = "out/modelo"
FRACS = (0.10, 0.25, 0.50)
METODOS = {"SIFT2": "out/pesos_sift2.txt", "COMMIT": "out/commit/pesos_commit.txt",
           "LiFE": "out/life/pesos_life.txt", "COMMIT2": "out/commit2/pesos_commit2.txt"}
CONJUNTOS = {"SIFT2+LiFE+COMMIT": ["SIFT2", "LiFE", "COMMIT"],
             "SIFT2+LiFE+COMMIT+COMMIT2": ["SIFT2", "LiFE", "COMMIT", "COMMIT2"],
             "LiFE+COMMIT2": ["LiFE", "COMMIT2"]}

H = pd.read_csv("out/hausdorff/hausdorff.csv").sort_values("hilo")
assert len(H) == 100000 and (H.hilo.values == np.arange(100000)).all(), "hausdorff.csv incompleto"
N = len(H)
W = {}
for m, f in METODOS.items():
    w = np.loadtxt(f, comments="#").ravel()
    assert w.size == N and np.isfinite(w).all() and (w >= 0).all(), f"{f}: vector inválido"
    W[m] = w
L = np.loadtxt("out/longitudes.txt", comments="#").ravel()
PCT = {m: a_percentil(w) for m, w in W.items()}
LOG = {m: np.log(np.where(w > 0, w, w[w > 0].min() / 2)) for m, w in W.items()}
ENTRADAS = {"percentil": PCT, "log peso": LOG}
desempate = np.random.default_rng(0).random(N)


def metricas(s, y):
    fila = {"AUC": roc_auc_score(y, s)}
    orden = np.lexsort((desempate[:len(s)], -s))
    for f in FRACS:
        k = int(round(f * len(s)))
        p = y[orden[:k]].mean()
        fila[f"precision_{int(f * 100)}%"] = p
        fila[f"lift_{int(f * 100)}%"] = p / y.mean()
    return fila


def evaluar(E):
    y = H.hd_min.values < E
    ent, pru = train_test_split(np.arange(N), test_size=0.5, stratify=y, random_state=0)
    filas, coefs = [], []
    refs = {"longitud sola": L, "COMMIT2 solo": W["COMMIT2"], "LiFE solo": W["LiFE"],
            "promedio Ricardo 4 métodos": np.mean([PCT[m] for m in W], axis=0),
            "promedio Ricardo SIFT2+COMMIT+LiFE": np.mean([PCT[m] for m in CONJUNTOS["SIFT2+LiFE+COMMIT"]], axis=0),
            "promedio Ricardo LiFE+COMMIT2": (PCT["LiFE"] + PCT["COMMIT2"]) / 2}
    for nombre, s in refs.items():
        filas.append({"tipo": "referencia", "modelo": nombre, "entradas": "", **metricas(s[pru], y[pru])})
    for tipo_ent, X0 in ENTRADAS.items():
        for conj, ms in CONJUNTOS.items():
            for con_L in (False, True):
                cols = ms + (["longitud"] if con_L else [])
                X = np.column_stack([X0[m] for m in ms] + ([np.log(L)] if con_L else []))
                mod = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
                mod.fit(X[ent], y[ent])
                s = mod.predict_proba(X[pru])[:, 1]
                nombre = f"logística {conj}" + (" + longitud" if con_L else "")
                filas.append({"tipo": "modelo", "modelo": nombre, "entradas": tipo_ent,
                              "AUC_entrenamiento": roc_auc_score(y[ent], mod.predict_proba(X[ent])[:, 1]),
                              **metricas(s, y[pru])})
                lr = mod[-1]
                coefs.append({"modelo": nombre, "entradas": tipo_ent, "intercepto": lr.intercept_[0],
                              **dict(zip(cols, lr.coef_[0]))})
    return pd.DataFrame(filas), pd.DataFrame(coefs), y, pru


os.makedirs(SAL, exist_ok=True)
pd.set_option("display.width", 250)
pd.options.display.float_format = "{:.3f}".format
aucs = []
for i, E in enumerate(EPS):
    R, C, y, pru = evaluar(E)
    R.to_csv(f"{SAL}/resultados_E{E:g}.csv", index=False)
    C.to_csv(f"{SAL}/coeficientes_E{E:g}.csv", index=False)
    aucs.append(R[["tipo", "modelo", "entradas", "AUC"]].rename(columns={"AUC": f"AUC_{E:g}mm"}))
    if i == 0:
        print(f"Etiqueta: hd_min < {E:g} mm | prueba: {len(pru)} hilos, tasa base {y[pru].mean():.1%}\n")
        cols = ["tipo", "modelo", "entradas", "AUC"] + [f"{c}_{int(f * 100)}%" for f in FRACS for c in ("precision", "lift")]
        print(R[cols].to_string(index=False))
        print("\nAUC entrenamiento vs prueba (si son parecidos, no hay sobreajuste):")
        print(R[R.tipo == "modelo"][["modelo", "entradas", "AUC_entrenamiento", "AUC"]].to_string(index=False))
        print("\nCoeficientes (entradas estandarizadas; negativo = a más peso, menos probable que sea verdadero):")
        print(C.to_string(index=False))
A = aucs[0]
for x in aucs[1:]:
    A = A.merge(x, on=["tipo", "modelo", "entradas"])
A.to_csv(f"{SAL}/auc_por_eps.csv", index=False)
if len(EPS) > 1:
    print("\nAUC en prueba con distintos ε de Hausdorff:")
    print(A.to_string(index=False))
print(f"\nguardado en {SAL}/")

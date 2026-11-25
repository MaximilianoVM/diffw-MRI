"""Gradient boosting ajustado para puntuar los hilos del tractograma.

Integrado al repo (2026-11-25): por omisión lee out/modelos/tabla_hilos.csv y escribe en out/modelos/; correr desde la raíz.
Fuera del repo: --tabla tabla_hilos.csv --salida .

Uso (desde la raíz del proyecto):
    pip install pandas scikit-learn numpy
    python scripts/modelo_boosting_ajustado.py --longitud     # escribe puntaje_boosting_ajustado_long.txt
    python scripts/modelo_boosting_ajustado.py                # escribe puntaje_boosting_ajustado.txt
    python scripts/modelo_boosting_ajustado.py --rapido       # sin busqueda de hiperparametros

Reglas:
  - NO se usan hd_min_mm ni etiqueta_5mm como entrada.
  - Se entrena con una mitad y se puntua la otra (intercambio de mitades): cada hilo
    queda puntuado por un modelo que no lo vio al entrenar.
  - Los hiperparametros se eligen DENTRO de la mitad de entrenamiento (con una validacion
    del 20 %), asi que la mitad que se puntua nunca interviene en esa eleccion.
  - El numero de arboles lo decide la parada temprana: se agregan arboles hasta que la
    pérdida en una validacion interna deja de mejorar.
"""
import argparse
import warnings
from itertools import product

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")

ap = argparse.ArgumentParser()
ap.add_argument("--longitud", action="store_true", help="incluir longitud_mm como entrada")
ap.add_argument("--rapido", action="store_true", help="usar hiperparametros fijos, sin busqueda")
ap.add_argument("--tabla", default="out/modelos/tabla_hilos.csv")
ap.add_argument("--salida", default="out/modelos", help="carpeta donde se escribe el puntaje")
args = ap.parse_args()

T = pd.read_csv(args.tabla)
y = T["etiqueta_5mm"].values

PESOS = ["SIFT2", "COMMIT", "LiFE", "COMMIT2"]
CON_CEROS = ["COMMIT", "LiFE", "COMMIT2"]   # los metodos que pueden asignar peso 0


def construir_entradas(T, con_longitud):
    # log de cada peso (el 1e-6 evita log(0))
    cols = [np.log(T[c].values + 1e-6) for c in PESOS]
    # indicador: 1 si el metodo conservo el hilo (peso > 0)
    cols += [(T[c].values > 0).astype(float) for c in CON_CEROS]
    # cuantos de esos metodos conservaron el hilo
    cols.append(sum((T[c].values > 0).astype(float) for c in CON_CEROS))
    if con_longitud:
        cols.append(T["longitud_mm"].values)
    return np.column_stack(cols)


X = construir_entradas(T, args.longitud)

# Hiperparametros que se prueban (learning_rate: cuanto aporta cada arbol;
# max_depth: profundidad maxima de cada arbol)
REJILLA = {"learning_rate": [0.03, 0.05, 0.1], "max_depth": [3, 4, 6]}
POR_DEFECTO = {"learning_rate": 0.05, "max_depth": 4}


def nuevo_modelo(lr, prof):
    # max_iter alto: la parada temprana decide cuantos arboles se usan realmente
    return HistGradientBoostingClassifier(
        learning_rate=lr, max_depth=prof, max_iter=1000, min_samples_leaf=50,
        l2_regularization=1.0, early_stopping=True, validation_fraction=0.15,
        n_iter_no_change=20, random_state=0)


def buscar_hiperparametros(X_tr, y_tr):
    """Elige los hiperparametros con 80 % / 20 % dentro de la mitad de entrenamiento."""
    X_a, X_v, y_a, y_v = train_test_split(X_tr, y_tr, test_size=0.2, stratify=y_tr, random_state=0)
    mejor_auc, mejores = -1, None
    for lr, prof in product(REJILLA["learning_rate"], REJILLA["max_depth"]):
        m = nuevo_modelo(lr, prof).fit(X_a, y_a)
        auc = roc_auc_score(y_v, m.predict_proba(X_v)[:, 1])
        if auc > mejor_auc:
            mejor_auc, mejores = auc, {"learning_rate": lr, "max_depth": prof}
    return mejores


def entrenar_y_puntuar(X_tr, y_tr, X_te):
    params = POR_DEFECTO if args.rapido else buscar_hiperparametros(X_tr, y_tr)
    modelo = nuevo_modelo(params["learning_rate"], params["max_depth"]).fit(X_tr, y_tr)
    return modelo.predict_proba(X_te)[:, 1], params, modelo.n_iter_


puntaje = np.zeros(len(T))
for a, b in (("entrenamiento", "prueba"), ("prueba", "entrenamiento")):
    tr = (T["conjunto"] == a).values
    te = (T["conjunto"] == b).values
    puntaje[te], params, n_arboles = entrenar_y_puntuar(X[tr], y[tr], X[te])
    print(f"entrenado con {a:13s} -> puntua {b:13s} | hiperparametros: {params} | arboles: {n_arboles}",
          flush=True)

pru = (T["conjunto"] == "prueba").values
print(f"\nAUC en la mitad de prueba: {roc_auc_score(y[pru], puntaje[pru]):.3f} "
      f"| longitud: {'si' if args.longitud else 'no'}")
orden = np.argsort(-puntaje)
for n in (10000, 25000, 50000):
    print(f"  conservando {n:>6} hilos: {100 * y[orden[:n]].mean():.1f} % verdaderos")

salida = f"{args.salida}/" + ("puntaje_boosting_ajustado_long.txt" if args.longitud else "puntaje_boosting_ajustado.txt")
np.savetxt(salida, puntaje, fmt="%.8g")
print("guardado", salida)

"""Crea la tabla única para quienes aplican modelos: una fila por hilo, con los pesos de cada método, la longitud,
la etiqueta de Hausdorff y la mitad (entrenamiento/prueba) en la que se evalúa.
Uso (raíz del proyecto):  python scripts/crear_tabla_modelos.py [E_mm=5]  ->  out/modelos/tabla_hilos.csv
La mitad es la misma que usa scripts/modelo.py (50/50 estratificada, semilla 0), para que todos comparen sobre los mismos hilos.
"""
import os, sys
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split

os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
E = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
H = pd.read_csv("out/hausdorff/hausdorff.csv").sort_values("hilo")
N = len(H); assert N == 100000 and (H.hilo.values == np.arange(N)).all()
T = pd.DataFrame({"hilo": np.arange(N), "longitud_mm": np.loadtxt("out/longitudes.txt", comments="#").ravel()})
LIFE = "out/life/pesos_life.txt" if os.path.exists("out/life/pesos_life.txt") else "out/equipos/life_100k/life_weights.txt"
for m, f in {"SIFT2": "out/pesos_sift2.txt", "COMMIT": "out/commit/pesos_commit.txt",
             "LiFE": LIFE, "COMMIT2": "out/commit2/pesos_commit2.txt"}.items():
    w = np.loadtxt(f, comments="#").ravel(); assert w.size == N and np.isfinite(w).all() and (w >= 0).all(), f
    T[m] = w
T["hd_min_mm"] = H.hd_min.values                                  # vacío = más de 10 mm
T[f"etiqueta_{E:g}mm"] = (H.hd_min.values < E).astype(int)       # 1 = el hilo corresponde al GT
y = T[f"etiqueta_{E:g}mm"].values
ent, pru = train_test_split(np.arange(N), test_size=0.5, stratify=y, random_state=0)
T["conjunto"] = "entrenamiento"; T.loc[pru, "conjunto"] = "prueba"
os.makedirs("out/modelos", exist_ok=True)
T.to_csv("out/modelos/tabla_hilos.csv", index=False, float_format="%.8g")
print(T.shape, "| verdaderos:", y.sum(), f"({y.mean():.1%})", "| prueba:", len(pru))
print(T.head(3).to_string())

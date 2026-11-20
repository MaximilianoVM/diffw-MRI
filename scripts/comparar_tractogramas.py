"""Paso 12: compara contra el GT, haz por haz, el tractograma que deja cada puntaje conservando el MISMO número de hilos.

Uso (desde la raíz del proyecto):  python scripts/comparar_tractogramas.py [E_mm=5]
Etiqueta: verdadero = hd_min < E mm (out/hausdorff/hausdorff.csv); el haz de cada hilo verdadero es el del MDF más
cercano (igual que normalizacion_ricardo.py --etiqueta hausdorff; usa la caché out/normalizacion/asignacion_mdf_*.npz).
Para cada puntaje y cada n (10 000, 25 000, 50 000) se conservan los n hilos de mayor puntaje (empates al azar fijo) y se
mide: % de falsos, haces detectados (de 21), cobertura, desborde y Dice promedio (vóxeles), y MDF simétrico promedio.
Puntajes: cada método solo, la longitud sola, promedios de Ricardo, el mínimo de percentiles LiFE+COMMIT2, mezclas de
longitud + COMMIT2 + LiFE (promedio y mínimo de percentiles, sin GT) y regresiones logísticas. Las logísticas se
evalúan con validación cruzada de 2 partes (se entrena en una mitad y se puntúa la otra, y al revés): ningún hilo se
puntúa con un modelo que lo vio. También se reportan AUC y precisión de cada puntaje sobre los 100 000 hilos.
Salidas en out/comparacion/: resumen.csv (una fila por puntaje y n), por_haz.csv, auc_precision.csv.
"""
import glob
import os
import sys

import nibabel as nib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from normalizacion_ricardo import a_percentil, a_voxeles, mascara, metricas_haz  # noqa: E402

E = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
SAL = "out/comparacion"
NS = (10000, 25000, 50000)
CACHE = "out/normalizacion/asignacion_mdf_ngt1000_s0.npz"
METODOS = {"SIFT2": "out/pesos_sift2.txt", "COMMIT": "out/commit/pesos_commit.txt",
           "LiFE": "out/life/pesos_life.txt", "COMMIT2": "out/commit2/pesos_commit2.txt"}

from dipy.tracking.distances import bundles_distances_mdf  # noqa: E402
from dipy.tracking.streamline import set_number_of_points  # noqa: E402

# ---- entradas
hilos = list(nib.streamlines.load("data/tracks_100k.tck").streamlines)
N = len(hilos)
H = pd.read_csv("out/hausdorff/hausdorff.csv").sort_values("hilo")
assert len(H) == N and (H.hilo.values == np.arange(N)).all()
y = H.hd_min.values < E
W = {m: np.loadtxt(f, comments="#").ravel() for m, f in METODOS.items()}
assert all(w.size == N for w in W.values())
L = np.loadtxt("out/longitudes.txt", comments="#").ravel()
P = {m: a_percentil(w) for m, w in W.items()}
P["longitud"] = a_percentil(L)
LOG = {m: np.log(np.where(w > 0, w, w[w > 0].min() / 2)) for m, w in W.items()}
LOG["longitud"] = np.log(L)


def logistica_cruzada(cols):
    """Puntaje fuera de muestra para los N hilos (2 partes estratificadas, semilla 0) y coeficientes promedio."""
    X = np.column_stack([LOG[c] for c in cols])
    s, coef = np.zeros(N), []
    for ent, pru in StratifiedKFold(2, shuffle=True, random_state=0).split(X, y):
        mod = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X[ent], y[ent])
        s[pru] = mod.predict_proba(X[pru])[:, 1]
        coef.append(mod[-1].coef_[0])
    return s, dict(zip(cols, np.mean(coef, axis=0).round(3)))


coefs = {}
PUNTAJES = {
    "SIFT2 solo": W["SIFT2"], "COMMIT solo": W["COMMIT"], "LiFE solo": W["LiFE"], "COMMIT2 solo": W["COMMIT2"],
    "longitud sola": L,
    "promedio Ricardo 4 métodos": np.mean([P[m] for m in METODOS], axis=0),
    "promedio LiFE+COMMIT2": (P["LiFE"] + P["COMMIT2"]) / 2,
    "mínimo LiFE+COMMIT2": np.minimum(P["LiFE"], P["COMMIT2"]),
    "promedio longitud+LiFE+COMMIT2": (P["longitud"] + P["LiFE"] + P["COMMIT2"]) / 3,
    "mínimo longitud+LiFE+COMMIT2": np.minimum.reduce([P["longitud"], P["LiFE"], P["COMMIT2"]]),
}
for nombre, cols in {"logística 4 métodos + longitud": ["SIFT2", "COMMIT", "LiFE", "COMMIT2", "longitud"],
                     "logística LiFE+COMMIT2": ["LiFE", "COMMIT2"],
                     "logística longitud+LiFE+COMMIT2": ["longitud", "LiFE", "COMMIT2"]}.items():
    PUNTAJES[nombre], coefs[nombre] = logistica_cruzada(cols)

# ---- GT por haz y asignación (misma lógica que normalizacion_ricardo.py --etiqueta hausdorff)
img = nib.load("data/ISMRM_2023_b3000.nii.gz")
forma, inv = img.shape[:3], np.linalg.inv(img.affine)
haces = sorted(f for f in glob.glob("data/GT/*.tck") if not f.endswith("all_tracks.tck"))
nombres = [os.path.basename(f)[:-4] for f in haces]
rng = np.random.default_rng(0)
gt_completo, gt_sub = [], []
for f in haces:                                      # misma submuestra que normalizacion_ricardo.py (semilla 0)
    s = list(nib.streamlines.load(f).streamlines)
    gt_completo.append(s)
    idx = rng.choice(len(s), size=min(1000, len(s)), replace=False)
    gt_sub.append(set_number_of_points([s[i] for i in idx], 20))
dmin = np.load(CACHE)["dmin"]
assert dmin.shape == (N, len(haces)), "caché MDF con otra forma: corre antes normalizacion_ricardo.py"
haz = dmin.argmin(axis=1)
dist = dmin[np.arange(N), haz]
haz_etq = np.where(y, haz, -1)
hilos20 = set_number_of_points(hilos, 20)
vox_hilo = a_voxeles(hilos, inv, forma)
npts = np.array([len(v) for v in vox_hilo])
vox_todos = np.concatenate(vox_hilo)
G = [mascara(np.concatenate(a_voxeles(s, inv, forma)), forma) for s in gt_completo]
print(f"etiqueta Hausdorff < {E:g} mm: {y.sum()} verdaderos ({y.mean():.1%}); {len(haces)} haces")


def evaluar(nombre, n, keep):
    filas = []
    for b, hb in enumerate(nombres):
        sel = keep & (haz_etq == b)
        M = mascara(vox_todos[np.repeat(sel, npts)], forma)
        fila = {"puntaje": nombre, "n": n, "conducto": hb, "hilos": int(sel.sum()), "detectado": bool(sel.any()),
                **metricas_haz(M, G[b])}
        if sel.any():
            elegidos = [hilos20[i] for i in np.flatnonzero(sel)]
            b_a = np.mean([bundles_distances_mdf(gt_sub[b][j:j + 200], elegidos).min(axis=1).mean()
                           for j in range(0, len(gt_sub[b]), 200)])
            fila["mdf_simetrico"] = (dist[sel].mean() + b_a) / 2
        else:
            fila["mdf_simetrico"] = np.nan
        filas.append(fila)
    df = pd.DataFrame(filas)
    return df, {"puntaje": nombre, "n": n, "pct_falsos": 100 * (keep & ~y).sum() / keep.sum(),
                "haces_detectados": int(df.detectado.sum()), "cobertura": df.cobertura.mean(),
                "desborde": df.desborde.mean(), "dice": df.dice.mean(), "mdf_simetrico": df.mdf_simetrico.mean()}


desempate = np.random.default_rng(0).random(N)
os.makedirs(SAL, exist_ok=True)
resumen, por_haz, ap = [], [], []
_, r = evaluar("sin filtrar", N, np.ones(N, bool))
resumen.append(r)
for nombre, s in PUNTAJES.items():
    orden = np.lexsort((desempate, -s))
    fila_ap = {"puntaje": nombre, "AUC": roc_auc_score(y, s)}
    for n in NS:
        keep = np.zeros(N, bool)
        keep[orden[:n]] = True
        df, r = evaluar(nombre, n, keep)
        resumen.append(r)
        por_haz.append(df)
        fila_ap[f"precision_{n // 1000}k"] = y[keep].mean()
    ap.append(fila_ap)
    print(f"  {nombre}: listo")
R, A = pd.DataFrame(resumen), pd.DataFrame(ap)
R.to_csv(f"{SAL}/resumen.csv", index=False)
pd.concat(por_haz).to_csv(f"{SAL}/por_haz.csv", index=False)
A.to_csv(f"{SAL}/auc_precision.csv", index=False)
pd.Series({k: str(v) for k, v in coefs.items()}, name="coeficientes").to_csv(f"{SAL}/coeficientes_logistica.csv")

pd.set_option("display.width", 250)
pd.options.display.float_format = "{:.3f}".format
print("\nAUC y precisión sobre los 100 000 hilos (logísticas: validación cruzada de 2 partes):")
print(A.to_string(index=False))
print("\nCoeficientes (log del peso, entradas estandarizadas, promedio de las 2 partes):")
for k, v in coefs.items():
    print(f"  {k}: {v}")
for n in NS:
    print(f"\n--- conservando n = {n} hilos ---")
    print(R[R.n.isin([n, N])].sort_values("pct_falsos").to_string(index=False))
print(f"\nguardado en {SAL}/")

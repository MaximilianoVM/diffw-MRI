"""MLP ajustado (red neuronal) para puntuar los hilos del tractograma.

RECONSTRUCCION: este script se escribio a partir de la descripcion de nota_modelo_mlp_ajustado.md
(docs/resultados/), porque el original del grupo de modelos no vino en la entrega. Sigue lo que la
nota especifica; lo que la nota no dice se marca abajo como SUPUESTO. Las cifras pueden diferir
ligeramente de las de la nota (AUC 0.727 sin longitud, 0.799 con longitud).

Uso (desde la raiz del proyecto):
    pip install torch pandas scikit-learn numpy
    python scripts/modelo_mlp_ajustado.py --longitud     # escribe puntaje_mlp_ajustado_long.txt
    python scripts/modelo_mlp_ajustado.py                # escribe puntaje_mlp_ajustado.txt
    python scripts/modelo_mlp_ajustado.py --semillas 1 --epocas 5   # prueba rapida
Por omision lee out/modelos/tabla_hilos.csv y escribe en out/modelos/.

Segun la nota:
  - Entradas: log(peso) de SIFT2, COMMIT, LiFE y COMMIT2; indicadores "peso > 0" de COMMIT, LiFE y
    COMMIT2; rango percentil de cada peso (QuantileTransformer ajustado solo con la mitad de
    entrenamiento); numero de metodos que conservaron el hilo; y, con --longitud, log(longitud) y
    las interacciones log(peso) x log(longitud).
  - Red 128-64-32 con BatchNorm y dropout (0.15 / 0.10), AdamW con recocido coseno, lotes de 1024,
    hasta 200 epocas con paciencia 15, validacion estratificada del 15 %, promedio de 5 semillas.
  - NO se usan hd_min_mm ni etiqueta_5mm como entrada.
  - Intercambio de mitades: cada hilo se puntua con un modelo entrenado en la otra mitad.
  - AUC en la mitad prueba; precision sobre los 100 000 hilos.
SUPUESTOS (la nota no los especifica):
  - dropout 0.15 tras la primera capa oculta y 0.10 tras la segunda y la tercera;
  - tasa de aprendizaje 1e-3, weight_decay 1e-4, ReLU;
  - la paciencia se mide sobre la perdida de validacion y se conservan los pesos de la mejor epoca;
  - las entradas se estandarizan con StandardScaler ajustado en la mitad de entrenamiento.
"""
import argparse

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import QuantileTransformer, StandardScaler
from torch import nn

ap = argparse.ArgumentParser()
ap.add_argument("--longitud", action="store_true", help="incluir log(longitud) e interacciones")
ap.add_argument("--semillas", type=int, default=5, help="redes que se promedian por mitad")
ap.add_argument("--epocas", type=int, default=200, help="maximo de epocas")
ap.add_argument("--tabla", default="out/modelos/tabla_hilos.csv")
ap.add_argument("--salida", default="out/modelos", help="carpeta donde se escribe el puntaje")
args = ap.parse_args()

T = pd.read_csv(args.tabla)
y = T["etiqueta_5mm"].values.astype(np.float32)

PESOS = ["SIFT2", "COMMIT", "LiFE", "COMMIT2"]
CON_CEROS = ["COMMIT", "LiFE", "COMMIT2"]   # los metodos que pueden asignar peso 0


def entradas_fijas(T, con_longitud):
    """Entradas que no se ajustan con datos (no pueden filtrar informacion entre mitades)."""
    logp = [np.log(T[c].values + 1e-6) for c in PESOS]
    cols = list(logp)
    cols += [(T[c].values > 0).astype(float) for c in CON_CEROS]
    cols.append(sum((T[c].values > 0).astype(float) for c in CON_CEROS))
    if con_longitud:
        logl = np.log(T["longitud_mm"].values)
        cols.append(logl)
        cols += [lp * logl for lp in logp]          # interacciones log(peso) x log(longitud)
    return np.column_stack(cols)


X_fijas = entradas_fijas(T, args.longitud)
W = T[PESOS].values


def preparar(tr, te):
    """Rango percentil y estandarizacion ajustados SOLO con la mitad de entrenamiento."""
    qt = QuantileTransformer(n_quantiles=1000, output_distribution="uniform", random_state=0)
    pct_tr, pct_te = qt.fit_transform(W[tr]), qt.transform(W[te])
    X_tr = np.column_stack([X_fijas[tr], pct_tr])
    X_te = np.column_stack([X_fijas[te], pct_te])
    sc = StandardScaler().fit(X_tr)
    return sc.transform(X_tr).astype(np.float32), sc.transform(X_te).astype(np.float32)


def red(d):
    return nn.Sequential(
        nn.Linear(d, 128), nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(0.15),
        nn.Linear(128, 64), nn.BatchNorm1d(64), nn.ReLU(), nn.Dropout(0.10),
        nn.Linear(64, 32), nn.BatchNorm1d(32), nn.ReLU(), nn.Dropout(0.10),
        nn.Linear(32, 1))


def entrenar_una(X_tr, y_tr, semilla):
    torch.manual_seed(semilla)
    np.random.seed(semilla)
    X_a, X_v, y_a, y_v = train_test_split(X_tr, y_tr, test_size=0.15, stratify=y_tr,
                                          random_state=semilla)
    X_a, y_a = torch.from_numpy(X_a), torch.from_numpy(y_a)
    X_v, y_v = torch.from_numpy(X_v), torch.from_numpy(y_v)
    m = red(X_a.shape[1])
    opt = torch.optim.AdamW(m.parameters(), lr=1e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epocas)
    perdida = nn.BCEWithLogitsLoss()
    mejor, mejor_estado, sin_mejora = np.inf, None, 0
    for _ in range(args.epocas):
        m.train()
        perm = torch.randperm(len(X_a))
        for i in range(0, len(X_a), 1024):
            idx = perm[i:i + 1024]
            if len(idx) < 2:        # BatchNorm necesita al menos 2 ejemplos
                continue
            opt.zero_grad()
            perdida(m(X_a[idx]).squeeze(1), y_a[idx]).backward()
            opt.step()
        sched.step()
        m.eval()
        with torch.no_grad():
            pv = perdida(m(X_v).squeeze(1), y_v).item()
        if pv < mejor - 1e-5:
            mejor, sin_mejora = pv, 0
            mejor_estado = {k: v.clone() for k, v in m.state_dict().items()}
        else:
            sin_mejora += 1
            if sin_mejora >= 15:
                break
    m.load_state_dict(mejor_estado)
    m.eval()
    return m


def entrenar_y_puntuar(tr, te):
    X_tr, X_te = preparar(tr, te)
    p = np.zeros(te.sum())
    for s in range(args.semillas):
        m = entrenar_una(X_tr, y[tr], s)
        with torch.no_grad():
            p += torch.sigmoid(m(torch.from_numpy(X_te)).squeeze(1)).numpy()
    return p / args.semillas


puntaje = np.zeros(len(T))
for a, b in (("entrenamiento", "prueba"), ("prueba", "entrenamiento")):
    tr = (T["conjunto"] == a).values
    te = (T["conjunto"] == b).values
    puntaje[te] = entrenar_y_puntuar(tr, te)
    print(f"entrenado con {a:13s} -> puntua {b:13s} | {args.semillas} semillas", flush=True)

pru = (T["conjunto"] == "prueba").values
print(f"\nAUC en la mitad de prueba: {roc_auc_score(y[pru], puntaje[pru]):.3f} "
      f"| longitud: {'si' if args.longitud else 'no'}")
orden = np.argsort(-puntaje)
for n in (10000, 25000, 50000):
    print(f"  conservando {n:>6} hilos: {100 * y[orden[:n]].mean():.1f} % verdaderos")

salida = f"{args.salida}/" + ("puntaje_mlp_ajustado_long.txt" if args.longitud else "puntaje_mlp_ajustado.txt")
np.savetxt(salida, puntaje, fmt="%.8g")
print("guardado", salida)

"""Normaliza a (0,1) el vector de pesos de un método y lo filtra con epsilon.
Uso: python scripts/filtrar_pesos.py pesos.txt metodo epsilon [carpeta_salida]
Entrada: un peso por hilo (en una línea o en columna), en el orden de data/tracks_100k.tck.
Salida (carpeta_salida, por defecto out/filtrado):
  pesos_norm_<metodo>.csv      hilo,peso_crudo,peso_norm,percentil   (100 000 filas)
  validos_<metodo>_eps<e>.csv  hilo,valido  (1 si peso_norm >= epsilon)
"""
import sys, os
import numpy as np

if len(sys.argv) < 4:
    sys.exit(__doc__)
f, metodo, eps = sys.argv[1], sys.argv[2], float(sys.argv[3])
out = sys.argv[4] if len(sys.argv) > 4 else "out/filtrado"
w = np.loadtxt(f, comments="#").ravel()
if w.size != 100000: sys.exit(f"ERROR: {w.size} pesos, deben ser 100000")
if not np.isfinite(w).all() or (w < 0).any(): sys.exit("ERROR: hay NaN/inf o pesos negativos")
if w.max() <= 0: sys.exit("ERROR: todos los pesos son 0")

wn = w / w.max()                                   # normalización principal: entre el máximo
u, inv, cnt = np.unique(w, return_inverse=True, return_counts=True)
rango = np.cumsum(cnt) - (cnt - 1) / 2.0           # rango promedio en empates (ceros de LiFE)
pct = (rango[inv] - 1) / (w.size - 1)              # opcional: percentil (Ricardo)
v = (wn >= eps).astype(int)
os.makedirs(out, exist_ok=True)
idx = np.arange(w.size)
np.savetxt(f"{out}/pesos_norm_{metodo}.csv", np.c_[idx, w, wn, pct],
           delimiter=",", header="hilo,peso_crudo,peso_norm,percentil", comments="",
           fmt=["%d", "%.10g", "%.10g", "%.6f"])
np.savetxt(f"{out}/validos_{metodo}_eps{eps:g}.csv", np.c_[idx, v],
           delimiter=",", header="hilo,valido", comments="", fmt="%d")
print(f"{metodo}: max={w.max():.6g}  ceros={(w==0).sum()}  eps={eps:g}  "
      f"validos={v.sum()} ({100*v.mean():.1f}%)  descartados={w.size-v.sum()}")

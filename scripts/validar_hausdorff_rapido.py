# Validación del Hausdorff rápido contra fuerza bruta (40 hilos al azar). Ver docs/hausdorff_eficiencia.md
# Uso (raíz del proyecto, con nibabel/scipy):  python scripts/validar_hausdorff_rapido.py   (tarda ~16 min)
import sys, time, numpy as np, nibabel as nib
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist
def remuestrea(S, paso):
    out, off = [], [0]
    for s in S:
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(s, axis=0), axis=1))]
        n = max(2, int(round(d[-1] / paso)) + 1); t = np.linspace(0, d[-1], n)
        out.append(np.stack([np.interp(t, d, s[:, c]) for c in range(3)], 1).astype(np.float32)); off.append(off[-1] + n)
    return np.concatenate(out), np.array(off)
def rapido(y, arbol, GP, GO, gid, EPS=10):
    tres = y[[0, len(y)//2, -1]]; cand = None
    for l in arbol.query_ball_point(tres, EPS):
        ids = np.unique(gid[l]); cand = ids if cand is None else np.intersect1d(cand, ids, assume_unique=True)
        if len(cand) == 0: break
    hd = np.inf
    for j in cand:
        D = cdist(y, GP[GO[j]:GO[j+1]]); hd = min(hd, max(D.min(1).max(), D.min(0).max()))
    return hd if hd <= EPS else np.nan
def bruta(y, GP, GO, ch=4000):
    best = np.inf; nG = len(GO)-1
    for a in range(0, nG, ch):
        b = min(a+ch, nG); P = GP[GO[a]:GO[b]]; off = GO[a:b] - GO[a]
        D = cdist(y, P)                                  # (n_y, puntos del trozo)
        ya = np.maximum.reduceat(D.min(0)[None, :], off, axis=1)[0]   # GT_j -> y
        yb = np.maximum.reduceat(np.minimum.reduceat(D, off, axis=1), np.arange(len(off)), axis=1) if False else None
        mn = np.minimum.reduceat(D, off, axis=1)         # (n_y, n_gt): min sobre puntos de cada GT_j
        a_dir = mn.max(0)                                # y -> GT_j
        best = min(best, np.maximum(a_dir, ya).min())
    return best
t0 = time.time()
Y = nib.streamlines.load("data/tracks_100k.tck").streamlines
G = nib.streamlines.load("data/GT/all_tracks.tck").streamlines
rng = np.random.default_rng(0); idx = np.sort(rng.choice(100000, 40, replace=False))
res = {}
for paso in (2.0, 1.0):
    GP, GO = remuestrea(G, paso); gid = np.repeat(np.arange(len(GO)-1, dtype=np.int32), np.diff(GO)); arbol = cKDTree(GP)
    print(f"GT paso {paso}: {len(GP)} puntos, {time.time()-t0:.0f}s", flush=True)
    YP, YO = remuestrea([Y[i] for i in idx], paso)
    res[paso] = [rapido(YP[YO[i]:YO[i+1]], arbol, GP, GO, gid) for i in range(len(idx))]
    if paso == 2.0:
        brut = []
        for i in range(len(idx)):
            h = bruta(YP[YO[i]:YO[i+1]], GP, GO); brut.append(h if h <= 10 else np.nan)
            print(f"  bruta {i+1}/40 {time.time()-t0:.0f}s", flush=True)
        res["bruta"] = brut
    del GP, GO, gid, arbol
r2, r1, rb = map(np.array, (res[2.0], res[1.0], res["bruta"]))
ok = ~np.isnan(rb) | ~np.isnan(r2)
print("hilos:", len(idx), "| con correspondencia <10 mm (bruta):", int((~np.isnan(rb)).sum()), "| (rapida):", int((~np.isnan(r2)).sum()))
print("NaN iguales rapida vs bruta:", bool((np.isnan(rb) == np.isnan(r2)).all()))
m = ~np.isnan(rb) & ~np.isnan(r2)
print("max |rapida - bruta| (mismo muestreo):", np.abs(r2[m]-rb[m]).max() if m.any() else None)
m2 = ~np.isnan(r1) & ~np.isnan(r2)
d = r2[m2]-r1[m2]
print("paso 2 vs paso 1 mm: media dif %.3f, max |dif| %.3f mm, n=%d" % (d.mean(), np.abs(d).max(), m2.sum()))
print("tiempo total", time.time()-t0)

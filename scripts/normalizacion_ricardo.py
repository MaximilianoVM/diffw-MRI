"""Normalización Ricardo: combina los pesos de los métodos por rango percentil y evalúa contra el GT por haz.

Implementa docs/equipos/Normalizacion Ricardo.md. Ajustes de docs/resultados/normalizacion.md:
.tck en vez de .trk, entradas del contrato del repo y etiqueta por haz con MDF.

Uso (desde la raíz del proyecto, con el entorno activado):
    python scripts/normalizacion_ricardo.py                                   # COMMIT + SIFT2
    python scripts/normalizacion_ricardo.py --pesos COMMIT=out/commit/pesos_commit.txt \
        SIFT2=out/pesos_sift2.txt LiFE=out/life/pesos_life.txt                # cuando llegue LiFE

Pasos:
  1. Verifica que cada vector de pesos tenga un peso por hilo del tractograma (si no, se detiene).
  2. Normaliza cada método por rango percentil: 0 se queda en 0; los > 0 valen rango/n.
  3. Combina: score = promedio de los percentiles; conservar si score >= umbral.
     Alternativa: voto mayoritario (peso > 0 en más de la mitad de los métodos).
  4. Asigna cada hilo al haz del GT más cercano por MDF mínimo (20 puntos), si está a < 5 mm;
     si no, es "falso". Se calcula una sola vez para los 100 000 hilos: cada método es un subconjunto.
  5. Por haz y método: detectado, cobertura, desborde y Dice (en vóxeles), y MDF simétrico.
  6. Elige el umbral (0.10 a 0.90, paso 0.05) con el Dice promedio más alto.
  7. Ranking de los métodos (Dice, cobertura, desborde, MDF, % falsas) y método ganador.

Salidas en out/normalizacion/:
  resultados_por_conducto.csv, resumen_metodos.csv, barrido_umbral.csv, curva_umbral.png,
  combinado_u<umbral>.tck, voto_mayoritario.tck, keep_combinado.txt, keep_voto.txt (0/1 por hilo),
  etiqueta_mdf.csv (haz más cercano y MDF de cada hilo: la etiqueta por haz que sirve a todos)
"""
import argparse
import glob
import os
import time

import nibabel as nib
import numpy as np
import pandas as pd
from scipy.stats import rankdata


# --------------------------------------------------------------------------- normalización
def a_percentil(w):
    """Rango percentil (sección 3): 0 se queda en 0; los > 0 valen rango/n, con empates promediados."""
    w = np.asarray(w, dtype=float)
    p = np.zeros_like(w)
    pos = w > 0
    if pos.any():
        p[pos] = rankdata(w[pos], method="average") / pos.sum()
    return p


def a_percentil_por_longitud(w, longitud, n_rangos=10):
    """Rango percentil dentro de cada rango de longitud (cuantiles de la longitud de todos los hilos).

    Igual que a_percentil, pero cada hilo solo compite con los de longitud parecida: dentro de cada rango,
    los de peso 0 se quedan en 0 y los de peso > 0 valen rango/n (n = hilos con peso > 0 en ese rango).
    Así un método que favorece a los hilos cortos (o largos) no les da percentiles altos solo por su longitud.
    """
    w = np.asarray(w, dtype=float)
    longitud = np.asarray(longitud, dtype=float)
    bordes = np.quantile(longitud, np.linspace(0, 1, n_rangos + 1))[1:-1]
    rango = np.digitize(longitud, bordes)               # 0 .. n_rangos-1
    p = np.zeros_like(w)
    for r in np.unique(rango):
        m = rango == r
        p[m] = a_percentil(w[m])
    return p


def combinar(pesos, longitud=None, n_rangos=0):
    """Promedio de percentiles y voto mayoritario. `pesos` es {método: vector}.
    Con `longitud` y n_rangos > 0, el percentil se calcula dentro de cada rango de longitud."""
    if longitud is not None and n_rangos > 0:
        P = np.vstack([a_percentil_por_longitud(w, longitud, n_rangos) for w in pesos.values()])
    else:
        P = np.vstack([a_percentil(w) for w in pesos.values()])
    score = P.mean(axis=0)
    votos = np.vstack([np.asarray(w) > 0 for w in pesos.values()]).sum(axis=0)
    voto = votos > len(pesos) / 2          # 2 de 3; con 2 métodos, los 2
    return score, voto


# --------------------------------------------------------------------------- utilidades
def mascara(puntos_vox, forma):
    """Vóxeles que tocan los puntos (índices enteros ya calculados) -> máscara booleana."""
    m = np.zeros(forma, bool)
    if len(puntos_vox):
        m[puntos_vox[:, 0], puntos_vox[:, 1], puntos_vox[:, 2]] = True
    return m


def a_voxeles(streamlines, inv_affine, forma):
    """Puntos (mm, RASMM) -> índices de vóxel por hilo; descarta los que caen fuera de la imagen."""
    out = []
    for s in streamlines:
        v = np.rint(s @ inv_affine[:3, :3].T + inv_affine[:3, 3]).astype(np.int32)
        dentro = np.all((v >= 0) & (v < np.array(forma)), axis=1)
        out.append(v[dentro])
    return out


def metricas_haz(M, G):
    vp = np.logical_and(M, G).sum()
    fp = np.logical_and(M, ~G).sum()
    fn = np.logical_and(~M, G).sum()
    return {"cobertura": vp / (vp + fn), "desborde": fp / (vp + fn),
            "dice": 2 * vp / (2 * vp + fp + fn) if (2 * vp + fp + fn) else 0.0}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tck", default="data/tracks_100k.tck")
    ap.add_argument("--pesos", nargs="+", default=["COMMIT=out/commit/pesos_commit.txt", "SIFT2=out/pesos_sift2.txt"],
                    help="METODO=archivo (un peso por hilo, orden del .tck)")
    ap.add_argument("--gt", default="data/GT", help="carpeta con un .tck por haz (se ignora all_tracks.tck)")
    ap.add_argument("--ref", default="data/ISMRM_2023_b3000.nii.gz", help="imagen de referencia (rejilla de vóxeles)")
    ap.add_argument("--salida", default="out/normalizacion")
    ap.add_argument("--mdf", type=float, default=5.0, help="umbral de MDF en mm para asignar un hilo a un haz")
    ap.add_argument("--n-gt", type=int, default=1000, help="hilos del GT por haz para el MDF (submuestra)")
    ap.add_argument("--semilla", type=int, default=0)
    ap.add_argument("--x-longitud", action="store_true",
                    help="multiplicar cada peso por la longitud del hilo (out/longitudes.txt) antes de normalizar")
    ap.add_argument("--corte", action="store_true",
                    help="en métodos sin ceros (SIFT2), poner en 0 la misma fracción de menor peso que COMMIT pone en 0")
    ap.add_argument("--etiqueta", choices=["mdf", "mascara", "hausdorff"], default="mdf",
                    help="mdf: MDF < --mdf mm al haz más cercano (especificación). mascara: >= --frac-mascara de "
                         "los puntos del hilo dentro de la máscara del haz dilatada 1 vóxel (no castiga hilos cortos). "
                         "hausdorff: hd_min < --eps-hd mm en --hausdorff (paso 8; vacío = falso); el haz de cada "
                         "hilo verdadero se toma del MDF más cercano")
    ap.add_argument("--eps-hd", type=float, default=5.0, help="umbral de Hausdorff en mm (con --etiqueta hausdorff)")
    ap.add_argument("--hausdorff", default="out/hausdorff/hausdorff.csv")
    ap.add_argument("--frac-mascara", type=float, default=0.9)
    ap.add_argument("--umbrales", type=float, nargs="+",
                    help="modo umbrales fijos: por cada u, eliminar los hilos con promedio < u, evaluar cada versión "
                         "contra el GT con todas las métricas y ordenarlas (p. ej. --umbrales 0.1 0.2 0.3 0.4 0.5)")
    ap.add_argument("--mismos-n", type=int, nargs="+", metavar="N",
                    help="comparar cada 'método' (puntaje) conservando sus N hilos de mayor valor (p. ej. --mismos-n 10000 25000 50000) "
                         "contra el GT con todas las métricas; incluye 'sin filtrar'. No combina los puntajes.")
    ap.add_argument("--por-longitud", type=int, default=0, metavar="N",
                    help="percentil dentro de N rangos de longitud (cuantiles), en vez de contra todos los hilos "
                         "(p. ej. --por-longitud 10 = deciles). 0 = percentil global (especificación original)")
    a = ap.parse_args()
    os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    os.makedirs(a.salida, exist_ok=True)
    rng = np.random.default_rng(a.semilla)

    from dipy.tracking.distances import bundles_distances_mdf
    from dipy.tracking.streamline import set_number_of_points

    # ---- 1. pesos y verificación
    tck = nib.streamlines.load(a.tck)
    hilos = list(tck.streamlines)
    N = len(hilos)
    pesos = {}
    for par in a.pesos:
        m, f = par.split("=", 1)
        w = np.loadtxt(f, comments="#").ravel()
        if len(w) != N:
            raise SystemExit(f"ERROR: {m} ({f}) tiene {len(w)} pesos y el tractograma {N} hilos. Deben coincidir.")
        if (w < 0).any() or np.isnan(w).any():
            raise SystemExit(f"ERROR: {m} tiene pesos negativos o NaN.")
        pesos[m] = w
        print(f"{m:7s} {f}: {N} pesos | = 0: {(w == 0).mean():.1%}")
    if len(pesos) < 3:
        print(f"AVISO: solo {len(pesos)} métodos ({', '.join(pesos)}); el voto mayoritario es 'peso > 0 en todos'.")
    if a.x_longitud:
        L = np.loadtxt("out/longitudes.txt", comments="#").ravel()
        pesos = {m: w * L for m, w in pesos.items()}
        print("variante: pesos x longitud")
    if a.corte:
        frac = (pesos["COMMIT"] == 0).mean() if "COMMIT" in pesos else 0.45
        for m, w in pesos.items():
            if not (w == 0).any():
                w = w.copy()
                w[w <= np.quantile(w, frac)] = 0
                pesos[m] = w
                print(f"variante: {m} sin ceros -> el {frac:.1%} de menor peso pasa a 0 (como COMMIT)")

    # ---- 2-3. normalización y combinación
    longitudes = np.loadtxt("out/longitudes.txt", comments="#").ravel()
    if a.por_longitud:
        print(f"variante: percentil dentro de {a.por_longitud} rangos de longitud")
    score, voto = combinar(pesos, longitudes, a.por_longitud)

    # ---- 4. asignación por MDF (una vez, para todos los hilos)
    img = nib.load(a.ref)
    forma, inv = img.shape[:3], np.linalg.inv(img.affine)
    haces = sorted(f for f in glob.glob(f"{a.gt}/*.tck") if not f.endswith("all_tracks.tck"))
    nombres = [os.path.basename(f)[:-4] for f in haces]
    gt_completo, gt_sub = [], []
    for f in haces:
        s = list(nib.streamlines.load(f).streamlines)
        gt_completo.append(s)
        idx = rng.choice(len(s), size=min(a.n_gt, len(s)), replace=False)
        gt_sub.append(set_number_of_points([s[i] for i in idx], 20))
    print(f"GT: {len(haces)} haces, {sum(map(len, gt_completo))} hilos; submuestra de {a.n_gt} por haz para el MDF")

    cache = f"out/normalizacion/asignacion_mdf_ngt{a.n_gt}_s{a.semilla}.npz"   # compartida por todas las variantes
    os.makedirs("out/normalizacion", exist_ok=True)
    hilos20 = set_number_of_points(hilos, 20)
    if os.path.exists(cache) and np.load(cache)["dmin"].shape == (N, len(haces)):
        dmin = np.load(cache)["dmin"]
        print(f"asignación MDF leída de {cache}")
    else:
        t0 = time.time()
        todos = [x for s in gt_sub for x in s]
        cortes = np.cumsum([0] + [len(s) for s in gt_sub])[:-1]
        dmin = np.empty((N, len(haces)), np.float32)
        for i in range(0, N, 2000):
            D = bundles_distances_mdf(hilos20[i:i + 2000], todos)
            dmin[i:i + 2000] = np.minimum.reduceat(D, cortes, axis=1)
        np.savez_compressed(cache, dmin=dmin)
        print(f"asignación MDF: {time.time() - t0:.0f} s")
    # ---- máscaras de vóxeles
    vox_hilo = a_voxeles(hilos, inv, forma)
    npts = np.array([len(v) for v in vox_hilo])
    vox_todos = np.concatenate(vox_hilo)
    G = [mascara(np.concatenate(a_voxeles(s, inv, forma)), forma) for s in gt_completo]

    if a.etiqueta == "mdf":
        haz = dmin.argmin(axis=1)
        dist = dmin[np.arange(N), haz]
        asignado = dist < a.mdf
        criterio = f"MDF < {a.mdf} mm"
    elif a.etiqueta == "hausdorff":
        H = pd.read_csv(a.hausdorff).sort_values("hilo")
        if len(H) != N or not (H.hilo.values == np.arange(N)).all():
            raise SystemExit(f"ERROR: {a.hausdorff} no tiene una fila por hilo (0..{N - 1}).")
        asignado = H.hd_min.values < a.eps_hd       # NaN (> 10 mm) < eps es False
        haz = dmin.argmin(axis=1)                   # haz para las métricas por conducto: el del MDF más cercano
        dist = dmin[np.arange(N), haz]
        criterio = f"Hausdorff < {a.eps_hd:g} mm"
    else:
        from scipy.ndimage import binary_dilation
        inicio = np.concatenate([[0], np.cumsum(npts)[:-1]])
        frac_dentro = np.zeros((N, len(G)), np.float32)
        con_puntos = npts > 0
        for b, Gb in enumerate(G):
            dentro = binary_dilation(Gb)[vox_todos[:, 0], vox_todos[:, 1], vox_todos[:, 2]].astype(np.float32)
            suma = np.add.reduceat(dentro, inicio[con_puntos]) if len(dentro) else 0
            frac_dentro[con_puntos, b] = suma / npts[con_puntos]
        haz = frac_dentro.argmax(axis=1)
        asignado = frac_dentro[np.arange(N), haz] >= a.frac_mascara
        dist = dmin[np.arange(N), haz]          # MDF al haz asignado (para el MDF simétrico)
        criterio = f">= {a.frac_mascara:.0%} de los puntos dentro del haz"
    haz_etq = np.where(asignado, haz, -1)
    pd.DataFrame({"hilo": np.arange(N), "haz": [nombres[h] if h >= 0 else "falso" for h in haz_etq],
                  "mdf_mm": dmin[np.arange(N), dmin.argmin(axis=1)].round(3)}).to_csv(
        f"{a.salida}/etiqueta_{a.etiqueta}.csv", index=False)
    print(f"etiqueta {a.etiqueta} ({criterio}): {asignado.sum()} hilos en algún haz ({asignado.mean():.1%});"
          f" falsos: {(~asignado).sum()}")
    from sklearn.metrics import roc_auc_score
    auc = {f"AUC {m}": roc_auc_score(asignado, w) for m, w in pesos.items()}
    auc["AUC score combinado"] = roc_auc_score(asignado, score)
    auc["AUC longitud (referencia)"] = roc_auc_score(asignado, np.loadtxt("out/longitudes.txt", comments="#").ravel())
    print("hilo por hilo (puntaje para predecir 'pertenece a un haz'):",
          " | ".join(f"{k[4:]} {v:.3f}" for k, v in auc.items()))

    def evaluar(nombre, keep, con_mdf=True):
        filas = []
        for b, hb in enumerate(nombres):
            sel = keep & (haz_etq == b)
            M = mascara(vox_todos[np.repeat(sel, npts)], forma)
            fila = {"metodo": nombre, "conducto": hb, "hilos": int(sel.sum()), "detectado": bool(sel.any()),
                    **metricas_haz(M, G[b])}
            if con_mdf:
                if sel.any():
                    a_b = dist[sel].mean()                                            # método -> GT
                    elegidos = [hilos20[i] for i in np.flatnonzero(sel)]
                    b_a = np.mean([bundles_distances_mdf(gt_sub[b][j:j + 200], elegidos).min(axis=1).mean()
                                   for j in range(0, len(gt_sub[b]), 200)])           # GT -> método
                    fila["mdf_simetrico"] = (a_b + b_a) / 2
                else:
                    fila["mdf_simetrico"] = np.nan
            filas.append(fila)
        df = pd.DataFrame(filas)
        resumen = {"metodo": nombre, "hilos_conservados": int(keep.sum()),
                   "conductos_detectados": int(df.detectado.sum()),
                   "pct_fibras_falsas": 100 * (keep & ~asignado).sum() / max(keep.sum(), 1),
                   "cobertura": df.cobertura.mean(), "desborde": df.desborde.mean(), "dice": df.dice.mean()}
        if con_mdf:
            resumen["mdf_simetrico"] = df.mdf_simetrico.mean()
        return df, resumen

    def guardar(keep, nombre):
        sub = [hilos[i] for i in np.flatnonzero(keep)]
        nib.streamlines.save(nib.streamlines.Tractogram(sub, affine_to_rasmm=np.eye(4)), f"{a.salida}/{nombre}")

    def ranking(R):
        lugares = pd.DataFrame({
            "dice": rankdata(-R.dice), "cobertura": rankdata(-R.cobertura), "desborde": rankdata(R.desborde),
            "mdf_simetrico": rankdata(R.mdf_simetrico), "pct_fibras_falsas": rankdata(R.pct_fibras_falsas)})
        R = R.copy()
        for c in lugares:
            R[f"lugar_{c}"] = lugares[c].values
        R["lugar_promedio"] = lugares.mean(axis=1).values
        return R.sort_values("lugar_promedio")

    # ---- modo mismos-n: cada puntaje conserva sus N hilos de mayor valor (comparación justa entre puntajes)
    if a.mismos_n:
        filas, tablas = [], []
        for n in a.mismos_n:
            for m, w in pesos.items():
                orden = np.lexsort((rng.random(N), -w))
                k = np.zeros(N, bool)
                k[orden[:n]] = True
                df, res = evaluar(f"{m}", k, con_mdf=False)
                res["haces_dice_0.3"] = int((df.dice >= 0.3).sum())   # «detectado» cuenta un haz con 1 solo hilo
                filas.append({"n": n, **res}); tablas.append(df.assign(n=n))
        df, res = evaluar("sin filtrar", np.ones(N, bool), con_mdf=False)
        res["haces_dice_0.3"] = int((df.dice >= 0.3).sum())
        filas.append({"n": N, **res}); tablas.append(df.assign(n=N))
        R = pd.DataFrame(filas)
        R.to_csv(f"{a.salida}/comparacion_mismos_n.csv", index=False)
        pd.concat(tablas).to_csv(f"{a.salida}/comparacion_mismos_n_por_conducto.csv", index=False)
        pd.set_option("display.width", 220)
        print("\n" + R[["n", "metodo", "hilos_conservados", "conductos_detectados", "haces_dice_0.3",
                        "pct_fibras_falsas", "cobertura", "desborde", "dice"]].round(3).to_string(index=False))
        print(f"guardado en {a.salida}/")
        return

    # ---- modo umbrales fijos: una versión del tractograma por umbral, todas contra el GT
    if a.umbrales:
        tablas, resumenes, comparables, tablas_m = [], [], [], []
        for u in a.umbrales:
            keep = score >= u
            df, res = evaluar(f"promedio >= {u:.2f}", keep)
            res = {"umbral": u, **res, "pct_conservado": 100 * keep.mean()}
            tablas.append(df)
            resumenes.append(res)
            guardar(keep, f"combinado_u{u:.2f}.tck")
            np.savetxt(f"{a.salida}/keep_u{u:.2f}.txt", keep.astype(int), fmt="%d")
            print(f"  umbral {u:.2f}: conserva {keep.sum()} hilos ({keep.mean():.1%})")
            # cada método solo, conservando el MISMO número de hilos (los de mayor peso; empates al azar)
            n = int(keep.sum())
            for m, w in pesos.items():
                orden = np.lexsort((rng.random(N), -w))          # mayor peso primero
                k = np.zeros(N, bool)
                k[orden[:n]] = True
                dfm, rm = evaluar(f"{m} solo, mismos {n} hilos", k)
                comparables.append({"umbral": u, **rm, "pct_conservado": 100 * k.mean()})
                tablas_m.append(dfm)
        R = ranking(pd.DataFrame(resumenes))
        C = pd.DataFrame(comparables)
        C.to_csv(f"{a.salida}/comparacion_mismo_n.csv", index=False)
        pd.concat(tablas_m).to_csv(f"{a.salida}/comparacion_mismo_n_por_conducto.csv", index=False)
        refs = []
        for m, keep in [*((f"{m} solo (peso > 0)", w > 0) for m, w in pesos.items()),
                        ("sin filtrar", np.ones(N, bool))]:
            df, res = evaluar(f"(ref) {m}", keep)
            tablas.append(df)
            refs.append({**res, "pct_conservado": 100 * keep.mean()})
        R = pd.concat([R, pd.DataFrame(refs)], ignore_index=True)
        pd.concat(tablas).to_csv(f"{a.salida}/resultados_por_conducto.csv", index=False)
        R.to_csv(f"{a.salida}/resumen_umbrales.csv", index=False)
        pd.Series(auc, name="valor").round(4).to_csv(f"{a.salida}/auc_por_hilo.csv")
        cols = ["metodo", "hilos_conservados", "pct_conservado", "conductos_detectados", "pct_fibras_falsas",
                "cobertura", "desborde", "dice", "mdf_simetrico", "lugar_promedio"]
        pd.set_option("display.width", 220)
        print("\n" + R[cols].round(3).to_string(index=False))
        print(f"\nEL QUE MÁS SE ACERCA AL GT (menor lugar promedio entre los {len(a.umbrales)} umbrales): {R.iloc[0].metodo}")
        print(f"guardado en {a.salida}/")
        return

    # ---- 6. barrido del umbral
    umbrales = np.round(np.arange(0.10, 0.901, 0.05), 2)
    barrido = pd.DataFrame([{"umbral": u, **evaluar(f"u{u}", score >= u, con_mdf=False)[1]} for u in umbrales])
    u_opt = float(barrido.loc[barrido.dice.idxmax(), "umbral"])
    barrido.drop(columns="metodo").to_csv(f"{a.salida}/barrido_umbral.csv", index=False)
    print(f"\numbral elegido (Dice promedio máximo): {u_opt}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot(barrido.pct_fibras_falsas, barrido.cobertura, "o-", color="#4C72B0")
    for _, r in barrido.iterrows():
        ax.annotate(f"{r.umbral:.2f}", (r.pct_fibras_falsas, r.cobertura), fontsize=7,
                    xytext=(4, 2), textcoords="offset points")
    r = barrido[barrido.umbral == u_opt].iloc[0]
    ax.plot(r.pct_fibras_falsas, r.cobertura, "o", ms=12, mfc="none", mec="#C44E52", mew=2,
            label=f"umbral elegido {u_opt:.2f} (Dice {r.dice:.3f})")
    ax.set_xlabel(f"% de fibras falsas (MDF ≥ {a.mdf:.0f} mm a todo haz)")
    ax.set_ylabel("cobertura promedio de los 21 haces")
    ax.set_title(f"Selección del umbral ({' + '.join(pesos)})")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(f"{a.salida}/curva_umbral.png", dpi=150)

    # ---- 5 y 7. evaluación de cada método y ranking
    metodos = {m: w > 0 for m, w in pesos.items()}
    metodos[f"combinado (u={u_opt})"] = score >= u_opt
    metodos["voto mayoritario"] = voto
    tablas, resumenes = [], []
    for m, keep in metodos.items():
        df, res = evaluar(m, keep)
        tablas.append(df)
        resumenes.append(res)
    _, ref = evaluar("sin filtrar (referencia)", np.ones(N, bool))
    R = pd.DataFrame(resumenes)
    lugares = pd.DataFrame({
        "dice": rankdata(-R.dice), "cobertura": rankdata(-R.cobertura), "desborde": rankdata(R.desborde),
        "mdf_simetrico": rankdata(R.mdf_simetrico), "pct_fibras_falsas": rankdata(R.pct_fibras_falsas)})
    R["lugar_promedio"] = lugares.mean(axis=1)
    R = R.sort_values("lugar_promedio")
    R = pd.concat([R, pd.DataFrame([ref])], ignore_index=True)
    pd.concat(tablas).to_csv(f"{a.salida}/resultados_por_conducto.csv", index=False)
    R.to_csv(f"{a.salida}/resumen_metodos.csv", index=False)
    pd.Series(auc, name="valor").round(4).to_csv(f"{a.salida}/auc_por_hilo.csv")

    # ---- tractogramas y keep_*.txt
    guardar(score >= u_opt, f"combinado_u{u_opt:.2f}.tck")
    guardar(voto, "voto_mayoritario.tck")
    np.savetxt(f"{a.salida}/keep_combinado.txt", (score >= u_opt).astype(int), fmt="%d")
    np.savetxt(f"{a.salida}/keep_voto.txt", voto.astype(int), fmt="%d")

    pd.set_option("display.width", 200)
    print("\n" + R.round(3).to_string(index=False))
    print(f"\nGANADOR (menor lugar promedio): {R.iloc[0].metodo}")
    print(f"guardado en {a.salida}/")


if __name__ == "__main__":
    main()

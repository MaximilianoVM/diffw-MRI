# Explicación del código de Hausdorff

Este documento explica **línea por línea** (por bloques) los scripts que calculan la etiqueta de Hausdorff:
qué hace cada parte y por qué. Para el *qué* y el *para qué* del cálculo ver `docs/hausdorff_instrucciones.md`;
para la justificación de la velocidad y la validación numérica ver `docs/hausdorff_eficiencia.md`.

| Archivo | Papel |
|---|---|
| `scripts/hausdorff_bloque.py` | El cálculo: distancia de Hausdorff de cada hilo al GT, por bloques; también une los bloques. |
| `scripts/08_hausdorff.sh` | Envoltorio del paso 8: verifica entradas (md5, GT) y llama al `.py`. |
| `scripts/validar_hausdorff_rapido.py` | Comprueba que el método rápido da lo mismo que la fuerza bruta (40 hilos). |
| `hausdorff_<Nombre>_bloque<k>/correr.sh` | Paquete autocontenido para que cada persona corra su bloque sin el repo. |

Los scripts que **usan** el resultado (`evaluar_filtrado.py`, `evaluar_normalizacion_hausdorff.py`, `modelo.py`,
`comparar_tractogramas.py`, …) solo leen `out/hausdorff/hausdorff.csv`; no se explican aquí.

---

## 1. Idea matemática en una página

Un hilo es una lista de puntos 3D. Para un hilo `y` del tractograma y uno `g` del GT:

```
d(p, g)        = min_{q ∈ g} ‖p − q‖                      distancia de un punto a un hilo
h(y → g)       = max_{p ∈ y} d(p, g)                      Hausdorff dirigido: el punto de y más alejado de g
d_H(y, g)      = max( h(y → g), h(g → y) )                Hausdorff simétrico
```

Por cada hilo `y` el script guarda:

- `hd_min     = min_g d_H(y, g)` — qué tan parecido es `y` al hilo del GT más parecido (la etiqueta principal; ε = 5 mm).
- `hd_dir_min = min_g h(y → g)` — "¿`y` está contenido en algún hilo del GT?" (no castiga que el GT sea más largo).
- `gt_hilo    = argmin_g d_H(y, g)`.

**Poda (lo que lo hace rápido).** Si `h(y → g) < 10 mm`, *todo* punto de `y` está a menos de 10 mm de `g`;
en particular su inicio, su punto medio y su final. Como `d_H ≥ h(y → g)`, lo mismo vale para `d_H < 10`.
Contrapositivo: si `g` no tiene ningún punto a < 10 mm de alguna de esas tres posiciones, entonces
`d_H(y,g) ≥ 10` y `h(y→g) ≥ 10`, y se puede descartar **sin error**. La poda es válida para las dos distancias.

El único cambio respecto a la definición exacta es el **remuestreo** a un punto cada 2 mm (se mide entre puntos,
no entre segmentos; error medido ≤ 0.24 mm) y el **tope** de 10 mm (más allá solo se sabe "> 10 mm").

---

## 2. `scripts/hausdorff_bloque.py`

### 2.1 Cabecera y configuración (líneas 22–38)

```python
os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
TCK, GT, SAL = "data/tracks_100k.tck", "data/GT/all_tracks.tck", "out/hausdorff"
```
- `os.chdir(...)`: se mueve a la carpeta padre de `scripts/` (la raíz del proyecto), así las rutas relativas
  funcionan sin importar desde dónde se llame. `realpath` resuelve el enlace `~/Proyecto_2_cerebro`.
- Rutas por omisión: tractograma oficial (100 000 hilos), GT (189 985 hilos, 21 haces) y carpeta de salida.

```python
opc = {a.split("=")[0]: a.split("=")[1] for a in sys.argv[1:] if a.startswith("--") and "=" in a}
pos = [a for a in sys.argv[1:] if not a.startswith("--")]
```
Analizador de argumentos casero (sin `argparse`):
- `opc`: diccionario con las opciones `--clave=valor` (p. ej. `{"--n": "200", "--gt": "all_tracks.tck"}`).
- `pos`: argumentos posicionales (`k` y `N`).
- `--unir` no lleva `=`, así que no entra en `opc`; se busca directamente en `sys.argv`.

```python
EPS_MAX, PASO = float(opc.get("--eps-max", 10)), float(opc.get("--paso", 2))
GT = opc.get("--gt", GT)
```
- `EPS_MAX` (10 mm): radio de la poda y tope de lo que se reporta.
- `PASO` (2 mm): separación del remuestreo.
- `--gt` permite usar otro archivo de GT (lo usa el modo paquete, donde el GT está junto a `correr.sh`).

### 2.2 Modo `--unir` (líneas 40–49)

```python
fs = sorted(glob.glob(f"{SAL}/bloque_*.csv"))
T = pd.concat([pd.read_csv(f) for f in fs]).sort_values("hilo").drop_duplicates("hilo")
```
Lee todos los `out/hausdorff/bloque_*.csv`, los apila, ordena por índice global de hilo y quita repetidos
(por si un bloque se copió dos veces). Ojo: `bloque_*` no incluye los `prueba_*.csv`, a propósito.

```python
if len(T) != 100000 or T.hilo.max() != 99999:
    print("AVISO: faltan hilos ...")
T.to_csv(f"{SAL}/hausdorff.csv", index=False)
for e in (2, 3, 5, 7, 10):
    print(f"  hd_min < {e:>2} mm: {(T.hd_min < e).mean():.1%} de los hilos")
```
- Avisa (no se detiene) si faltan bloques.
- Guarda el archivo unido `out/hausdorff/hausdorff.csv`.
- Imprime la fracción de hilos con correspondencia para varios ε. Los vacíos (`NaN`) dan `False` en
  `T.hd_min < e`, es decir, cuentan como "lejos", que es lo correcto.

(La columna `etiqueta_5mm` del `hausdorff.csv` versionado se añadió después, fuera de este script.)

### 2.3 Qué hilos le tocan a este bloque (líneas 51–56)

```python
k, N = int(pos[0]), int(pos[1])
tam = -(-100000 // N)                 # techo de 100000 / N
ini, fin = (k - 1) * tam, min(k * tam, 100000)
if "--n" in opc:
    fin = min(fin, ini + int(opc["--n"]))
```
- `-(-a // b)` es el truco de Python para la división entera **hacia arriba** (`ceil`). Con N = 7, `tam = 14 286`.
- Bloque `k` = hilos `[ini, fin)`. El último bloque se recorta a 100 000 (con N = 7 el bloque 7 tiene 14 284 hilos).
- `--n=200`: prueba rápida, solo los primeros 200 hilos del bloque.

### 2.4 Remuestreo (función `remuestrea`, líneas 59–68)

```python
def remuestrea(S, paso):
    out, off = [], [0]
    for s in S:
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(s, axis=0), axis=1))]
        n = max(2, int(round(d[-1] / paso)) + 1)
        t = np.linspace(0, d[-1], n)
        out.append(np.stack([np.interp(t, d, s[:, c]) for c in range(3)], 1).astype(np.float32))
        off.append(off[-1] + n)
    return np.concatenate(out), np.array(off)
```
Para cada hilo `s` (matriz `m × 3`):
1. `np.diff` → vectores entre puntos consecutivos; `norm` → longitud de cada segmento; `cumsum` con un 0 delante →
   `d`, la **longitud de arco** acumulada en cada punto original (`d[-1]` = longitud total del hilo).
2. `n` = número de puntos nuevos para que queden ≈ `paso` mm entre ellos (mínimo 2: inicio y fin).
3. `t` = `n` posiciones equiespaciadas sobre la longitud de arco.
4. `np.interp` interpola x, y, z por separado en esas posiciones → hilo remuestreado `n × 3`.
5. `float32` para ahorrar memoria (el GT remuestreado tiene ≈ 10 millones de puntos).

**Formato de salida "aplanado".** En lugar de una lista de arreglos se devuelve:
- `P`: todos los puntos de todos los hilos concatenados (`total × 3`);
- `off`: desplazamientos; el hilo `j` ocupa `P[off[j]:off[j+1]]`.

Es el mismo esquema que usan las matrices dispersas (CSR). Permite un solo árbol KD sobre todos los puntos y
recuperar un hilo con un corte barato.

### 2.5 Preparar el GT (líneas 71–78)

```python
G = nib.streamlines.load(GT).streamlines
GP, GO = remuestrea(G, PASO)
del G
gt_de_punto = np.repeat(np.arange(len(GO) - 1, dtype=np.int32), np.diff(GO))
arbol = cKDTree(GP)
```
- Carga el GT con nibabel y lo remuestrea; `del G` libera la versión original.
- `gt_de_punto[i]` = a qué hilo del GT pertenece el punto `i` de `GP`. `np.diff(GO)` es el número de puntos de
  cada hilo, y `np.repeat` repite el índice del hilo esa cantidad de veces. Ejemplo: `GO = [0, 3, 5]` →
  `gt_de_punto = [0, 0, 0, 1, 1]`.
- `cKDTree(GP)`: árbol KD sobre los ≈ 10 M puntos del GT. Construirlo tarda ≈ 1 min y se hace una sola vez por
  corrida; después cada búsqueda "puntos a menos de r de q" es casi logarítmica en vez de recorrer todo.

### 2.6 Cargar el bloque (líneas 80–86)

```python
if "--tck" in opc:   # modo paquete
    Y = nib.streamlines.load(opc["--tck"]).streamlines[:int(opc.get("--n", 10**9))]
    ini = int(opc.get("--offset", 0))
    fin = ini + len(Y)
else:
    Y = nib.streamlines.load(TCK).streamlines[ini:fin]
YP, YO = remuestrea(Y, PASO)
```
Dos modos:
- **Normal (repo):** carga `data/tracks_100k.tck` completo y toma el corte `[ini:fin]`.
- **Paquete:** el `.tck` que se pasa con `--tck` *ya es solo el bloque* (p. ej. `bloque6.tck`), así cada persona
  no necesita el tractograma completo. `--offset` es el índice global de su primer hilo (71 430 para el bloque 6),
  para que la columna `hilo` salga en la numeración del tractograma de 100 000 y los bloques se puedan unir.
  Aquí `ini`/`fin` se recalculan e ignoran lo calculado en §2.3.

Después se remuestrea el bloque con el mismo paso que el GT (importante: ambos lados con el mismo muestreo).

### 2.7 Bucle principal: poda + Hausdorff exacta (líneas 87–110)

```python
for i in range(fin - ini):
    y = YP[YO[i]:YO[i + 1]]
    tres = y[[0, len(y) // 2, -1]]
```
`y` es el hilo `i` del bloque; `tres` son sus puntos de inicio, medio y final (matriz `3 × 3`).

**Paso 1: candidatos.**
```python
    cand = None
    for lista in arbol.query_ball_point(tres, EPS_MAX):
        ids = np.unique(gt_de_punto[lista])
        cand = ids if cand is None else np.intersect1d(cand, ids, assume_unique=True)
        if len(cand) == 0:
            break
```
- `query_ball_point(tres, 10)` devuelve, para cada uno de los 3 puntos, la lista de índices de puntos del GT a
  ≤ 10 mm.
- `gt_de_punto[lista]` convierte "puntos" en "hilos del GT"; `np.unique` los deja sin repetir (y ordenados,
  requisito de `intersect1d(..., assume_unique=True)`).
- Se intersectan las tres listas: sobreviven solo los hilos del GT que pasan cerca del inicio **y** del medio
  **y** del final de `y` (la condición necesaria de §1).
- Si la intersección se vacía, se corta antes: no hay candidato posible.

**Paso 2: Hausdorff exacta contra cada candidato.**
```python
    hd, dr, mejor = np.inf, np.inf, -1
    for j in cand:
        D = cdist(y, GP[GO[j]:GO[j + 1]])
        a, b = D.min(1).max(), D.min(0).max()
        if max(a, b) < hd:
            hd, mejor = max(a, b), int(j)
        dr = min(dr, a)
```
- `D` = matriz de distancias entre cada punto de `y` (filas) y cada punto de `GT_j` (columnas).
- `D.min(1)`: para cada punto de `y`, su distancia al hilo `GT_j`; `.max()` → `a = h(y → GT_j)`.
- `D.min(0)`: para cada punto de `GT_j`, su distancia a `y`; `.max()` → `b = h(GT_j → y)`.
- `max(a, b)` = `d_H(y, GT_j)`. Se guarda el mínimo sobre candidatos (`hd`) y quién lo logra (`mejor`).
- `dr` es el mínimo de la dirigida `a`. Puede venir de un `GT_j` distinto de `mejor` (p. ej. un hilo del GT largo
  que contiene a `y`).

**Paso 3: aplicar el tope.**
```python
    if hd > EPS_MAX:
        hd, mejor = np.nan, -1
    if dr > EPS_MAX:
        dr = np.nan
    filas.append((ini + i, hd, dr, mejor))
```
- Un candidato pasó la poda (sus puntos están cerca de las 3 posiciones) pero su Hausdorff real puede ser > 10 mm;
  en ese caso, o si no hubo candidatos (`hd = inf`), se guarda `NaN` = "más de 10 mm" y `gt_hilo = -1`.
- La fila usa el índice **global** `ini + i`.
- Cada 1000 hilos imprime el avance y el tiempo transcurrido.

### 2.8 Guardar (líneas 112–116)

```python
sal = f"{SAL}/bloque_{k}_de_{N}.csv" if "--n" not in opc else f"{SAL}/prueba_{k}_de_{N}.csv"
```
- Corrida real → `out/hausdorff/bloque_<k>_de_<N>.csv`; con `--n` → `prueba_<k>_de_<N>.csv` (para que una
  prueba nunca se confunda con un bloque ni entre en `--unir`).
- El resumen final `T.hd_min.notna().mean()` es la fracción con `hd_min < 10 mm`.

**Columnas del CSV:** `hilo` (0–99 999), `hd_min` (mm o vacío), `hd_dir_min` (mm o vacío), `gt_hilo` (índice del
GT o −1).

### 2.9 Costo

| | Por hilo | 14 286 hilos (1 bloque) |
|---|---|---|
| Fuerza bruta (189 985 hilos del GT) | ≈ 22 s | ≈ 3.6 días |
| Con poda (decenas de candidatos) | ≈ 0.02–0.12 s | ≈ 5–35 min (el bloque 1 tardó 276 s en esta Mac) |

Memoria ≈ 1.5–2 GB, dominada por el GT remuestreado y su árbol KD.

---

## 3. `scripts/08_hausdorff.sh`

```bash
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python}
[ -x .venv/bin/python ] && PY=.venv/bin/python
```
- `set -euo pipefail`: se detiene ante cualquier error, variable no definida o fallo dentro de una tubería.
- Se mueve a la raíz del proyecto.
- Elige el intérprete: `$PY` si se definió, si no `python`; y si existe el `.venv` de macOS, usa ese
  (el `python3` del sistema no tiene nibabel).

```bash
if [ "${1:-}" = "unir" ]; then
  $PY scripts/hausdorff_bloque.py --unir; exit 0
fi
[ $# -eq 2 ] || { echo "Uso: ..."; exit 1; }
```
`bash scripts/08_hausdorff.sh unir` llama al modo de unión (§2.2). Si no, exige exactamente dos argumentos `k N`.

```bash
esperado=66ba3e6efe1fadf5b534d3947b2b138f
real=$( (md5sum data/tracks_100k.tck 2>/dev/null || md5 -r data/tracks_100k.tck) | cut -d' ' -f1)
[ "$real" = "$esperado" ] || { echo "ERROR: ..."; exit 1; }
[ -s data/GT/all_tracks.tck ] || { echo "ERROR: falta data/GT/all_tracks.tck"; exit 1; }
```
- **Comprobación crítica:** el md5 del tractograma debe ser el oficial. Si cada computadora tuviera otro
  `tracks_100k.tck`, el "hilo 50 000" sería un hilo distinto en cada una y los bloques no se podrían unir ni
  cruzar con los pesos.
- `md5sum` (Linux/WSL) o `md5 -r` (macOS): funciona en ambos sistemas.
- `-s` comprueba que el GT exista y no esté vacío.

Finalmente llama `hausdorff_bloque.py "$1" "$2"`.

---

## 4. Paquetes por bloque: `hausdorff_<Nombre>_bloque<k>/correr.sh`

Cada paquete (p. ej. `hausdorff_Richie_bloque6/`) trae: `correr.sh`, `scripts/hausdorff_bloque.py` (idéntico al del
repo), `bloque<k>.tck` (solo los hilos de ese bloque) y `LEEME.md`. El GT (`all_tracks.tck`) se copia a mano.

```bash
cd "$(dirname "$0")"
PY=${PY:-python3}
[ -f all_tracks.tck ] || { echo "ERROR: copia el GT ..."; exit 1; }
$PY -c "import nibabel, numpy, pandas, scipy" 2>/dev/null || $PY -m pip install --user nibabel numpy pandas scipy
```
- Trabaja dentro de la carpeta del paquete (no necesita el repo ni Git).
- Instala las 4 librerías solo si faltan.

```bash
if [ "${1:-}" = "prueba" ]; then
  $PY scripts/hausdorff_bloque.py 6 7 --gt=all_tracks.tck --tck=bloque6.tck --offset=71430 --n=200
  ...; exit 0
fi
$PY scripts/hausdorff_bloque.py 6 7 --gt=all_tracks.tck --tck=bloque6.tck --offset=71430
cp out/hausdorff/bloque_6_de_7.csv bloque_6_de_7_Richie.csv
```
- Usa el **modo paquete** de §2.6: `--tck` con el bloque y `--offset` con el índice global de su primer hilo.
- `prueba`: 200 hilos para comprobar en 1–2 min que todo funciona.
- Copia el resultado a un nombre con la persona, para saber de quién es cada CSV al juntarlos.

Ojo: como `os.chdir` del `.py` sube un nivel desde `scripts/`, en el paquete la "raíz" es la carpeta del paquete,
y la salida queda en `<paquete>/out/hausdorff/`.

Procedimiento que se siguió al recibir un bloque: verificar que `bloque<k>.tck` coincide con el corte
correspondiente de `tracks_100k.tck`, correr, revisar el número de filas y copiar a `out/hausdorff/`.

---

## 5. `scripts/validar_hausdorff_rapido.py`

Comprueba que la poda no cambia el resultado. Tarda ≈ 16 min.

- `remuestrea`: igual que en §2.4.
- `rapido(...)`: el mismo algoritmo de §2.7 (solo `hd_min`), empaquetado como función.
- `bruta(y, GP, GO, ch=4000)`: compara `y` contra **todos** los hilos del GT, en trozos de 4000 hilos para no
  agotar la memoria:
  ```python
  P = GP[GO[a]:GO[b]]; off = GO[a:b] - GO[a]   # puntos del trozo y dónde empieza cada hilo dentro de él
  D = cdist(y, P)                               # distancias y × puntos del trozo
  ya = np.maximum.reduceat(D.min(0)[None, :], off, axis=1)[0]   # h(GT_j → y) para cada j del trozo
  mn = np.minimum.reduceat(D, off, axis=1)      # (n_y × n_gt): distancia de cada punto de y a cada GT_j
  a_dir = mn.max(0)                             # h(y → GT_j)
  best = min(best, np.maximum(a_dir, ya).min())
  ```
  `np.minimum.reduceat` / `np.maximum.reduceat` aplican el mínimo/máximo **por segmentos** definidos por `off`,
  es decir, por hilo del GT, sin bucle de Python. Es la misma fórmula de Hausdorff, vectorizada.
  (La línea `yb = ... if False else None` es código muerto: nunca se evalúa y no afecta el resultado.)
- Programa principal: elige 40 hilos al azar con semilla fija (`default_rng(0)`), y:
  1. con paso 2 mm calcula `rapido` y `bruta`;
  2. con paso 1 mm calcula `rapido` (para medir el efecto del remuestreo).
- Reporta: cuántos tienen correspondencia < 10 mm con cada método, si los vacíos coinciden, la diferencia máxima
  rápido vs bruta (resultado: **0.0 mm**) y la diferencia paso 2 vs paso 1 (media 0.032 mm, máx 0.236 mm).

---

## 6. Flujo completo

```
data/tracks_100k.tck ─┐
                      ├─ 08_hausdorff.sh k 7  (×7 computadoras, o paquetes correr.sh)
data/GT/all_tracks.tck┘        │
                               ▼
              out/hausdorff/bloque_k_de_7.csv   (k = 1..7)
                               │  08_hausdorff.sh unir
                               ▼
              out/hausdorff/hausdorff.csv  (100 000 filas; + etiqueta_5mm = hd_min < 5)
                               │
                               ▼
   10_evaluar.sh, 11_modelo.sh, comparar_tractogramas.py, modelos de árboles …
```

Resultado obtenido: `hd_min < 5 mm` en 33.3 % de los hilos (33 349; etiqueta principal), `< 10 mm` en 58.6 %;
la dirigida `hd_dir_min < 5 mm` en 70.6 %.

## 7. Detalles a tener en cuenta

- **Vacío ≠ 0.** Un `hd_min` vacío significa "más de 10 mm" (lejos), no "distancia cero". Al etiquetar,
  `hd_min < ε` ya trata los vacíos como falsos.
- **ε ≤ 10 mm.** Como el cálculo tiene tope en 10 mm, no se puede evaluar un ε mayor sin volver a correr con
  `--eps-max` más grande (más lento: hay más candidatos).
- **Mismo tractograma en todas las máquinas** (md5): de eso depende que los índices `hilo` signifiquen lo mismo.
- **Mismo `N` en todas las máquinas**: si no, los bloques se traslapan o dejan huecos (`--unir` avisa).
- `gt_hilo` corresponde al mínimo simétrico; el hilo del GT que da `hd_dir_min` no se guarda.
- Hausdorff es estricta: un hilo que sigue bien un haz solo en un tramo, o que es mucho más corto que todos los
  hilos del GT, sale lejos en `hd_min` (por eso existe también `hd_dir_min`).

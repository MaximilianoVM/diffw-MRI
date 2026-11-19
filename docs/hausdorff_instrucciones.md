# Etiqueta por Hausdorff: reparto entre computadoras

**Qué es:** para cada uno de los 100 000 hilos de `data/tracks_100k.tck`, la distancia de Hausdorff al hilo más parecido del ground truth (189 985 hilos en `data/GT/all_tracks.tck`). Con eso se decide qué hilos "tienen correspondencia con el GT" (`hd_min < ε`). Es la pregunta 1 de la junta del 17 nov (`docs/junta_17nov.md`).

**Por qué se reparte:** el cálculo directo de las notas (cada hilo contra todo el GT) tarda ≈ 3 días por 10 000 hilos. El script `scripts/hausdorff_bloque.py` descarta primero los hilos del GT que no pasan cerca y mide solo a los candidatos: **≈ 0.1 s por hilo**, es decir ≈ 25 min por bloque de 14 286 hilos y ≈ 3 h si una sola computadora hiciera todo. Se reparte igual, porque así se termina en media hora.

## 1. Qué necesita cada computadora

- El proyecto actualizado (`git pull`) y el entorno (`conda activate dwmri` o el `.venv` de macOS). Solo usa `numpy`, `scipy`, `nibabel` y `pandas`.
- `data/tracks_100k.tck` con `md5` `66ba3e6efe1fadf5b534d3947b2b138f` (el script lo comprueba y se detiene si no coincide).
- `data/GT/all_tracks.tck` (231 MB).
- ≈ 1.5 GB de RAM libres. No necesita GPU ni MRtrix.

## 2. Reparto

Los hilos se dividen en 7 bloques consecutivos (un bloque por computadora):

| Bloque | Hilos | Computadora |
|---|---|---|
| 1 | 0 – 14 285 | por asignar |
| 2 | 14 286 – 28 571 | por asignar |
| 3 | 28 572 – 42 857 | por asignar |
| 4 | 42 858 – 57 143 | por asignar |
| 5 | 57 144 – 71 429 | por asignar |
| 6 | 71 430 – 85 715 | por asignar |
| 7 | 85 716 – 99 999 | por asignar |

Con otro número de computadoras se usa el mismo comando con otra `N` (por ejemplo `3 10` para bloques de 10 000, como en las notas). Todas deben usar **la misma `N`**.

## 3. Qué corre cada quien

Desde la raíz del proyecto, con el entorno activado (el ejemplo es el bloque 3 de 7):

```bash
bash scripts/08_hausdorff.sh 3 7
```
Remuestrea el GT y el bloque cada 2 mm, calcula las distancias y guarda `out/hausdorff/bloque_3_de_7.csv` (columnas `hilo, hd_min, hd_dir_min, gt_hilo`). Tarda ≈ 25 min.

**Se espera:** al final imprime algo como `guardado out/hausdorff/bloque_3_de_7.csv | con correspondencia < 10 mm: 58 %`. En una prueba con 300 hilos del bloque 1 fue 58 %. El archivo pesa < 1 MB: se manda por WhatsApp o Drive a quien junta.

Prueba rápida antes de la corrida completa (≈ 1 min): `python scripts/hausdorff_bloque.py 3 7 --n=100`.

## 4. Quién junta

Pone los 7 CSV en `out/hausdorff/` y corre:

```bash
bash scripts/08_hausdorff.sh unir
```
Junta los bloques en `out/hausdorff/hausdorff.csv` (100 000 filas) y avisa si falta algún hilo. También imprime qué porcentaje de hilos queda con correspondencia para varios umbrales.

## 5. Qué contiene el resultado

| Columna | Significado |
|---|---|
| `hilo` | posición del hilo en `data/tracks_100k.tck` (empieza en 0) |
| `hd_min` | mínima distancia de Hausdorff (mm) a un hilo del GT. **Vacío** = ningún hilo del GT a menos de 10 mm |
| `hd_dir_min` | Hausdorff dirigido: qué tan lejos está el punto más alejado del hilo de *algún* hilo del GT. Es más tolerante con hilos cortos que están dentro de un haz |
| `gt_hilo` | índice del hilo del GT más cercano según `hd_min` |

Se guardan **distancias**, no 0/1: el umbral `ε` se decide después (`hd_min < ε` ⇒ el hilo corresponde al GT). Ver `ACTUALIZACION.md` para la propuesta de `ε`.

## 6. Instrucciones para el Claude de cada quien (copiar y pegar)

> Lee `docs/hausdorff_instrucciones.md` y `scripts/08_hausdorff.sh`. Mi bloque es el **X de 7**. Comprueba que `data/tracks_100k.tck` y `data/GT/all_tracks.tck` existan y que el entorno tenga numpy, scipy, nibabel y pandas. Corre primero la prueba rápida (`--n=100`) y, si funciona, `bash scripts/08_hausdorff.sh X 7`. No modifiques ningún script, no hagas commit ni push, y avísame cuando exista `out/hausdorff/bloque_X_de_7.csv`.

## 7. Detalles del cálculo (por si hay dudas)

- **Remuestreo:** cada hilo se reduce a un punto cada 2 mm a lo largo de su longitud. La distancia se mide entre puntos, así que el error es menor que 1 mm. Cambia con `--paso=1` (más lento).
- **Poda exacta:** si `d_H(y, g) < ε`, cada punto de `y` está a menos de ε de `g`. Se toman 3 puntos de `y` (inicio, medio y fin) y solo se miden los hilos del GT que tienen un punto cerca de los tres. No pierde ningún hilo con distancia menor que `--eps-max` (10 mm).
- **Verificación:** contra la fuerza bruta (todos los pares) sobre 100 hilos y 3 000 hilos del GT, la diferencia máxima fue 0.05 mm y no se perdió ninguno.
- **Hausdorff simétrico** (`hd_min`): el máximo de las dos distancias dirigidas. Si un hilo del tractograma es solo un tramo de un haz largo, `hd_min` lo castiga; `hd_dir_min` no.

# Paso 9: normalizar y filtrar los pesos de un método

Paso B del objetivo (junta 17-nov): cada método entrega 100 000 pesos; se normalizan a (0,1) y se filtran con ε.

## Uso
```bash
bash scripts/09_filtrar_pesos.sh <pesos.txt> <metodo> [epsilon=0.1] [carpeta=out/filtrado]
bash scripts/09_filtrar_pesos.sh out/pesos_sift2.txt sift2 0.1
bash scripts/09_filtrar_todos.sh 0.1      # todos los métodos que existan en esta computadora
```
Solo requiere Python 3 y numpy. Entrada: un peso por hilo, en el orden de `data/tracks_100k.tck`, ≥0, sin NaN.

## Qué hace
1. **Normalización principal:** `peso_norm = peso / max(peso)`  → valores en [0,1].
2. **Filtro:** `valido = 1` si `peso_norm >= ε`, si no 0.
3. **Opcional:** columna `percentil` (rango del hilo entre 0 y 1; los empates, p. ej. los ceros de LiFE, comparten rango promedio).

## Salidas (`out/filtrado/`)
| Archivo | Columnas |
|---|---|
| `pesos_norm_<metodo>.csv` | `hilo, peso_crudo, peso_norm, percentil` (100 000 filas, `hilo` empieza en 0) |
| `validos_<metodo>_eps<ε>.csv` | `hilo, valido` |

## Ejemplo (ε = 0.1, tractograma oficial)
| Método | Pesos = 0 | Válidos |
|---|---|---|
| SIFT2 (nuestra corrida) | 0 | 93 978 (94.0 %) |
| LiFE (entrega de Andrea) | 25 388 | 50 239 (50.2 %) |

Con ε = 0.01: SIFT2 conserva 100 %, LiFE 72 %. ε = 0.01 es inerte para SIFT2 (sus pesos se centran en ~1).

## Notas
- ε sigue por definir; el script lo recibe como argumento para poder barrerlo.
- Los pesos de SIFT2 del equipo SIFT2 (máx 3.7069) difieren un poco de los nuestros (máx 3.7022); conviene que cada método entregue su propio vector pero con el mismo tractograma.
- COMMIT y COMMIT2 se corren en la Mac: allá basta `bash scripts/09_filtrar_todos.sh 0.1`.

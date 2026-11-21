# Tractograma filtrado contra el GT (paso D, sección 3.4)

Sección 3.4 de `docs/siguiente_mac_normalizacion.md` (2026-11-19, Mac). Hasta aquí todo se midió **hilo por hilo**; esto mide **el tractograma
filtrado como un todo**: qué haces (de 21) se recuperan, con qué solape y cuántos hilos falsos quedan.

**Reproducir** (≈ 1 min en total):
```
python scripts/puntajes_candidatos.py 5
python scripts/normalizacion_ricardo.py --etiqueta hausdorff --eps-hd 5 --mismos-n 10000 25000 50000 \
  --salida out/normalizacion/tractograma_hausdorff --pesos <los 10 puntajes de la sección 3.4>
```
Salidas: `out/normalizacion/tractograma_hausdorff/comparacion_mismos_n.csv` y `comparacion_mismos_n_por_conducto.csv`.

**Cómo se mide.** Cada puntaje conserva sus n hilos de mayor valor (empates al azar). Un hilo es verdadero si su Hausdorff al GT es < 5 mm, y se
asigna al haz del GT más cercano por MDF. **% falsos** = hilos conservados que no son verdaderos. **Cobertura, desborde y Dice** se calculan en
vóxeles, por haz, **solo con los hilos verdaderos** conservados de ese haz (los falsos no entran a la máscara: su costo es el % de falsos), y se
promedian sobre los 21 haces. **Detectados** = haces con al menos 1 hilo verdadero; como eso cuenta un haz con un solo hilo, se agrega
**Dice ≥ 0.3** = haces recuperados de verdad.

**Verificación de la herramienta.** La fila «sin filtrar» da 100 000 hilos y **66.651 % de falsos = 1 − 0.33349** (tasa base de Hausdorff 5 mm) ✔,
21 haces detectados y Dice 0.771, igual que la corrida de `--umbrales` con esta etiqueta. Los AUC por hilo de la misma corrida reproducen
`modelo_y_normalizacion_hausdorff.md` (SIFT2 0.426, COMMIT 0.449, LiFE 0.601, COMMIT2 0.634, longitud 0.652, mínimo LiFE+COMMIT2 0.630,
modelo 4 métodos + longitud 0.703). Un script independiente (`scripts/comparar_tractogramas.py`, otra implementación del mismo cálculo) da cifras
idénticas en los puntajes deterministas (p. ej. mínimo LiFE+COMMIT2 con 10 000: 45.66 % falsos, 16 haces, Dice 0.374).
La opción `--mismos-n` funcionó a la primera; solo se le agregó la columna `haces_dice_0.3`.

## Lectura en 5 líneas
1. **Sí hay contradicción con la evaluación por hilo.** Los puntajes con mejor precisión (mínimo LiFE+COMMIT2, COMMIT2, modelos) **pierden haces
   enteros**: BPS izquierdo y derecho, Fornix, ICP izquierdo y derecho (y CA). Con 25 000 hilos recuperan 14 de 21 haces con Dice ≥ 0.3; COMMIT y
   SIFT2, los peores por hilo (75–78 % falsos), recuperan 20 de 21 y tienen el Dice más alto (0.70 y 0.62).
2. **La causa es COMMIT2:** pone peso 0 al 99.7 % de los hilos verdaderos de BPS y al 100 % de los de Fornix e ICP (su group lasso apaga conexiones
   completas). Todo puntaje que dependa de COMMIT2 hereda esa pérdida. LiFE sí conserva entre el 53 % y el 92 % de esos hilos.
3. **El modelo con longitud es el que más haces pierde** (7 de 21 con 10 000 hilos): se queda con hilos largos y abandona los haces cortos (ICP ≈ 60 mm).
   La longitud sola es la peor en haces (5 con 10 000).
4. **No existe un ganador en las dos cosas.** Pocos falsos → mínimo LiFE+COMMIT2 (46.8 % con 25 000), pero 14 haces. Todos los haces → COMMIT
   (20 haces, Dice 0.70), pero 74.7 % de falsos, peor que no filtrar (66.7 %). Lo que cubre todo sin empeorar es el modelo de los 3 métodos pedidos
   (25 000: 15 haces, 57.4 % falsos) o LiFE solo (17 haces, 58.9 %).
5. **Con 50 000 hilos casi todos recuperan 20 haces** y el % de falsos de los buenos sube a 54–59 %: a ese tamaño el filtro ya ayuda poco.
   Para presentar, la combinación honesta es: mínimo LiFE+COMMIT2 para limpiar, avisando que pierde BPS, Fornix e ICP porque COMMIT2 los apaga.

## 1. Tablas por n
Referencias obligatorias incluidas: sin filtrar, longitud sola, COMMIT2 solo, SIFT2, COMMIT y LiFE.

### n = 10 000 hilos
| Puntaje | Hilos | Haces detectados (de 21) | Haces con Dice ≥ 0.3 | % falsos | Cobertura | Desborde | Dice |
|---|---|---|---|---|---|---|---|
| mínimo LiFE+COMMIT2 | 10 000 | 16 | 13 | **45.7 %** | 0.281 | 0.028 | 0.374 |
| promedio LiFE+COMMIT2 | 10 000 | 15 | 12 | 47.9 % | 0.240 | 0.024 | 0.323 |
| modelo 3 métodos (SIFT2+LiFE+COMMIT) | 10 000 | 14 | 11 | 59.1 % | 0.230 | 0.026 | 0.311 |
| modelo 4 métodos | 10 000 | 15 | 12 | 55.0 % | 0.280 | 0.031 | 0.357 |
| modelo 4 métodos + longitud | 10 000 | 10 | 7 | 52.6 % | 0.151 | 0.014 | 0.201 |
| SIFT2 | 10 000 | 20 | 10 | 86.6 % | 0.235 | 0.024 | 0.340 |
| COMMIT | 10 000 | 19 | **19** | 85.3 % | **0.377** | 0.022 | **0.515** |
| LiFE | 10 000 | 14 | 9 | 57.0 % | 0.200 | 0.021 | 0.280 |
| COMMIT2 | 10 000 | 15 | 13 | 51.3 % | 0.266 | 0.024 | 0.353 |
| longitud sola | 10 000 | 7 | 5 | 68.3 % | 0.112 | 0.014 | 0.152 |
| sin filtrar | 100 000 | 21 | 20 | 66.7 % | 0.772 | 0.192 | 0.771 |

### n = 25 000 hilos
| Puntaje | Hilos | Haces detectados (de 21) | Haces con Dice ≥ 0.3 | % falsos | Cobertura | Desborde | Dice |
|---|---|---|---|---|---|---|---|
| mínimo LiFE+COMMIT2 | 25 000 | 16 | 14 | **46.8 %** | 0.432 | 0.068 | 0.493 |
| promedio LiFE+COMMIT2 | 25 000 | 16 | 14 | 51.2 % | 0.415 | 0.055 | 0.493 |
| modelo 3 métodos (SIFT2+LiFE+COMMIT) | 25 000 | 18 | 15 | 57.4 % | 0.394 | 0.056 | 0.484 |
| modelo 4 métodos | 25 000 | 16 | 14 | 49.7 % | 0.438 | 0.069 | 0.497 |
| modelo 4 métodos + longitud | 25 000 | 15 | 13 | 51.8 % | 0.344 | 0.047 | 0.415 |
| SIFT2 | 25 000 | 20 | **20** | 78.5 % | 0.506 | 0.070 | 0.616 |
| COMMIT | 25 000 | 20 | **20** | 74.7 % | **0.603** | 0.068 | **0.703** |
| LiFE | 25 000 | 18 | 17 | 58.9 % | 0.384 | 0.051 | 0.487 |
| COMMIT2 | 25 000 | 16 | 14 | 47.5 % | 0.438 | 0.063 | 0.502 |
| longitud sola | 25 000 | 13 | 9 | 57.8 % | 0.251 | 0.034 | 0.317 |
| sin filtrar | 100 000 | 21 | 20 | 66.7 % | 0.772 | 0.192 | 0.771 |

### n = 50 000 hilos
| Puntaje | Hilos | Haces detectados (de 21) | Haces con Dice ≥ 0.3 | % falsos | Cobertura | Desborde | Dice |
|---|---|---|---|---|---|---|---|
| mínimo LiFE+COMMIT2 ¹ | 50 000 | 21 | 20 | 58.5 % | 0.708 | 0.132 | **0.753** |
| promedio LiFE+COMMIT2 | 50 000 | 20 | 20 | 56.8 % | 0.609 | 0.110 | 0.676 |
| modelo 3 métodos (SIFT2+LiFE+COMMIT) | 50 000 | 21 | 20 | 58.7 % | 0.639 | 0.114 | 0.711 |
| modelo 4 métodos | 50 000 | 21 | 20 | 54.0 % | 0.620 | 0.120 | 0.678 |
| modelo 4 métodos + longitud | 50 000 | 18 | 18 | **53.4 %** | 0.608 | 0.113 | 0.657 |
| SIFT2 | 50 000 | 20 | 20 | 71.3 % | 0.660 | 0.123 | 0.718 |
| COMMIT | 50 000 | 20 | 20 | 69.1 % | 0.705 | 0.130 | 0.749 |
| LiFE | 50 000 | 20 | 20 | 59.2 % | 0.626 | 0.117 | 0.696 |
| COMMIT2 ¹ | 50 000 | 20 | 20 | 57.8 % | 0.690 | 0.129 | 0.736 |
| longitud sola | 50 000 | 16 | 15 | 57.6 % | 0.488 | 0.094 | 0.536 |
| sin filtrar | 100 000 | 21 | 20 | 66.7 % | 0.772 | 0.192 | 0.771 |

¹ COMMIT2 solo tiene 36 928 hilos con peso > 0 y el mínimo LiFE+COMMIT2 32 000: para llegar a 50 000 se completan con hilos de puntaje 0
elegidos **al azar**. Esos hilos al azar son los que les devuelven los haces perdidos; con 50 000 sus filas no miden al método.

## 2. Dice por haz de los 3 mejores (n = 25 000)
Los 3 con menos falsos: mínimo LiFE+COMMIT2, COMMIT2 y modelo 4 métodos. Se agregan el modelo con longitud (el mejor AUC), COMMIT (el que más
haces cubre) y LiFE. Entre paréntesis, hilos verdaderos conservados en ese haz. Ordenado de los haces que más se pierden a los que menos.

| Haz | mínimo LiFE+COMMIT2 | COMMIT2 | modelo 4 métodos | modelo 4 + longitud | COMMIT | LiFE | sin filtrar |
|---|---|---|---|---|---|---|---|
| CP | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0.13 (1) |
| CA | 0 (0) | 0 (0) | 0 (0) | 0.31 (1) | 0.66 (5) | 0 (0) | 0.73 (33) |
| **ICP_left** | **0 (0)** | **0 (0)** | **0 (0)** | **0 (0)** | 0.73 (216) | 0.27 (9) | 0.78 (644) |
| **ICP_right** | **0 (0)** | **0 (0)** | **0 (0)** | **0 (0)** | 0.71 (133) | 0.35 (29) | 0.78 (486) |
| **Fornix** | **0 (0)** | **0 (0)** | **0 (0)** | **0 (0)** | 0.8 (190) | 0 (0) | 0.81 (834) |
| **BPS_left** | **0.03 (2)** | **0.08 (5)** | **0.05 (3)** | **0.08 (5)** | 0.61 (213) | 0.41 (258) | 0.78 (2 174) |
| **BPS_right** | **0.04 (3)** | **0.07 (6)** | **0.06 (5)** | **0.08 (7)** | 0.65 (369) | 0.41 (415) | 0.8 (3 374) |
| SCP_left | 0.76 (224) | 0.76 (242) | 0.63 (39) | 0 (0) | 0.74 (129) | 0.32 (6) | 0.76 (448) |
| SCP_right | 0.71 (130) | 0.69 (93) | 0.7 (65) | 0 (0) | 0.74 (92) | 0.35 (7) | 0.78 (361) |
| OR_left | 0.68 (307) | 0.73 (317) | 0.68 (267) | 0.49 (64) | 0.74 (145) | 0.62 (303) | 0.78 (413) |
| OR_right | 0.69 (371) | 0.7 (356) | 0.7 (375) | 0.67 (320) | 0.69 (152) | 0.69 (421) | 0.78 (570) |
| UF_left | 0.72 (517) | 0.77 (674) | 0.73 (432) | 0.62 (140) | 0.85 (392) | 0.64 (266) | 0.86 (1 783) |
| UF_right | 0.71 (547) | 0.76 (644) | 0.73 (446) | 0.53 (113) | 0.81 (315) | 0.58 (203) | 0.83 (1 497) |
| CC | 0.65 (3 012) | 0.7 (3 736) | 0.61 (2 239) | 0.7 (3 693) | 0.65 (1 307) | 0.53 (1 558) | 0.75 (5 412) |
| Cingulum_left | 0.68 (802) | 0.64 (504) | 0.73 (1 096) | 0.73 (1 092) | 0.66 (234) | 0.7 (803) | 0.81 (2 172) |
| Cingulum_right | 0.75 (1 161) | 0.73 (900) | 0.76 (1 185) | 0.73 (1 083) | 0.66 (311) | 0.69 (846) | 0.81 (2 039) |
| SLF_left | 0.72 (906) | 0.68 (693) | 0.79 (1 009) | 0.66 (686) | 0.79 (457) | 0.69 (1 034) | 0.81 (2 110) |
| SLF_right | 0.78 (1 074) | 0.78 (923) | 0.78 (1 010) | 0.68 (549) | 0.82 (507) | 0.71 (823) | 0.83 (2 377) |
| ILF_left | 0.75 (694) | 0.78 (860) | 0.82 (936) | 0.77 (807) | 0.81 (329) | 0.69 (507) | 0.86 (1 990) |
| ILF_right | 0.8 (1 002) | 0.8 (873) | 0.8 (960) | 0.8 (957) | 0.78 (316) | 0.73 (436) | 0.84 (1 889) |
| MCP | 0.88 (2 537) | 0.89 (2 309) | 0.88 (2 519) | 0.88 (2 540) | 0.86 (510) | 0.86 (2 358) | 0.89 (2 742) |

(El Dice por haz de todos los puntajes y los tres n está en `comparacion_mismos_n_por_conducto.csv`.)

**Qué se pierde, y por qué.** Los mejores pierden los mismos 7 haces. La razón está en los pesos:

| Haz | Hilos verdaderos | % con COMMIT2 > 0 | % con LiFE > 0 | % con COMMIT > 0 | Longitud mediana (mm) |
|---|---|---|---|---|---|
| BPS_left | 2 174 | **0.3 %** | 59.2 % | 34.0 % | 139 |
| BPS_right | 3 374 | **0.2 %** | 56.6 % | 35.9 % | 141 |
| Fornix | 834 | **0.0 %** | 53.4 % | 62.1 % | 98 |
| ICP_left | 644 | **0.0 %** | 92.2 % | 58.2 % | 61 |
| ICP_right | 486 | **0.0 %** | 90.3 % | 54.9 % | 62 |
| CA | 33 | 3.0 % | 93.9 % | 54.5 % | 112 |
| *(comparación) CC* | 5 412 | 77.5 % | 86.6 % | 57.6 % | 116 |
| *(comparación) MCP* | 2 742 | 99.4 % | 97.3 % | 56.6 % | 124 |
| *todos los verdaderos* | 33 349 | 53.9 % | 82.9 % | 52.1 % | 106 |

COMMIT2 apaga por completo BPS, Fornix e ICP. El modelo de 4 métodos, aun sin longitud, también los pierde porque le da mucho peso a COMMIT2.
ICP además es corto (≈ 60 mm), y por eso los puntajes con longitud lo descartan.

## 3. Qué falta / advertencias
- **COMMIT2 aquí es solo λ = 1e-2.** Ya existe un barrido de λ (1e-4, 1e-3, 5e-3, 1e-2) en `docs/resultados/commit2.md`, evaluado con la etiqueta MDF: con λ = 1e-3
  conserva los 21 haces con 31 % de falsos, y con λ = 1e-4 también los 21 (42 %). **Falta repetir esa comparación con la etiqueta de Hausdorff y a igual número de hilos**
  (sección 3.5 de `docs/siguiente_mac_normalizacion.md`): puede cambiar la recomendación, porque el problema de BPS/Fornix/ICP viene de λ = 1e-2.
- La diferencia en pesos distintos de cero con la corrida original de COMMIT2 (62 779 contra 36 928) está documentada en `docs/resultados/commit2.md`; no depende de nadie más.
- Dice y cobertura solo cuentan los hilos verdaderos: un método con 85 % de falsos puede tener buen Dice (COMMIT con 10 000). Hay que leerlos
  siempre junto al % de falsos.
- CP tiene 1 solo hilo verdadero en todo el tractograma: no se puede recuperar con ningún filtro.
- Un solo fantoma y un solo tractograma, como el resto del análisis.

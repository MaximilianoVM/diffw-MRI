# Percentil por rango de longitud (2026-11-13)

Variante de la normalización Ricardo (`docs/Normalizacion Ricardo.md`). Todo es igual, salvo **contra quién se compara cada hilo** al calcular su percentil.

## 1. Por qué

Con el percentil global, cada hilo se ordena contra los 100 000. Pero los pesos dependen de la longitud del hilo, no solo de qué tan bueno es:

| Método | Spearman del peso con la longitud |
|---|---|
| COMMIT | −0.20 (favorece los cortos: su peso es por unidad de longitud) |
| SIFT2 | −0.41 (favorece los cortos) |
| COMMIT2 (λ = 1e-2) | +0.27 (favorece los largos) |

Con el percentil global, un hilo corto saca percentil alto en COMMIT y SIFT2 solo por ser corto, y el promedio arrastra ese sesgo. En la evaluación anterior eso hacía que **mientras más se filtraba, más fibras falsas quedaban** (de 47 % a 60 % con COMMIT + SIFT2).

## 2. Qué cambia

**Percentil global (especificación original):**
$$p_i = \frac{\operatorname{rango}(w_i \text{ entre todos los hilos con } w > 0)}{n_{>0}}$$

**Percentil por rango de longitud:**
1. Se divide a los 100 000 hilos en **10 rangos de longitud** con el mismo número de hilos cada uno (deciles de `out/longitudes.txt`): 11–29, 29–56, 56–74, 74–86, 86–95, 95–105, 105–114, 114–126, 126–141 y 141–200 mm.
2. **Dentro de cada rango** se aplica exactamente la regla de Ricardo: peso 0 se queda en 0; los de peso > 0 se ordenan de menor a mayor y valen lugar/n, donde n es el número de hilos con peso > 0 **en ese rango**. Empates con rango promedio.
3. Lo demás no cambia: promedio de los percentiles de los métodos y eliminar los hilos con promedio < umbral.

$$p_i = \frac{\operatorname{rango}(w_i \text{ entre los hilos con } w > 0 \text{ del mismo rango de longitud que } i)}{n_{>0,\ \text{rango}}}$$

Así, un hilo corto con percentil alto significa "tiene mucho peso **comparado con otros hilos cortos**", no "es corto".

### Ejemplo (está en el test)

| Hilo | Longitud | Peso | Percentil global | Percentil por longitud (2 rangos) |
|---|---|---|---|---|
| 1 | 10 mm | 1 | 1/7 = 0.14 | 1/3 = 0.33 |
| 2 | 10 mm | 2 | 0.29 | 0.67 |
| 3 | 10 mm | 3 | 0.43 | **1.00** |
| 4 | 10 mm | 0 | 0 | 0 |
| 5 | 100 mm | 10 | 0.57 | 0.25 |
| 6 | 100 mm | 20 | 0.71 | 0.50 |
| 7 | 100 mm | 30 | 0.86 | 0.75 |
| 8 | 100 mm | 40 | 1.00 | **1.00** |

Con el percentil global, los cortos nunca pasan de 0.43 porque sus pesos son más chicos en términos absolutos. Por longitud, el mejor de cada grupo vale 1.

## 3. Implementación

- `a_percentil_por_longitud(w, longitud, n_rangos=10)` en `scripts/normalizacion_ricardo.py`, con la opción `--por-longitud N` (0 = percentil global).
- Test en `scripts/test_normalizacion.py`: el ejemplo de arriba, y que con un solo rango da lo mismo que el percentil global. El ejemplo original de Ricardo sigue pasando.
- `scripts/07_normalizacion.sh` ahora corre las dos versiones: `out/normalizacion/umbrales/` (global) y `out/normalizacion/umbrales_longitud/` (por longitud).

```bash
python scripts/normalizacion_ricardo.py --umbrales 0.1 0.2 0.3 0.4 0.5 --por-longitud 10 \
  --pesos COMMIT=out/commit/pesos_commit.txt SIFT2=out/pesos_sift2.txt COMMIT2=out/commit2/pesos_commit2.txt \
  --salida out/normalizacion/cs2_longitud
```

La evaluación es la misma de antes: etiqueta por haz con MDF < 5 mm, métricas por haz y comparación con cada método solo con el mismo número de hilos.

## 4. Resultados

Se corrieron tres combinaciones de métodos, cada una con el percentil global y por longitud (`out/normalizacion/<combinación>_{global,longitud}/`). Referencia: **sin filtrar = 45.2 % de falsas, cobertura 0.818, Dice 0.750**.

### AUC por hilo del score combinado (etiqueta MDF; 0.5 = azar)

| Combinación | Global | Por longitud |
|---|---|---|
| COMMIT + SIFT2 | 0.366 | **0.451** |
| COMMIT + SIFT2 + COMMIT2 (λ = 1e-2) | 0.460 | **0.528** |
| COMMIT + SIFT2 + COMMIT2 (λ = 1e-3) | 0.436 | **0.511** |

Normalizar por longitud sube el AUC en 0.07–0.09 en las tres. Con COMMIT2, el score combinado por primera vez queda **por encima del azar**.

### % de fibras falsas según el umbral

| Combinación | Percentil | u = 0.1 | 0.2 | 0.3 | 0.4 | 0.5 |
|---|---|---|---|---|---|---|
| COMMIT + SIFT2 | global | 47.1 | 50.0 | 53.3 | 56.8 | 59.5 |
| | por longitud | 45.6 | 46.7 | 48.4 | 50.4 | 51.3 |
| + COMMIT2 (λ = 1e-2) | global | 46.5 | 47.4 | 47.9 | 49.3 | 52.0 |
| | por longitud | 44.6 | 44.4 | **43.8** | **42.4** | **41.0** |
| + COMMIT2 (λ = 1e-3) | global | 47.0 | 48.4 | 49.4 | 51.4 | 53.6 |
| | por longitud | 44.9 | 45.0 | 45.0 | 44.4 | 43.5 |

**Lo que cambia de fondo:** con el percentil global, subir el umbral siempre empeoraba (más falsas). Con el percentil por longitud y COMMIT2 incluido, **subir el umbral mejora**: de 44.6 % a 41.0 %. Es la primera versión combinada que baja de las 45.2 % de "sin filtrar".

### Todas las métricas: COMMIT + SIFT2 + COMMIT2 (λ = 1e-2)

| Percentil | Umbral | Hilos | Haces | % falsas ↓ | Cobertura ↑ | Desborde ↓ | Dice ↑ | MDF (mm) ↓ | Lugar |
|---|---|---|---|---|---|---|---|---|---|
| global | 0.1 (ganador) | 82 873 | 21 | 46.5 | 0.797 | 0.303 | 0.743 | 2.55 | 2.0 |
| global | 0.3 | 49 364 | 21 | 47.9 | 0.738 | 0.216 | 0.738 | 2.65 | 3.2 |
| global | 0.5 | 22 162 | 20 | 52.0 | 0.604 | 0.106 | 0.681 | 2.87 | 4.2 |
| por longitud | 0.1 | 82 430 | 21 | 44.6 | 0.800 | 0.302 | 0.745 | 2.55 | 3.0 |
| **por longitud** | **0.3 (ganador)** | **48 874** | 20 | **43.8** | 0.748 | 0.219 | 0.741 | **2.45** | **2.6** |
| por longitud | 0.5 | 21 632 | 20 | 41.0 | 0.643 | 0.123 | 0.706 | 2.70 | 3.4 |

Con el percentil por longitud, **el ganador deja de ser el umbral que menos filtra**: es u = 0.3. Conserva la mitad de los hilos con menos falsas que "sin filtrar", casi el mismo Dice (0.741 contra 0.750) y el mejor MDF de todas las versiones (2.45 mm). Pierde un haz de 21.

### Con el mismo número de hilos (por longitud, + COMMIT2 λ = 1e-2)

| Umbral (n) | Combinado | COMMIT solo | SIFT2 solo | COMMIT2 solo |
|---|---|---|---|---|
| | % falsas / cobertura / Dice | | | |
| 0.3 (48 874)* | 43.8 / 0.748 / 0.741 | 49.9 / 0.762 / 0.748 | 57.0 / 0.720 / 0.725 | **30.7** / 0.748 / 0.738 |
| 0.4 (34 226) | 42.4 / **0.707** / 0.730 | 54.3 / 0.725 / **0.741** | 63.0 / 0.656 / 0.700 | **19.0** / 0.533 / 0.542 |
| 0.5 (21 632) | 41.0 / 0.643 / 0.706 | 61.8 / **0.654** / **0.718** | 69.5 / 0.546 / 0.635 | **18.0** / 0.454 / 0.504 |

\* COMMIT2 solo tiene 36 928 hilos con peso > 0; en 0.3 completa con hilos de peso 0 al azar.

- El combinado por longitud **ya le gana a COMMIT solo y a SIFT2 solo en % de falsas**: 41–44 % contra 50–62 % y 57–70 %. Con el percentil global quedaba entre COMMIT y SIFT2.
- COMMIT2 solo sigue siendo el más limpio, pero con umbrales altos pierde haces (16–17 de 21) y la cobertura cae a 0.45–0.53. El combinado conserva 20 haces y cobertura 0.64–0.71: **es el mejor equilibrio entre limpieza y cobertura**.

## 5. Conclusión

| | Percentil global | Percentil por longitud |
|---|---|---|
| AUC del score (con COMMIT2) | 0.46 (peor que azar) | 0.53 |
| Al subir el umbral | empeora | mejora (con COMMIT2) |
| Umbral ganador | siempre el mínimo (0.1) | 0.3 con COMMIT2 |
| ¿Algún combinado mejora a "sin filtrar" en % de falsas? | no | sí (41–44 % contra 45.2 %) |
| Frente a cada método solo | entre COMMIT y SIFT2 | mejor que COMMIT y que SIFT2; más equilibrado que COMMIT2 |

**Recomendación:** usar el percentil por rango de longitud (`--por-longitud 10`) con COMMIT, SIFT2, COMMIT2 (λ = 1e-2) y LiFE, y umbral 0.3 (ver 5.1). **Actualizada en 5.2:** mejor COMMIT2 + LiFE con percentil global, u = 0.1.

### 5.1 Con LiFE (14 nov)

Mismo esquema (`bash scripts/07_normalizacion.sh`, que agrega LiFE solo si existe `out/life/pesos_life.txt`). Resultados en `out/normalizacion/umbrales_longitud/`.

| Por longitud | u = 0.1 | 0.2 | 0.3 | 0.4 | 0.5 |
|---|---|---|---|---|---|
| % falsas sin LiFE | 44.6 | 44.4 | 43.8 | 42.4 | 41.0 |
| **% falsas con LiFE** | 44.3 | 43.3 | **41.7** | 39.9 | 36.7 |

| Por longitud, u = 0.3 | Hilos | Haces | % falsas ↓ | Cobertura ↑ | Desborde ↓ | Dice ↑ | MDF (mm) ↓ |
|---|---|---|---|---|---|---|---|
| COMMIT + SIFT2 + COMMIT2 | 48 874 | 20 | 43.8 | 0.748 | 0.219 | 0.741 | 2.45 |
| **+ LiFE** | **53 890** | 20 | **41.7** | 0.747 | 0.222 | 0.739 | **2.43** |
| LiFE solo (peso > 0) | 74 612 | 21 | 40.1 | 0.765 | 0.274 | 0.738 | 2.55 |
| sin filtrar | 100 000 | 21 | 45.2 | 0.818 | 0.332 | 0.750 | 2.47 |

- Con LiFE, u = 0.3 sigue ganando y mejora en todo lo importante: **conserva 5 000 hilos más y aun así baja las falsas** (43.8 → 41.7 %), con la misma cobertura y Dice.
- El AUC del score combinado sube de 0.53 a 0.556.
- LiFE solo ya está en 40.1 % de falsas con 21 haces: es el mejor método individual que no pierde haces.

### 5.2 Comparación con el mismo número de hilos, en las dos normalizaciones (14 nov)

Cada fila compara el combinado con cada método solo, quedándose con los mismos n hilos de mayor peso. Archivos: `comparacion_mismo_n.csv` en `out/normalizacion/{umbrales, umbrales_longitud, c2l_global, c2l_longitud}/`.

**AUC por hilo (etiqueta MDF):** COMMIT 0.420 · SIFT2 0.345 · COMMIT2 0.684 · LiFE 0.655 · longitud sola 0.747.
COMMIT y SIFT2 están **por debajo del azar** hilo por hilo: sus pesos altos caen más en hilos falsos. Al promediarlos con COMMIT2 y LiFE, ensucian el score.

#### a) COMMIT + SIFT2 + COMMIT2 + LiFE

% falsas / cobertura / Dice (haces, si son menos de 21):

| Norm. | u (n) | Combinado | COMMIT solo | SIFT2 solo | COMMIT2 solo | LiFE solo |
|---|---|---|---|---|---|---|
| global | 0.1 (89 580) | 45.2 / 0.807 / 0.751 | 45.7 / 0.809 / 0.747 | 46.3 / 0.809 / 0.749 | 43.6 / 0.813 / 0.751 | 43.6 / 0.811 / 0.752 |
| global | 0.3 (54 946) | 43.2 / 0.740 / 0.735 (20) | 48.8 / 0.775 / 0.751 | 55.0 / 0.737 / 0.730 | **33.6** / 0.767 / 0.748 | **33.6** / 0.705 / 0.718 |
| global | 0.5 (17 936) | 34.4 / 0.550 / 0.638 (20) | 65.1 / 0.618 / 0.700 (20) | 72.1 / 0.491 / 0.593 (20) | **18.5** / 0.413 / 0.477 (16) | 27.0 / 0.355 / 0.431 (18) |
| longitud | 0.1 (88 610) | 44.3 / 0.808 / 0.751 | 45.8 / 0.809 / 0.747 | 46.4 / 0.808 / 0.748 | 43.4 / 0.812 / 0.751 | 43.4 / 0.810 / 0.752 |
| longitud | 0.3 (53 890) | 41.7 / 0.747 / 0.739 (20) | 49.0 / 0.772 / 0.749 | 55.4 / 0.735 / 0.730 | **33.1** / 0.766 / 0.748 | 33.4 / 0.696 / 0.710 (20) |
| longitud | 0.5 (19 489) | 36.7 / 0.569 / 0.651 (20) | 63.5 / 0.636 / 0.709 (20) | 70.8 / 0.517 / 0.613 (20) | **18.2** / 0.433 / 0.492 (16) | 27.3 / 0.375 / 0.450 (19) |

- En las dos normalizaciones, el combinado de cuatro **le gana a COMMIT y a SIFT2, pero pierde contra COMMIT2 solo y LiFE solo** en % de falsas con cualquier n. En u = 0.3, COMMIT2 solo es mejor en todo: 33 % de falsas contra 42–43 %, con igual o mejor cobertura y Dice.
- La normalización por longitud mejora un poco al combinado de cuatro (41.7 contra 43.2 % en u = 0.3), pero no cambia la conclusión.

#### b) Solo COMMIT2 + LiFE (los dos con AUC > 0.5)

| Norm. | AUC score | Ganador | Hilos | Haces | % falsas | Cobertura | Dice | MDF (mm) |
|---|---|---|---|---|---|---|---|---|
| **global** | **0.713** | u = 0.1 | 66 287 | 21 | **33.8** | 0.756 | 0.736 | 2.59 |
| longitud | 0.652 | u = 0.1 | 68 507 | 21 | 38.0 | 0.743 | 0.729 | 2.62 |

Con el mismo n (global), % falsas / cobertura / Dice (haces):

| u (n) | COMMIT2 + LiFE | COMMIT2 solo | LiFE solo |
|---|---|---|---|
| 0.1 (66 287) | **33.8** / 0.756 / 0.736 (21) | 38.1 / **0.787** / **0.747** (21) | 37.0 / 0.748 / 0.733 (21) |
| 0.2 (54 352) | **29.9** / 0.689 / 0.702 (20) | 33.4 / **0.765** / **0.744** (21) | 33.5 / 0.702 / 0.717 (21) |
| 0.3 (42 402) | 26.5 / 0.591 / 0.624 (19) | **26.1** / **0.707** / **0.718** (20) | 31.1 / 0.624 / 0.672 (20) |

- **Es la primera combinación cuyo score supera a cada método solo** (AUC 0.713 contra 0.684 y 0.655).
- En u = 0.1 y 0.2 tiene **menos falsas que cualquiera de los dos solos** con el mismo n, a cambio de un poco menos de cobertura que COMMIT2. Desde u = 0.3, COMMIT2 solo ya es mejor.
- Aquí **la normalización por longitud empeora** (AUC 0.65 contra 0.71). COMMIT2 y LiFE favorecen los hilos largos (Spearman con la longitud +0.27 y +0.26), y la longitud sí predice si un hilo pertenece a un haz (AUC 0.747). Normalizar por longitud les quita esa señal. Antes ayudaba porque corregía el sesgo contrario de COMMIT y SIFT2 hacia los hilos cortos.
- Ojo con COMMIT2 solo: tiene 36 928 hilos con peso > 0; para n mayores se completa con hilos de peso 0 al azar.

#### Conclusión de 5.2

| Combinación | Mejor normalización | ¿Le gana a cada método solo con el mismo n? |
|---|---|---|
| COMMIT + SIFT2 + COMMIT2 + LiFE | por longitud (u = 0.3) | solo a COMMIT y SIFT2 |
| **COMMIT2 + LiFE** | **global (u = 0.1–0.2)** | **sí en % falsas**; COMMIT2 conserva un poco más de cobertura |

**Nueva recomendación:** COMMIT2 + LiFE con percentil global y u = 0.1. Conserva 66 287 hilos y los 21 haces, con 33.8 % de falsas (sin filtrar: 45.2 %) y Dice 0.736. Con u = 0.2 baja a 29.9 % de falsas, pero pierde un haz. COMMIT y SIFT2 sirven por conexión (matriz), no para elegir hilos.

## 6. Cuidados

- **La etiqueta MDF sigue sesgada por longitud** (castiga a los hilos cortos). El percentil por longitud no lo corrige, pero sí quita la longitud del score: el combinado ya no gana ni pierde por preferir hilos de cierto largo. Eso hace la comparación más justa, no más optimista.
- **10 rangos es una elección.** Con muy pocos se parece al percentil global; con muchos, cada rango tiene pocos hilos y el percentil se vuelve ruidoso (≈ 10 000 hilos por rango aquí está bien). Se puede probar 5 o 20 con `--por-longitud`.
- **El umbral se elige con el mismo GT con que se evalúa**, así que el resultado es optimista. Lo correcto es elegirlo con la mitad de los haces y evaluar con la otra.
- El "lugar promedio" ordena solo entre los 5 umbrales de cada combinación, no entre combinaciones.

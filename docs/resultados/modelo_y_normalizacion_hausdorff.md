# Normalización de Ricardo y modelo, evaluados contra la etiqueta de Hausdorff

Pasos 3.1 y 3.2 de `docs/siguiente_mac_normalizacion.md` (2026-11-19, Mac). Reproducir: `bash scripts/11_modelo.sh` (≈ 30 s).

- **Etiqueta:** verdadero = `hd_min < 5 mm` en `out/hausdorff/hausdorff.csv` → 33 349 de 100 000 hilos (**tasa base 33.3 %**). Se repitió con 3 y 7 mm.
- **Métodos:** SIFT2, COMMIT, LiFE y COMMIT2 (pesos del contrato, orden de `tracks_100k.tck`).
- **Métricas:** AUC (0.5 = azar) y **precisión** = % de verdaderos entre los n hilos de mayor puntaje. Lift = precisión / 33.3 %.
- Las cifras de la sección 1 de `siguiente_mac_normalizacion.md` se reproducen exactamente (SIFT2 0.426, COMMIT 0.449, LiFE 0.601, COMMIT2 0.634, longitud 0.652; promedios 0.485 / 0.541 / 0.649; voto 2 de 3: 33 719 hilos con 30.2 %).

## Lectura en 5 líneas
1. **El promedio de Ricardo con los 3 métodos pedidos no sirve** (AUC 0.485, precisión por debajo de la tasa base): SIFT2 y COMMIT lo arrastran. Con los 4 métodos llega a 0.541; ninguna variante (por longitud, ×longitud, corte) supera a la longitud sola (0.652).
2. **Un modelo sí aprovecha los 3 métodos pedidos:** la logística le pone coeficiente **negativo** a SIFT2 y a COMMIT y sube de 0.486 a **0.623** sin longitud. Con la longitud, el coeficiente de SIFT2 se va a ≈ 0 (lo que aportaba era longitud); el de COMMIT sigue negativo (−0.13).
3. **El mejor clasificador global** es la logística con los 4 métodos + longitud (AUC 0.70; sin longitud 0.68). Sin sobreajuste: el AUC de entrenamiento y el de prueba difieren < 0.01.
4. **Para filtrar (quedarse con pocos hilos muy confiables) gana LiFE + COMMIT2:** el mínimo de sus percentiles (los dos altos) da **54.3 %** de verdaderos con 10 000 hilos y 53.2 % con 25 000, contra 48.7 % / 52.5 % de COMMIT2 solo y 31.7 % / 42.2 % de la longitud. Los modelos con longitud ordenan mejor en global pero son peores en ese extremo.
5. **Las conclusiones no cambian con ε = 3 o 7 mm** (mismo orden). Con 3 mm la longitud pierde fuerza (0.567) y COMMIT2 / LiFE + COMMIT2 quedan arriba; con 7 mm todo sube un poco.

## 1. Normalización de Ricardo (3.1) — `scripts/evaluar_normalizacion_hausdorff.py`
Puntaje = percentil (0 se queda en 0); combinaciones = promedio de percentiles. Precisión al conservar n hilos de 100 000.

| Normalización | Puntaje | AUC | Precisión 10 000 | Precisión 25 000 | Precisión 50 000 |
|---|---|---|---|---|---|
| referencia | longitud sola | 0.652 | 31.7 % | 42.2 % | 42.4 % |
| referencia | COMMIT2 solo | 0.634 | 48.7 % | 52.5 % | 42.3 % |
| global | SIFT2 | 0.426 | 13.4 % | 21.5 % | 28.7 % |
| global | COMMIT | 0.449 | 14.7 % | 25.3 % | 30.9 % |
| global | LiFE | 0.601 | 42.9 % | 41.1 % | 40.8 % |
| global | promedio 4 | 0.541 | 45.6 % | 39.0 % | 35.6 % |
| global | promedio SIFT2+COMMIT+LiFE | 0.485 | 30.0 % | 29.0 % | 32.7 % |
| global | promedio LiFE+COMMIT2 | 0.649 | 52.1 % | 48.8 % | 43.2 % |
| por longitud (deciles) | SIFT2 | 0.505 | 23.9 % | 31.2 % | 34.1 % |
| por longitud | promedio 4 | 0.555 | 42.3 % | 39.5 % | 36.8 % |
| por longitud | promedio SIFT2+COMMIT+LiFE | 0.509 | 31.0 % | 32.4 % | 33.9 % |
| por longitud | promedio LiFE+COMMIT2 | 0.610 | 49.2 % | 44.5 % | 39.9 % |
| ×longitud | SIFT2 | 0.620 | 32.8 % | 39.5 % | 41.1 % |
| ×longitud | promedio 4 | 0.640 | 47.4 % | 45.1 % | 42.3 % |
| ×longitud | promedio SIFT2+COMMIT+LiFE | 0.613 | 40.4 % | 40.5 % | 40.9 % |
| ×longitud | promedio LiFE+COMMIT2 | **0.660** | 51.8 % | 49.0 % | **44.3 %** |
| corte (SIFT2 sin ceros) | SIFT2 | 0.421 | 13.4 % | 21.5 % | 28.7 % |
| corte | promedio SIFT2+COMMIT+LiFE | 0.474 | 24.7 % | 27.3 % | 31.7 % |

Votos (percentil > 0.5 en al menos 2 métodos; conservan su propio número de hilos):

| Normalización | Voto | Hilos | Precisión | Recall |
|---|---|---|---|---|
| global | ≥ 2 de 3 (SIFT2+COMMIT+LiFE) | 33 719 | 30.2 % | 30.6 % |
| global | ≥ 2 de 4 | 41 291 | 34.1 % | 42.3 % |
| ×longitud | ≥ 2 de 3 | 36 183 | 41.5 % | 45.1 % |
| ×longitud | ≥ 2 de 4 | 41 397 | 42.3 % | 52.5 % |

### LiFE + COMMIT2: otras formas de juntarlos
| Combinación | AUC | Precisión 10 000 | Precisión 25 000 | Precisión 50 000 |
|---|---|---|---|---|
| promedio de percentiles (Ricardo) | 0.649 | 52.1 % | 48.8 % | 43.2 % |
| promedio de percentiles ×longitud | 0.660 | 51.8 % | 49.0 % | 44.3 % |
| **mínimo de percentiles** (los dos altos) | 0.630 | **54.3 %** | **53.2 %** | 41.4 % |
| producto de percentiles | 0.629 | 52.9 % | 52.8 % | 41.4 % |
| producto de pesos crudos | 0.628 | 51.2 % | 52.5 % | 41.4 % |
| máximo de percentiles (alguno alto) | 0.625 | 41.9 % | 42.7 % | 42.6 % |

| Voto LiFE + COMMIT2 | Hilos | Precisión | Recall |
|---|---|---|---|
| intersección (peso > 0 en los dos) | 32 043 | 50.6 % | 48.7 % |
| los dos percentiles > 0.5 | 10 637 | 54.4 % | 17.3 % |
| unión (peso > 0 en alguno) | 79 497 | 36.9 % | 88.1 % |

Con `scripts/normalizacion_ricardo.py --etiqueta hausdorff` (nueva opción; métricas por haz, salida en `out/normalizacion/hausdorff_global/`), el promedio de los 4 métodos con umbral 0.2 conserva 74 882 hilos con 65.8 % de falsos (sin filtrar: 66.7 %), y COMMIT2 solo (peso > 0) 36 928 con 51.4 % de falsos pero detecta 17 de 21 haces.

## 2. Modelo (3.2) — `scripts/modelo.py`
Regresión logística, entradas estandarizadas, 50 % entrenamiento / 50 % prueba (estratificado, semilla 0). Todo en la mitad de prueba (50 000 hilos); precisión al conservar el 10 / 25 / 50 % de mayor puntaje (= 10 000 / 25 000 / 50 000 de 100 000).

| Puntaje | Entradas | AUC | Precisión 10 % | Precisión 25 % | Precisión 50 % |
|---|---|---|---|---|---|
| longitud sola | | 0.649 | 31.1 % | 41.8 % | 42.1 % |
| COMMIT2 solo | | 0.633 | 48.5 % | 52.3 % | 42.3 % |
| promedio Ricardo SIFT2+COMMIT+LiFE | | 0.486 | 30.0 % | 28.9 % | 32.7 % |
| promedio Ricardo 4 métodos | | 0.541 | 45.7 % | 38.9 % | 35.6 % |
| promedio Ricardo LiFE+COMMIT2 | | 0.649 | 52.2 % | 48.7 % | 43.2 % |
| logística SIFT2+LiFE+COMMIT | percentil | 0.623 | 40.9 % | 42.9 % | 41.5 % |
| logística SIFT2+LiFE+COMMIT + longitud | log peso | 0.662 | 42.5 % | 43.6 % | 42.8 % |
| logística 4 métodos | log peso | 0.683 | 45.5 % | 50.2 % | 45.9 % |
| logística 4 métodos + longitud | log peso | **0.701** | 47.7 % | 47.9 % | **46.5 %** |
| logística LiFE+COMMIT2 | log peso | 0.658 | 51.3 % | **53.1 %** | 43.1 % |
| logística LiFE+COMMIT2 + longitud | log peso | 0.700 | 48.0 % | 48.1 % | 46.4 % |

(Las 12 variantes, con percentil y con log del peso, están en `out/modelo/resultados_E5.csv`; percentil y log dan AUC parecidos, ±0.015.)

Coeficientes (entradas estandarizadas, log del peso; negativo = a más peso, menos probable que el hilo sea verdadero):

| Modelo | SIFT2 | COMMIT | LiFE | COMMIT2 | longitud |
|---|---|---|---|---|---|
| SIFT2+LiFE+COMMIT | **−0.26** | −0.03 | +0.34 | | |
| SIFT2+LiFE+COMMIT + longitud | +0.03 | −0.04 | +0.25 | | +0.88 |
| 4 métodos | **−0.28** | −0.04 | +0.21 | +0.50 | |
| 4 métodos + longitud | −0.03 | −0.05 | +0.16 | +0.36 | +0.77 |
| LiFE+COMMIT2 | | | +0.22 | +0.49 | |
| LiFE+COMMIT2 + longitud | | | +0.16 | +0.35 | +0.79 |

Con percentil en vez de log, COMMIT queda en −0.13 a −0.15 aun con longitud (`out/modelo/coeficientes_E5.csv`).

## 3. Con otros ε (AUC)
| Puntaje | 3 mm | 5 mm | 7 mm |
|---|---|---|---|
| longitud sola | 0.567 | 0.652 | 0.702 |
| COMMIT2 solo | 0.639 | 0.634 | 0.655 |
| promedio Ricardo SIFT2+COMMIT+LiFE | 0.530 | 0.485 | 0.467 |
| promedio Ricardo LiFE+COMMIT2 | 0.648 | 0.649 | 0.675 |
| logística 4 métodos (log, prueba) | 0.664 | 0.683 | 0.726 |
| logística 4 métodos + longitud (log, prueba) | 0.679 | 0.701 | 0.752 |

## 4. Qué falta / advertencias
- El paso D pide además **comparar el tractograma** del modelo contra el GT (Dice por haz, etc.): se puede hacer con el modo `--umbrales` de `normalizacion_ricardo.py` pasándole el puntaje del modelo como un «método».
- La logística es lineal; un modelo no lineal (árboles) podría sacar algo más, sobre todo de la interacción peso × longitud.
- El orden de los vectores de COMMIT y COMMIT2 solo se verificó por tamaño; ningún AUC salió ≈ 0.5 exacto, así que no hay señal de un orden equivocado.

# Modelo: Gradient boosting ajustado (con entradas, parada temprana y búsqueda de hiperparámetros)

> **Integrado al repo el 2026-11-25** (entrega del grupo de modelos). Script: `scripts/modelo_boosting_ajustado.py`; puntajes en `out/modelos/` (no se suben a Git; se regeneran).
> **Verificado:** con los puntajes entregados y `out/modelos/tabla_hilos.csv` se reproducen el AUC en `prueba` y las precisiones de la tabla de abajo (diferencias ≤ 0.1 puntos, por desempates); el AUC es casi igual en las dos mitades, sin señales de fuga de datos.
> **Reproducir desde la raíz:** `python scripts/modelo_boosting_ajustado.py --longitud` y `python scripts/modelo_boosting_ajustado.py` (escriben en `out/modelos/`).
> **No vinieron en la entrega:** el MLP ajustado y `comparar_modelos.py`, que la tabla menciona como referencia.
> **Pendiente:** comparar el tractograma filtrado por haces (sección 3.6 de `docs/siguiente_mac_normalizacion.md`).

**Archivos entregados:** `puntaje_boosting_ajustado_long.txt` (con longitud) y `puntaje_boosting_ajustado.txt` (sin longitud).
Ambos: 100 000 líneas, en el orden de `tabla_hilos.csv`, valores en [0, 1]. Script: `modelo_boosting_ajustado.py`.

## Qué se hizo

Se partió del `HistGradientBoostingClassifier` de `comparar_modelos.py` (300 árboles, `max_depth=4`, `learning_rate=0.05`) y se ajustó en tres frentes.

**Entradas.** log(peso) de los 4 métodos, los indicadores «peso > 0» de COMMIT, LiFE y COMMIT2, el **número de métodos que conservaron el hilo**, y —en la variante con longitud— `longitud_mm`. No se agregaron rangos percentiles ni interacciones peso × longitud, como sí se hizo con el MLP: un árbol solo mira umbrales, así que una transformación monótona no le cambia nada, y las interacciones las construye al encadenar preguntas.

**Número de árboles por parada temprana.** En vez de fijar 300 árboles, se permiten hasta 1 000 y el entrenamiento se detiene cuando la pérdida en una validación interna (15 %) no mejora en 20 iteraciones. Así el número de árboles lo decide el propio modelo (entre 65 y 406, según la variante y la mitad). Además se agregó regularización L2 (`l2_regularization=1.0`) y `min_samples_leaf=50`.

**Búsqueda de hiperparámetros** dentro de la mitad de entrenamiento: se separa un 20 % de validación y se prueba esta rejilla (9 combinaciones), eligiendo la de mayor AUC de validación.

| Hiperparámetro | Valores probados | Qué controla |
|---|---|---|
| `learning_rate` | 0.03, 0.05, 0.1 | cuánto aporta cada árbol |
| `max_depth` | 3, 4, 6 | profundidad máxima de cada árbol |

Elegidos: en las cuatro corridas quedó `max_depth=6`; la tasa de aprendizaje fue 0.05 o 0.1 con longitud, y 0.1 o 0.03 sin longitud.

Reglas respetadas: no se usan `hd_min_mm` ni `etiqueta_5mm` como entrada; cada hilo se puntúa con un modelo entrenado en la otra mitad; el AUC se reporta en `prueba`.

## Cómo funciona

El modelo es una suma de árboles pequeños, donde cada uno corrige los errores de los anteriores:

```
F_M(x) = F_0 + ν · Σ_m h_m(x)          p(x) = 1 / (1 + e^(−F_M(x)))
```

`F_0` es el log-odds de la proporción global de verdaderos, `h_m` es un árbol de profundidad ≤ `max_depth`, y `ν` es la tasa de aprendizaje. En cada paso, `h_m` se ajusta a los residuos `y − p` (el gradiente negativo de la entropía cruzada) y se suma al modelo. Es un descenso de gradiente en el espacio de funciones.

## Cómo se evaluó (y por qué solo con la mitad)

Igual que el MLP ajustado: se entrena solo con `conjunto == "entrenamiento"` y se reporta en `prueba`, porque si se entrena y se evalúa con los mismos hilos el modelo ya vio las respuestas y el AUC mide memoria.

Se hace el **intercambio de mitades**: entrenar con `entrenamiento` → puntuar `prueba`; entrenar con `prueba` → puntuar `entrenamiento`. Cada hilo termina con un puntaje de un modelo que **no lo vio al entrenar**.

La búsqueda de hiperparámetros se hace **dentro** de la mitad con la que se entrena (80 % / 20 %), y la parada temprana usa una validación interna distinta, por lo que la mitad que se puntúa nunca interviene. No se entrenó un modelo final con los 100 000 hilos a propósito, porque no habría forma honesta de reportar qué tan bueno es.

Por eso los números se leen distinto según la columna:

- el **AUC se mide solo en `prueba`** (una mitad, sin contaminar), con intervalo de confianza del 95 % por bootstrap sobre esos 50 000 hilos;
- las **precisiones usan los 100 000 hilos**, porque tras el intercambio todos son fuera de muestra.

## Qué contiene el archivo de puntajes

`puntaje_boosting_ajustado_long.txt` (y su gemelo sin longitud): **100 000 líneas**, una por hilo, en el mismo orden de `tabla_hilos.csv`, un número por línea en [0, 1]: la probabilidad estimada de que el hilo sea verdadero. Cuanto mayor, más creíble el hilo. Para filtrar se ordena de mayor a menor y se conservan los primeros `n`.

Lo que se obtiene: conservando los **25 000** hilos de mayor puntaje, **62.4 %** son verdaderos (contra 33.3 % sin filtrar y 50.2 % con la logística); con los **10 000** mejores, **70.4 %**. Además, entre esos 25 000 quedan el **24.2 %** de los 15 389 hilos verdaderos a los que COMMIT2 asigna peso 0.

## Resultados

AUC en la mitad `prueba` (con intervalo de confianza del 95 %); precisión sobre los 100 000 hilos puntuados por intercambio de mitades. Para comparar: el mejor método solo, COMMIT2, tiene AUC 0.633.

| Modelo | longitud | AUC | IC 95 % | 10 000 | 25 000 | 50 000 |
|---|---|---|---|---|---|---|
| logística (referencia) | no | 0.688 | 0.683 – 0.693 | 46.5 % | 50.2 % | 46.0 % |
| logística (referencia) | sí | 0.699 | 0.695 – 0.704 | 45.0 % | 48.8 % | 46.7 % |
| boosting sin ajustar | no | 0.725 | 0.721 – 0.730 | 63.4 % | 56.4 % | 47.4 % |
| boosting sin ajustar | sí | 0.793 | 0.789 – 0.797 | 69.8 % | 61.8 % | 52.5 % |
| **boosting ajustado** | no | **0.727** | 0.723 – 0.732 | **63.8 %** | **56.5 %** | **47.5 %** |
| **boosting ajustado** | sí | **0.798** | 0.794 – 0.801 | **70.4 %** | **62.4 %** | **52.7 %** |
| bosque ajustado | sí | 0.799 | 0.795 – 0.802 | 71.4 % | 62.8 % | 53.0 % |
| MLP ajustado | sí | 0.799 | 0.795 – 0.803 | 70.8 % | 62.8 % | 53.0 % |

## Conclusiones

1. **El ajuste mejora al boosting, de forma moderada.** El AUC sube de 0.793 a 0.798 con longitud (diferencia pareada +0.004, IC 95 % +0.003 a +0.005) y de 0.725 a 0.727 sin ella (+0.002). En precisión con 10 000 hilos, de 69.8 % a 70.4 %. Lo que más pesa es permitir árboles más profundos (`max_depth=6`).
2. **Queda ligeramente por debajo del bosque ajustado y del MLP ajustado**, pero por muy poco: boosting − MLP = −0.0015 (IC −0.0030 a −0.0001) y boosting − bosque = −0.0013 (IC −0.0026 a +0.0001). Los tres son equivalentes en la práctica, con puntajes correlacionados en 0.96 o más. El boosting es el más rápido de entrenar (alrededor de un minuto por variante).
3. **Lo grande no es el ajuste, es la no linealidad y la longitud.** El boosting le saca ~0.10 de AUC a la logística, y la longitud aporta ~0.07 de AUC.
4. **Sobre los haces que se pierden:** el boosting ajustado con longitud conserva entre sus 25 000 mejores el 24.2 % de los hilos verdaderos con peso 0 en COMMIT2 (la logística, 0.5 %). Sin longitud solo el 1.8 %. Para medir de verdad «haces recuperados» hace falta `etiqueta_hausdorff.csv`, que no viene en el paquete.
5. **Limitaciones.** (a) Con `max_depth=6` en el borde de la rejilla, ampliarla podría dar una mejora pequeña adicional. (b) El intervalo de confianza solo refleja la variación del conjunto de prueba, no la de la partición ni la de la semilla de la parada temprana. (c) Es un solo cerebro simulado y un solo tractograma: no sabemos si esto se traslada a otros datos.

## Cómo reproducirlo

```
pip install pandas scikit-learn numpy
python modelo_boosting_ajustado.py --longitud     # escribe puntaje_boosting_ajustado_long.txt
python modelo_boosting_ajustado.py                # escribe puntaje_boosting_ajustado.txt
python modelo_boosting_ajustado.py --rapido       # sin búsqueda de hiperparámetros (segundos)
```
Con `tabla_hilos.csv` en la misma carpeta (o `--tabla ruta/tabla_hilos.csv`).
Tarda alrededor de un minuto por variante en una laptop sin GPU.

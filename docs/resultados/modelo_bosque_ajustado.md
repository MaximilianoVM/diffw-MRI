# Modelo: Bosque aleatorio ajustado (con entradas y búsqueda de hiperparámetros)

> **Integrado al repo el 2026-11-25** (entrega del grupo de modelos). Script: `scripts/modelo_bosque_ajustado.py`; puntajes en `out/modelos/` (no se suben a Git; se regeneran).
> **Verificado:** con los puntajes entregados y `out/modelos/tabla_hilos.csv` se reproducen el AUC en `prueba` y las precisiones de la tabla de abajo (diferencias ≤ 0.1 puntos, por desempates); el AUC es casi igual en las dos mitades, sin señales de fuga de datos.
> **Reproducir desde la raíz:** `python scripts/modelo_bosque_ajustado.py --longitud` y `python scripts/modelo_bosque_ajustado.py` (escriben en `out/modelos/`).
> **No vinieron en la entrega:** el MLP ajustado y `comparar_modelos.py`, que la tabla menciona como referencia.
> **Pendiente:** comparar el tractograma filtrado por haces (sección 3.6 de `docs/siguiente_mac_normalizacion.md`).

**Archivos entregados:** `puntaje_bosque_ajustado_long.txt` (con longitud) y `puntaje_bosque_ajustado.txt` (sin longitud).
Ambos: 100 000 líneas, en el orden de `tabla_hilos.csv`, valores en [0, 1]. Script: `modelo_bosque_ajustado.py`.

## Qué se hizo

Se partió del bosque aleatorio de `comparar_modelos.py` (200 árboles, `min_samples_leaf=50`) y se ajustó en dos frentes.

**Entradas.** log(peso) de los 4 métodos, los indicadores «peso > 0» de COMMIT, LiFE y COMMIT2, el **número de métodos que conservaron el hilo**, y —en la variante con longitud— `longitud_mm`. No se agregaron rangos percentiles ni interacciones peso × longitud, como sí se hizo con el MLP: un árbol solo mira umbrales, así que una transformación monótona (log, percentil) no le cambia nada, y las interacciones las construye sola al encadenar preguntas.

**Entrenamiento.** 400 árboles (antes 200) y una búsqueda de hiperparámetros dentro de la mitad de entrenamiento: se separa un 20 % de validación y se prueba esta rejilla (6 combinaciones, 100 árboles cada una), eligiendo la de mayor AUC de validación.

| Hiperparámetro | Valores probados | Qué controla |
|---|---|---|
| `min_samples_leaf` | 20, 50, 100 | hilos mínimos por hoja (menos = árboles más profundos) |
| `max_features` | `sqrt` (≈ 2 de 8), 0.5 (la mitad) | variables que mira cada árbol en cada pregunta |

Elegidos (en las dos direcciones del intercambio de mitades): con longitud `min_samples_leaf=20` y `max_features=0.5`; sin longitud `min_samples_leaf=100` y `max_features=0.5`.

Reglas respetadas: no se usan `hd_min_mm` ni `etiqueta_5mm` como entrada; cada hilo se puntúa con un modelo entrenado en la otra mitad; el AUC se reporta en `prueba`.

## Cómo funciona

Un bosque promedia `B = 400` árboles de decisión. Cada uno se entrena con una muestra aleatoria con reemplazo de los hilos (*bootstrap*) y, en cada pregunta, solo considera un subconjunto aleatorio de variables:

```
p(x) = (1 / B) · Σ_b  T_b(x)
```

Donde `T_b(x)` es la proporción de hilos verdaderos de la hoja en que cae `x` según el árbol `b`. Promediar árboles distintos reduce la inestabilidad de un árbol suelto: `Var = ρσ² + (1 − ρ)σ² / B`.

## Cómo se evaluó (y por qué solo con la mitad)

Igual que el MLP ajustado: se entrena solo con `conjunto == "entrenamiento"` y se reporta en `prueba`, porque si se entrena y se evalúa con los mismos hilos el modelo ya vio las respuestas y el AUC mide memoria.

No se desperdicia la mitad de los datos. Se hace el **intercambio de mitades**: entrenar con `entrenamiento` → puntuar `prueba`; entrenar con `prueba` → puntuar `entrenamiento`. Cada hilo termina con un puntaje de un modelo que **no lo vio al entrenar**.

La búsqueda de hiperparámetros se hace **dentro** de la mitad con la que se entrena (80 % / 20 %), por lo que la mitad que se puntúa nunca interviene en esa elección. No se entrenó un modelo final con los 100 000 hilos a propósito, por la misma razón que en el MLP: no habría forma honesta de reportar qué tan bueno es.

Por eso los números se leen distinto según la columna:

- el **AUC se mide solo en `prueba`** (una mitad, sin contaminar), con intervalo de confianza del 95 % por bootstrap sobre esos 50 000 hilos;
- las **precisiones usan los 100 000 hilos**, porque tras el intercambio todos son fuera de muestra.

## Qué contiene el archivo de puntajes

`puntaje_bosque_ajustado_long.txt` (y su gemelo sin longitud): **100 000 líneas**, una por hilo, en el mismo orden de `tabla_hilos.csv`, un número por línea en [0, 1]: la fracción de árboles que votan «verdadero» para ese hilo. Cuanto mayor, más creíble el hilo. Para filtrar se ordena de mayor a menor y se conservan los primeros `n`.

Lo que se obtiene: conservando los **25 000** hilos de mayor puntaje, **62.8 %** son verdaderos (contra 33.3 % sin filtrar y 50.2 % con la logística); con los **10 000** mejores, **71.4 %**. Además, entre esos 25 000 quedan el **25.0 %** de los 15 389 hilos verdaderos a los que COMMIT2 asigna peso 0.

## Resultados

AUC en la mitad `prueba` (con intervalo de confianza del 95 %); precisión sobre los 100 000 hilos puntuados por intercambio de mitades. Para comparar: el mejor método solo, COMMIT2, tiene AUC 0.633.

| Modelo | longitud | AUC | IC 95 % | 10 000 | 25 000 | 50 000 |
|---|---|---|---|---|---|---|
| logística (referencia) | no | 0.688 | 0.683 – 0.693 | 46.5 % | 50.2 % | 46.0 % |
| logística (referencia) | sí | 0.699 | 0.695 – 0.704 | 45.0 % | 48.8 % | 46.7 % |
| bosque sin ajustar | no | 0.724 | 0.720 – 0.729 | 63.6 % | 56.5 % | 47.3 % |
| bosque sin ajustar | sí | 0.791 | 0.787 – 0.795 | 69.6 % | 61.6 % | 52.4 % |
| **bosque ajustado** | no | **0.725** | 0.721 – 0.729 | **63.8 %** | **56.6 %** | **47.4 %** |
| **bosque ajustado** | sí | **0.799** | 0.795 – 0.802 | **71.4 %** | **62.8 %** | **53.0 %** |
| boosting ajustado | sí | 0.798 | 0.794 – 0.801 | 70.4 % | 62.4 % | 52.7 % |
| MLP ajustado | sí | 0.799 | 0.795 – 0.803 | 70.8 % | 62.8 % | 53.0 % |

## Conclusiones

1. **El ajuste mejora al bosque, sobre todo con longitud.** El AUC sube de 0.791 a 0.799 (diferencia pareada +0.008, IC 95 % +0.007 a +0.009) y la precisión con 10 000 hilos de 69.6 % a 71.4 %. Sin longitud la mejora es mínima (+0.001). La ganancia viene de árboles más profundos (hojas de 20 hilos) que miran más variables por pregunta.
2. **Empata con el MLP ajustado y con el boosting ajustado.** Diferencias pareadas de AUC: MLP − bosque = +0.0001 (IC −0.0012 a +0.0016); bosque − boosting = +0.0013 (IC −0.0001 a +0.0026). En la práctica los tres son equivalentes; sus puntajes están correlacionados en 0.96 o más. El bosque entrena en unos minutos y no necesita escalar variables.
3. **Lo grande no es el ajuste, es la no linealidad y la longitud.** El bosque le saca ~0.10 de AUC a la logística, y la longitud aporta ~0.07 de AUC.
4. **Sobre los haces que se pierden:** el bosque ajustado con longitud conserva entre sus 25 000 mejores el 25.0 % de los hilos verdaderos con peso 0 en COMMIT2 (la logística, 0.5 %). Sin longitud solo el 4.1 %: la longitud es lo que permite rescatarlos. Para medir de verdad «haces recuperados» hace falta `etiqueta_hausdorff.csv`, que no viene en el paquete.
5. **Limitaciones.** (a) Los hiperparámetros elegidos quedaron en el borde de la rejilla (hojas de 20 y la mitad de las variables), así que ampliarla podría dar una mejora pequeña adicional. (b) El intervalo de confianza solo refleja la variación del conjunto de prueba, no la de la semilla ni la de la partición. (c) Es un solo cerebro simulado y un solo tractograma: no sabemos si esto se traslada a otros datos.

## Cómo reproducirlo

```
pip install pandas scikit-learn numpy
python modelo_bosque_ajustado.py --longitud     # escribe puntaje_bosque_ajustado_long.txt
python modelo_bosque_ajustado.py                # escribe puntaje_bosque_ajustado.txt
python modelo_bosque_ajustado.py --rapido       # sin búsqueda de hiperparámetros (más rápido)
```
Con `tabla_hilos.csv` en la misma carpeta (o `--tabla ruta/tabla_hilos.csv`).
Tarda unos 3 minutos por variante en un equipo de un solo núcleo, y menos con más núcleos.

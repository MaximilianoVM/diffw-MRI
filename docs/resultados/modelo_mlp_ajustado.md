# Modelo: MLP ajustado (red neuronal del profesor, con entradas y entrenamiento afinados)

> **Integrado al repo el 2026-11-27** (entrega del grupo de modelos; llegó solo esta nota).
> **No vinieron:** el script original, los puntajes `puntaje_mlp_ajustado*.txt`, `comparacion_modelos.csv`, `modelo_mlp.py` ni `comparar_modelos.py`. Las cifras de abajo son las de la nota y **no se han verificado**.
> **Script reconstruido:** `scripts/modelo_mlp_ajustado.py`, escrito a partir de esta descripción; los detalles que la nota no especifica están marcados como supuestos en su encabezado. **No se ha corrido**; sus cifras pueden diferir ligeramente.
> **Reproducir desde la raíz:** `python scripts/modelo_mlp_ajustado.py --longitud` y `python scripts/modelo_mlp_ajustado.py` (requiere `torch`; ~10 min por variante; escriben en `out/modelos/`).
> **Pendiente:** con esos puntajes, el tractograma filtrado por haces (filas del MLP en `tab:modelos-haces` y `tab:haces-perdidos`).
> **Ojo al comparar:** la tabla de abajo usa el bosque y el boosting *sin ajustar* (0.795 / 0.796 con longitud). Contra los ajustados (0.799 / 0.798) el MLP empata.

**Archivos entregados:** `puntaje_mlp_ajustado_long.txt` (con longitud) y `puntaje_mlp_ajustado.txt` (sin longitud).
Ambos: 100 000 líneas, en el orden de `tabla_hilos.csv`, valores en [0, 1]. Script: `modelo_mlp_ajustado.py`.

## Qué se hizo

Se partió del `modelo_mlp.py` que recomendó el profesor (MLP en PyTorch, 64-32, 3 semillas,
intercambio de mitades) y se ajustó en dos frentes:

**Entradas.** Además de log(peso) de los 4 métodos y los indicadores «peso > 0» de COMMIT, LiFE y
COMMIT2, se agregó: el **rango percentil** de cada peso (ajustado solo con la mitad de
entrenamiento, con `QuantileTransformer`), el **número de métodos que conservaron el hilo**, y
—en la variante con longitud— **log(longitud)** y las **interacciones log(peso) × log(longitud)**.
Esto último es lo que más mueve el resultado: la red lineal por tramos no reconstruye sola el
producto peso × longitud, y esa interacción es justo donde el LEEME señalaba la oportunidad.

**Entrenamiento.** Red 128-64-32 con BatchNorm y dropout (0.15 / 0.10), AdamW con recocido coseno,
lotes de 1024, hasta 200 épocas con paciencia 15, partición de validación estratificada y promedio
de 5 semillas.

Reglas respetadas: no se usan `hd_min_mm` ni `etiqueta_5mm` como entrada; cada hilo se puntúa con un
modelo entrenado en la otra mitad; el AUC se reporta en `prueba`.

## Cómo se evaluó (y por qué solo con la mitad)

Se entrena solo con `conjunto == "entrenamiento"` y se reporta en `prueba`, como pide la regla 2 del
LEEME: si se entrena y se evalúa con los mismos hilos, el modelo ya vio las respuestas y el AUC sale
inflado — mide memoria, no capacidad de filtrar hilos nuevos.

No se desperdicia la mitad de los datos. Se hace el **intercambio de mitades** que ya traía
`ejemplo_modelo.py`:

1. entrenar con `entrenamiento` (50 000) → puntuar `prueba` (50 000);
2. entrenar con `prueba` → puntuar `entrenamiento`.

Son dos modelos, y cada hilo termina con un puntaje de un modelo que **no lo vio al entrenar**. Así
los 100 000 hilos quedan puntuados de forma honesta, que es lo que necesita la comparación de haces
del tractograma completo (sección 8 del LEEME). Con un solo modelo entrenado en una mitad, los otros
50 000 hilos se quedarían sin puntaje utilizable.

Dentro de cada entrenamiento se aparta además un 15 % estratificado como validación, solo para
decidir cuándo parar (early stopping): cada red ve ~42 500 hilos y nunca toca la otra mitad. El
rango percentil (`QuantileTransformer`) también se ajusta solo con la mitad de entrenamiento, para
no filtrar información de la mitad de evaluación.

Por eso los números se leen distinto según la columna:

- el **AUC se mide solo en `prueba`** (una sola mitad, sin contaminar) — es la cifra comparable
  contra el 0.683 de la logística del LEEME;
- las **precisiones usan los 100 000 hilos**, porque tras el intercambio todos son fuera de muestra;
  es la misma convención que imprime `ejemplo_modelo.py`.

No se entrenó un modelo final con los 100 000 hilos a propósito: no quedaría ningún hilo sin ver y
no habría forma honesta de reportar qué tan bueno es. El entregable de este proyecto *es* el archivo
de puntajes, así que tiene que ser fuera de muestra por construcción.

## Qué contiene el archivo de puntajes

`puntaje_mlp_ajustado_long.txt` (y su gemelo sin longitud): **100 000 líneas**, una por hilo, en el
mismo orden de `tabla_hilos.csv` (`hilo` 0, 1, 2…), un número por línea en [0, 1] — la probabilidad
estimada de que el hilo sea verdadero. Cuanto mayor, más creíble el hilo; para filtrar se ordena de
mayor a menor y se conservan los primeros n.

Lo que se obtiene al usarlo: conservando los **25 000** hilos de mayor puntaje, **62.8 %** son
verdaderos (contra 33.3 % sin filtrar y 50.3 % con la logística del ejemplo); con los **10 000**
mejores, **70.8 %**. Además rescata el **22.5 %** de los hilos verdaderos a los que COMMIT2 asigna
peso 0 — los de BPS, Fornix e ICP, los haces que los filtros precisos pierden enteros.

## Resultados

AUC en la mitad `prueba`; precisión sobre los 100 000 hilos puntuados por intercambio de mitades
(la misma convención que imprime `ejemplo_modelo.py`, cuya logística de 4 pesos reproduce
exactamente el 0.683 del LEEME).

| Modelo | longitud | AUC | 10 000 | 25 000 | 50 000 |
|---|---|---|---|---|---|
| logística (ejemplo del LEEME) | no | 0.683 | 45.0 % | 50.3 % | 46.0 % |
| logística (ejemplo del LEEME) | sí | 0.698 | 44.7 % | 48.4 % | 46.7 % |
| bosque aleatorio | no | 0.721 | 63.0 % | 56.4 % | 47.1 % |
| bosque aleatorio | sí | 0.795 | 70.3 % | 62.3 % | 52.6 % |
| boosting (`HistGradientBoosting`) | no | 0.728 | 64.0 % | 56.6 % | 47.5 % |
| boosting | sí | 0.796 | 70.6 % | 62.5 % | 52.6 % |
| MLP del profe (original) | no | 0.716 | 61.6 % | 55.4 % | 47.0 % |
| MLP del profe (original) | sí | 0.785 | 67.0 % | 60.3 % | 52.0 % |
| **MLP ajustado** | no | **0.727** | **63.8 %** | **56.5 %** | **47.6 %** |
| **MLP ajustado** | sí | **0.799** | **70.8 %** | **62.8 %** | **52.9 %** |

La tabla completa (incluye MLP de scikit-learn y las variantes con entradas enriquecidas para la
logística y el boosting) está en `comparacion_modelos.csv`.

*(La figura de comparación de modelos no vino en la entrega.)*

## Conclusiones

1. **El ajuste sí mejora al MLP original**: +0.014 de AUC sin longitud (0.716 → 0.727) y +0.014 con
   longitud (0.785 → 0.799); en precisión con 10 000 hilos, de 67.0 % a 70.8 %. La mayor parte de la
   ganancia viene de las entradas nuevas, no del tamaño de la red.
2. **El MLP ajustado queda primero en las cuatro medidas**, pero por muy poco sobre el boosting
   (0.799 vs 0.796 de AUC; 70.8 % vs 70.6 % con 10 000 hilos). La diferencia está dentro de lo que
   mueve una semilla: **en la práctica empatan**. El boosting entrena en segundos y el MLP en
   minutos, así que si hay que elegir uno solo, el boosting es el más barato; el MLP ajustado es el
   mejor si se quiere el número más alto.
3. **Lo grande no es el modelo, es la no linealidad**: cualquiera de los tres no lineales (bosque,
   boosting, MLP) le saca ~0.10 de AUC y ~25 puntos de precisión con 10 000 hilos a la logística.
   La logística es lineal y no puede representar «peso alto *y* hilo largo».
4. **La longitud aporta mucho** (+0.07 de AUC en los no lineales), así que todo se reporta con y sin
   ella, como pide el LEEME. Sin longitud el MLP ajustado sigue arriba (0.727), es decir, los pesos
   por sí solos ya se combinan mejor de forma no lineal.
5. **Sobre los haces que se pierden:** entre los 25 000 hilos mejor puntuados, el MLP ajustado con
   longitud rescata el **22.5 %** de los hilos verdaderos a los que COMMIT2 asigna peso 0
   (15 389 hilos; son los de BPS, Fornix e ICP). La logística rescata ~0.1 %. No está resuelto, pero
   es un cambio de orden de magnitud respecto al punto de partida. Para medir de verdad «haces
   recuperados» hace falta `etiqueta_hausdorff.csv`, que no viene en el paquete.
6. Es un solo cerebro simulado y un solo tractograma: no sabemos si esto se traslada a otros datos.

## Cómo reproducirlo

```
pip install torch pandas scikit-learn numpy
python modelo_mlp_ajustado.py --longitud     # escribe puntaje_mlp_ajustado_long.txt
python modelo_mlp_ajustado.py                # escribe puntaje_mlp_ajustado.txt
```
Con `tabla_hilos.csv` en la misma carpeta (o `--tabla out/modelos/tabla_hilos.csv`).
Tarda ~10 min por variante en una laptop sin GPU.

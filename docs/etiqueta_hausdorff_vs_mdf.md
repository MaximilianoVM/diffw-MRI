# Etiqueta por hilo: Hausdorff (la que pide el investigador) y MDF (la que usamos)

**Decisión:** la etiqueta oficial es Hausdorff, como se pidió en la junta. La MDF se conserva como **comparación complementaria**, y aquí se argumenta por qué vale la pena mostrarla.

## 1. Qué mide cada una

Las dos comparan un hilo del tractograma `y` con un hilo del GT `g`, y se queda con el `g` más cercano.

| | Hausdorff | MDF (distancia media directa) |
|---|---|---|
| Qué calcula | la **peor** discrepancia: el punto de un hilo más lejano del otro hilo (el máximo entre los dos sentidos) | la discrepancia **promedio** entre puntos que se corresponden en orden, con los dos hilos remuestreados a 20 puntos |
| Sensible a | un solo tramo que se aparta, aunque el resto coincida | el recorrido completo, punta a punta |
| Hilos de distinta longitud | un hilo que es un tramo de otro queda lejos (el tramo que sobra del largo manda) | queda lejos si los hilos no se corresponden extremo con extremo |
| Costo | alto sin poda (≈ 3 días por 10 000 hilos); ≈ 0.1 s por hilo con la poda de `scripts/hausdorff_bloque.py` | bajo (≈ 2 min para los 100 000 hilos con 1 000 hilos por haz) |
| Implementado | `scripts/hausdorff_bloque.py` (`docs/hausdorff_instrucciones.md`) | `scripts/normalizacion_ricardo.py` → `out/normalizacion/etiqueta_mdf.csv` |

## 2. Por qué argumentar MDF

1. **Es mucho más barata y ya está calculada.** Permite iterar rápido (cambiar el umbral, probar variantes) mientras se termina el Hausdorff.
2. **Es una medida estándar para comparar hilos:** QuickBundles (agrupamiento de fibras) la usa y DIPY la trae lista. Si el investigador la acepta, se ahorra el cálculo pesado.
3. **Es más estable.** Hausdorff depende de un único punto y es sensible a la longitud: un hilo cortado cerca de su extremo queda lejos del GT por unos milímetros. MDF promedia.
4. **Nuestro resultado depende fuertemente de la etiqueta**, así que conviene mostrar más de una. Con MDF < 5 mm el 54.8 % de los hilos "corresponde" al GT, pero solo el 3.9 % de los menores de 56 mm. Con una etiqueta por máscara es el 94 %. Una etiqueta que castiga la longitud cambia qué método parece mejor (`docs/resultados/normalizacion.md`, variantes).

## 3. Por qué Hausdorff sigue siendo necesaria

1. Es lo que pidió el investigador, y es una medida estándar para "este hilo está contenido en un hilo del GT".
2. No depende de que los extremos coincidan ni del remuestreo a 20 puntos.
3. La versión dirigida (`hd_dir_min`) responde justo a "¿este hilo está dentro de un haz real?", que es la pregunta de la junta, y no castiga a los hilos cortos que caen dentro de un haz.

## 4. Qué haremos con las dos

- Calcular Hausdorff (`out/hausdorff/hausdorff.csv`) y comparar con `etiqueta_mdf.csv`: de los hilos que cada una marca como válidos, cuántos coinciden (matriz de confusión, para varios ε) y si cambia el orden de los métodos.
- Si coinciden en lo importante, se presenta MDF como la versión rápida y Hausdorff como la oficial. Si no coinciden, se explica la diferencia (probablemente los hilos cortos).
- **Aún no está comprobado** que den resultados parecidos: se sabe cómo difieren en teoría, no cuánto en estos datos.

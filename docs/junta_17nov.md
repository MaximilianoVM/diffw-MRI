# Junta con el investigador (2026-11-17): objetivo

Transcripción de `docs/diff_MRI_junta17nov.pdf` (6 páginas de notas a mano). Lo que está entre [corchetes] es interpretación nuestra de la letra; hay que confirmarlo.

## Idea general

1. **Tractograma:** 100 000 hilos generados con MRtrix (`tckgen`).
2. **Tres métodos, tres vectores:** SIFT2, LiFE y COMMIT dan, cada uno, **un peso por hilo**: `x_S`, `x_L`, `x_C` ∈ ℝ^100 000. [Ejemplo en la página 1 para un hilo: `x_S = 0.01`, `x_L = 0.5`, `x_C = 0.45`.]
3. **Normalizar** cada vector a (0, 1).

**Sobre los 100 000 hilos:** no son "todos los posibles". `tckgen ... -select 100000` se detiene al aceptar 100 000 hilos; es un tamaño que se eligió (el GT tiene 189 985). Todos los métodos pesan **esos mismos 100 000**, en el orden de `data/tracks_100k.tck`.

## Filtrado simple (páginas 2 y 3)

Con un umbral ε [el valor 0.01 es de ejemplo; **está por definir**, ver `ACTUALIZACION.md`]: si el peso normalizado del hilo `i` en el método es menor que ε, el hilo `y_i` es **no válido**; si no, es **válido**. Cada método da así su tractograma filtrado, y los tres se comparan con el **ground truth** (página 3).

## Pregunta 1 (página 4): ¿qué hilos del tractograma corresponden al GT?

> ¿Qué "pelito" está en la estimación del tractograma de MRtrix y tiene correspondencia con el GT?

- Se usa la **distancia de Hausdorff** con un umbral: si `d_H(y_i, ŷ_j) < ε`, con `ŷ_j` un hilo del GT, entonces `y_i` **tiene correspondencia con el GT**.
- Para cada hilo `i` se calcula `d_H(y_i, ŷ_j)` contra **todos** los `j` del GT.
- Es costoso: [≈ 3 días por bloque de 10 000 hilos], así que se reparte en bloques (`i = 1…10 000`, `10 001…20 000`, …) entre varias personas o máquinas.
- Resultado: una **etiqueta 0/1 por hilo** (corresponde al GT o no).

## Pregunta 2 (página 5): ¿un modelo ayuda a filtrar mejor?

Cada hilo `y_i` tiene tres números `(x_iS, x_iL, x_iC)` y la etiqueta del GT (0/1). [En la nota hay una marca de verificación en S, C y GT, y una cruz en L: probablemente LiFE aún no estaba disponible; ahora sí. **LiFE se queda**, se desconoce por qué se marcó así.]

> Dados `x_S`, `x_L`, `x_C` y la etiqueta 0/1 del GT: ¿puedo entrenar un modelo que me ayude a tener un mejor resultado en el filtrado?

Modelo propuesto [es solo una propuesta: se puede usar otro, o este]: una combinación lineal `x_S·α + x_L·β + x_C·γ → {0, 1}` (es decir, una regresión logística o lineal sobre los tres pesos). Alternativa ya comentada con Ricardo: **voto** (el hilo es válido si al menos 2 de los 3 métodos lo aceptan), que sirve de comparación.

## Resultado final (página 6)

El **tractograma filtrado con el modelo entrenado** se compara contra el GT. COMMIT, SIFT2 y LiFE entran como datos de entrada del modelo.

## En resumen

| Paso | Qué es |
|---|---|
| A | Un vector de 100 000 pesos por método (ya hecho) |
| B | Normalizar a (0, 1) y filtrar con ε; comparar cada método con el GT |
| C | Etiqueta 0/1 por hilo con Hausdorff contra el GT |
| D | Entrenar un modelo `(x_S, x_L, x_C) → etiqueta` y comparar su tractograma filtrado con el GT |

**Lo que las notas no mencionan:** las matrices 84 × 84, COMMIT2, el barrido de λ, la normalización por longitud ni el análisis del eje `y`. Todo eso quedó como trabajo adicional (ver `docs/conclusiones.md`).

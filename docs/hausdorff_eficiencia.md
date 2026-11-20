# Por qué el Hausdorff tarda ~35 minutos por bloque y no días

Las notas de la junta (17-nov) estimaban **≈ 3 días por cada 10 000 hilos**. Nuestro cálculo tarda ≈ **0.12 s por hilo**
(≈ 20 min por 10 000). No es magia ni un atajo que cambie la respuesta: se evita medir lo que no puede ser una
respuesta. Este documento explica cómo, y presenta la comprobación de que el resultado es el mismo.

## 1. De dónde sale el "3 días"
Fuerza bruta: cada hilo `y` del tractograma se compara contra **los 189 985 hilos del GT**, punto contra punto.
Cada hilo tiene ~45 puntos a 2 mm (los hilos miden ≈ 90 mm) y el GT entero tiene ≈ 10 millones de puntos remuestreados.
Por hilo son ≈ 45 × 10 000 000 ≈ 450 millones de distancias, y hay que repetirlo 100 000 veces.

Medido aquí (ver §4), la fuerza bruta cuesta **≈ 22 s por hilo** incluso con el remuestreo a 2 mm
(sin remuestrear sería peor). Extrapolado: 22 s × 10 000 hilos ≈ 61 h ≈ **2.5 días**, que coincide con la estimación de las notas.

## 2. Qué hace nuestro script
`scripts/hausdorff_bloque.py`. La distancia de Hausdorff entre `y` y un hilo del GT `g` es
`d_H = max( max_{p∈y} d(p,g) , max_{q∈g} d(q,y) )`. La idea clave es una desigualdad:

> Si `d_H(y,g) < 10 mm`, **cada** punto de `y` está a menos de 10 mm de `g`, en particular el inicio, el medio y el
> final de `y`. Entonces `g` tiene un punto a menos de 10 mm de cada una de esas tres posiciones.

Contrapositivo: un `g` que no tiene ningún punto a menos de 10 mm de alguna de esas tres posiciones **no puede**
tener `d_H < 10`, y se puede descartar sin calcularle nada. El procedimiento:
1. Remuestrear GT e hilos a un punto cada 2 mm.
2. Construir un árbol KD (`scipy.spatial.cKDTree`) con los ≈ 10 millones de puntos del GT (se hace una vez, ≈ 1 min).
3. Para cada `y`, consultar al árbol qué hilos del GT tienen un punto a ≤ 10 mm de su inicio, de su medio y de su final,
   e intersectar las tres listas. Normalmente quedan decenas de hilos, no 189 985.
4. Calcular la Hausdorff **exacta** (matriz completa de distancias punto a punto) solo contra esos candidatos.
5. Si no queda ninguno, o el mejor pasa de 10 mm, se guarda vacío («más de 10 mm»).

Es decir: la poda solo descarta hilos del GT que **demostrablemente** están a más de 10 mm. Lo que sí se mide, se mide completo.

## 2.1. Dos fuentes de diferencia con la definición exacta
1. **Tope de 10 mm.** Solo sabemos «hd_min < 10 mm» o «más». Es suficiente porque ε será ≤ 10 mm (propuesta 5 mm, barrido 2–10).
2. **Remuestreo a 2 mm.** Se mide entre puntos, no entre segmentos. El error esperado es del orden de la mitad del paso (≤ 1 mm)
   y se midió mucho menor (§4).

## 3. Resumen de costos
| | Fuerza bruta | Nuestro script |
|---|---|---|
| Comparaciones por hilo | ≈ 450 millones | solo contra los candidatos (decenas de hilos del GT) |
| Tiempo por hilo | ≈ 22 s (medido) | ≈ 0.12 s (medido) |
| 10 000 hilos | ≈ 2.5 días | ≈ 20 min |
| 100 000 hilos | ≈ 25 días en una computadora | ≈ 3.3 h en una; ≈ 35 min por bloque con 7 |
| Memoria | alta | ≈ 2 GB (el GT remuestreado) |

## 4. Comprobación (40 hilos al azar)
Script: `scripts/validar_hausdorff_rapido.py` (semilla fija; 40 hilos de los 100 000, comparados contra los 189 985 del GT).

| Prueba | Resultado |
|---|---|
| Hilos con correspondencia < 10 mm | 23 de 40 con fuerza bruta y 23 de 40 con el método rápido |
| ¿Los mismos hilos quedan sin correspondencia? | Sí, coinciden los 40 |
| Diferencia máxima entre fuerza bruta y método rápido (mismo remuestreo) | **0.0 mm** |
| Efecto del remuestreo: 2 mm vs 1 mm (23 hilos comparables) | diferencia media 0.032 mm, máxima 0.236 mm |

Lectura: (a) la poda no pierde ningún candidato: da **exactamente** lo mismo que la fuerza bruta; (b) el remuestreo a 2 mm
cambia el resultado como máximo 0.24 mm, muy por debajo de los ε que se piensan usar (2–10 mm).

Limitaciones honestas: la muestra es de 40 hilos (no los 100 000: la fuerza bruta completa es justo lo que no se quiere correr);
la fuerza bruta de la comprobación también usa el remuestreo a 2 mm, así que el error de remuestreo se midió aparte comparando con 1 mm,
no contra el cálculo continuo exacto.

## 5. Repartir en bloques
Con el tiempo reducido, los 100 000 hilos son ≈ 3.3 h en una computadora. Se repartieron en 7 bloques (uno por persona, ≈ 14 286 hilos,
≈ 35 min cada uno) solo para terminar en una tarde. Los resultados son independientes entre hilos, así que repartir no cambia nada.
Instrucciones de reparto: `docs/hausdorff_instrucciones.md`.

## 6. Respuesta corta para el doctor
«No usamos otro criterio: es la misma distancia de Hausdorff simétrica contra los 189 985 hilos del GT. Lo único que hicimos fue
no calcularla contra los hilos del GT que, por geometría, están a más de 10 mm (un índice espacial KD-tree sobre los puntos del GT).
Comparamos con la fuerza bruta en 40 hilos al azar y el resultado es idéntico; el remuestreo a 2 mm cambia a lo más 0.24 mm.»

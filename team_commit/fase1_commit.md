# Fase 1: matriz 84 × 84 ponderada por COMMIT

Cierre de la fase 1 (10 nov 2026). Entregable: **`out/matriz_peso_commit_84x84_corregida.xlsx`**.

## ¿Está lista para entregar?

Sí, como matriz 84 × 84 ponderada por COMMIT.

- **Formato:** 84 × 84, simétrica, diagonal en cero, sin valores vacíos. Mismo formato que el Excel inicial (una hoja, R1–R84).
- **Región 15:** queda en cero porque no existe en `Parcels_free.nii`. Es correcto.
- **Parecido con el ground truth:** recupera 446 de las 529 conexiones reales, con AUC 0.83 por conexión. El Excel inicial recuperaba 125.
- **Reproducible:** `bash scripts/04_matrices.sh` vuelve a dar exactamente los mismos números con nuestro `tracks_100k.tck`.

Dos cosas a tener en cuenta:

- **Falta decidir la versión.** COMMIT a secas es la que se entrega y usa la misma definición que el Excel inicial. COMMIT × longitud concentra más peso en las conexiones reales (79 % contra 64 %). Las dos están en `out/`.
- **Depende del tractograma.** La matriz sale de nuestro `tracks_100k.tck`; con otro tractograma los números cambian un poco, porque `tckgen` es aleatorio.

## Correcciones respecto al Excel inicial

1. **Eje *y* de los gradientes invertido.** El `.bvec` necesita el eje *y* con el signo cambiado, y `dwigradcheck` lo confirma. Sin esa corrección los hilos salían de unos 42 mm de media y seguían direcciones equivocadas. Ahora miden 92 mm. La corrección se aplica en MRtrix y en COMMIT.
2. **`fiber_shift=0.5` en COMMIT.** MRtrix pone el centro del vóxel en 0 y COMMIT en 0.5. Sin el ajuste, los hilos quedaban desplazados medio vóxel respecto a la señal.
3. **`-mask` en `tckgen`,** para que los hilos no salgan del cerebro.
4. **Ball con `d_isos=[1.7e-3, 3.0e-3]`** en lugar de `[2.0e-3]`.

## Cómo cambia el resultado

Comparación con el conectoma del ground truth, que tiene 529 conexiones reales:

| | Excel inicial | Corregida |
|---|---|---|
| Conexiones del GT recuperadas | 125 | **446** |
| Conexiones de la matriz que existen en el GT | 21 % | **37 %** |
| Peso total en conexiones reales | 31 % | **64 %** |

Todas las matrices sobre el mismo tractograma de 100 000 hilos:

| Matriz | Conexiones > 0 | Del GT recuperadas | Peso en conexiones del GT | AUC por conexión |
|---|---|---|---|---|
| sin_pesos | 1322 | 460 | 81 % | — |
| sift2 | 1322 | 460 | 75 % | — |
| **commit** (entregada) | **1203** | **446** | **64 %** | **0.829** |
| commit_x_long | 1203 | 446 | 79 % | 0.846 |

**Lo que se mantiene:** la región 15 sigue en cero porque no existe en `Parcels_free.nii`.

**COMMIT a secas o × longitud:** el peso de COMMIT es por unidad de longitud, así que favorece las conexiones cortas. Multiplicando cada peso por la longitud del hilo, el peso en conexiones reales sube a 79 % (`out/matriz_commit_x_long.xlsx`).

**Por hilo, COMMIT no separa los buenos de los malos:** con la etiqueta por extremos da AUC 0.458, igual que el azar. Esto no afecta a la matriz, pero sí a la regla de decisión de la fase 2.

## Mensaje de entrega

> Hola, les paso la matriz 84 × 84 ponderada por COMMIT corregida: `matriz_peso_commit_84x84_corregida.xlsx`. Tiene el mismo formato que la que nos mandaron (una hoja, R1–R84).
>
> **Qué corregimos respecto al Excel inicial:**
>
> 1. **Eje *y* de los gradientes invertido.** El `.bvec` necesita el eje *y* con el signo cambiado, y `dwigradcheck` lo confirma. Sin esa corrección los hilos salían de unos 42 mm de media y seguían direcciones equivocadas. Ahora miden 92 mm. La corrección se aplica tanto en MRtrix como en COMMIT.
> 2. **`fiber_shift=0.5` en COMMIT.** MRtrix pone el centro del vóxel en 0 y COMMIT en 0.5. Sin el ajuste, los hilos quedaban desplazados medio vóxel respecto a la señal.
> 3. **`-mask` en `tckgen`,** para que los hilos no salgan del cerebro.
> 4. **Ball con `d_isos=[1.7e-3, 3.0e-3]`** en lugar de `[2.0e-3]`.
>
> **Cómo cambia el resultado,** comparando con el conectoma del ground truth (529 conexiones reales):
>
> | | Excel inicial | Corregida |
> |---|---|---|
> | Conexiones del GT recuperadas | 125 | **446** |
> | Conexiones de la matriz que existen en el GT | 21 % | **37 %** |
> | Peso total en conexiones reales | 31 % | **64 %** |
>
> **Lo que se mantiene:** la región 15 sigue en cero porque no existe en `Parcels_free.nii`.
>
> **Pendiente de decidir:** el peso de COMMIT es por unidad de longitud, así que favorece las conexiones cortas. Si se multiplica cada peso por la longitud del hilo, el peso en conexiones reales sube a 79 %. También tenemos esa versión (`matriz_commit_x_long.xlsx`), por si prefieren usarla.
>
> Los comandos completos están en `pipeline.md`.

## Pasos siguientes (fase 2)

1. **Decidir en equipo** si la matriz oficial es COMMIT a secas o × longitud.
2. **Que el otro equipo reproduzca.** Que instalen MRtrix 3.0.8 y Python 3.13, descarguen `tracks_100k.tck` de Drive y corran `02 --sin-tckgen`, `03` y `04`. Deben salir los números de control de `pipeline.md`.
3. **Repartir el trabajo:** quién hace LiFE, quién SIFT2 y quién la etiqueta por haz.
4. **Pesos de LiFE (DIPY)** sobre el mismo `tracks_100k.tck`. Si no cabe en memoria, acordar un subconjunto común con `tckedit -number 20000` y correr los tres métodos sobre él.
5. **Etiqueta por haz contra el GT** (`data/GT/*.tck`), común a los tres métodos. La etiqueta por extremos es débil: el 21 % de los hilos del propio GT no termina en ninguna región.
6. **Evaluar los tres métodos por hilo** con `scripts/evaluar_pesos.py` y la etiqueta nueva: AUC, qué descarta cada uno y si coinciden entre sí.
7. **Comprobar la hipótesis de redundancia de COMMIT:** que peso 0 signifique "redundante" y no "falso". Por ejemplo, correr COMMIT con menos hilos y ver si bajan los pesos en 0 entre los hilos buenos.
8. **Diseñar la regla de decisión** que combine COMMIT, SIFT2 y LiFE para conservar o descartar cada hilo. Medirla con la misma etiqueta.

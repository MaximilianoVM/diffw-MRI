# Estado del proyecto (2026-11-10)

## Entregable: matriz de peso COMMIT 84 × 84

**Tenemos la matriz, pero la generó el otro equipo, no nosotros.**
Está en `equipo_chat/matriz_peso_commit_84x84_corregida.xlsx`. Su hoja mide A1:CG85, o sea 84 filas y 84 columnas más los encabezados R1–R84. No la hemos abierto para revisar los valores.
**En este repo todavía no hemos corrido ningún paso.** `out/` solo tiene archivos viejos.

## Paso a paso

| Paso | Script | Estado en este repo |
|---|---|---|
| 1. Gradientes con `y` invertido, máscara, respuesta, FOD | `01_preprocess.sh` | Escrito, **sin correr** |
| 2. Tractograma 100k, longitudes, SIFT2 | `02_tractography.sh` | Escrito, **sin correr** |
| 3. COMMIT | `03_commit.sh` | Escrito, **sin correr** |
| 4. Matrices 84 × 84, Excel, evaluación | `04_matrices.sh` | Escrito, **sin correr** |

"Escrito" quiere decir que la sintaxis es válida y que los comandos son los del otro equipo. No se ha probado con los datos de este repo.

## Qué falta para tener nuestra propia matriz

1. ~~Un entorno con MRtrix3 y COMMIT.~~ Listo: `conda activate dwmri` (ver `environment.yml`).
2. El `tracks_100k.tck` del otro equipo (por Drive, 109 MB), para obtener sus mismos números.
3. Correr los pasos 1 a 4. Con 11 GB de RAM, COMMIT podría dar `Killed`; en ese caso, subconjunto de 20 000 hilos.
4. Comparar con los números de control de `pipeline.md`: media de longitud ≈ 92 mm, NRMSE ≈ 0.106, 446 conexiones del GT recuperadas.

## Lo que ya sabemos (según el otro equipo, sin reproducir)

- Con el eje `y` invertido los hilos miden ≈ 92 mm en vez de ≈ 42 mm.
- COMMIT recupera 446 de 529 conexiones del GT; la versión anterior recuperaba 125.
- COMMIT pone en 0 el 45 % de los hilos, y casi todas las conexiones que elimina son falsas.
- Ningún método por sí solo limpia el tractograma: quedan ≈ 750 conexiones que no existen en el GT.

## Pendiente del proyecto

- LiFE: sin empezar.
- Etiqueta por haz contra el GT: sin hacer (la aproximación actual da AUC 0.46 por hilo).
- Regla de decisión que combine COMMIT, SIFT2 y LiFE: sin empezar.
- Decidir si se entrega COMMIT a secas o × longitud.
- Reparto del trabajo entre los equipos: sin decidir.

## Archivos en la raíz

| Archivo | Qué es |
|---|---|
| `README.md`, `pipeline.md` | el proyecto y sus pasos |
| `estado.md` | este archivo |
| `para_equipo_organizar.md` | lo que le pasamos al otro equipo para que organice su proyecto como el nuestro |
| `pedido_para_su_claude.md` | el pedido anterior, ya cumplido; se puede borrar |
| `equipo_chat/`, `team_commit/` | lo que mandó el otro equipo (versión corregida y versión vieja) |

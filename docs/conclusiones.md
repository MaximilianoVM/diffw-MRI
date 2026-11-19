# Conclusiones hasta ahora (2026-11-17)

> **Nota (18 nov):** tras la junta con el investigador el objetivo es más simple (`docs/junta_17nov.md`). Estas conclusiones cubren todo lo hecho, incluido lo adicional (matrices 84 × 84, COMMIT2, normalización por longitud).

Resumen de lo que sabemos con los cuatro métodos (COMMIT, SIFT2, COMMIT2 y LiFE) sobre **el mismo tractograma**: `data/tracks_100k.tck`, 100 000 hilos, `md5` `66ba3e6efe1fadf5b534d3947b2b138f`. Cada punto dice dónde está el detalle.

> Los números salen de las corridas de la Mac (documentos de abajo). **Esta laptop no los reprodujo**, salvo el conteo del tractograma y las matrices de LiFE antiguas.

## 1. Estado

| Método | Pesos por hilo | Matriz 84 × 84 | Quién |
|---|---|---|---|
| COMMIT | `out/commit/pesos_commit.txt` | `matriz_peso_commit_84x84_corregida.xlsx` (entregable) | nosotros |
| SIFT2 | `out/pesos_sift2.txt` | `out/matriz_sift2.xlsx` | equipo SIFT2 / nosotros |
| COMMIT2 | `out/commit2/pesos_commit2.txt` (λ = 1e-2; también 5e-3, 1e-3, 1e-4) | `out/matriz_commit2.xlsx` | nosotros |
| LiFE | `out/life/pesos_life.txt` (llegó el 14 nov) | `out/matriz_peso_life_84x84.xlsx` | equipo LiFE |

La matriz anterior de LiFE (su propio tractograma, 653 conexiones, 132 del GT) quedó descartada: no salía de nuestro `.tck`. La nueva sí.

## 2. Por conexión (la matriz 84 × 84)

**Cómo se construye una matriz y qué significa "conteo", "pesos" y "× longitud"**

Cada celda `(i, j)` de la matriz junta los hilos del tractograma que unen la región `i` con la región `j`. Lo que cambia es **cuánto aporta cada hilo** a su celda:

| Matriz | Cada hilo aporta | Celda `(i, j)` | Cómo se hace |
|---|---|---|---|
| **Conteo (sin pesos)** | 1 | cuántos hilos unen `i` con `j` | `tck2connectome` sin `-tck_weights_in` |
| **Con pesos** (SIFT2, COMMIT, COMMIT2, LiFE) | el peso que le dio el método | suma de los pesos de esos hilos | `tck2connectome ... -tck_weights_in pesos.txt` |
| **COMMIT × longitud** | su peso × su longitud en mm | suma de `peso × longitud` | se multiplica cada peso por `out/longitudes.txt` y se vuelve a armar la matriz |

- **El conteo es el control:** es lo que sale si no usamos ningún método, solo el tractograma tal cual. Si un método con pesos no queda mejor que el conteo, sus pesos no aportan información a nivel de matriz.
- **"Mejora al conteo"** significa: la matriz con pesos se parece **más al GT** que la matriz de conteo, con las mismas tres medidas de la tabla:
  - *% peso en GT:* de todo el peso de la matriz, qué fracción cae en conexiones que existen en el GT (más alto = mejor).
  - *AUC conexión:* si ordenamos las conexiones por su valor, qué tan arriba quedan las reales (0.5 = azar, 1 = perfecto).
  - *Pearson con GT:* correlación entre la matriz y la matriz del GT.
- **Por qué × longitud en COMMIT:** el peso de COMMIT es por unidad de longitud, así que un hilo corto puede tener peso alto solo por ser corto. Multiplicar por la longitud devuelve su aporte total y quita ese sesgo hacia los cortos. Por eso COMMIT × longitud queda mejor que COMMIT a secas (Pearson 0.881 contra 0.731). SIFT2, COMMIT2 y LiFE no lo necesitan para la matriz.
- La diagonal (hilos con los dos extremos en la misma región) se pone en 0 en todas.

GT: 529 conexiones reales de 3486 pares. Sin pesos, el tractograma ya tiene 1322 conexiones y recupera 460.

| Matriz | Conexiones > 0 | Del GT | % peso en GT | AUC conexión | Pearson con GT |
|---|---|---|---|---|---|
| sin pesos (control) | 1322 | 460 | 80.5 | 0.857 | 0.894 |
| SIFT2 | 1322 | 460 | 74.6 | 0.850 | 0.795 |
| COMMIT | 1203 | 446 | 63.8 | 0.829 | 0.731 |
| COMMIT × longitud | 1203 | 446 | 79.0 | 0.846 | 0.881 |
| COMMIT2 (λ = 1e-2) | 86 | 70 | 91.9 | 0.564 | 0.788 |
| **LiFE** | 1168 | 442 | **90.7** | 0.851 | **0.923** |

1. **LiFE es el único cuya matriz con pesos queda mejor que la de conteo** en % de peso en el GT (90.7 contra 80.5) y en Pearson (0.923 contra 0.894), y casi la iguala en AUC. Pone en 0 (descarta) 154 de las 1322 conexiones y pierde solo 18 reales.
2. **COMMIT y SIFT2 quedan peor que el conteo** en esas medidas. COMMIT solo se acerca si se multiplica por la longitud (ver arriba).
3. **COMMIT2 con λ alto apaga conexiones reales.** Con λ = 1e-2 solo deja 86 conexiones. λ es una perilla entre limpieza y cobertura (ver 4).
4. Detalle: `docs/resultados/matrices.md`.

## 3. Por hilo (¿distingue hilos buenos de malos?)

AUC por hilo contra la etiqueta MDF (MDF < 5 mm a un haz del GT). 0.5 es azar.

| Puntaje | AUC |
|---|---|
| SIFT2 | 0.345 |
| COMMIT | 0.420 |
| LiFE | 0.655 |
| COMMIT2 (λ = 1e-2) | 0.684 |
| **longitud del hilo sola** | **0.747** |

1. **COMMIT y SIFT2 ordenan al revés** (AUC < 0.5): sus pesos altos caen más en hilos falsos.
2. **COMMIT2 y LiFE sí separan** (0.65–0.68), y casi no se parecen a COMMIT ni a SIFT2 hilo por hilo (Spearman ≈ 0).
3. **La longitud sola le gana a todos.** Los hilos verdaderos miden 107.5 mm de media y los falsos 73.6 mm. COMMIT y SIFT2 favorecen cortos; COMMIT2 y LiFE favorecen largos (Spearman con la longitud +0.27 y +0.26).
4. **Dentro de un mismo rango de longitud**, COMMIT y SIFT2 casi no aportan (AUC 0.45–0.57).
5. Detalle: `docs/resultados/normalizacion.md`.

## 4. COMMIT2 y el valor de λ

| | COMMIT | λ = 1e-4 | λ = 1e-3 | λ = 5e-3 | λ = 1e-2 |
|---|---|---|---|---|---|
| Peso = 0 | 44.8 % | 50.5 % | 51.0 % | 58.3 % | 63.1 % |
| Conexiones del GT (de 529) | 446 | 337 | 172 | 99 | 70 |
| Haces detectados (de 21) | 21 | 21 | 21 | 20 | 17 |
| % fibras falsas (sin filtrar: 45.2) | 48.7 | 41.7 | 31.2 | 25.0 | 21.2 |
| Dice (sin filtrar: 0.750) | 0.750 | 0.740 | 0.704 | 0.633 | 0.545 |

- Subir λ baja las falsas pero pierde haces y conexiones reales.
- **λ = 1e-4 y 1e-3** son los puntos útiles: conservan los 21 haces. Con 1e-4 se bajan las falsas casi sin costo; con 1e-3 se bajan más (31 %) a cambio de Dice 0.70.
- **Nota:** el COMMIT2 es nuestro (Sarahi lo dejó a medias y lo terminamos nosotros). Su corrida inicial reportaba 62 779 hilos activos con λ = 1e-2 y la nuestra da 36 928. No es un pendiente: la nuestra es la versión de referencia, con grupos por par de regiones, pesos de grupo adaptativos y el tractograma oficial. Detalle: `docs/resultados/commit2.md`.

## 5. Combinar métodos (normalización de Ricardo)

Se implementó (`scripts/normalizacion_ricardo.py`, con test del ejemplo) y se evaluó contra el GT haz por haz.

1. **Con COMMIT + SIFT2 solo, no sirve.** El umbral óptimo siempre es el mínimo (conservar casi todo), subir el umbral aumenta las falsas (47 → 60 %), y nada supera a "sin filtrar". La causa principal es la longitud.
2. **Normalizar por rango de longitud** (`--por-longitud 10`) mejora el AUC del score en 0.07–0.09 y hace que subir el umbral deje de empeorar. Es una variante nuestra, no de la especificación original (`docs/resultados/normalizacion.md`).
3. **La mejor combinación hasta ahora: COMMIT2 + LiFE con percentil global y u = 0.1.** Conserva 66 287 hilos y los 21 haces, con 33.8 % de falsas (sin filtrar: 45.2 %) y Dice 0.736. Su score tiene AUC 0.713, por encima de cada método solo.
4. **Pero con el mismo número de hilos, COMMIT2 solo y LiFE solo ganan o empatan** a partir de u = 0.3. Agregar COMMIT y SIFT2 al promedio ensucia el score.
5. **COMMIT y SIFT2 sirven por conexión (matriz), no para elegir hilos.**

## 6. Cuidados (cómo leer todo esto)

- **La etiqueta MDF está sesgada por longitud:** castiga a los hilos cortos (solo el 3.9 % de los menores de 56 mm cuenta como verdadero). La etiqueta por máscara, en cambio, es demasiado permisiva (94 % verdaderos). Ninguna es buena; falta una intermedia. Parte de "COMMIT va al revés" viene de la etiqueta.
- **El Dice no sirve para elegir el umbral:** queda entre 0.746 y 0.759 en 40 combinaciones y el máximo siempre es "sin filtrar".
- **El umbral se elige con el mismo GT con que se evalúa:** es optimista.
- **"Peso 0 = eliminó"** es una hipótesis. SIFT2 nunca da 0, por eso se usa `--corte` (el 45 % inferior pasa a 0).
- **Si se compara con COMMIT2 solo** en n grandes, tiene solo 36 928 hilos con peso > 0 y se completa con ceros al azar.
- **El eje `y`:** cambia la tractografía (hilos de ≈ 40 a ≈ 92 mm); en SIFT2 casi no cambia los pesos (0.989). En COMMIT y LiFE no se aisló su efecto (la mejora de COMMIT mezcla cuatro cambios). Ver `docs/explicacion_commit.md`.

## 7. Qué recomendamos hoy

| Para qué | Usar |
|---|---|
| Matriz de conectividad | **LiFE** (mejor que el conteo); COMMIT (a secas o × longitud) como entregable propio del equipo |
| Filtrar hilos | **COMMIT2 + LiFE**, percentil global, u = 0.1–0.2; o COMMIT2 con λ = 1e-3 si se quiere un solo método |
| No usar para elegir hilos | COMMIT y SIFT2 por separado |

## 8. Pendiente

1. Regenerar los mapas de COMMIT que se pisaron: `bash scripts/03_commit.sh` (≈ 75 s en la Mac).
2. **Etiqueta intermedia por haz** (p. ej. fracción de puntos del hilo a ≤ 2 mm del haz). Las dos actuales están sesgadas.
3. Elegir el umbral con la mitad de los haces y evaluar con la otra.
4. Decidir λ, y si COMMIT2 reemplaza a COMMIT en la combinación.
5. Aislar cuánto aporta el eje `y` en COMMIT y LiFE (`--sin-corregir-y` en la Mac).
6. Avisar al equipo SIFT2 y a LiFE: usar `-zero_diagonal`.
7. Rehacer el enfoque según la junta del 17 de nov (`docs/junta_17nov.md`): etiqueta por Hausdorff y modelo entrenado.

## Dónde está cada cosa

| Tema | Archivo |
|---|---|
| Matrices y comparación de los cuatro métodos | `docs/resultados/matrices.md` |
| COMMIT2, barrido de λ | `docs/resultados/commit2.md` |
| Normalización Ricardo con COMMIT + SIFT2 (+ COMMIT2) | `docs/resultados/normalizacion.md` |
| Percentil por longitud, con LiFE | `docs/resultados/normalizacion.md` |
| Qué hace COMMIT y cómo leer la matriz | `docs/explicacion_commit.md` |
| Cosas por aclarar entre equipos | `docs/explicacion_commit.md` |

# Normalización de Ricardo: resultados

Evaluación de la idea de `docs/equipos/Normalizacion Ricardo.md` (percentil por rango de los pesos, promedio y umbral) contra el GT. Tres partes:

- **A. Resultados** con COMMIT + SIFT2 (+ COMMIT2): implementación, resultados, variantes de etiqueta.
- **B. Percentil por rango de longitud** (variante nuestra) y resultados con LiFE.
- **C. Consideraciones iniciales** (revisión antes de implementar; ya resueltas en A y B).

Se corre con `bash scripts/07_normalizacion.sh`. Código: `scripts/normalizacion_ricardo.py`, test: `scripts/test_normalizacion.py`.

---

# A. Resultados


### Actualización: con COMMIT2 (COMMIT + SIFT2 + COMMIT2)

COMMIT2 se corrió aquí con `scripts/correr_commit2.py` (λ = 1e-2, group lasso por par de regiones, pesos de grupo por cardinalidad y adaptativos), en 1 min 6 s.

**Dos arreglos al script de Maximiliano:**
1. Con `group_weights_adaptive=True`, COMMIT exige un ajuste sin regularizar antes (`Group weights cannot be computed if the fit without regularisation has not been performed before`). Se agregó `mit.fit()` antes de `set_regularisation`.
2. `save_results()` guardaba en la carpeta del diccionario de COMMIT (`out/commit/COMMIT/Results_StickZeppelinBall/`) y **pisaba los resultados detallados de COMMIT**. Ahora guarda con el sufijo `_COMMIT2` y mueve todo a `out/commit2/`. Los pesos de COMMIT (`out/commit/pesos_commit.txt`) no se tocaron. Los mapas de NRMSE y compartimentos de COMMIT se perdieron en la primera corrida y se recuperan con `bash scripts/03_commit.sh` (≈ 75 s).

**Ojo:** nuestra corrida deja **36 928 hilos con peso > 0 (63 % en 0)**. La de la compañera reportaba 62 779 con el mismo λ. Puede deberse a los pesos de grupo adaptativos, a otros grupos (ella usó 85 × 85 con el nodo 0) o a otro tractograma. Hay que preguntarle.

#### COMMIT2 solo

| | COMMIT | SIFT2 | **COMMIT2** |
|---|---|---|---|
| Peso = 0 | 44.8 % | 0 % | 63.1 % |
| Spearman con la longitud | −0.20 | −0.41 | **+0.27** (favorece los largos) |
| AUC por hilo, etiqueta MDF | 0.420 | 0.345 | **0.684** |
| AUC por hilo, etiqueta por extremos | 0.458 | 0.430 | **0.804** |
| Matriz: conexiones > 0 / del GT | 1203 / 446 | 1322 / 460 | **86 / 70** |
| Matriz: % peso en GT / AUC conexión / Pearson | 64 % / 0.829 / 0.731 | 75 % / 0.850 / 0.795 | 92 % / 0.564 / 0.788 |
| Haces detectados / % fibras falsas / cobertura (peso > 0) | 21 / 48.7 / 0.776 | 21 / 45.2 / 0.818 | **17 / 21.2 / 0.540** |

Es el primer método que **separa hilos buenos de malos** (AUC 0.68–0.80), y casi no se correlaciona con COMMIT ni con SIFT2 (Spearman por hilo ≈ 0.01). El precio: con λ = 1e-2 apaga conexiones completas. Se queda con 86 de 1322 conexiones, recupera solo 70 de las 529 reales y pierde 4 de los 21 haces. La AUC por extremos (0.80) está inflada, porque los grupos de COMMIT2 se definen con los mismos pares de regiones que esa etiqueta. La de MDF (0.68) es la más honesta.

#### Normalización con los tres

| Versión | Hilos | Haces | % falsas ↓ | Cobertura ↑ | Desborde ↓ | Dice ↑ | MDF ↓ | Lugar |
|---|---|---|---|---|---|---|---|---|
| **promedio ≥ 0.1** | 82 873 | 21 | 46.5 | **0.797** | 0.303 | 0.743 | **2.55** | **2.0** |
| promedio ≥ 0.2 | 66 821 | 21 | 47.4 | 0.776 | 0.265 | **0.744** | 2.59 | 2.4 |
| promedio ≥ 0.3 | 49 364 | 21 | 47.9 | 0.738 | 0.216 | 0.738 | 2.65 | 3.2 |
| promedio ≥ 0.4 | 35 066 | 20 | 49.3 | 0.689 | 0.166 | 0.721 | 2.57 | 3.2 |
| promedio ≥ 0.5 | 22 162 | 20 | 52.0 | 0.604 | **0.106** | 0.681 | 2.87 | 4.2 |
| *sin filtrar* | *100 000* | *21* | *45.2* | *0.818* | *0.332* | *0.750* | *2.47* | — |

Con COMMIT2, el % de falsas sube mucho menos con el umbral (de 46.5 a 52.0, contra 47.1 a 59.5 con solo COMMIT + SIFT2), pero sigue sin bajar del tractograma sin filtrar. El ganador sigue siendo 0.1.

#### Con el mismo número de hilos

| Umbral (n) | Combinado | COMMIT solo | SIFT2 solo | COMMIT2 solo |
|---|---|---|---|---|
| | % falsas / cobertura / Dice | | | |
| 0.3 (49 364)* | 47.9 / 0.738 / 0.738 | 49.8 / 0.764 / 0.748 | 56.8 / 0.721 / 0.726 | **30.9** / 0.749 / 0.739 |
| 0.4 (35 066) | 49.3 / 0.689 / 0.721 | 53.9 / **0.728** / **0.742** | 62.5 / 0.662 / 0.702 | **19.4** / 0.535 / 0.543 (17 haces) |
| 0.5 (22 162) | 52.0 / 0.604 / 0.681 | 61.2 / **0.658** / **0.719** | 69.2 / 0.553 / 0.639 | **18.0** / 0.459 / 0.507 (16 haces) |

\* COMMIT2 solo tiene 36 928 hilos con peso > 0. En 0.1–0.3 completa con hilos de peso 0 elegidos al azar, así que ahí no es del todo comparable.

**Lectura:**
- **COMMIT2 es el más preciso:** solo 18–19 % de falsas.
- **COMMIT es el que mejor cubre los haces:** mayor cobertura y Dice.
- **El combinado queda en medio en todo** y no gana en ninguna métrica principal.
- **SIFT2 es el peor en todo**, salvo en desborde.

La decisión depende de qué importe más: tractograma limpio (COMMIT2) o haces completos (COMMIT). Antes de decidir conviene **probar un λ más chico en COMMIT2** (p. ej. `--lambda=5e-3` o `1e-3`): debería conservar más haces sin perder tanta precisión.

---

### Umbrales fijos 0.1–0.5 (lo que se pidió)

Procedimiento: en cada método se ordenan los hilos de menor a mayor peso y cada uno recibe su lugar/n (los de peso 0 se quedan en 0). Luego se promedian, hilo por hilo, las ponderaciones de los métodos. Con ese promedio se arman **cinco versiones del tractograma**, eliminando los hilos con promedio < 0.1, 0.2, 0.3, 0.4 y 0.5. Cada versión se compara contra el GT, haz por haz, con las métricas de la especificación (etiqueta MDF < 5 mm).

```bash
bash scripts/07_normalizacion.sh
# o: python scripts/normalizacion_ricardo.py --umbrales 0.1 0.2 0.3 0.4 0.5 --salida out/normalizacion/umbrales
```

| Versión | Hilos conservados | % conservado | Conductos detectados | % fibras falsas ↓ | Cobertura ↑ | Desborde ↓ | Dice ↑ | MDF simétrico (mm) ↓ | Lugar promedio |
|---|---|---|---|---|---|---|---|---|---|
| **promedio ≥ 0.10** | 84 278 | 84.3 | 21 | **47.1** | **0.804** | 0.313 | **0.749** | **2.49** | **1.8** |
| promedio ≥ 0.20 | 69 862 | 69.9 | 21 | 50.0 | 0.783 | 0.276 | 0.744 | 2.58 | 2.4 |
| promedio ≥ 0.30 | 55 700 | 55.7 | 21 | 53.3 | 0.761 | 0.242 | 0.743 | 2.63 | 3.2 |
| promedio ≥ 0.40 | 42 774 | 42.8 | 21 | 56.8 | 0.731 | 0.204 | 0.738 | 2.70 | 3.8 |
| promedio ≥ 0.50 | 31 493 | 31.5 | 20 | 59.5 | 0.690 | **0.167** | 0.723 | 2.59 | 3.8 |
| *ref.: COMMIT solo (peso > 0)* | *55 220* | *55.2* | *21* | *48.7* | *0.776* | *0.253* | *0.750* | *2.58* | — |
| *ref.: sin filtrar* | *100 000* | *100* | *21* | *45.2* | *0.818* | *0.332* | *0.750* | *2.47* | — |

Lugares por métrica (1 = mejor): 0.10 gana en Dice, cobertura, MDF y % de falsas; 0.50 gana solo en desborde, porque al conservar menos hilos se sale menos del haz.

**El que más se acerca al GT es "promedio ≥ 0.10"**, el que menos elimina. Cada umbral más alto empeora casi todas las métricas, y ninguno supera a "sin filtrar". La explicación está en las secciones de abajo: hilo por hilo, los pesos de COMMIT y SIFT2 favorecen los hilos cortos, y la etiqueta MDF marca la mayoría de los cortos como falsos. Por eso, mientras más se filtra, más proporción de falsos queda.

Archivos en `out/normalizacion/umbrales/`: `resumen_umbrales.csv` (con el lugar en cada métrica), `resultados_por_conducto.csv`, `combinado_u0.10.tck` … `combinado_u0.50.tck` y `keep_u0.10.txt` … `keep_u0.50.txt` (un 0/1 por hilo).

#### Comparado con COMMIT solo y SIFT2 solo, con el mismo número de hilos

Comparar con "cada método con peso > 0" es injusto: SIFT2 nunca da 0, así que no eliminaría nada. Para que la comparación sea justa, en cada umbral cada método solo conserva **los mismos n hilos** que la versión combinada: los de mayor peso según ese método (`comparacion_mismo_n.csv`).

| Umbral (n hilos) | Versión | % falsas ↓ | Cobertura ↑ | Desborde ↓ | Dice ↑ | MDF (mm) ↓ |
|---|---|---|---|---|---|---|
| 0.1 (84 278) | combinado | 47.1 | 0.804 | 0.313 | **0.749** | **2.49** |
| | COMMIT solo | **46.0** | **0.806** | **0.309** | 0.748 | 2.53 |
| | SIFT2 solo | 47.3 | 0.801 | 0.314 | 0.747 | 2.50 |
| 0.2 (69 862) | combinado | 50.0 | 0.783 | 0.276 | 0.744 | 2.58 |
| | COMMIT solo | **47.1** | **0.795** | 0.282 | **0.751** | **2.55** |
| | SIFT2 solo | 50.5 | 0.770 | **0.275** | 0.736 | 2.63 |
| 0.3 (55 700) | combinado | 53.3 | 0.761 | 0.242 | 0.743 | 2.63 |
| | COMMIT solo | **48.6** | **0.777** | 0.254 | **0.751** | **2.58** |
| | SIFT2 solo | 54.7 | 0.740 | **0.237** | 0.731 | 2.71 |
| 0.4 (42 774) | combinado | 56.8 | 0.731 | 0.204 | 0.738 | 2.70 |
| | COMMIT solo | **51.4** | **0.748** | 0.209 | **0.745** | **2.45** |
| | SIFT2 solo | 59.4 | 0.699 | **0.196** | 0.719 | 2.81 |
| 0.5 (31 493) | combinado | 59.5 | 0.690 | 0.167 | 0.723 | 2.59 |
| | COMMIT solo | **55.5** | **0.715** | 0.170 | **0.739** | **2.53** |
| | SIFT2 solo | 64.3 | 0.640 | **0.155** | 0.692 | 2.97 |

**Lectura:**
- **COMMIT solo es el mejor en casi todo** a partir de 0.2: menos fibras falsas, más cobertura, mejor Dice y mejor MDF.
- **SIFT2 solo es el peor**, salvo en desborde. Que gane ahí no es buena señal: se queda con hilos más cortos, que ocupan menos vóxeles.
- **El combinado queda en medio, siempre peor que COMMIT solo.** Promediar con SIFT2 arrastra a COMMIT hacia abajo, porque SIFT2 ordena peor los hilos.
- **Ojo con 0.1 y 0.2:** COMMIT solo tiene 55 220 hilos con peso > 0. Para llegar a 84 278 (u = 0.1) y a 69 862 (u = 0.2), COMMIT tiene que completar con hilos de peso 0 elegidos al azar. En esos dos umbrales, su ventaja viene en parte de esa selección al azar. Desde 0.3, la comparación es limpia.
- **Ninguna versión supera a "sin filtrar"** (45.2 % de falsas, cobertura 0.818, Dice 0.750), por la razón explicada abajo: los pesos favorecen los hilos cortos y la etiqueta MDF los cuenta como falsos.

---

Implementación de `docs/Normalizacion Ricardo.md` con los dos métodos que ya pesan el tractograma oficial. **LiFE queda pendiente**: entra solo cuando exista `out/life/pesos_life.txt`.

```bash
bash scripts/07_normalizacion.sh      # test + normalización + evaluación (≈ 4 min la primera vez, 30 s después)
```

### Qué se implementó

| Sección de la especificación | Dónde | Estado |
|---|---|---|
| 1. Verificar longitud y orden de los pesos | `normalizacion_ricardo.py` | ✅ se detiene si no hay 100 000 pesos ≥ 0 sin NaN |
| 3. Rango percentil (`rankdata` promedio, 0 se queda en 0) | `a_percentil()` | ✅ |
| 4. Test con el ejemplo | `scripts/test_normalizacion.py` | ✅ da 0.33, 0.92, 0.25, 0.17, 0.83; se conservan las fibras 2 y 5 |
| 5. Combinación (promedio ≥ umbral) y voto mayoritario | `combinar()` | ✅ voto = peso > 0 en más de la mitad de los métodos |
| 6. Barrido del umbral 0.10–0.90 (paso 0.05), Dice máximo, `curva_umbral.png` | | ✅ |
| 7. Asignación por MDF (20 puntos, < 5 mm al haz más cercano), métricas por haz y ranking | | ✅ `comparar_metodos.py` no existía; se escribió dentro del mismo script |
| 8. Salidas | `out/normalizacion/` | ✅ en `.tck` en vez de `.trk` |

**Detalles de la implementación:**
- **MDF:** los 21 haces de `data/GT/`, con una submuestra de 1000 hilos por haz (semilla 0), como permite la sección 9. La asignación de los 100 000 hilos se calcula una sola vez (105 s), porque cada método es un subconjunto de esos mismos hilos. Queda en caché en `out/normalizacion/asignacion_mdf.npz`.
- **Máscaras:** vóxeles de la rejilla de la DWI (2 mm) que tocan los puntos de los hilos. Los puntos van cada 1 mm, tanto en el tractograma como en el GT. La máscara de cada haz verdadero usa todos sus hilos, no la submuestra.
- **Ranking:** solo entre los métodos evaluados. "Sin filtrar" aparece como referencia y no entra al ranking.
- **Etiqueta por haz:** queda en `out/normalizacion/etiqueta_mdf.csv`, con el haz más cercano y la MDF de cada hilo. Es la etiqueta que faltaba para evaluar hilo por hilo, y la pueden usar todos.

### Resultados

Asignación: **54 761 hilos (54.8 %) caen a menos de 5 mm de algún haz; 45 239 son "falsos"**.

| Método | Hilos conservados | Conductos detectados | % fibras falsas | Cobertura | Desborde | Dice | MDF simétrico (mm) | Lugar promedio |
|---|---|---|---|---|---|---|---|---|
| SIFT2 | 100 000 | 21 | 45.2 | 0.818 | 0.332 | 0.750 | 2.47 | 2.0 |
| combinado (u = 0.10) | 84 278 | 21 | 47.1 | 0.804 | 0.313 | 0.749 | 2.49 | 2.6 |
| COMMIT | 55 220 | 21 | 48.7 | 0.776 | 0.253 | 0.750 | 2.58 | 2.7 |
| voto mayoritario | 55 220 | 21 | 48.7 | 0.776 | 0.253 | 0.750 | 2.58 | 2.7 |
| *sin filtrar (referencia)* | *100 000* | *21* | *45.2* | *0.818* | *0.332* | *0.750* | *2.47* | — |

Archivos: `resumen_metodos.csv`, `resultados_por_conducto.csv`, `barrido_umbral.csv`, `curva_umbral.png`, `combinado_u0.10.tck`, `voto_mayoritario.tck`, `keep_combinado.txt`, `keep_voto.txt`, `etiqueta_mdf.csv`.

### Cómo leerlos: con dos métodos el resultado es degenerado

1. **"SIFT2 gana" porque no filtra nada.** SIFT2 no pone ningún peso en 0. Con la regla "peso 0 = eliminó" de la especificación, conserva los 100 000 hilos y es idéntico a "sin filtrar".
2. **El voto mayoritario es igual a COMMIT.** Con dos métodos, el voto exige peso > 0 en los dos, y como SIFT2 siempre es > 0, decide solo COMMIT.
3. **El umbral elegido queda en el borde (0.10).** El Dice baja conforme sube el umbral, así que el "óptimo" es conservar casi todo.
4. **Subir el umbral aumenta el % de fibras falsas** (de 47 % con u = 0.10 a 89 % con u = 0.90). Los hilos con peso alto son *más* probablemente falsos, no menos. Hilo por hilo, con la etiqueta MDF:

| Puntaje | AUC para predecir "pertenece a un haz" |
|---|---|
| COMMIT | 0.420 |
| SIFT2 | 0.345 |
| score Ricardo (promedio de percentiles) | 0.366 |
| **longitud del hilo** | **0.747** |
| COMMIT × longitud | 0.471 |
| SIFT2 × longitud | 0.651 |

AUC < 0.5 significa que el peso ordena al revés. COMMIT pone en 0 al 48.3 % de los hilos verdaderos y solo al 40.6 % de los falsos.

**La razón principal es la longitud.** Los hilos verdaderos miden 107.5 mm de media y los falsos 73.6 mm. COMMIT da el peso por unidad de longitud y SIFT2 tiene Spearman −0.41 con la longitud: los dos favorecen los hilos cortos, y los hilos cortos son los que la etiqueta MDF marca como falsos.

**Ojo, la etiqueta MDF también está sesgada por longitud.** La MDF compara los hilos remuestreados a 20 puntos. Un hilo corto que va *dentro* de un haz real pero solo cubre un tramo queda lejos de los hilos completos del haz, y se marca falso aunque esté en el lugar correcto. Así que parte del "AUC al revés" viene de la etiqueta, no solo de los métodos. Es una limitación del criterio de la especificación (sección 7), no de la implementación.

### Qué falta decidir (antes de LiFE)

1. **Qué significa "eliminado" en SIFT2.** Opción (b) de `consideraciones_normalizacion_ricardo.md`: tratar como eliminado el 45 % de menor peso, el mismo % que COMMIT pone en 0. Sin eso, SIFT2 nunca filtra.
2. **Corregir la longitud:** usar COMMIT × longitud (y SIFT2 × longitud) antes de normalizar. Es lo que más sube el AUC (0.47 y 0.65).
3. **Etiqueta MDF más justa con hilos cortos:** por ejemplo, la distancia de cada punto del hilo al haz (el hilo "está dentro" del haz) en lugar de la MDF punta a punta; o excluir los hilos cortos de la evaluación.
4. **El umbral se elige con el mismo GT con que se evalúa:** es optimista. Conviene elegirlo con la mitad de los haces y evaluar con la otra.

Con LiFE (tres métodos), el voto mayoritario y el promedio dejan de depender solo de COMMIT, pero los puntos 1–3 siguen aplicando.

---

### Variantes probadas

Se probaron 2 etiquetas por 4 opciones de pesos, todas con el mismo script (`out/normalizacion/variantes/<etiqueta>_<opción>/`):

- **Etiqueta `mdf`** (la de la especificación): MDF < 5 mm al haz más cercano.
- **Etiqueta `mascara`** (nueva, `--etiqueta mascara`): al menos el 90 % de los puntos del hilo cae dentro de la máscara de un haz, dilatada 1 vóxel. No castiga a los hilos cortos.
- **Opciones:** `base`; `corte` (`--corte`: el 44.8 % de menor peso de SIFT2 pasa a 0, igual que COMMIT); `xlong` (`--x-longitud`: peso × longitud); `xlong_corte` (las dos).

```bash
python scripts/normalizacion_ricardo.py --etiqueta mascara --corte --salida out/normalizacion/variantes/mascara_corte
```

#### Resultados (combinado con el umbral elegido; sin filtrar como referencia)

| Etiqueta | Opción | % verdaderos | AUC hilo: COMMIT / SIFT2 / score | Umbral | Hilos | % falsas | Cobertura | Dice | Ganador |
|---|---|---|---|---|---|---|---|---|---|
| mdf | sin filtrar | 54.8 | — | — | 100 000 | 45.2 | 0.818 | 0.750 | — |
| mdf | base | | 0.420 / 0.345 / 0.366 | 0.10 | 84 278 | 47.1 | 0.804 | 0.749 | SIFT2 (= sin filtrar) |
| mdf | corte | | 0.420 / 0.344 / 0.361 | 0.10 | 60 522 | 51.9 | 0.774 | 0.746 | COMMIT |
| mdf | xlong | | 0.471 / 0.651 / 0.585 | 0.10 | 87 978 | 41.9 | 0.808 | 0.747 | SIFT2 (= sin filtrar) |
| mdf | xlong_corte | | 0.471 / 0.607 / 0.543 | 0.15 | 57 424 | 42.7 | 0.773 | 0.747 | COMMIT |
| máscara | sin filtrar | 93.8 | — | — | 100 000 | 6.2 | 0.844 | 0.759 | — |
| máscara | base | | 0.580 / 0.616 / 0.619 | 0.10 | 84 278 | 5.4 | 0.837 | 0.759 | SIFT2 (= sin filtrar) |
| máscara | corte | | 0.580 / 0.594 / 0.606 | 0.20 | 49 753 | 4.4 | 0.800 | 0.755 | COMMIT / combinado (empate) |
| máscara | xlong | | 0.555 / 0.398 / 0.465 | 0.35 | 48 800 | 6.6 | 0.788 | 0.758 | SIFT2 (= sin filtrar) |
| máscara | xlong_corte | | 0.555 / 0.418 / 0.482 | 0.20 | 51 189 | 6.5 | 0.794 | 0.759 | COMMIT |

#### Dentro de cada rango de longitud, los pesos casi no distinguen

AUC por hilo dentro de cada quintil de longitud (0.5 = no aporta nada):

| Longitud (mm) | mdf: COMMIT / SIFT2 / score | máscara: COMMIT / SIFT2 / score |
|---|---|---|
| 11–56 | 0.36 / 0.40 / 0.35 | 0.63 / 0.64 / 0.66 |
| 56–86 | 0.47 / 0.45 / 0.46 | 0.53 / 0.47 / 0.49 |
| 86–105 | 0.47 / 0.39 / 0.42 | 0.55 / 0.49 / 0.52 |
| 105–126 | 0.49 / 0.47 / 0.48 | 0.54 / 0.54 / 0.54 |
| 126–200 | 0.50 / 0.49 / 0.50 | 0.54 / 0.57 / 0.57 |

#### Lectura

1. **Las dos etiquetas están sesgadas por longitud, en sentidos opuestos.** Con MDF, solo el 3.9 % de los hilos de menos de 56 mm cuenta como verdadero: castiga a los cortos. Con la máscara, el 94 % de todos los hilos cuenta como verdadero: es demasiado permisiva. Por eso multiplicar por la longitud "ayuda" con una etiqueta (AUC del score 0.37 → 0.59) y "perjudica" con la otra (0.62 → 0.47). Ese efecto mide la etiqueta, no a los métodos.
2. **Una vez fijada la longitud, COMMIT y SIFT2 casi no separan hilos buenos de malos** (AUC 0.45–0.57 en casi todos los rangos). Ninguna forma de combinarlos puede sacar información que los pesos no tienen. Donde sí funcionan es por conexión (AUC 0.83–0.85; ver `integracion_metodos.md`).
3. **El Dice no sirve para elegir el umbral.** Queda entre 0.746 y 0.759 en las 40 combinaciones, y el máximo siempre es "sin filtrar". La ocupación de vóxeles se satura: quitar hilos casi nunca vacía un vóxel del haz. Por eso el umbral elegido siempre cae en el borde bajo.
4. **`--corte` es necesario por definición, no por resultados.** Sin él, SIFT2 nunca elimina nada, el voto mayoritario es igual a COMMIT y "SIFT2 gana" solo porque no filtra.

#### Recomendación

| Decisión | Recomendación | Por qué |
|---|---|---|
| "Eliminado" en SIFT2 | **usar `--corte`** | que los métodos eliminen la misma fracción; sin eso SIFT2 y el voto no participan |
| Peso × longitud | **no usarlo por ahora** | su efecto cambia de signo según la etiqueta; no se puede decidir con estas etiquetas |
| Criterio del umbral | **no usar el Dice**; usar una fracción fija (p. ej. conservar el 55 %, como COMMIT) o "menor % de falsas con cobertura ≥ X" | el Dice es plano y siempre elige no filtrar |
| Etiqueta | **ninguna de las dos es buena**; hace falta una intermedia | p. ej. fracción de puntos a ≤ 2 mm de los hilos del haz verdadero (sin dilatar), o criterio tipo Tractometer con regiones de los extremos |

**Configuración que conviene hoy:** rango percentil con `--corte`, sin × longitud, y con una fracción fija conservada en lugar del Dice. Con la etiqueta de máscara, esa combinación (u = 0.20, 49 753 hilos) baja las fibras falsas de 6.2 % a 4.4 % y conserva cobertura 0.80 con el mismo Dice. Con la etiqueta MDF no hay ninguna combinación que mejore a "sin filtrar" sin multiplicar por la longitud. La conclusión de fondo no cambia con la variante: con COMMIT y SIFT2, filtrar hilo por hilo apenas mejora el tractograma. Hay que ver si LiFE aporta información distinta.


---

# B. Percentil por rango de longitud


Variante de la normalización Ricardo (`docs/Normalizacion Ricardo.md`). Todo es igual, salvo **contra quién se compara cada hilo** al calcular su percentil.

### 1. Por qué

Con el percentil global, cada hilo se ordena contra los 100 000. Pero los pesos dependen de la longitud del hilo, no solo de qué tan bueno es:

| Método | Spearman del peso con la longitud |
|---|---|
| COMMIT | −0.20 (favorece los cortos: su peso es por unidad de longitud) |
| SIFT2 | −0.41 (favorece los cortos) |
| COMMIT2 (λ = 1e-2) | +0.27 (favorece los largos) |

Con el percentil global, un hilo corto saca percentil alto en COMMIT y SIFT2 solo por ser corto, y el promedio arrastra ese sesgo. En la evaluación anterior eso hacía que **mientras más se filtraba, más fibras falsas quedaban** (de 47 % a 60 % con COMMIT + SIFT2).

### 2. Qué cambia

**Percentil global (especificación original):**
$$p_i = \frac{\operatorname{rango}(w_i \text{ entre todos los hilos con } w > 0)}{n_{>0}}$$

**Percentil por rango de longitud:**
1. Se divide a los 100 000 hilos en **10 rangos de longitud** con el mismo número de hilos cada uno (deciles de `out/longitudes.txt`): 11–29, 29–56, 56–74, 74–86, 86–95, 95–105, 105–114, 114–126, 126–141 y 141–200 mm.
2. **Dentro de cada rango** se aplica exactamente la regla de Ricardo: peso 0 se queda en 0; los de peso > 0 se ordenan de menor a mayor y valen lugar/n, donde n es el número de hilos con peso > 0 **en ese rango**. Empates con rango promedio.
3. Lo demás no cambia: promedio de los percentiles de los métodos y eliminar los hilos con promedio < umbral.

$$p_i = \frac{\operatorname{rango}(w_i \text{ entre los hilos con } w > 0 \text{ del mismo rango de longitud que } i)}{n_{>0,\ \text{rango}}}$$

Así, un hilo corto con percentil alto significa "tiene mucho peso **comparado con otros hilos cortos**", no "es corto".

#### Ejemplo (está en el test)

| Hilo | Longitud | Peso | Percentil global | Percentil por longitud (2 rangos) |
|---|---|---|---|---|
| 1 | 10 mm | 1 | 1/7 = 0.14 | 1/3 = 0.33 |
| 2 | 10 mm | 2 | 0.29 | 0.67 |
| 3 | 10 mm | 3 | 0.43 | **1.00** |
| 4 | 10 mm | 0 | 0 | 0 |
| 5 | 100 mm | 10 | 0.57 | 0.25 |
| 6 | 100 mm | 20 | 0.71 | 0.50 |
| 7 | 100 mm | 30 | 0.86 | 0.75 |
| 8 | 100 mm | 40 | 1.00 | **1.00** |

Con el percentil global, los cortos nunca pasan de 0.43 porque sus pesos son más chicos en términos absolutos. Por longitud, el mejor de cada grupo vale 1.

### 3. Implementación

- `a_percentil_por_longitud(w, longitud, n_rangos=10)` en `scripts/normalizacion_ricardo.py`, con la opción `--por-longitud N` (0 = percentil global).
- Test en `scripts/test_normalizacion.py`: el ejemplo de arriba, y que con un solo rango da lo mismo que el percentil global. El ejemplo original de Ricardo sigue pasando.
- `scripts/07_normalizacion.sh` ahora corre las dos versiones: `out/normalizacion/umbrales/` (global) y `out/normalizacion/umbrales_longitud/` (por longitud).

```bash
python scripts/normalizacion_ricardo.py --umbrales 0.1 0.2 0.3 0.4 0.5 --por-longitud 10 \
  --pesos COMMIT=out/commit/pesos_commit.txt SIFT2=out/pesos_sift2.txt COMMIT2=out/commit2/pesos_commit2.txt \
  --salida out/normalizacion/cs2_longitud
```

La evaluación es la misma de antes: etiqueta por haz con MDF < 5 mm, métricas por haz y comparación con cada método solo con el mismo número de hilos.

### 4. Resultados

Se corrieron tres combinaciones de métodos, cada una con el percentil global y por longitud (`out/normalizacion/<combinación>_{global,longitud}/`). Referencia: **sin filtrar = 45.2 % de falsas, cobertura 0.818, Dice 0.750**.

#### AUC por hilo del score combinado (etiqueta MDF; 0.5 = azar)

| Combinación | Global | Por longitud |
|---|---|---|
| COMMIT + SIFT2 | 0.366 | **0.451** |
| COMMIT + SIFT2 + COMMIT2 (λ = 1e-2) | 0.460 | **0.528** |
| COMMIT + SIFT2 + COMMIT2 (λ = 1e-3) | 0.436 | **0.511** |

Normalizar por longitud sube el AUC en 0.07–0.09 en las tres. Con COMMIT2, el score combinado por primera vez queda **por encima del azar**.

#### % de fibras falsas según el umbral

| Combinación | Percentil | u = 0.1 | 0.2 | 0.3 | 0.4 | 0.5 |
|---|---|---|---|---|---|---|
| COMMIT + SIFT2 | global | 47.1 | 50.0 | 53.3 | 56.8 | 59.5 |
| | por longitud | 45.6 | 46.7 | 48.4 | 50.4 | 51.3 |
| + COMMIT2 (λ = 1e-2) | global | 46.5 | 47.4 | 47.9 | 49.3 | 52.0 |
| | por longitud | 44.6 | 44.4 | **43.8** | **42.4** | **41.0** |
| + COMMIT2 (λ = 1e-3) | global | 47.0 | 48.4 | 49.4 | 51.4 | 53.6 |
| | por longitud | 44.9 | 45.0 | 45.0 | 44.4 | 43.5 |

**Lo que cambia de fondo:** con el percentil global, subir el umbral siempre empeoraba (más falsas). Con el percentil por longitud y COMMIT2 incluido, **subir el umbral mejora**: de 44.6 % a 41.0 %. Es la primera versión combinada que baja de las 45.2 % de "sin filtrar".

#### Todas las métricas: COMMIT + SIFT2 + COMMIT2 (λ = 1e-2)

| Percentil | Umbral | Hilos | Haces | % falsas ↓ | Cobertura ↑ | Desborde ↓ | Dice ↑ | MDF (mm) ↓ | Lugar |
|---|---|---|---|---|---|---|---|---|---|
| global | 0.1 (ganador) | 82 873 | 21 | 46.5 | 0.797 | 0.303 | 0.743 | 2.55 | 2.0 |
| global | 0.3 | 49 364 | 21 | 47.9 | 0.738 | 0.216 | 0.738 | 2.65 | 3.2 |
| global | 0.5 | 22 162 | 20 | 52.0 | 0.604 | 0.106 | 0.681 | 2.87 | 4.2 |
| por longitud | 0.1 | 82 430 | 21 | 44.6 | 0.800 | 0.302 | 0.745 | 2.55 | 3.0 |
| **por longitud** | **0.3 (ganador)** | **48 874** | 20 | **43.8** | 0.748 | 0.219 | 0.741 | **2.45** | **2.6** |
| por longitud | 0.5 | 21 632 | 20 | 41.0 | 0.643 | 0.123 | 0.706 | 2.70 | 3.4 |

Con el percentil por longitud, **el ganador deja de ser el umbral que menos filtra**: es u = 0.3. Conserva la mitad de los hilos con menos falsas que "sin filtrar", casi el mismo Dice (0.741 contra 0.750) y el mejor MDF de todas las versiones (2.45 mm). Pierde un haz de 21.

#### Con el mismo número de hilos (por longitud, + COMMIT2 λ = 1e-2)

| Umbral (n) | Combinado | COMMIT solo | SIFT2 solo | COMMIT2 solo |
|---|---|---|---|---|
| | % falsas / cobertura / Dice | | | |
| 0.3 (48 874)* | 43.8 / 0.748 / 0.741 | 49.9 / 0.762 / 0.748 | 57.0 / 0.720 / 0.725 | **30.7** / 0.748 / 0.738 |
| 0.4 (34 226) | 42.4 / **0.707** / 0.730 | 54.3 / 0.725 / **0.741** | 63.0 / 0.656 / 0.700 | **19.0** / 0.533 / 0.542 |
| 0.5 (21 632) | 41.0 / 0.643 / 0.706 | 61.8 / **0.654** / **0.718** | 69.5 / 0.546 / 0.635 | **18.0** / 0.454 / 0.504 |

\* COMMIT2 solo tiene 36 928 hilos con peso > 0; en 0.3 completa con hilos de peso 0 al azar.

- El combinado por longitud **ya le gana a COMMIT solo y a SIFT2 solo en % de falsas**: 41–44 % contra 50–62 % y 57–70 %. Con el percentil global quedaba entre COMMIT y SIFT2.
- COMMIT2 solo sigue siendo el más limpio, pero con umbrales altos pierde haces (16–17 de 21) y la cobertura cae a 0.45–0.53. El combinado conserva 20 haces y cobertura 0.64–0.71: **es el mejor equilibrio entre limpieza y cobertura**.

### 5. Conclusión

| | Percentil global | Percentil por longitud |
|---|---|---|
| AUC del score (con COMMIT2) | 0.46 (peor que azar) | 0.53 |
| Al subir el umbral | empeora | mejora (con COMMIT2) |
| Umbral ganador | siempre el mínimo (0.1) | 0.3 con COMMIT2 |
| ¿Algún combinado mejora a "sin filtrar" en % de falsas? | no | sí (41–44 % contra 45.2 %) |
| Frente a cada método solo | entre COMMIT y SIFT2 | mejor que COMMIT y que SIFT2; más equilibrado que COMMIT2 |

**Recomendación:** usar el percentil por rango de longitud (`--por-longitud 10`) con COMMIT, SIFT2, COMMIT2 (λ = 1e-2) y LiFE, y umbral 0.3 (ver 5.1). **Actualizada en 5.2:** mejor COMMIT2 + LiFE con percentil global, u = 0.1.

#### 5.1 Con LiFE (14 nov)

Mismo esquema (`bash scripts/07_normalizacion.sh`, que agrega LiFE solo si existe `out/life/pesos_life.txt`). Resultados en `out/normalizacion/umbrales_longitud/`.

| Por longitud | u = 0.1 | 0.2 | 0.3 | 0.4 | 0.5 |
|---|---|---|---|---|---|
| % falsas sin LiFE | 44.6 | 44.4 | 43.8 | 42.4 | 41.0 |
| **% falsas con LiFE** | 44.3 | 43.3 | **41.7** | 39.9 | 36.7 |

| Por longitud, u = 0.3 | Hilos | Haces | % falsas ↓ | Cobertura ↑ | Desborde ↓ | Dice ↑ | MDF (mm) ↓ |
|---|---|---|---|---|---|---|---|
| COMMIT + SIFT2 + COMMIT2 | 48 874 | 20 | 43.8 | 0.748 | 0.219 | 0.741 | 2.45 |
| **+ LiFE** | **53 890** | 20 | **41.7** | 0.747 | 0.222 | 0.739 | **2.43** |
| LiFE solo (peso > 0) | 74 612 | 21 | 40.1 | 0.765 | 0.274 | 0.738 | 2.55 |
| sin filtrar | 100 000 | 21 | 45.2 | 0.818 | 0.332 | 0.750 | 2.47 |

- Con LiFE, u = 0.3 sigue ganando y mejora en todo lo importante: **conserva 5 000 hilos más y aun así baja las falsas** (43.8 → 41.7 %), con la misma cobertura y Dice.
- El AUC del score combinado sube de 0.53 a 0.556.
- LiFE solo ya está en 40.1 % de falsas con 21 haces: es el mejor método individual que no pierde haces.

#### 5.2 Comparación con el mismo número de hilos, en las dos normalizaciones (14 nov)

Cada fila compara el combinado con cada método solo, quedándose con los mismos n hilos de mayor peso. Archivos: `comparacion_mismo_n.csv` en `out/normalizacion/{umbrales, umbrales_longitud, c2l_global, c2l_longitud}/`.

**AUC por hilo (etiqueta MDF):** COMMIT 0.420 · SIFT2 0.345 · COMMIT2 0.684 · LiFE 0.655 · longitud sola 0.747.
COMMIT y SIFT2 están **por debajo del azar** hilo por hilo: sus pesos altos caen más en hilos falsos. Al promediarlos con COMMIT2 y LiFE, ensucian el score.

##### a) COMMIT + SIFT2 + COMMIT2 + LiFE

% falsas / cobertura / Dice (haces, si son menos de 21):

| Norm. | u (n) | Combinado | COMMIT solo | SIFT2 solo | COMMIT2 solo | LiFE solo |
|---|---|---|---|---|---|---|
| global | 0.1 (89 580) | 45.2 / 0.807 / 0.751 | 45.7 / 0.809 / 0.747 | 46.3 / 0.809 / 0.749 | 43.6 / 0.813 / 0.751 | 43.6 / 0.811 / 0.752 |
| global | 0.3 (54 946) | 43.2 / 0.740 / 0.735 (20) | 48.8 / 0.775 / 0.751 | 55.0 / 0.737 / 0.730 | **33.6** / 0.767 / 0.748 | **33.6** / 0.705 / 0.718 |
| global | 0.5 (17 936) | 34.4 / 0.550 / 0.638 (20) | 65.1 / 0.618 / 0.700 (20) | 72.1 / 0.491 / 0.593 (20) | **18.5** / 0.413 / 0.477 (16) | 27.0 / 0.355 / 0.431 (18) |
| longitud | 0.1 (88 610) | 44.3 / 0.808 / 0.751 | 45.8 / 0.809 / 0.747 | 46.4 / 0.808 / 0.748 | 43.4 / 0.812 / 0.751 | 43.4 / 0.810 / 0.752 |
| longitud | 0.3 (53 890) | 41.7 / 0.747 / 0.739 (20) | 49.0 / 0.772 / 0.749 | 55.4 / 0.735 / 0.730 | **33.1** / 0.766 / 0.748 | 33.4 / 0.696 / 0.710 (20) |
| longitud | 0.5 (19 489) | 36.7 / 0.569 / 0.651 (20) | 63.5 / 0.636 / 0.709 (20) | 70.8 / 0.517 / 0.613 (20) | **18.2** / 0.433 / 0.492 (16) | 27.3 / 0.375 / 0.450 (19) |

- En las dos normalizaciones, el combinado de cuatro **le gana a COMMIT y a SIFT2, pero pierde contra COMMIT2 solo y LiFE solo** en % de falsas con cualquier n. En u = 0.3, COMMIT2 solo es mejor en todo: 33 % de falsas contra 42–43 %, con igual o mejor cobertura y Dice.
- La normalización por longitud mejora un poco al combinado de cuatro (41.7 contra 43.2 % en u = 0.3), pero no cambia la conclusión.

##### b) Solo COMMIT2 + LiFE (los dos con AUC > 0.5)

| Norm. | AUC score | Ganador | Hilos | Haces | % falsas | Cobertura | Dice | MDF (mm) |
|---|---|---|---|---|---|---|---|---|
| **global** | **0.713** | u = 0.1 | 66 287 | 21 | **33.8** | 0.756 | 0.736 | 2.59 |
| longitud | 0.652 | u = 0.1 | 68 507 | 21 | 38.0 | 0.743 | 0.729 | 2.62 |

Con el mismo n (global), % falsas / cobertura / Dice (haces):

| u (n) | COMMIT2 + LiFE | COMMIT2 solo | LiFE solo |
|---|---|---|---|
| 0.1 (66 287) | **33.8** / 0.756 / 0.736 (21) | 38.1 / **0.787** / **0.747** (21) | 37.0 / 0.748 / 0.733 (21) |
| 0.2 (54 352) | **29.9** / 0.689 / 0.702 (20) | 33.4 / **0.765** / **0.744** (21) | 33.5 / 0.702 / 0.717 (21) |
| 0.3 (42 402) | 26.5 / 0.591 / 0.624 (19) | **26.1** / **0.707** / **0.718** (20) | 31.1 / 0.624 / 0.672 (20) |

- **Es la primera combinación cuyo score supera a cada método solo** (AUC 0.713 contra 0.684 y 0.655).
- En u = 0.1 y 0.2 tiene **menos falsas que cualquiera de los dos solos** con el mismo n, a cambio de un poco menos de cobertura que COMMIT2. Desde u = 0.3, COMMIT2 solo ya es mejor.
- Aquí **la normalización por longitud empeora** (AUC 0.65 contra 0.71). COMMIT2 y LiFE favorecen los hilos largos (Spearman con la longitud +0.27 y +0.26), y la longitud sí predice si un hilo pertenece a un haz (AUC 0.747). Normalizar por longitud les quita esa señal. Antes ayudaba porque corregía el sesgo contrario de COMMIT y SIFT2 hacia los hilos cortos.
- Ojo con COMMIT2 solo: tiene 36 928 hilos con peso > 0; para n mayores se completa con hilos de peso 0 al azar.

##### Conclusión de 5.2

| Combinación | Mejor normalización | ¿Le gana a cada método solo con el mismo n? |
|---|---|---|
| COMMIT + SIFT2 + COMMIT2 + LiFE | por longitud (u = 0.3) | solo a COMMIT y SIFT2 |
| **COMMIT2 + LiFE** | **global (u = 0.1–0.2)** | **sí en % falsas**; COMMIT2 conserva un poco más de cobertura |

**Nueva recomendación:** COMMIT2 + LiFE con percentil global y u = 0.1. Conserva 66 287 hilos y los 21 haces, con 33.8 % de falsas (sin filtrar: 45.2 %) y Dice 0.736. Con u = 0.2 baja a 29.9 % de falsas, pero pierde un haz. COMMIT y SIFT2 sirven por conexión (matriz), no para elegir hilos.

### 6. Cuidados

- **La etiqueta MDF sigue sesgada por longitud** (castiga a los hilos cortos). El percentil por longitud no lo corrige, pero sí quita la longitud del score: el combinado ya no gana ni pierde por preferir hilos de cierto largo. Eso hace la comparación más justa, no más optimista.
- **10 rangos es una elección.** Con muy pocos se parece al percentil global; con muchos, cada rango tiene pocos hilos y el percentil se vuelve ruidoso (≈ 10 000 hilos por rango aquí está bien). Se puede probar 5 o 20 con `--por-longitud`.
- **El umbral se elige con el mismo GT con que se evalúa**, así que el resultado es optimista. Lo correcto es elegirlo con la mitad de los haces y evaluar con la otra.
- El "lugar promedio" ordena solo entre los 5 umbrales de cada combinación, no entre combinaciones.


---

# C. Consideraciones iniciales


Revisión del 2026-11-13 de `docs/Normalizacion Ricardo.md` contra los datos de este repo. **Conclusión: es factible.** Su ejemplo de la sección 4 da exactamente sus valores (0.33, 0.92, 0.25, 0.17, 0.83; se conservan las fibras 2 y 5). Lo que sigue son ajustes para que funcione con nuestros archivos.

### 1. Archivos de entrada (contrato del repo)

Todos los métodos pesan **el mismo tractograma**, `data/tracks_100k.tck` (100 000 hilos, `md5` `66ba3e6efe1fadf5b534d3947b2b138f`), y entregan un `.txt` con 100 000 pesos ≥ 0 en el orden del `.tck`.

| Método | Pesos | Estado |
|---|---|---|
| SIFT2 | `out/pesos_sift2.txt` | listo |
| COMMIT | `out/commit/pesos_commit.txt` | listo (corrido en la Mac) |
| COMMIT2 | `out/commit2/pesos_commit2.txt` | integrado (`scripts/06_commit2.sh`); falta el archivo de pesos |
| LiFE | `out/life/pesos_life.txt` | pendiente: su matriz actual es de otro tractograma |

Cargar con `np.loadtxt(f, comments="#").ravel()` (SIFT2 trae una cabecera `#`). Comprobar longitud 100 000 y orden, como pide Ricardo. `out/` y `data/` no se suben a Git; se comparten por Drive.

### 2. Ajustes que hay que decidir

1. **Un 0 no significa lo mismo en cada método.** COMMIT pone en 0 el 45 % de los hilos; SIFT2 no pone ninguno (0 de 100 000, pesos entre 0.19 y 3.7). Con el promedio de percentiles, SIFT2 nunca "elimina" un hilo y el umbral 0.5 pasa a decidirlo casi COMMIT. Opciones: (a) dejarlo así y decirlo; (b) para SIFT2 y LiFE tratar como "eliminado" el 45 % de menor peso (el mismo % que COMMIT); (c) usar solo el voto mayoritario con ese corte común.
2. **La longitud sesga los rangos.** Los pesos de COMMIT son por unidad de longitud y favorecen hilos cortos; SIFT2 tiene Spearman −0.41 con la longitud. Probar también COMMIT × longitud (`out/pesos_commit_x_long.txt`, ya lo genera `04_matrices.sh`).
3. **Elegir el umbral con el mismo GT con que se evalúa es optimista.** Declararlo en el informe, o elegir el umbral con la mitad de los haces y evaluar con la otra.
4. **Peso 0 = "eliminó"** es una hipótesis, no un hecho comprobado (decisión 3.5 de `aclaraciones_equipo.md`).

### 3. Lo que falta o no encaja

- Pide partir de `comparar_metodos.py` (segmentación por MDF, Dice): **no existe en el repo**. Hay que escribirlo o pedírselo a quien lo tenga.
- Habla de `.trk`; nosotros usamos `.tck` (`nibabel` lo lee; `load_tractogram` de DIPY también). Guardar la salida como `.tck` evita convertir.
- `dipy` ya está en `requirements.txt`; `matplotlib` no está en `environment.yml` (agregarlo con versión fija si se usa).
- El GT está en `data/GT/` (21 haces `.tck` y `all_tracks.tck`, ≈ 189 985 hilos). El MDF contra todo el GT hay que hacerlo por bloques.
- La etiqueta por haz (MDF < 5 mm al haz más cercano) es la misma que falta para evaluar hilo por hilo (decisión 3.4). Conviene hacerla una vez y que la usen todos.
- Las matrices 84 × 84 se comparan con la **diagonal en 0** (`np.fill_diagonal(M, 0)`); no aplica a esta normalización, que es por hilo.

### 4. Sobre `docs/Normalizacion.py`

No se usa para esto: normaliza matrices dividiendo entre el máximo, y en las matrices de LiFE ese máximo está en la diagonal (distorsiona RMSE y Frobenius). Es otro enfoque (matrices, no hilos).

### 5. Dónde dejar la implementación

Siguiendo `guia_equipo.md`: script en `scripts/` con el siguiente número libre (`07_...`), entrega `out/keep_<estrategia>.txt` (un 0 o 1 por hilo) y su sección en `pipeline.md` con comandos sueltos y "Se espera". Incluir el test del ejemplo (`test_normalizacion.py`).


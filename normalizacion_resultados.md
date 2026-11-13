# Normalización Ricardo: resultados con COMMIT + SIFT2 (2026-11-13)

## Actualización: con COMMIT2 (COMMIT + SIFT2 + COMMIT2)

COMMIT2 se corrió aquí con `scripts/correr_commit2.py` (λ = 1e-2, group lasso por par de regiones, pesos de grupo por cardinalidad y adaptativos), en 1 min 6 s.

**Dos arreglos al script de Maximiliano:**
1. Con `group_weights_adaptive=True`, COMMIT exige un ajuste sin regularizar antes (`Group weights cannot be computed if the fit without regularisation has not been performed before`). Se agregó `mit.fit()` antes de `set_regularisation`.
2. `save_results()` guardaba en la carpeta del diccionario de COMMIT (`out/commit/COMMIT/Results_StickZeppelinBall/`) y **pisaba los resultados detallados de COMMIT**. Ahora guarda con el sufijo `_COMMIT2` y mueve todo a `out/commit2/`. Los pesos de COMMIT (`out/commit/pesos_commit.txt`) no se tocaron. Los mapas de NRMSE y compartimentos de COMMIT se perdieron en la primera corrida y se recuperan con `bash scripts/03_commit.sh` (≈ 75 s).

**Ojo:** nuestra corrida deja **36 928 hilos con peso > 0 (63 % en 0)**. La de la compañera reportaba 62 779 con el mismo λ. Puede deberse a los pesos de grupo adaptativos, a otros grupos (ella usó 85 × 85 con el nodo 0) o a otro tractograma. Hay que preguntarle.

### COMMIT2 solo

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

### Normalización con los tres

| Versión | Hilos | Haces | % falsas ↓ | Cobertura ↑ | Desborde ↓ | Dice ↑ | MDF ↓ | Lugar |
|---|---|---|---|---|---|---|---|---|
| **promedio ≥ 0.1** | 82 873 | 21 | 46.5 | **0.797** | 0.303 | 0.743 | **2.55** | **2.0** |
| promedio ≥ 0.2 | 66 821 | 21 | 47.4 | 0.776 | 0.265 | **0.744** | 2.59 | 2.4 |
| promedio ≥ 0.3 | 49 364 | 21 | 47.9 | 0.738 | 0.216 | 0.738 | 2.65 | 3.2 |
| promedio ≥ 0.4 | 35 066 | 20 | 49.3 | 0.689 | 0.166 | 0.721 | 2.57 | 3.2 |
| promedio ≥ 0.5 | 22 162 | 20 | 52.0 | 0.604 | **0.106** | 0.681 | 2.87 | 4.2 |
| *sin filtrar* | *100 000* | *21* | *45.2* | *0.818* | *0.332* | *0.750* | *2.47* | — |

Con COMMIT2, el % de falsas sube mucho menos con el umbral (de 46.5 a 52.0, contra 47.1 a 59.5 con solo COMMIT + SIFT2), pero sigue sin bajar del tractograma sin filtrar. El ganador sigue siendo 0.1.

### Con el mismo número de hilos

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

## Umbrales fijos 0.1–0.5 (lo que se pidió)

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

### Comparado con COMMIT solo y SIFT2 solo, con el mismo número de hilos

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

## Qué se implementó

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

## Resultados

Asignación: **54 761 hilos (54.8 %) caen a menos de 5 mm de algún haz; 45 239 son "falsos"**.

| Método | Hilos conservados | Conductos detectados | % fibras falsas | Cobertura | Desborde | Dice | MDF simétrico (mm) | Lugar promedio |
|---|---|---|---|---|---|---|---|---|
| SIFT2 | 100 000 | 21 | 45.2 | 0.818 | 0.332 | 0.750 | 2.47 | 2.0 |
| combinado (u = 0.10) | 84 278 | 21 | 47.1 | 0.804 | 0.313 | 0.749 | 2.49 | 2.6 |
| COMMIT | 55 220 | 21 | 48.7 | 0.776 | 0.253 | 0.750 | 2.58 | 2.7 |
| voto mayoritario | 55 220 | 21 | 48.7 | 0.776 | 0.253 | 0.750 | 2.58 | 2.7 |
| *sin filtrar (referencia)* | *100 000* | *21* | *45.2* | *0.818* | *0.332* | *0.750* | *2.47* | — |

Archivos: `resumen_metodos.csv`, `resultados_por_conducto.csv`, `barrido_umbral.csv`, `curva_umbral.png`, `combinado_u0.10.tck`, `voto_mayoritario.tck`, `keep_combinado.txt`, `keep_voto.txt`, `etiqueta_mdf.csv`.

## Cómo leerlos: con dos métodos el resultado es degenerado

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

## Qué falta decidir (antes de LiFE)

1. **Qué significa "eliminado" en SIFT2.** Opción (b) de `consideraciones_normalizacion_ricardo.md`: tratar como eliminado el 45 % de menor peso, el mismo % que COMMIT pone en 0. Sin eso, SIFT2 nunca filtra.
2. **Corregir la longitud:** usar COMMIT × longitud (y SIFT2 × longitud) antes de normalizar. Es lo que más sube el AUC (0.47 y 0.65).
3. **Etiqueta MDF más justa con hilos cortos:** por ejemplo, la distancia de cada punto del hilo al haz (el hilo "está dentro" del haz) en lugar de la MDF punta a punta; o excluir los hilos cortos de la evaluación.
4. **El umbral se elige con el mismo GT con que se evalúa:** es optimista. Conviene elegirlo con la mitad de los haces y evaluar con la otra.

Con LiFE (tres métodos), el voto mayoritario y el promedio dejan de depender solo de COMMIT, pero los puntos 1–3 siguen aplicando.

---

## Variantes probadas

Se probaron 2 etiquetas por 4 opciones de pesos, todas con el mismo script (`out/normalizacion/variantes/<etiqueta>_<opción>/`):

- **Etiqueta `mdf`** (la de la especificación): MDF < 5 mm al haz más cercano.
- **Etiqueta `mascara`** (nueva, `--etiqueta mascara`): al menos el 90 % de los puntos del hilo cae dentro de la máscara de un haz, dilatada 1 vóxel. No castiga a los hilos cortos.
- **Opciones:** `base`; `corte` (`--corte`: el 44.8 % de menor peso de SIFT2 pasa a 0, igual que COMMIT); `xlong` (`--x-longitud`: peso × longitud); `xlong_corte` (las dos).

```bash
python scripts/normalizacion_ricardo.py --etiqueta mascara --corte --salida out/normalizacion/variantes/mascara_corte
```

### Resultados (combinado con el umbral elegido; sin filtrar como referencia)

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

### Dentro de cada rango de longitud, los pesos casi no distinguen

AUC por hilo dentro de cada quintil de longitud (0.5 = no aporta nada):

| Longitud (mm) | mdf: COMMIT / SIFT2 / score | máscara: COMMIT / SIFT2 / score |
|---|---|---|
| 11–56 | 0.36 / 0.40 / 0.35 | 0.63 / 0.64 / 0.66 |
| 56–86 | 0.47 / 0.45 / 0.46 | 0.53 / 0.47 / 0.49 |
| 86–105 | 0.47 / 0.39 / 0.42 | 0.55 / 0.49 / 0.52 |
| 105–126 | 0.49 / 0.47 / 0.48 | 0.54 / 0.54 / 0.54 |
| 126–200 | 0.50 / 0.49 / 0.50 | 0.54 / 0.57 / 0.57 |

### Lectura

1. **Las dos etiquetas están sesgadas por longitud, en sentidos opuestos.** Con MDF, solo el 3.9 % de los hilos de menos de 56 mm cuenta como verdadero: castiga a los cortos. Con la máscara, el 94 % de todos los hilos cuenta como verdadero: es demasiado permisiva. Por eso multiplicar por la longitud "ayuda" con una etiqueta (AUC del score 0.37 → 0.59) y "perjudica" con la otra (0.62 → 0.47). Ese efecto mide la etiqueta, no a los métodos.
2. **Una vez fijada la longitud, COMMIT y SIFT2 casi no separan hilos buenos de malos** (AUC 0.45–0.57 en casi todos los rangos). Ninguna forma de combinarlos puede sacar información que los pesos no tienen. Donde sí funcionan es por conexión (AUC 0.83–0.85; ver `integracion_metodos.md`).
3. **El Dice no sirve para elegir el umbral.** Queda entre 0.746 y 0.759 en las 40 combinaciones, y el máximo siempre es "sin filtrar". La ocupación de vóxeles se satura: quitar hilos casi nunca vacía un vóxel del haz. Por eso el umbral elegido siempre cae en el borde bajo.
4. **`--corte` es necesario por definición, no por resultados.** Sin él, SIFT2 nunca elimina nada, el voto mayoritario es igual a COMMIT y "SIFT2 gana" solo porque no filtra.

### Recomendación

| Decisión | Recomendación | Por qué |
|---|---|---|
| "Eliminado" en SIFT2 | **usar `--corte`** | que los métodos eliminen la misma fracción; sin eso SIFT2 y el voto no participan |
| Peso × longitud | **no usarlo por ahora** | su efecto cambia de signo según la etiqueta; no se puede decidir con estas etiquetas |
| Criterio del umbral | **no usar el Dice**; usar una fracción fija (p. ej. conservar el 55 %, como COMMIT) o "menor % de falsas con cobertura ≥ X" | el Dice es plano y siempre elige no filtrar |
| Etiqueta | **ninguna de las dos es buena**; hace falta una intermedia | p. ej. fracción de puntos a ≤ 2 mm de los hilos del haz verdadero (sin dilatar), o criterio tipo Tractometer con regiones de los extremos |

**Configuración que conviene hoy:** rango percentil con `--corte`, sin × longitud, y con una fracción fija conservada en lugar del Dice. Con la etiqueta de máscara, esa combinación (u = 0.20, 49 753 hilos) baja las fibras falsas de 6.2 % a 4.4 % y conserva cobertura 0.80 con el mismo Dice. Con la etiqueta MDF no hay ninguna combinación que mejore a "sin filtrar" sin multiplicar por la longitud. La conclusión de fondo no cambia con la variante: con COMMIT y SIFT2, filtrar hilo por hilo apenas mejora el tractograma. Hay que ver si LiFE aporta información distinta.

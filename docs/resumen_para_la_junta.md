# Resumen del proyecto para la junta con el doctor (19-nov-2026)

Para leer **antes de la junta**, incluso si no has seguido el trabajo de cerca. Va de lo general a lo detallado: si solo tienes 5 minutos, lee las secciones 1, 2, 9 (tractograma contra el GT) y 10 (estado).
Cada sección dice dónde están los detalles por si alguien quiere profundizar.

---

## 1. Lo esencial en 10 líneas
1. Tenemos **100 000 streamlines** (hilos: trayectorias 3D que representan fibras del cerebro) generados con MRtrix a partir de un fantoma simulado (ISMRM 2023). Un **ground truth (GT)** dice qué fibras existen de verdad: 189 985 hilos en 21 haces.
2. Cuatro métodos le dan a cada hilo **un peso** (qué tan creíble es): **SIFT2, COMMIT, LiFE** (los tres que pidió el doctor) y **COMMIT2** (un extra).
3. Cada vector de pesos se **normaliza a (0, 1)** y se **filtra** con un umbral ε: los hilos por debajo se descartan.
4. Para saber si el filtro acierta, necesitábamos una verdad por hilo. La calculamos con la **distancia de Hausdorff** de cada hilo al GT, repartida entre 7 personas. **Con ε = 5 mm, 1 de cada 3 hilos (33.3 %) corresponde al GT.**
5. Evaluamos cada método contra esa verdad. **Resultado: SIFT2 y COMMIT, solos, no sirven para filtrar (están por debajo del azar); LiFE y COMMIT2 sirven un poco; COMMIT2 es el mejor.**
6. La causa: los pesos de SIFT2 y COMMIT dependen mucho de la **longitud** del hilo (SIFT2 da pesos altos a hilos cortos, que casi nunca son verdaderos). Sin ese efecto, sus pesos no dicen nada sobre si el hilo es verdadero.
7. **Un modelo** (regresión logística) que combina los pesos **sí** aprovecha los 3 métodos del doctor: aprende a restarle importancia a SIFT2 y COMMIT. AUC 0.62 con los 3 métodos; 0.70 con los 4 y la longitud.
8. Para quedarse con **pocos hilos muy confiables**, lo mejor es **LiFE + COMMIT2**: 54 % de aciertos conservando 10 000 hilos (contra 33 % sin filtrar). **Pero** pierde haces enteros (punto 9).
9. **Tractograma filtrado completo contra el GT (ya medido):** lo que mejor acierta hilo por hilo recupera 14 haces, contra 20 sin filtrar: **pierde 6** (BPS izquierdo y derecho, Fornix, ICP izquierdo y derecho, y CA), porque COMMIT2 les pone peso 0 a casi todos sus hilos. SIFT2 y COMMIT, que fallan hilo por hilo, sí cubren 20 de 21 haces, pero dejan 75–78 % de hilos falsos. **Ningún filtro logra a la vez pocos falsos y todos los haces.** Falta fijar el ε final con el doctor y redactar el informe.
10. Todo es reproducible con scripts numerados (`scripts/01…11`), ver sección 13.

---

## 2. El objetivo (qué pidió el doctor, junta del 17-nov)
Detalle: `docs/junta_17nov.md`. Simplificando:
- **Entrada:** 100 000 hilos pesados por SIFT2, LiFE y COMMIT (un vector de 100 000 números por método).
- **Filtrado simple:** normalizar cada vector a (0, 1) y descartar los hilos con peso < ε. Cada método da su tractograma filtrado, y se compara con el GT.
- **Pregunta 1:** ¿qué hilos corresponden al GT? Se decide con la distancia de Hausdorff (< ε en mm). Es la «verdad» de referencia.
- **Pregunta 2:** ¿un modelo que combine los tres pesos filtra mejor que cada uno? Se entrena con la etiqueta del GT y se compara el tractograma que produce contra el GT.
- Todo lo demás que hicimos antes (matrices 84×84, COMMIT2, barrido de λ, corrección del eje y…) quedó como **extras**: `docs/resultados/extras.md`.

---

## 3. Los datos y los cuatro vectores de pesos
| | Qué es | Dónde |
|---|---|---|
| Tractograma | 100 000 hilos (`tckgen`, iFOD2), el mismo para todos (md5 66ba3e6e…) | `data/tracks_100k.tck` |
| GT | 189 985 hilos, 21 haces | `data/GT/all_tracks.tck` |
| SIFT2 | pesos entre 0.19 y 3.7, ninguno es cero | `out/pesos_sift2.txt` |
| COMMIT | 44.8 % de los pesos son cero | `out/commit/pesos_commit.txt` |
| LiFE | 25.4 % de los pesos son cero (entrega de Andrea y su equipo sobre este mismo tractograma) | `out/equipos/life_100k/life_weights.txt` |
| COMMIT2 (extra) | 63.1 % de ceros (group lasso, λ = 1e-2) | `out/commit2/pesos_commit2.txt` |

Regla que cumplen todos: **100 000 pesos ≥ 0, sin NaN, en el orden de `tracks_100k.tck`**. Un peso cero significa «el método eliminó ese hilo».
Solo se verificó el orden de COMMIT y COMMIT2 por el tamaño del vector; ningún resultado salió «exactamente al azar», que sería la señal de un orden equivocado.

---

## 4. Paso 9: normalizar y filtrar con ε (por método)
Script: `bash scripts/09_filtrar_pesos.sh <pesos> <metodo> <epsilon>`. Detalle: `docs/filtrado_pesos.md`.
1. **Normalizar:** `peso_norm = peso / máximo` → valores entre 0 y 1. (Es lo que usaron el equipo de SIFT2 y el script de matrices. También calcula el **percentil** como columna opcional, que es la normalización de Ricardo.)
2. **Filtrar:** el hilo es *válido* si `peso_norm ≥ ε`.

Con **ε = 0.1** quedan cosas muy distintas por método:
| Método | Hilos válidos | % |
|---|---|---|
| SIFT2 | 93 978 | 94.0 % |
| COMMIT | 9 911 | 9.9 % |
| LiFE | 50 239 | 50.2 % |
| COMMIT2 | 564 | 0.6 % |

**Lección:** un mismo ε no significa lo mismo en cada método. SIFT2 casi no descarta nada (sus pesos están todos cerca de 1); en COMMIT unos pocos hilos tienen pesos enormes y el máximo «aplasta» al resto. El doctor dijo que ε = 0.01 era un ejemplo, **no un valor decidido**; por eso conviene comparar a **igual número de hilos conservados** (sección 7).

---

## 5. Paso 8: la «verdad» por hilo con Hausdorff
Detalle: `docs/hausdorff_instrucciones.md`, `docs/hausdorff_eficiencia.md`, `docs/etiqueta_hausdorff_vs_mdf.md`.

**Qué es.** La distancia de Hausdorff mide qué tan parecidas son dos trayectorias *de punta a punta*: es el peor desajuste entre ellas. Para cada hilo buscamos el hilo del GT más parecido y guardamos esa distancia en mm (`hd_min`). Un hilo **corresponde al GT** si `hd_min < ε`.

**Quién lo hizo.** Se repartió en 7 bloques de ~14 286 hilos, uno por persona (Max, Andrea, Jacqueline, Mario, Pablo, Richie, Sarai). Los 7 resultados se unieron en `out/hausdorff/hausdorff.csv` (100 000 filas). Todos los bloques dieron porcentajes casi idénticos (33 ± 0.5 % a 5 mm), lo que indica que todos usaron los mismos archivos.

**Resultado:**
| ε (mm) | Hilos que corresponden al GT |
|---|---|
| 2 | 2.6 % |
| 3 | 13.0 % |
| **5** | **33.3 %** (33 349 hilos) |
| 7 | 46.0 % |
| 10 | 58.6 % |

**ε = 5 mm** es nuestra propuesta principal (≈ 2.5 vóxeles de 2 mm; el mismo valor que usamos antes con otra etiqueta, para poder comparar). **Está pendiente de que el doctor lo confirme.** Con 2 mm casi no habría hilos verdaderos; las conclusiones no cambian con 3 o 7 mm.

**Por qué no tardó 3 días.** Las notas estimaban ≈ 3 días por 10 000 hilos (comparar cada hilo contra los 189 985 del GT). Nosotros descartamos primero, con un índice espacial, los hilos del GT que geométricamente están a más de 10 mm (no pueden ser la respuesta), y calculamos la distancia exacta solo contra los pocos que quedan. Medido: **fuerza bruta ≈ 22 s por hilo; nuestro método ≈ 0.12 s**. En 40 hilos al azar el resultado es **idéntico** (diferencia máxima 0.0 mm), y remuestrear a 2 mm cambia a lo más 0.24 mm. Respuesta corta para el doctor: sección 11.

**Qué significa «verdadero».** Es una aproximación: «este hilo está a menos de ε mm de algún hilo del GT». Depende de ε y exige coincidencia de punta a punta. Existe porque el fantoma es simulado y conocemos el GT; con datos reales no habría GT.

---

## 6. Paso 10: ¿acierta cada método? (evaluación por hilo)
Script: `bash scripts/10_evaluar.sh`. Detalle: `docs/evaluacion_filtrado.md`.

**Cómo se lee.** Usamos la etiqueta de Hausdorff (5 mm) como respuesta correcta y comparamos con lo que cada método conserva:
- **Precisión:** de los hilos que el método conserva, qué % es verdadero. *Sin filtrar daría 33.3 % (la «tasa base»); un método sirve si la supera.*
- **Recall:** de todos los hilos verdaderos, qué % logra conservar.
- **AUC:** si el peso, solo, ordena los hilos verdaderos por encima de los falsos. **0.5 = azar; menos de 0.5 = va al revés.**
- **Longitud como referencia:** una regla tonta, «me quedo con los hilos largos». Un método debería superarla.

**Resultado (AUC):**
| Método | AUC |
|---|---|
| SIFT2 | 0.426 |
| COMMIT | 0.449 |
| LiFE | 0.601 |
| COMMIT2 | 0.634 |
| *longitud sola* | *0.652* |

**Precisión conservando los n hilos de mayor peso** (comparación justa entre métodos):
| n | SIFT2 | COMMIT | LiFE | COMMIT2 | longitud |
|---|---|---|---|---|---|
| 10 000 | 13.4 % | 14.7 % | 42.9 % | **48.7 %** | 31.7 % |
| 25 000 | 21.5 % | 25.3 % | 41.1 % | **52.5 %** | 42.2 % |
| 50 000 | 28.7 % | 30.9 % | 40.8 % | 42.3 % | 42.4 % |

**Lectura.**
- **SIFT2 y COMMIT están por debajo del azar:** sus pesos más altos caen en hilos *más falsos* que la media; filtrar con ellos **empeora** la proporción de verdaderos. Esto coincide con lo que reportó el equipo de SIFT2 por su cuenta (AUC ≈ 0.42) y con lo que medimos antes con otra etiqueta.
- **LiFE y COMMIT2 aportan**, hasta 1.2–1.6 veces mejor que no filtrar.
- **Ninguno supera claramente a la longitud sola** (0.652): una buena parte de lo que «ven» los métodos es que los hilos largos son más probables.

---

## 7. ¿Por qué SIFT2 y COMMIT salen mal? (la longitud)
| | AUC global | corr(peso, longitud) | AUC **dentro de hilos de longitud parecida** |
|---|---|---|---|
| SIFT2 | 0.426 | **−0.41** | 0.508 |
| COMMIT | 0.449 | −0.20 | 0.485 |
| LiFE | 0.601 | +0.27 | 0.529 |
| COMMIT2 | 0.634 | +0.27 | 0.576 |

- SIFT2 asigna **pesos altos a hilos cortos** (correlación −0.41), y los hilos cortos casi nunca coinciden con el GT. Eso hunde su AUC.
- Si comparamos solo hilos de longitud parecida, SIFT2 queda en ≈ 0.51 y COMMIT en ≈ 0.49: **sus pesos no dicen nada propio sobre si el hilo es verdadero.** No están «al revés»; simplemente no aportan.
- LiFE y COMMIT2 conservan algo propio, pequeño (0.53 y 0.58).

**Normalización de Ricardo (percentil).** Convierte cada peso en «qué lugar ocupa el hilo dentro de su método» (0 se queda en 0), para poder promediar métodos con escalas distintas. Lo que hace y lo que no:
- **No cambia el AUC de ningún método** (el orden de los hilos es el mismo): SIFT2 sigue en 0.426. No arregla el problema anterior.
- Sí resuelve el problema de la **escala** y permite promediar.
- **Promediar los 3 métodos del doctor no sirve** (AUC 0.485; precisión 30 %, peor que no filtrar): SIFT2 y COMMIT arrastran el promedio. Con LiFE + COMMIT2 sube a 0.649.
- La regla de voto «al menos 2 de 3 métodos» da 30.2 % de aciertos (peor que el 33.3 % sin filtrar).
- Percentil *por rangos de longitud* o multiplicar por la longitud: ninguna variante supera a la longitud sola (0.652).
Detalle: `docs/resultados/modelo_y_normalizacion_hausdorff.md`, `docs/resultados/normalizacion.md`.

---

## 8. Paso 11: el modelo
Script: `bash scripts/11_modelo.sh` (≈ 30 s). Regresión logística: entra el peso de cada método (y opcionalmente la longitud) y sale la probabilidad de que el hilo sea verdadero. **Se entrena con la mitad de los hilos y se evalúa en la otra mitad** (50/50, semilla fija), para no engañarnos.

| Modelo | AUC en prueba |
|---|---|
| longitud sola | 0.649 |
| COMMIT2 solo | 0.633 |
| promedio de Ricardo, 3 métodos | 0.486 |
| **logística: SIFT2 + LiFE + COMMIT** (los 3 del doctor) | **0.623** |
| logística: 3 métodos + longitud | 0.662 |
| logística: 4 métodos | 0.683 |
| **logística: 4 métodos + longitud** | **0.701** |

- **El modelo sí le saca provecho a los 3 métodos** del doctor: pasa de 0.486 (promedio) a 0.623. Aprende un **coeficiente negativo para SIFT2 y COMMIT** (a más peso, *menos* probable que sea verdadero) y positivo para LiFE; una regla fija como promediar no puede hacer eso.
- Con la longitud como entrada, el coeficiente de SIFT2 se va a ≈ 0: lo que aportaba era longitud. Por eso mostramos siempre el resultado **con y sin** longitud.
- No hay sobreajuste: el AUC de entrenamiento y el de prueba difieren menos de 0.01.
- **Para filtrar poco y bien** (quedarse con hilos muy confiables), gana **LiFE + COMMIT2** con el mínimo de sus percentiles (los dos deben ser altos): **54.3 %** de verdaderos con 10 000 hilos y 53.2 % con 25 000 (COMMIT2 solo: 48.7 % / 52.5 %; longitud: 31.7 % / 42.2 %). Los modelos con longitud ordenan mejor en general, pero son peores en ese extremo.
- **Con ε de Hausdorff de 3 y 7 mm el orden de los métodos es el mismo.** (Con 3 mm la longitud pierde fuerza: 0.567.)

---

## 9. El tractograma filtrado contra el GT (haz por haz)
Detalle: `docs/resultados/tractograma_modelo_vs_gt.md`. Scripts: `python scripts/puntajes_candidatos.py 5` y `scripts/normalizacion_ricardo.py --etiqueta hausdorff --mismos-n 10000 25000 50000` (≈ 1 min).

Hasta la sección 8 medimos **«¿cada hilo acierta?»**. Aquí medimos **«¿el conjunto se parece al GT?»**, que es lo que la junta pide literalmente. Cada puntaje conserva el **mismo número de hilos** (los de mayor puntaje) y el tractograma resultante se compara con los 21 haces del GT:
- **% falsos:** de los hilos conservados, cuántos no corresponden al GT (Hausdorff ≥ 5 mm). *Sin filtrar: 66.7 %.*
- **Haces recuperados:** haces con Dice ≥ 0.3 (contar «al menos un hilo» sería engañoso: un haz con 2 hilos no está recuperado).
- **Dice:** solape en vóxeles entre lo que queda de cada haz y el haz del GT, promediado sobre los 21. Solo cuenta los hilos verdaderos; los falsos se miden aparte, con el % de falsos.

**Conservando 25 000 hilos (de 100 000):**
| Puntaje | % falsos | Haces recuperados (de 21) | Dice |
|---|---|---|---|
| mínimo LiFE + COMMIT2 | **46.8 %** | 14 | 0.49 |
| COMMIT2 solo | 47.5 % | 14 | 0.50 |
| modelo 4 métodos | 49.7 % | 14 | 0.50 |
| modelo 4 métodos + longitud | 51.8 % | 13 | 0.42 |
| modelo 3 métodos del doctor (SIFT2 + LiFE + COMMIT) | 57.4 % | 15 | 0.48 |
| LiFE solo | 58.9 % | 17 | 0.49 |
| longitud sola | 57.8 % | 9 | 0.32 |
| COMMIT solo | 74.7 % | **20** | **0.70** |
| SIFT2 solo | 78.5 % | **20** | 0.62 |
| *sin filtrar (100 000 hilos)* | *66.7 %* | *20* | *0.77* |

**Lectura.**
- **Esta evaluación contradice a la de por hilo.** Lo más preciso por hilo (mínimo LiFE + COMMIT2, COMMIT2, los modelos) deja menos falsos, pero **pierde los mismos 6 haces**: BPS izquierdo y derecho, Fornix, ICP izquierdo y derecho, y CA (que tiene solo 33 hilos verdaderos). CP no cuenta: tiene 1 solo hilo verdadero y no se recupera ni sin filtrar. SIFT2 y COMMIT, los peores por hilo, recuperan 20 de 21.
- **La causa es COMMIT2:** les pone peso 0 al 99.7 % de los hilos verdaderos de BPS y al 100 % de los de Fornix e ICP (su group lasso apaga conexiones completas). Todo puntaje que dependa de COMMIT2 hereda esa pérdida. LiFE sí conserva entre el 53 % y el 92 % de esos hilos.
- **El modelo con longitud es el que más haces pierde** (7 de 21 con 10 000 hilos): se queda con hilos largos y abandona los haces cortos, como ICP (≈ 60 mm).
- **No hay un ganador en las dos cosas.** Si se prioriza un tractograma limpio: mínimo LiFE + COMMIT2 (46.8 % de falsos, 14 haces). Si se prioriza no perder haces: el modelo de los 3 métodos del doctor (15 haces, 57.4 %) o LiFE solo (17 haces, 58.9 %), ambos mejores que no filtrar. COMMIT cubre 20 haces, pero con más falsos que no filtrar.
- **Con 50 000 hilos casi todos recuperan 20 haces** y el % de falsos de los mejores sube a 54–59 %: a ese tamaño el filtro ayuda poco.
- **Pendiente:** COMMIT2 se corrió con λ = 1e-2. Con un λ menor quizá no apague BPS, Fornix e ICP. Hay que revisarlo con Sarahi (su corrida y la nuestra ya diferían en el número de pesos distintos de cero: 62 779 contra 36 928).

---

## 10. Estado respecto al objetivo
| | Qué pide el objetivo | Estado |
|---|---|---|
| A | 100 000 pesos por método | **Hecho** (SIFT2, LiFE, COMMIT; COMMIT2 extra) |
| B | Normalizar a (0,1), filtrar con ε y comparar cada método con el GT | **Hecho**: por hilo (precisión/AUC) y por tractograma (haces recuperados, Dice, % falsos; sección 9). Falta el ε definitivo |
| C | Etiqueta por hilo con Hausdorff | **Hecho** (ε = 5 mm, pendiente de confirmar) |
| D | Modelo de los 3 pesos y comparar su tractograma con el GT | **Hecho** (secciones 8 y 9) |
| — | Informe | Por hacer |

**Qué falta, en orden:**
1. **Decidir con el doctor qué se prioriza:** un tractograma limpio (pocos falsos, pero se pierden BPS, Fornix e ICP) o no perder haces (más falsos). La sección 9 tiene las dos opciones.
2. **Revisar COMMIT2 con Sarahi:** con un λ menor quizá no apague BPS, Fornix e ICP, y eso cambiaría la recomendación.
3. Fijar el ε final (de Hausdorff y de los pesos) con el doctor.
4. Redactar el informe.

---

## 11. Preguntas que puede hacer el doctor (y respuestas)
**«¿Por qué su Hausdorff no tardó 3 días?»** Es la misma distancia contra los 189 985 hilos del GT. Solo evitamos calcularla contra los hilos del GT que geométricamente están a más de 10 mm, con un índice espacial (KD-tree). Lo comprobamos contra fuerza bruta en 40 hilos al azar: resultado idéntico. La fuerza bruta mide 22 s/hilo (≈ 2.5 días por 10 000 hilos: coincide con su estimación); la nuestra, 0.12 s/hilo.

**«¿Por qué ε = 5 mm?»** Es una propuesta: ≈ 2.5 vóxeles, y el mismo valor con el que comparamos antes. Guardamos las distancias, no el 0/1, así que cualquier ε se obtiene sin recalcular. Con 3 y 7 mm las conclusiones no cambian.

**«¿Por qué SIFT2 sale por debajo del azar?»** Da pesos altos a hilos cortos, y los cortos casi nunca están en el GT. Entre hilos de longitud parecida su peso no distingue verdaderos de falsos (AUC 0.51). Es coherente con que SIFT2 busca ajustar la señal, no la plausibilidad anatómica.

**«¿Entonces los métodos no sirven?»** Hilo por hilo, SIFT2 y COMMIT no; LiFE y COMMIT2 sirven moderadamente. Combinados con un modelo sí se aprovechan los 3 (AUC 0.62 con los 3 del doctor, 0.70 con los 4 y la longitud). Pero en el tractograma completo SIFT2 y COMMIT son los que mejor conservan los 21 haces (sección 9): dejan muchos falsos, pero no apagan haces enteros.

**«¿Qué tractograma filtrado recomiendan?»** Depende de qué se priorice. Para un tractograma limpio, el mínimo de LiFE + COMMIT2 (con 25 000 hilos: 46.8 % de falsos contra 66.7 % sin filtrar), avisando que pierde BPS, Fornix e ICP. Para no perder haces, el modelo de los 3 métodos del doctor o LiFE solo (15–17 de 21 haces, ≈ 58 % de falsos).

**«¿Por qué se pierden BPS, Fornix e ICP?»** Porque COMMIT2 les pone peso 0 a casi todos sus hilos verdaderos (99.7–100 %): su regularización apaga conexiones completas. Cualquier combinación con COMMIT2 hereda esa pérdida. Lo vamos a revisar con otro λ.

**«¿El modelo no está haciendo trampa con la etiqueta?»** Se entrena con la mitad de los hilos y se evalúa en la otra mitad; los AUC de entrenamiento y prueba difieren < 0.01. Falta además validar en otro conjunto (otro fantoma o tractograma).

**«¿Y la longitud?»** La longitud sola ya da AUC 0.65. Por eso reportamos los modelos con y sin ella, para ver cuánto aportan los pesos de verdad.

**«¿Por qué conservan LiFE?»** Se quedó por indicación del doctor; resultó de los más útiles junto con COMMIT2.

**«¿Y las matrices 84×84?»** Ya no son el entregable. Se hicieron antes y quedan como extra: `docs/resultados/matrices.md`, `docs/explicacion_commit.md`.

---

## 12. Limitaciones (para decirlas nosotros antes de que pregunten)
- Es **un solo fantoma simulado** y un solo tractograma. No sabemos si se generaliza.
- «Verdadero» = cerca del GT (Hausdorff < ε). Es estricto: un hilo que sigue bien al GT solo en un tramo cuenta como falso.
- Un solo ε principal (5 mm); y un solo corte entrenamiento/prueba 50/50.
- La regresión logística es lineal; un modelo no lineal podría extraer más, sobre todo de la interacción peso × longitud.
- El orden de los vectores de COMMIT y COMMIT2 se verificó solo por tamaño.
- El Dice por haz solo cuenta los hilos verdaderos: un método con 85 % de falsos puede tener buen Dice. Hay que leerlo siempre junto al % de falsos.
- COMMIT2 se corrió con un solo λ (1e-2), y es el que apaga BPS, Fornix e ICP.
- Los pesos de SIFT2 del equipo de SIFT2 (máx 3.7069) difieren un poco de los nuestros (máx 3.7022): usamos los nuestros.
- Los porcentajes de hilos falsos de la normalización vieja (con otra etiqueta) **no** son comparables con los de ahora.

---

## 13. Dónde está cada cosa
| Paso | Script | Qué hace |
|---|---|---|
| 01–03, 05 | `01_preprocess`, `02_tractography` (+SIFT2), `03_commit`, `05_life` | datos y pesos de cada método |
| 04, 06, 07 | `04_matrices`, `06_commit2`, `07_normalizacion` | extras (matrices, COMMIT2, normalización de Ricardo) |
| 08 | `08_hausdorff.sh` | etiqueta por Hausdorff (por bloques; `unir` los junta) |
| 09 | `09_filtrar_pesos.sh`, `09_filtrar_todos.sh` | normalizar y filtrar con ε |
| 10 | `10_evaluar.sh` | evalúa cada método contra Hausdorff |
| 11 | `11_modelo.sh` | normalización de Ricardo y modelo vs Hausdorff |
| D (tractograma) | `puntajes_candidatos.py` + `normalizacion_ricardo.py --etiqueta hausdorff --mismos-n …` | tractograma filtrado contra el GT, haz por haz (sección 9) |

Documentos: `README.md` (mapa), `pipeline.md` (pasos y números de control), `ACTUALIZACION.md` (estado), `docs/diagramas.md` (flujo de datos y fases), `docs/conclusiones.md` (conclusiones anteriores).

---

## 14. Glosario
- **Streamline / hilo:** trayectoria 3D (lista de puntos en mm) que representa una fibra.
- **Tractograma:** conjunto de streamlines. **GT (ground truth):** las fibras verdaderas del fantoma simulado.
- **Peso:** número que un método le da a cada hilo (qué tan creíble es).
- **ε (épsilon):** umbral. Hay dos distintos: el de los **pesos** (descartar si peso normalizado < ε) y el de **Hausdorff** (verdadero si distancia < ε mm).
- **Distancia de Hausdorff:** el peor desajuste entre dos trayectorias, de punta a punta.
- **Precisión / recall / AUC / tasa base / lift:** ver sección 6. Lift = precisión ÷ tasa base (1 = igual que no filtrar).
- **Percentil (Ricardo):** el lugar que ocupa el peso de un hilo dentro de su método, entre 0 y 1.
- **Dice:** solape entre dos conjuntos de vóxeles (0 = nada, 1 = idénticos).
- **MDF:** otra distancia entre hilos (usada con una etiqueta anterior, 54.8 % a 5 mm); queda solo para comparar.

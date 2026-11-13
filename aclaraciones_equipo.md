# Qué hay que aclarar como equipo

Revisión del 2026-11-13 (actualizada tras traer lo que subió la Mac: `integracion_metodos.md`). Cada punto dice qué es, **cómo lo sabemos** (para poder comprobarlo) y qué hay que hacer o decidir.

Equipos: **COMMIT** (ya hecho en la Mac), **SIFT2** y **LiFE**.

---

## 1. Lo que ya está claro

| # | Hecho | Cómo se comprueba |
|---|---|---|
| 1 | **Hay un solo tractograma oficial:** `data/tracks_100k.tck`, 100 000 hilos. | `md5sum data/tracks_100k.tck` debe dar `66ba3e6efe1fadf5b534d3947b2b138f`. `tckstats`: media 92.13, mediana 95.21, std 40.65. |
| 2 | **COMMIT está hecho** (en la Mac). Entregó la matriz `matriz_peso_commit_84x84_corregida.xlsx`: 1203 conexiones con peso, 446 de las 529 del GT recuperadas. | Abrir el `.xlsx` (84 × 84, simétrica, diagonal 0). |
| 3 | **SIFT2 usó el tractograma común.** Su `Connectome_SIFT2_100k.csv` tiene exactamente las mismas 1322 conexiones que el `.tck` oficial. | Comparar qué celdas son > 0 contra `tck2connectome` del `.tck` oficial sin pesos. |
| 4 | **LiFE todavía no usó el tractograma común.** Su `conn_life_full.csv` tiene 595 conexiones y 154 no existen en el `.tck` oficial. | Mismo método de comparación. |
| 5 | **El eje `y` cambia la tractografía.** Con los gradientes tal cual, los hilos salen de ≈ 36–42 mm; con `y` invertido, de ≈ 92 mm. | Pruebas controladas (solo cambian los gradientes). Detalle en `explicacion_commit.md`, sección 6. |

### Sobre el eje `y`: qué sabemos y qué no

Invertir un solo eje **no es simétrico**: es un espejo. Una fibra que apunta a (1, 1, 0) pasaría a verse como (1, −1, 0). Lo que sí es simétrico es invertir los tres ejes a la vez.

| Pregunta | Respuesta |
|---|---|
| ¿Cambia la tractografía? | **Sí, demostrado** (hilos de ≈ 36–42 mm a ≈ 92 mm; la dirección del tensor concuerda mejor con el GT, |cos| 0.40 → 0.64). |
| ¿Explica toda la mejora de la matriz de COMMIT (125 → 446 conexiones reales)? | **No se sabe.** En la versión corregida cambiaron cuatro cosas a la vez (`y`, `fiber_shift`, `-mask` en `tckgen`, difusividades del Ball). Habría que probarlas una por una. |
| ¿Cambia los pesos de SIFT2? | **Casi no** (prueba del 2026-11-13, mismo tractograma, FOD con y sin `y` corregido: correlación de pesos por hilo 0.989, de la matriz 0.9999). |
| ¿Cambia los pesos de COMMIT o de LiFE? | **No se ha probado.** Es una hipótesis razonable (comparan la dirección de cada hilo con la señal), pero sigue siendo hipótesis. |

### Sobre la diagonal de las matrices

- La celda `(i, i)` cuenta los hilos cuyos **dos extremos caen en la misma región**. No es una conexión entre regiones.
- Las matrices de SIFT2 y LiFE la traen con valores (suma 5968 y 14.8); la de COMMIT la trae en 0 porque se usó `-zero_diagonal`.
- **No cambia las otras celdas.** Es el mismo cálculo con una opción distinta. Por eso **nadie tiene que repetir nada**: al comparar, se pone la diagonal en 0 (`np.fill_diagonal(M, 0)`). Solo importa si se suman totales o se normaliza sin quitarla, porque contamina esos números.
- Convención para el equipo: **las comparaciones se hacen con la diagonal en 0**, y cada quien entrega su matriz como la tenga.

---

## 2. Lo que hay que preguntar o corregir

### Equipo de SIFT2: ¿de qué FOD salieron los pesos?

`tcksift2` necesita dos cosas: el tractograma y una **FOD**. Esa FOD se calcula con `dwi2fod`, a partir de la imagen y los gradientes. La pregunta es si la FOD de SIFT2 usó los gradientes **con `y` invertido** (como el `.tck` oficial) o **sin invertir**.

**Qué buscar en su script**
1. La línea `tcksift2 <tractograma> <FOD> <pesos>`: ¿qué archivo está en la posición de `<FOD>`? (`ODF.nii`, `fod.mif`...).
2. El comando que **generó** ese archivo, `dwi2fod csd ...`: ¿le pasaron `-fslgrad ....bvec ....bval` (sin invertir) o `out/dwi.mif` / `-grad gradientes_y.b` (invertido)?
3. Lo mismo para el comando `dwi2response` anterior.
4. Su archivo viejo (`Comandos SIFT2.txt`) usaba `-fslgrad` con el `.bvec` original.

**Qué preguntarles**
> ¿Qué archivo le pasaron a `tcksift2` como FOD y con qué comando lo generaron: con `-fslgrad` del `.bvec` original, o con `dwi.mif` (gradientes con `y` invertido)? ¿Y pueden mandarnos el `pesos_sift2.txt` además de la matriz?

**Por qué importa poco:** en la prueba del 2026-11-13 la matriz de SIFT2 casi no cambió entre usar una FOD y otra (0.9999). La matriz que mandaron queda incluso un poco más cerca de la FOD **sin** corregir (cociente mediano 1.000, contra 0.998 con la corregida), pero la diferencia es tan pequeña que no sirve para decidir. Hay que preguntarles.

### Equipo de LiFE
1. **Usar el tractograma oficial** (`data/tracks_100k.tck`) y no generar el suyo.
2. **Gradientes:** la Mac comprobó que el `.bvec` crudo en DIPY es idéntico a nuestra tabla corregida, así que su lectura con `read_bvals_bvecs` es correcta. No hay que cambiarla (la inversión de `y` solo importa al importar a MRtrix con `-fslgrad`). Queda corregido lo que escribí antes.
3. **Entregar 100 000 pesos** (`pesos_life.txt`) en el orden del `.tck`, además de la matriz.
4. **Reportar** número de hilos, memoria, tiempo y porcentaje de pesos en 0.

### Equipo de COMMIT
- **Ya está hecho en la Mac.** No hace falta repetirlo aquí. Lo único pendiente es que entreguen `out/commit/pesos_commit.txt` (un peso por hilo), porque con la matriz sola no se puede comparar hilo por hilo con SIFT2 y LiFE.

---

## 3. Lo que hay que decidir juntos

| # | Decisión | Opciones | Recomendación |
|---|---|---|---|
| 3.1 | **LiFE: ¿100 000 hilos o una submuestra?** Con 100 000 gasta ≈ 7.7 GB de RAM. | (a) `todos` en una máquina con RAM; (b) la misma submuestra en los tres métodos. | (a) si alguna máquina aguanta; si no, (b). Lo que no sirve es que cada método use hilos distintos. |
| 3.2 | **COMMIT: ¿matriz "a secas" o × longitud?** El peso de COMMIT va por unidad de longitud y favorece los hilos cortos. | Entregar una o las dos. | Entregar las dos y decidir con las métricas de la sección 4. |
| 3.3 | **¿Cómo comparar pesos de métodos distintos?** Las unidades no coinciden. | Por rangos, o normalizando. | Por rangos. |
| 3.4 | **¿Qué es un hilo "bueno"?** La etiqueta por extremos que hay hoy es débil (AUC 0.46 por hilo para COMMIT). | Etiqueta por haz con distancia al GT y un umbral. | Por haz. Falta fijar el umbral y quién lo hace. |
| 3.5 | **¿Qué significa un peso 0?** | "Descartar" o "redundante". | Es una hipótesis sin comprobar; no darlo por hecho en el informe. |
| 3.6 | **Reparto** de las etiquetas por haz, la comparación entre métodos y la regla de decisión. | Un equipo por tarea. | Asignar responsables esta semana. |

---

## 4. Cómo vamos a comparar

**Entre métodos**
- Por hilo: correlación de rangos entre pares de métodos y solape de los hilos con peso 0. Necesita los archivos de pesos.
- Por conexión: correlación entre las matrices 84 × 84 (con la diagonal en 0) y cuántas conexiones elimina cada método.

**Contra el ground truth**
- Por conexión (ya se puede): `scripts/evaluar_pesos.py` compara cada matriz con el conectoma del GT (529 conexiones reales).
- Por hilo (falta): requiere la etiqueta por haz de la decisión 3.4.

**Sobre la máscara.** Ninguna comparación usa la máscara del cerebro; solo limita dónde se calcula. Ver `explicacion_commit.md`, sección 2.

---

## 5. Lo que no sabemos todavía

- (Resuelto por la Mac) La FOD de SIFT2 usó el `.bvec` crudo y otra máscara; efecto pequeño (Pearson de pesos 0.989). Sigue pendiente pedirles `pesos_sift2.txt` si quieren su versión; la nuestra es `out/pesos_sift2.txt`.
- Cuánto de la mejora de COMMIT se debe al eje `y` y cuánto a los otros tres cambios.
- Si `y` afecta los pesos de COMMIT y de LiFE.
- Si LiFE sobre el tractograma oficial da resultados parecidos a los que ya tienen.

Prueba que lo aclararía: repetir COMMIT cambiando **una sola cosa a la vez** (la Mac tiene el script y la opción `--sin-corregir-y`).

---

## 6. Lista corta para alinear a todos

- [ ] Todos tienen `data/tracks_100k.tck` con el `md5` del punto 1.
- [ ] Cada método entrega `pesos_<metodo>.txt` con 100 000 pesos (≥ 0, sin `NaN`) y su matriz 84 × 84.
- [ ] Las comparaciones se hacen con la diagonal en 0.
- [ ] LiFE corre `correr_life.py` sobre `data/tracks_100k.tck`.
- [ ] SIFT2 aclara de qué FOD salieron sus pesos.
- [ ] Se decide 3.1, 3.2 y 3.6.

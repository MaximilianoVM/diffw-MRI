# Siguiente paso (Mac): normalización de Ricardo y modelo, evaluados contra Hausdorff

Para el Claude de la Mac y para Ricardo. Haz `git pull` antes de empezar (trae `out/hausdorff/hausdorff.csv` y el paso 10).
Contexto: `docs/junta_17nov.md`, `docs/evaluacion_filtrado.md`, `docs/hausdorff_eficiencia.md`.

## 1. Lo que ya medimos (Hausdorff < 5 mm = verdadero; 33 349 de 100 000 hilos; tasa base 33.3 %)
AUC del peso como clasificador de la etiqueta (0.5 = azar). Se calculó con numpy en la laptop de desarrollo.

| | AUC global | corr(peso, longitud) | AUC peso×longitud | AUC percentil por decil de longitud | AUC **dentro** de cada decil de longitud |
|---|---|---|---|---|---|
| SIFT2 | 0.426 | **−0.41** | 0.620 | 0.505 | 0.508 |
| COMMIT | 0.449 | −0.20 | 0.482 | 0.498 | 0.485 |
| LiFE | 0.601 | +0.27 | 0.620 | 0.517 | 0.529 |
| COMMIT2 | 0.634 | +0.27 | 0.633 | 0.561 | 0.576 |
| longitud sola | 0.652 | | | | |

Combinaciones al estilo Ricardo (promedio de percentiles):
| Percentil | Promedio SIFT2+COMMIT+LiFE | + COMMIT2 | LiFE+COMMIT2 |
|---|---|---|---|
| global (especificación) | AUC 0.485 | 0.541 | 0.649 |
| por decil de longitud | AUC 0.509 | 0.555 | 0.610 |

Regla «≥ 2 de 3» (percentil > 0.5 en al menos 2 métodos): con SIFT2+COMMIT+LiFE conserva 33 719 hilos con precisión 30.2 % (peor que
la tasa base 33.3 %); con LiFE+COMMIT2 conserva 10 637 con 54.4 %.

## 2. Qué dicen estos números
1. **SIFT2 y COMMIT salen por debajo del azar por la longitud.** SIFT2 da pesos altos a hilos cortos (correlación −0.41) y los
   hilos cortos casi nunca son verdaderos. Al comparar solo hilos de longitud parecida (último bloque de la tabla), SIFT2 ≈ 0.51 y COMMIT ≈ 0.49: **sus
   pesos no aportan información propia sobre la etiqueta**, no están al revés.
2. **La normalización percentil global de Ricardo no cambia el AUC de ningún método** (es una transformación monótona; SIFT2 sigue en 0.426).
   Resuelve otra cosa: pone los tres métodos en la misma escala para poder promediarlos. Esa es su utilidad.
3. **Percentil por decil de longitud** quita el efecto de la longitud y lleva a SIFT2 a 0.505: confirma el punto 1. No «mejora» SIFT2: muestra que sin longitud no hay señal.
4. **Multiplicar por longitud (peso×L)** sube SIFT2 a 0.62, pero es longitud, no SIFT2.
5. **Promediar con SIFT2 y COMMIT empeora** el resultado (0.485 vs 0.649 sin ellos): arrastran al promedio.
6. **LiFE y COMMIT2 sí tienen algo propio**, pequeño (0.53 y 0.58 dentro de deciles de longitud).
7. Un modelo supervisado puede usar un coeficiente **negativo** para SIFT2 y la longitud como entrada: ese ajuste es justo lo que la regla fija «promediar» no puede hacer.

## 3. Qué hacer en la Mac (en este orden)

### 3.1 Evaluar lo de Ricardo con la etiqueta de Hausdorff (no con MDF)
`scripts/normalizacion_ricardo.py` hoy evalúa con MDF (`--etiqueta mdf|mascara`). Añade `--etiqueta hausdorff`, que lea
`out/hausdorff/hausdorff.csv` (columna `hd_min`; verdadero = `hd_min < --eps-hd`, por omisión 5; vacío = falso). No cambies el comportamiento de las opciones existentes.
Corre, con COMMIT, SIFT2, LiFE y COMMIT2:
- percentil global; `--por-longitud 10`; `--x-longitud`; `--corte` (SIFT2 sin ceros).
- combinaciones: promedio de los 4; de LiFE+COMMIT2; voto «≥ 2 de 3» y «≥ 2 de 4».
Reporta, para cada una: AUC, precisión/recall/lift al conservar los n = 10 000, 25 000 y 50 000 hilos de mayor puntaje, y compara
**siempre** con (a) la longitud sola y (b) COMMIT2 solo. Se puede reutilizar `scripts/evaluar_filtrado.py` (funciones `auc` y `metr`).

### 3.2 Modelo (paso 11) con separación entrenamiento/prueba
- Entradas: percentil global de cada método (o log del peso) + longitud (`out/longitudes.txt`). Salida: etiqueta Hausdorff < 5 mm.
- Regresión logística (sklearn). **Separar** 50/50 con semilla fija y estratificado por etiqueta; ajustar solo con entrenamiento, reportar solo en prueba.
- Variantes: (i) con y sin longitud; (ii) solo los 3 métodos pedidos (SIFT2, LiFE, COMMIT); (iii) con COMMIT2.
- Imprimir los **coeficientes** (esperable: SIFT2 negativo). Comparar en prueba contra longitud sola, COMMIT2 solo y el promedio de Ricardo.
- Ojo: un modelo con longitud puede estar aprendiendo «hilo largo = verdadero». Mostrar siempre el resultado **sin** longitud para saber cuánto aportan los pesos.

### 3.3 Dónde dejar resultados
`docs/resultados/modelo_y_normalizacion_hausdorff.md` (tablas + una lectura de 5 líneas). Scripts nuevos con número libre (`11_modelo.sh` + `.py`).
Sube solo código, `.md` y tablas pequeñas (CSV < 5 MB). No renombres ni muevas nada existente. Avisa con el hash del commit.

## 4. Advertencias
- Los vectores de COMMIT y COMMIT2 se asumen en el orden de `tracks_100k.tck` (solo se verificó el tamaño). Si el AUC de COMMIT sale ≈ 0.5 exacto, sospechar orden.
- ε de Hausdorff = 5 mm es propuesta; repetir con 3 y 7 mm para ver si las conclusiones cambian.
- Las cifras de la sección 1 las generó un script efímero de la laptop de desarrollo; el paso 3.1 debe reproducirlas dentro del repo.

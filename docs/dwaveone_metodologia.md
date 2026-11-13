# DWaveOne: su metodología y qué nos sirve

Resumen de `DWaveOne_RP1_03_2025.pdf` (reporte, 3 págs.) y `Presentacion_DWaveOne_RP1_03_2025.pdf` (19 diapositivas).
Equipo DWaveOne (Erick Zúñiga y Nelly Zambrano), Laboratorio de Resolución de Problemas 1, 2025, con los mismos datos del ISMRM Challenge (actualización 2023).

---

## 1. Qué pregunta responden

**¿Qué software genera el tractograma más parecido al ground truth?**

No filtran streamlines ni usan COMMIT, SIFT2 o LiFE. Comparan tractogramas completos. Nuestro problema va un paso después: con un tractograma fijo, decidir qué streamlines conservar. Aun así, su forma de medir el parecido con el GT es justo la pieza que nos falta.

## 2. Qué hicieron

### 2.1 Tres tractogramas

| Software | Modelo / algoritmo | Hilos | Longitud media (mm) | Longitud total | Densidad |
|---|---|---|---|---|---|
| MRtrix3 | FOD por CSD, iFOD2 (probabilístico) | 100 000 | 35.76 | 3.58 M | 1 538.5 |
| DIPY | DTI (tensor) | 482 816 | 27.47 | 13.26 M | 7 315.4 |
| DSI-Studio | QSDR | 706 075 | 9.60 | 6.78 M | 100 867.9 |
| Ground truth | — | 189 985 | 103.74 | 19.71 | 2 878.6 |

(Tabla 1 del reporte; las unidades de "Total Len" y "Density" no se aclaran.)

### 2.2 Dos métricas contra el GT

**Dice volumétrico.** De cada tractograma se saca un mapa de densidad; un vóxel cuenta como ocupado si su densidad es mayor que 0. Luego:

$$\mathrm{DICE}(A,B) = \frac{2\,|A \cap B|}{|A| + |B|}$$

donde $|A \cap B|$ es el número de vóxeles ocupados en los dos.

**Distancia MDF (minimum average direct-flip) por streamline.** Cada hilo se remuestrea a $K = 20$ puntos y:

$$d_{\text{directa}}(s,t) = \frac{1}{K}\sum_{i=1}^{K} \lVert s_i - t_i \rVert, \qquad
\mathrm{MDF}(s,t) = \min\big(d(s,t),\ d(s, t^{F})\big)$$

$t^{F}$ es el hilo recorrido al revés; así no importa en qué sentido se trazó cada uno. MDF = 0 significa hilos idénticos.

**QuickBundles** (Garyfallidis 2012) agrupa los hilos en clusters con un umbral de 10 mm. Comparan cada hilo con los del cluster cercano, con un máximo de 20 hilos por cluster. Así no hace falta calcular todas las distancias hilo contra hilo.

### 2.3 Resultados

| Software | Dice | MDF media (mm) | MDF mediana | MDF desv. est. | Hilos evaluados |
|---|---|---|---|---|---|
| **DIPY** | **0.874** | **17.7** | 17.0 | 6.9 | 27 040 |
| MRtrix3 | 0.826 | 19.3 | 18.9 | 5.9 | 27 122 |
| DSI-Studio | 0.000 | 110.2 | 111.0 | 21.1 | 28 320 |

Concluyen que DIPY es el que mejor se aproxima al GT y DSI-Studio el peor. El 0 de DSI-Studio se debe a que su tractograma quedó en otro sistema de coordenadas y no lograron alinearlo. Los hilos evaluados son menos que los generados porque recortaron los que salen de los límites de la imagen.

## 3. Observaciones críticas

1. **Su tractograma de MRtrix muestra el error del eje y.** Mide 35.8 mm de media contra 103.7 mm del GT. Sin invertir el eje *y* del `.bvec`, nosotros obteníamos ≈ 42 mm; con la corrección, 92 mm. Es muy probable que no lo corrigieran, y que por eso MRtrix les quedara detrás de DIPY. DIPY lee el `.bvec` directo y no tiene ese problema.
2. **El Dice con umbral "> 0" es muy permisivo.** Un solo hilo que cruce un vóxel lo marca como ocupado, así que un tractograma con muchos falsos positivos puede tener Dice alto. Mide cobertura, no precisión.
3. **Comparan tractogramas con distinto número de hilos** (100 000 contra 482 816 contra 706 075). La densidad y el Dice dependen mucho de eso.
4. **La MDF se reporta para todo el tractograma**, no por haz. No dice qué hilos son válidos ni a qué haz pertenecen; solo da la distribución de distancias.
5. **Usan solo `all_tracks.tck`**, no los 21 haces del GT por separado.

## 4. Qué nos sirve a nosotros

**La MDF es la etiqueta por haz que nos falta.** Hoy `scripts/evaluar_pesos.py` etiqueta cada hilo por sus extremos (si las dos regiones que une están conectadas en el GT). Esa etiqueta es débil: el 27 % de nuestros hilos no termina en ninguna región, y con ella los tres métodos dan un AUC por hilo cercano al azar (COMMIT 0.458, SIFT2 0.430). Con la MDF a los haces del GT, cada hilo se etiqueta por su forma y su recorrido, no solo por dónde termina.

**El Dice sirve como métrica del tractograma filtrado.** Una vez aplicada la regla de decisión, el Dice entre el tractograma que conservamos y el GT mide cuánta cobertura se pierde. Conviene reportarlo junto con un umbral más exigente que "> 0".

## 5. Qué tenemos y qué nos falta para hacer lo mismo

| Qué | Estado |
|---|---|
| DIPY con QuickBundles y MDF (`dipy.segment.clustering.QuickBundles`, `dipy.tracking.streamline.set_number_of_points`) | ✅ en `.venv` (DIPY 1.12.1) |
| Los 21 haces del GT por separado | ✅ `data/GT/*.tck` |
| Tractograma y GT en el mismo espacio (mm) | ✅ `out/tracks_100k.tck` y `data/GT/` comparten coordenadas; no tenemos el problema que ellos tuvieron con DSI-Studio |
| Eje *y* corregido | ✅ `out/tracks_100k.tck` mide 92 mm de media |
| Mapas de densidad para el Dice | ✅ `tckmap` de MRtrix (ya probado en `extras/exploracion/`: `gt_bin.mif`, `mis_bin.mif`) |
| **Script de etiquetado por MDF** | ❌ falta escribirlo (ver abajo) |
| **Umbral de MDF para "válido"** | ❌ por decidir: 10 mm (el de su QuickBundles) o barrer varios valores |
| Pesos de LiFE sobre `out/tracks_100k.tck` | ❌ pendiente: con nuestros hilos de 92 mm pide ≈ 20 GB de RAM |

### Plan del script de etiquetado

1. Remuestrear a 20 puntos cada hilo de `out/tracks_100k.tck` y de cada haz de `data/GT/`.
2. Por cada haz del GT, sacar sus centroides con QuickBundles (umbral 10 mm).
3. Para cada hilo nuestro, calcular la MDF mínima a los centroides de cada haz y quedarse con el haz más cercano.
4. Etiquetar: **válido** si esa MDF es menor que el umbral, **inválido** si no. Guardar también a qué haz pertenece y la distancia.
5. Pasar esa etiqueta a `scripts/evaluar_pesos.py` en lugar de la etiqueta por extremos y recalcular el AUC por hilo de COMMIT, SIFT2 y LiFE.

Con eso la regla de decisión (combinar los tres pesos para conservar o descartar cada hilo) se puede entrenar y medir con una etiqueta confiable, y el Dice del tractograma filtrado contra el GT completa la evaluación.

## Referencias citadas por DWaveOne que nos sirven

- Garyfallidis et al. (2012). QuickBundles, a method for tractography simplification. *Frontiers in Neuroscience* 6:175.
- Garyfallidis et al. (2014). Dipy, a library for the analysis of diffusion MRI data. *Frontiers in Neuroinformatics* 8:8.
- Neher et al. (2015). The ISMRM 2015 Tractography Challenge. https://tractometer.org/ismrm2015/home/

# Normalización Ricardo

Instrucciones para implementar la normalización por **rango percentil** de los pesos de COMMIT, LIFE y SIFT2. El objetivo es combinar los tres métodos de filtrado de tractografía en uno solo y evaluarlo contra el ground truth.

---

## 1. Contexto

- Hay **un solo tractograma** de cerebro completo (`tractograma.tck` o `.trk`).
- Ese mismo tractograma se filtró con tres métodos, y cada uno asigna **un peso a cada fibra**:
  - **COMMIT:** pesos ≥ 0 (archivo típico: `streamline_weights.txt` en la carpeta de resultados de COMMIT).
  - **LIFE (DIPY):** pesos β ≥ 0 (`FiberFit.beta`).
  - **SIFT2 (MRtrix, `tcksift2`):** archivo `.txt` con un peso por fibra; las líneas que empiezan con `#` son comentarios.
  - Si en vez de SIFT2 se usó **SIFT** normal, no hay pesos: cada fibra vale **1** si se conservó y **0** si se eliminó.
- Peso **0** significa que el método **eliminó** la fibra.
- Hay un **ground truth** con un archivo por conducto.

**Requisito crítico:** los tres vectores de pesos deben tener **la misma longitud y el mismo orden de fibras** que el tractograma original. Antes de hacer cualquier otra cosa, verificarlo y detenerse con un error claro si no coincide.

---

## 2. El problema

Cada método usa una escala distinta (COMMIT ≈ 0.001–0.01, LIFE ≈ 0–40, SIFT2 ≈ 0–4), así que no se pueden promediar tal como vienen: el método con números más grandes dominaría.

**Solución:** no usar el valor del peso, sino **el lugar que ocupa cada fibra** dentro de su método.

---

## 3. Algoritmo de normalización (por método)

Para el vector de pesos `w` de un método:

1. Las fibras con `w = 0` se quedan en **0**.
2. Las fibras con `w > 0` se ordenan de menor a mayor.
3. A cada una se le asigna `lugar / n`, donde `n` es el número de fibras con peso > 0. La de menor peso recibe `1/n` y la de mayor peso recibe `1`.
4. **Empates:** usar el rango promedio (`scipy.stats.rankdata(method="average")`).
5. **SIFT normal** (0/1): se usa directamente, sin normalizar.

```python
import numpy as np
from scipy.stats import rankdata

def a_percentil(w):
    w = np.asarray(w, dtype=float)
    p = np.zeros_like(w)
    pos = w > 0
    if pos.any():
        p[pos] = rankdata(w[pos], method="average") / pos.sum()
    return p
```

---

## 4. Ejemplo para verificar (test unitario obligatorio)

Pesos originales:

| Fibra | COMMIT | LIFE | SIFT2 |
|---|---|---|---|
| 1 | 0.002 | 15 | 0.8 |
| 2 | 0.008 | 40 | 3.5 |
| 3 | 0 | 5 | 1.2 |
| 4 | 0.005 | 0 | 0 |
| 5 | 0.010 | 25 | 2.0 |

Orden de las fibras con peso > 0 (en cada método hay 4, así que los lugares valen 0.25, 0.50, 0.75 y 1):

| Lugar | COMMIT | LIFE | SIFT2 |
|---|---|---|---|
| 0.25 | 0.002 | 5 | 0.8 |
| 0.50 | 0.005 | 15 | 1.2 |
| 0.75 | 0.008 | 25 | 2.0 |
| 1.00 | 0.010 | 40 | 3.5 |

Resultado normalizado y promedio:

| Fibra | COMMIT | LIFE | SIFT2 | Promedio |
|---|---|---|---|---|
| 1 | 0.25 | 0.50 | 0.25 | 0.33 |
| 2 | 0.75 | 1.00 | 1.00 | 0.92 |
| 3 | 0 | 0.25 | 0.50 | 0.25 |
| 4 | 0.50 | 0 | 0 | 0.17 |
| 5 | 1.00 | 0.75 | 0.75 | 0.83 |

Con umbral 0.5 se conservan las **fibras 2 y 5**.

Implementar esto como test (`test_normalizacion.py`) y comprobar que los valores coinciden (tolerancia 0.01).

---

## 5. Combinación

```python
score = (p_commit + p_life + p_sift2) / 3
conservar = score >= umbral
```

Guardar el tractograma combinado (`combinado_u{umbral}.trk`) solo con las fibras conservadas.

Implementar también, como alternativa de comparación, el **voto mayoritario**: conservar las fibras con peso > 0 en al menos 2 de los 3 métodos.

---

## 6. Elegir el umbral

El umbral no se elige a ojo:

1. Probar umbrales de 0.1 a 0.9, en pasos de 0.05.
2. Para cada umbral, generar el tractograma combinado y evaluarlo contra el ground truth (sección 7).
3. Elegir el umbral con el **Dice promedio más alto**.
4. Graficar **cobertura vs. % de fibras falsas** para todos los umbrales (`curva_umbral.png`), marcando el umbral elegido.

---

## 7. Evaluación contra el ground truth

Evaluar **COMMIT, SIFT2, LIFE, combinado (umbral óptimo) y voto mayoritario** con las mismas métricas. Partir del script `comparar_metodos.py`, que ya hace la segmentación por MDF, Dice y MDF.

Para cada método:

1. Remuestrear las fibras a 20 puntos.
2. Asignar cada fibra al conducto del ground truth más cercano por MDF mínimo, si está a menos de 5 mm. Si no, contarla como **fibra falsa**.
3. Por cada conducto, convertir las fibras en máscara de vóxeles (`density_map > 0`) y calcular:

| Métrica | Fórmula | Mejor si es |
|---|---|---|
| Conductos detectados | conductos con ≥ 1 fibra asignada | Alto |
| % fibras falsas | fibras sin conducto / total | Bajo |
| Cobertura | VP / (VP + FN) | Alto |
| Desborde | FP / (VP + FN) | Bajo |
| Dice | 2·VP / (2·VP + FP + FN) | Alto |
| MDF simétrico (mm) | promedio del MDF mínimo A→B y B→A | Bajo |

(VP, FP y FN se cuentan en vóxeles, comparando contra la máscara del conducto verdadero.)

4. Ranking final: ordenar los métodos en Dice, cobertura, desborde, MDF y % de fibras falsas (1 = mejor), y promediar los lugares. El menor promedio gana.

---

## 8. Salidas esperadas

- `resultados_por_conducto.csv`: método × conducto con todas las métricas.
- `resumen_metodos.csv`: promedios por método y ranking final.
- `curva_umbral.png`: curva de selección del umbral.
- `combinado_u{umbral}.trk` y `voto_mayoritario.trk`.
- Mensaje final en consola con el método ganador.

---

## 9. Notas para la implementación

- Librerías: `dipy`, `nibabel`, `numpy`, `scipy`, `pandas`, `matplotlib`.
- Recibir rutas por argumentos (`argparse`): tractograma, pesos de cada método, carpeta del ground truth e imagen NIfTI de referencia.
- Cargar los tractogramas con `load_tractogram(..., bbox_valid_check=False)` y pasarlos a RASMM antes de calcular distancias o máscaras.
- Calcular el MDF por bloques y submuestrear el ground truth si es muy grande, para no agotar la memoria.
- Fijar la semilla aleatoria para que los resultados sean reproducibles.
- Antes de usar datos reales, correr el test de la sección 4.

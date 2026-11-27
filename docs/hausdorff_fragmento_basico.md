# Hausdorff con poda espacial: fragmento básico

Versión simplificada del núcleo de `scripts/hausdorff_bloque.py` (líneas 73-108), para explicar la lógica.
No es ejecutable por sí sola: `remuestrea` y `GT` vienen del script completo.

```python
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist

EPS = 10  # mm: radio de la poda

# --- Preparación (una sola vez) ---
# GP: todos los puntos del GT concatenados; GO: dónde empieza cada hilo del GT
GP, GO = remuestrea(GT, paso=2)
gt_de_punto = np.repeat(np.arange(len(GO) - 1), np.diff(GO))  # punto -> hilo del GT al que pertenece
arbol = cKDTree(GP)                                            # árbol KD con ~10 millones de puntos

# --- Para cada hilo y del tractograma ---
def hausdorff_min(y):
    # 1) Poda: hilos del GT que pasan cerca del inicio, del medio y del final de y
    tres = y[[0, len(y) // 2, -1]]
    cand = None
    for vecinos in arbol.query_ball_point(tres, EPS):   # puntos del GT a < EPS de cada posición
        ids = np.unique(gt_de_punto[vecinos])            # ...convertidos a hilos del GT
        cand = ids if cand is None else np.intersect1d(cand, ids)
        if len(cand) == 0:
            return np.nan                                # nadie cerca: "más de 10 mm"

    # 2) Hausdorff exacto solo contra los candidatos (decenas, no 189 985)
    mejor = np.inf
    for j in cand:
        D = cdist(y, GP[GO[j]:GO[j + 1]])   # distancias entre todos los puntos de y y de g_j
        a = D.min(axis=1).max()             # el punto de y más alejado de g_j
        b = D.min(axis=0).max()             # el punto de g_j más alejado de y
        mejor = min(mejor, max(a, b))       # d_H(y, g_j) = max(a, b)
    return mejor if mejor <= EPS else np.nan

# Etiqueta: verdadero si hausdorff_min(y) < 5
```

## Lógica

1. **Preparar una sola vez:** todos los puntos del GT van a un árbol KD, junto con un arreglo que dice a qué hilo
   pertenece cada punto.
2. **Podar:** si `d_H(y, g) < 10 mm`, cada punto de `y` está a menos de 10 mm de `g`; en particular su inicio, su
   medio y su final. Se hacen tres consultas al árbol y solo sobreviven los hilos del GT que aparecen en las tres.
   Si no sobrevive ninguno, la respuesta es "más de 10 mm".
3. **Medir:** Hausdorff exacto solo contra los sobrevivientes; se toma el menor. La etiqueta se obtiene después,
   comparando esa distancia con 5 mm.

Costo: ≈ 22 s por hilo con fuerza bruta contra ≈ 0.12 s con poda. Validado en 40 hilos al azar con
`scripts/validar_hausdorff_rapido.py` (diferencia máxima 0.0 mm).

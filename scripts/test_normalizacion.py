"""Test obligatorio de la normalización (docs/equipos/Normalizacion Ricardo.md, sección 4).

Uso (desde la raíz del proyecto):  python scripts/test_normalizacion.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from normalizacion_ricardo import a_percentil, combinar  # noqa: E402

commit = [0.002, 0.008, 0, 0.005, 0.010]
life = [15, 40, 5, 0, 25]
sift2 = [0.8, 3.5, 1.2, 0, 2.0]

esperado = {
    "COMMIT": [0.25, 0.75, 0, 0.50, 1.00],
    "LIFE": [0.50, 1.00, 0.25, 0, 0.75],
    "SIFT2": [0.25, 1.00, 0.50, 0, 0.75],
}
for nombre, w in [("COMMIT", commit), ("LIFE", life), ("SIFT2", sift2)]:
    assert np.allclose(a_percentil(w), esperado[nombre], atol=0.01), (nombre, a_percentil(w))

score, voto = combinar({"COMMIT": commit, "LIFE": life, "SIFT2": sift2})
assert np.allclose(score, [0.33, 0.92, 0.25, 0.17, 0.83], atol=0.01), score
assert list(np.flatnonzero(score >= 0.5) + 1) == [2, 5]
assert list(np.flatnonzero(voto) + 1) == [1, 2, 3, 5]          # > 0 en al menos 2 de 3
assert np.allclose(a_percentil([0, 2, 2, 5]), [0, 0.5, 0.5, 1.0])  # empates: rango promedio

# percentil por rango de longitud: cada hilo solo compite con los de su rango
from normalizacion_ricardo import a_percentil_por_longitud  # noqa: E402
w = [1, 2, 3, 0, 10, 20, 30, 40]
L = [10, 10, 10, 10, 100, 100, 100, 100]                   # 2 rangos: cortos y largos
assert np.allclose(a_percentil_por_longitud(w, L, 2), [1/3, 2/3, 1, 0, 0.25, 0.5, 0.75, 1.0])
# con un solo rango es igual al percentil global
assert np.allclose(a_percentil_por_longitud(commit, [1, 2, 3, 4, 5], 1), a_percentil(commit))

print("OK: percentiles", {k: v for k, v in esperado.items()})
print("OK: percentil por rango de longitud")
print("OK: promedio", np.round(score, 2).tolist(), "-> con umbral 0.5 se conservan las fibras 2 y 5")

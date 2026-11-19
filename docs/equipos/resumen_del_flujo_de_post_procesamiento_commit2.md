# Resumen del Flujo de Post-procesamiento de Tractografía con COMMIT2

Este documento recopila los pasos realizados, las configuraciones óptimas seleccionadas, los scripts utilizados y las rutas de los archivos resultantes del análisis de conectividad cerebral mediante **COMMIT2**.

---

## 1. Selección del Modelo y Parámetros Óptimos
Tras evaluar distintos valores de regularización ($\lambda$) en el modelo COMMIT2, se determinó la siguiente configuración óptima que equilibra la escasez del haz (eliminación de falsos positivos) y la densidad interna:

* **Archivo de pesos seleccionado:** `commit2_lam1e-2_weights.txt` ($\lambda = 1 \times 10^{-2}$)
* **Imagen anatómica de referencia:** `ISMRM_2023_b3000.nii.gz`
* **Tractograma original:** `tracks.tck` (100,000 streamlines iniciales)
* **Streamlines activas resultantes:** **62,779** streamlines con peso positivo ($w > 0$).

---

## 2. Filtrado del Tractograma
Se filtró el tractograma original utilizando los índices de aquellas fibras cuyos pesos optimizados en `commit2_lam1e-2_weights.txt` fueran mayores a cero, descartando así los falsos positivos biológicos.

* **Archivo generado:** `tacks_100k_commit2_filtrado.tck` (~25 MB).

---

## 3. Generación de la Matriz de Conectividad Ponderada
Para construir el conectoma estructural ponderado por los pesos de COMMIT2, se cruzaron los valores de `commit2_lam1e-2_weights.txt` con las asignaciones de nodos (`assignments.txt`, estructurado en 2 columnas `[nodo_origen, nodo_destino]` por cada línea correspondiente al índice de cada streamline).

### Script utilizado (`generar_matriz_pesos.py`)
```python
import numpy as np
import os

weights_file = '../commit2_lam1e-2_weights.txt'
assignments_file = '../assignments.txt'
output_matrix_csv = 'matriz_conectividad_commit2_lam1e-2.csv'

# Cargar pesos y asignaciones
weights = np.loadtxt(weights_file)
assignments = np.loadtxt(assignments_file, dtype=int)

# Determinar dimensiones de la matriz (85 regiones)
max_node = np.max(assignments)
n_nodes = max_node + 1
connectome = np.zeros((n_nodes, n_nodes))

# Sumar los pesos de las fibras activas en la matriz simétrica
for s_idx, row in enumerate(assignments):
    n1, n2 = row[0], row[1]
    w = weights[s_idx]
    
    if w > 0:
        connectome[n1, n2] += w
        if n1 != n2:
            connectome[n2, n1] += w

# Exportar matriz a CSV
np.savetxt(output_matrix_csv, connectome, delimiter=',')
```

* **Archivo generado:** `matriz_conectividad_commit2_lam1e-2.csv` (Matriz simétrica de $85 \times 85$).

---

## 4. Ubicación de los Archivos Finales

Los archivos procesados se encuentran disponibles tanto en la carpeta de trabajo del proyecto como copiados en tu directorio personal (*Home*) para fácil acceso y visualización:

| Archivo | Descripción | Ubicación Original | Copia en Carpeta Personal |
| :--- | :--- | :--- | :--- |
| **`tacks_100k_commit2_filtrado.tck`** | Tractograma filtrado (62,779 fibras activas) | `~/desafio/datos/dataset/DWIs/commit2/` | `/home/saraih/` |
| **`matriz_conectividad_commit2_lam1e-2.csv`** | Matriz de conectividad ponderada ($85 \times 85$) | `~/desafio/datos/dataset/DWIs/commit2/` | `/home/saraih/` |

---

## 5. Próximos Pasos Recomendados
* **Visualización del tractograma:** Puedes abrir `tacks_100k_commit2_filtrado.tck` superpuesto sobre `ISMRM_2023_b3000.nii.gz` utilizando **MRtrix3 (`mrview`)** o **TrackVis**.
* **Análisis de grafos:** Puedes cargar `matriz_conectividad_commit2_lam1e-2.csv` en Python (`numpy`/`networkx`/`bctpy`) o MATLAB para calcular métricas topológicas (eficiencia global, modularidad, fuerza de nodo, etc.).
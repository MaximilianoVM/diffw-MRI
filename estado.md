# Estado del proyecto (2026-11-13)

## Entregable: matriz de peso COMMIT 84 × 84

**Hecho y reproducido por nosotros.** `out/matriz_peso_commit_84x84_corregida.xlsx` (84 × 84, simétrica, diagonal 0, encabezados R1–R84), generada el 2026-11-10 con el `tracks_100k.tck` compartido. `out/` no se sube a Git: se comparte por Drive.

## Paso a paso

| Paso | Script | Estado |
|---|---|---|
| 1. Gradientes con `y` invertido, máscara, respuesta, FOD | `01_preprocess.sh` | Corrido |
| 2. Tractograma 100k, longitudes, SIFT2 | `02_tractography.sh` | Corrido con el `.tck` compartido. `tckstats`: media 92.13, mediana 95.21 |
| 3. COMMIT | `03_commit.sh` | Corrido en macOS (1 min 15 s). `out/commit/pesos_commit.txt` |
| 4. Matrices 84 × 84, Excel, evaluación | `04_matrices.sh` | Corrido. `out/matriz_*.xlsx`, `out/evaluacion_commit.txt` |

## Resultados (de `out/evaluacion_commit.txt`)

- COMMIT pone en 0 a 44 780 hilos (45 %).
- **Por conexión** funciona: 1203 conexiones > 0, recupera 446 de 529 del GT, 64 % del peso en conexiones del GT, **AUC 0.829** (× longitud: 79 %, AUC 0.846).
- **Por hilo** no, con la etiqueta por extremos: **AUC 0.458** (× longitud 0.500; la longitud sola da 0.635). Descartar los de peso 0 elimina malos al ritmo del azar (44 % vs 45 %).
- Ningún método por sí solo limpia el tractograma: quedan ≈ 750 conexiones que no existen en el GT.

## Pendiente del proyecto

- LiFE: sin empezar (otro equipo).
- Etiqueta por haz contra el GT, común a los tres métodos: sin hacer. La de extremos es débil (26 713 hilos no terminan en ninguna región).
- Regla de decisión que combine COMMIT, SIFT2 y LiFE: sin empezar.
- Decidir si se entrega COMMIT a secas o × longitud.

## Entorno

- WSL/Linux: `conda activate dwmri` (`environment.yml`).
- macOS: `source .venv/bin/activate` (`requirements.txt`) + MRtrix3 3.0.8.
- COMMIT falla con rutas con acentos o espacios; `correr_commit.py` crea `~/Proyecto_2_cerebro` si hace falta.

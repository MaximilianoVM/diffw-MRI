# Proyecto Cerebro: ¿cómo saber si un streamline es bueno?

Desafío DW-MRI (Laboratorio de Resolución de Problemas I, CIMAT). Sobre el fantoma ISMRM 2015 se genera un tractograma de 100 000 hilos (`data/tracks_100k.tck`) y se pesa cada hilo con **SIFT2, LiFE y COMMIT**. Objetivo (junta del 17 nov, `docs/junta_17nov.md`): normalizar esos tres vectores de pesos, filtrar los hilos, y ver si un modelo entrenado con la etiqueta del ground truth filtra mejor que cada método por separado.

**¿Vienes a integrarte (persona o Claude)? Lee primero `ACTUALIZACION.md`.**

```
README.md           este archivo
ACTUALIZACION.md    estado, cambios y siguientes pasos (el único seguimiento en la raíz)
pipeline.md         los pasos, comando por comando
environment.yml     entorno conda (WSL/Linux): MRtrix + COMMIT
requirements.txt    versiones exactas de Python (venv, macOS)
data/               entrada y tracks_100k.tck (no se sube; ver data/README.md)
out/                todo lo generado; casi nada se sube (sí: vectores de pesos, hausdorff.csv, out/modelos/tabla_hilos.csv)
Proyecto2_Laboratorio/  reporte en LaTeX (main.tex); el PDF no se sube
scripts/            01_preprocess  02_tractography  03_commit  04_matrices  05_life  06_commit2  07_normalizacion  08_hausdorff  09_filtrar_pesos  10_evaluar  11_modelo  modelo_bosque_ajustado  modelo_boosting_ajustado  crear_tabla_modelos
                    + los .py de apoyo (correr_*, comparar_*, evaluar_pesos, normalizacion_ricardo...)
docs/
  junta_17nov.md        objetivo según el investigador
  diagramas.md          flujo de datos y fases del proyecto
  filtrado_pesos.md     paso 9: normalizar (entre el máximo) y filtrar con ε
  evaluacion_filtrado.md  paso 10: precisión/recall/AUC de cada método vs Hausdorff
  resumen_para_la_junta.md  estado completo del proyecto, fácil de leer (para la junta)
  para_continuar_modelos.md  guía para quien continúa con los modelos (incluye la tabla de datos)
  siguiente_mac_normalizacion.md  tareas para la Mac (3.5: COMMIT2 con otros λ; 3.6: haces con los modelos del grupo; 3.7: actualizar el reporte LaTeX)
  conclusiones.md       qué sabemos hasta ahora
  explicacion_commit.md qué hace COMMIT y cómo se lee la matriz 84 x 84
  guia_equipo.md        reglas de trabajo y contrato de pesos
  metodologia_comparacion.md  cómo se calculan las métricas
  hausdorff_eficiencia.md   por qué no tardamos días (para el doctor)
  hausdorff_instrucciones.md  reparto del cálculo de la etiqueta entre computadoras
  etiqueta_hausdorff_vs_mdf.md  por qué Hausdorff y por qué mostrar también MDF
  resultados/           extras.md (resumen), matrices.md, commit2.md, normalizacion.md, modelo_y_normalizacion_hausdorff.md,
                        tractograma_modelo_vs_gt.md, modelo_bosque_ajustado.md y modelo_boosting_ajustado.md (grupo de modelos)
  equipos/              lo que mandaron SIFT2, LiFE, COMMIT2 y el pipeline anterior
```

Entorno, una de dos:

```bash
conda env create -f environment.yml && conda activate dwmri                                  # WSL/Linux
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && source .venv/bin/activate   # macOS (+ MRtrix3 3.0.8)
```

Para correr todo:

```bash
bash scripts/01_preprocess.sh && bash scripts/02_tractography.sh && bash scripts/03_commit.sh && bash scripts/04_matrices.sh
```

Resultado: `out/matriz_peso_commit_84x84_corregida.xlsx`. COMMIT falla con rutas con acentos o espacios; `correr_commit.py` lo resuelve creando `~/Proyecto_2_cerebro` (ver `pipeline.md`).

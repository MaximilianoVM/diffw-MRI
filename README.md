# Proyecto Cerebro: ¿cómo saber si un streamline es bueno?

Desafío DW-MRI (Laboratorio de Resolución de Problemas I, CIMAT). Sobre el fantoma ISMRM 2015 se genera un tractograma y se pesa cada hilo con COMMIT, SIFT2 y LiFE para decidir cuáles conservar. Esta parte produce la matriz de conectividad 84 × 84 ponderada por COMMIT.

```
README.md         este archivo
estado.md         qué está hecho y qué falta
pipeline.md       los pasos, comando por comando
environment.yml   entorno conda (WSL/Linux): MRtrix + COMMIT
requirements.txt  versiones exactas de Python (venv, macOS)
data/             entrada y tracks_100k.tck (no se sube; ver data/README.md)
out/              todo lo generado, plano (COMMIT en out/commit/); no se sube
integracion_metodos.md  COMMIT, SIFT2 y LiFE sobre el mismo tractograma: diferencias con los equipos y comparación
guia_equipo.md    reglas para todos los equipos y sus Claudes (contrato de pesos)
explicacion_commit.md  qué hace COMMIT y cómo se lee la matriz
aclaraciones_equipo.md  qué hay que aclarar entre equipos
consideraciones_normalizacion_ricardo.md  ajustes a la idea de normalización por percentil
normalizacion_resultados.md  normalización Ricardo con COMMIT + SIFT2 (bash scripts/07_normalizacion.sh)
commit2_resultados.md  COMMIT2: arreglos al script, barrido de λ y comparación (bash scripts/barrido_lambda_commit2.sh)
normalizacion_por_longitud.md  percentil por rango de longitud (--por-longitud 10): explicación y resultados
scripts/          01_preprocess.sh  02_tractography.sh  03_commit.sh  04_matrices.sh  05_life.sh  06_commit2.sh
                  correr_commit2.py
                  correr_commit.py  correr_life.py  exportar_matriz84.py  evaluar_pesos.py
                  comparar_matrices.py  comparar_pesos.py
team_commit/      pipeline anterior del otro equipo (referencia)
extras/           guías, versiones anteriores y exploración (local, no se sube)
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

# Filtrado de streamlines en DW-MRI (desafío ISMRM)

Generamos un tractograma del fantoma ISMRM, calculamos pesos por streamline con
**SIFT2, COMMIT y LiFE** y decidimos cuáles conservar.

```
README.md        este archivo
environment.yml  entorno conda (MRtrix + COMMIT)
pipeline.md      los pasos explicados comando por comando
data/            entrada (no se toca)
out/             todo lo que generamos
scripts/         01_preprocess.sh  02_tractography.sh  03_commit.sh  04_matrices.sh
                 correr_commit.py  exportar_matriz84.py  evaluar_pesos.py
team_commit/     pipeline anterior del otro equipo (referencia)
equipo_chat/     intercambio con el otro equipo (local, no se sube)
```

Entorno: `conda env create -f environment.yml && conda activate dwmri`.
Los datos no se suben a Git: ver `data/README.md`.
Para correr todo: `bash scripts/01_preprocess.sh`, luego `02`, `03` y `04`.

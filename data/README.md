# data/ (no se sube a Git)

Aquí van los datos de entrada. Se descargan de la carpeta común del equipo:

```
ISMRM_2023_b3000.nii.gz   DWI
ISMRM_2023_b3000.bval
ISMRM_2023_b3000.bvec
Parcels_free.nii          parcelación (84 regiones)
T1.nii.gz, T1_dwi.nii.gz  anatómicas
GT/                       ground truth: 21 haces .tck + all_tracks.tck
```

Después de bajarlos, desde la raíz del proyecto: `mkdir -p out` y sigue `pipeline.md`.

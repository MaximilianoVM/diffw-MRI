# Diagramas del proyecto

Se ven como dibujo en GitHub y en VS Code (con la extensión de Mermaid). En la terminal se leen como texto.

## 1. Pasos (scripts) y qué hace cada uno

| Script | Qué hace | Parte del objetivo de la junta |
|---|---|---|
| `01_preprocess.sh` | gradientes con `y` invertido, máscara, respuesta y FOD | base |
| `02_tractography.sh` | genera (o usa) `data/tracks_100k.tck`; longitudes; **pesos SIFT2** | paso A |
| `03_commit.sh` | **pesos COMMIT** | paso A |
| `05_life.sh` | **pesos LiFE** (los entregó el equipo de LiFE) | paso A |
| `04_matrices.sh` | matrices 84 × 84 y su evaluación contra el GT | extra |
| `06_commit2.sh` | COMMIT2 (variante) y su matriz | extra |
| `07_normalizacion.sh` | normalización de Ricardo y combinación de métodos | extra / paso B parcial |
| `08_hausdorff.sh` | etiqueta por Hausdorff, por bloques | paso C |
| `09_...` (por hacer) | filtrado individual: normalizar y barrer ε por método | paso B |
| `10_...` (por hacer) | modelo `(x_S, x_L, x_C) → etiqueta` | paso D |

La numeración sigue el **orden en que se fueron agregando**, no el orden del objetivo nuevo. `pipeline.md` documenta los pasos 1, 2, 3, 4, 6 y 8 (faltan por escribir las secciones de los pasos 5 y 7).

## 2. Flujo de datos

```mermaid
flowchart TD
    subgraph ENTRADA["data/ (entrada, no se modifica)"]
        DWI["ISMRM_2023_b3000<br/>.nii.gz .bval .bvec"]
        PARC["Parcels_free.nii<br/>84 regiones"]
        GT["GT/<br/>21 haces + all_tracks.tck<br/>189 985 hilos"]
    end

    DWI -->|"01_preprocess<br/>(y invertido)"| MIF["out/dwi.mif<br/>mask.mif · fod.mif"]
    MIF -->|"tckgen<br/>(02_tractography)"| TCK[["data/tracks_100k.tck<br/>100 000 hilos<br/>md5 66ba3e6e..."]]

    TCK --> SIFT["SIFT2<br/>tcksift2 + FOD"]
    TCK --> COMMIT["COMMIT<br/>03_commit + dwi.mif"]
    TCK --> LIFE["LiFE (DIPY)<br/>05_life + dwi"]
    MIF --> SIFT
    MIF --> COMMIT
    DWI --> LIFE

    SIFT --> XS["x_S<br/>out/pesos_sift2.txt<br/>100 000 pesos"]
    COMMIT --> XC["x_C<br/>out/commit/pesos_commit.txt<br/>100 000 pesos"]
    LIFE --> XL["x_L<br/>out/life/pesos_life.txt<br/>100 000 pesos"]

    XS --> NORM["Paso B: normalizar a (0,1)<br/>y filtrar con ε, método por método"]
    XL --> NORM
    XC --> NORM
    NORM --> FILT["3 tractogramas filtrados"]

    TCK --> HAUS["Paso C: 08_hausdorff<br/>(7 computadoras)"]
    GT --> HAUS
    HAUS --> LAB["out/hausdorff/hausdorff.csv<br/>etiqueta por hilo<br/>hd_min &lt; ε ⇒ corresponde al GT"]

    FILT -->|"comparar"| EVAL["Evaluación contra el GT<br/>(% falsas, cobertura, Dice, ...)"]
    LAB --> EVAL
    GT --> EVAL

    XS --> MOD["Paso D: modelo<br/>x_S·α + x_L·β + x_C·γ → 0/1<br/>(entrenamiento y prueba separados)"]
    XL --> MOD
    XC --> MOD
    LAB -->|"etiqueta"| MOD
    MOD --> FILT2["tractograma filtrado<br/>por el modelo"]
    FILT2 --> EVAL

    TCK -.->|"04_matrices"| MAT["matrices 84×84<br/>(extra)"]
    PARC -.-> MAT
    XS -.-> MAT
    XC -.-> MAT
    XL -.-> MAT
```

Cuadro `[[ ]]` = el archivo central que comparten todos. Líneas punteadas = el trabajo extra (matrices).

## 3. Fases del proyecto

```mermaid
flowchart LR
    F0["Fase 0<br/>Preparar datos<br/>y entorno<br/>(HECHA)"]
    F1["Fase 1<br/>Un tractograma<br/>y tres vectores de pesos<br/>SIFT2 · COMMIT · LiFE<br/>(HECHA)"]
    F2["Fase 2 · Paso B<br/>Normalizar a (0,1)<br/>y filtrar con ε<br/>por método<br/>(POR HACER)"]
    F3["Fase 3 · Paso C<br/>Etiqueta por Hausdorff<br/>contra el GT<br/>(LISTA PARA CORRER)"]
    F4["Fase 4 · Paso D<br/>Modelo entrenado<br/>con la etiqueta<br/>(POR HACER)"]
    F5["Fase 5<br/>Comparar todo<br/>con el GT<br/>e informe"]

    F0 --> F1 --> F2 --> F5
    F1 --> F3 --> F4 --> F5
    F2 -.->|"se evalúa mejor con la etiqueta"| F3

    X["Extras ya hechos<br/>matrices 84×84 · COMMIT2 y λ<br/>percentil por longitud · eje y"]
    F1 -.-> X
    X -.->|"contexto"| F5
```

| Fase | Estado | Dónde |
|---|---|---|
| 0. Datos y entorno | hecha | `environment.yml`, `data/README.md` |
| 1. Tractograma y tres vectores de pesos | hecha | pasos 1–3 y 5; archivos en `docs/interno/ACTUALIZACION.md` sección 4 |
| 2. Normalizar y filtrar con ε (paso B) | por hacer (el siguiente script) | `docs/interno/ACTUALIZACION.md` sección 5 |
| 3. Etiqueta por Hausdorff (paso C) | script listo y probado; falta correrlo en 7 computadoras | `docs/hausdorff_instrucciones.md` |
| 4. Modelo entrenado (paso D) | por hacer | `docs/junta_17nov.md` |
| 5. Comparación con el GT e informe | por hacer | — |
| Extras | hechos | `docs/resultados/extras.md` |

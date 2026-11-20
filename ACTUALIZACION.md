# Actualización para el Claude de la Mac (2026-11-18)

**Léelo completo antes de tocar nada.** Es el único `.md` de seguimiento en la raíz; cuando termines algo, actualiza **este archivo** (tabla de la sección 3) y no crees otros en la raíz.

## 1. Qué cambió

1. **Objetivo simplificado** tras la junta con el investigador (17 nov): no es una matriz 84 × 84, sino **pesar los 100 000 hilos con SIFT2, LiFE y COMMIT, normalizarlos, filtrar, y ver si un modelo entrenado con la etiqueta del GT filtra mejor**. Ver `docs/junta_17nov.md`.
2. **Reorganización de documentos.** La raíz queda con `README.md`, `pipeline.md` y este archivo. Todo lo demás está en `docs/`:

| Antes | Ahora |
|---|---|
| `estado.md`, `aclaraciones_equipo.md` | este archivo / `docs/explicacion_commit.md` (la parte de la diagonal) |
| `integracion_metodos.md` | `docs/resultados/matrices.md` |
| `commit2_resultados.md` | `docs/resultados/commit2.md` |
| `normalizacion_resultados.md`, `normalizacion_por_longitud.md`, `consideraciones_normalizacion_ricardo.md` | `docs/resultados/normalizacion.md` (una sola, con partes A, B y C) |
| `explicacion_commit.md`, `guia_equipo.md`, `metodologia_comparacion.md`, `conclusiones.md` | `docs/` (mismo nombre) |
| `instrucciones_life.md`, `team_commit/`, y los archivos de los equipos que estaban en `docs/` | `docs/equipos/` |

3. Se actualizaron las referencias en `README.md`, `pipeline.md`, `docs/*` y los comentarios de `scripts/`. Si un `.md` tuyo apunta a un nombre viejo, corrígelo.
4. **Nada de código cambió**, salvo la ruta de `docs/equipos/life_antiguo/conn_life_full.csv` en `scripts/comparar_matrices.py`.

## 2. Reglas

- Resultados nuevos van a `docs/resultados/` (un archivo por tema); no más `.md` sueltos en la raíz.
- Comandos reproducibles van a `pipeline.md`. Reglas de trabajo en `docs/guia_equipo.md`.
- Cualquiera puede actualizar cualquier archivo del proyecto (documentos, estado, scripts), aunque lo haya escrito otra persona, para que todo quede al día; se avisa en el mensaje del commit.
- Los pesos de cada método siguen el contrato de `docs/guia_equipo.md` (100 000 números ≥ 0 en el orden de `data/tracks_100k.tck`).
- `data/` y `out/` no se suben a Git (salvo `out/equipos/life_100k/`, que ya estaba subido). No hagas commit ni push sin que el usuario lo pida.

## 3. Estado frente al objetivo nuevo

| Paso (de `docs/junta_17nov.md`) | Estado |
|---|---|
| A. Vector de 100 000 pesos por método | **Hecho** para SIFT2, COMMIT, LiFE (y COMMIT2 como extra). Contrato cumplido. |
| B. Normalizar a (0, 1), filtrar con ε, comparar cada método con el GT | **Parcial.** Hay percentiles y cortes, pero no el esquema simple de la junta (ε = 0.01 sobre pesos normalizados) |
| C. Etiqueta 0/1 por hilo con **Hausdorff** | **Hecho** (2026-11-19). Los 7 bloques están en `distancias_hausdorff/` y juntos en `out/hausdorff/hausdorff.csv` (subido a Git). **ε = 5 mm decidido:** `etiqueta_5mm` = 1 si `hd_min` < 5 mm → 33 349 verdaderos (33.3 %). La etiqueta MDF < 5 mm (`out/normalizacion/etiqueta_mdf.csv`, 54.8 %) queda solo para comparar |
| D. Modelo `(x_S, x_L, x_C) → etiqueta` y comparar su tractograma | **Hecho** (2026-11-19). Modelo: regresión logística 50/50 (`scripts/11_modelo.sh`, AUC en prueba 0.62 con los 3 métodos, 0.70 con los 4 + longitud). Tractograma contra el GT con el mismo número de hilos (`normalizacion_ricardo.py --mismos-n`): el mínimo LiFE+COMMIT2 deja menos falsos (46.8 % con 25 000) pero pierde BPS, Fornix e ICP porque COMMIT2 les pone peso 0; COMMIT y SIFT2 cubren 20 de 21 haces con 75–78 % de falsos. Ver `docs/resultados/tractograma_modelo_vs_gt.md` |

## 4. Dónde están los vectores de pesos (paso A)

Un archivo por método, 100 000 números ≥ 0, en el orden de `data/tracks_100k.tck`:

| Método | Archivo | Dónde está |
|---|---|---|
| SIFT2 | `out/pesos_sift2.txt` | laptop de desarrollo y Mac (una sola línea con cabecera `#`) |
| COMMIT | `out/commit/pesos_commit.txt` | **subido a Git** (commit `c22f920`, 2026-11-19) |
| LiFE | `out/life/pesos_life.txt` (= `out/equipos/life_100k/life_weights.txt`, subido a Git) | LiFE sí está en el repo |
| COMMIT2 (extra) | `out/commit2/pesos_commit2.txt` | **subido a Git** (commit `c22f920`, λ = 1e-2) |

Cargar: `np.loadtxt(archivo, comments="#").ravel()`. COMMIT, COMMIT2 y LiFE llegan con `git pull`; solo SIFT2 hay que pasarlo por Drive si falta (el `.gitignore` ya lo permite, pero todavía no está subido).

## 5. Siguientes pasos

**Paso B (el primero): filtrar cada método por separado.** Cada vector se normaliza a (0, 1) y se descartan los hilos con peso < ε, **método por método** (páginas 2 y 3 de la junta). Cada método da así su tractograma filtrado, que se compara con el GT. Falta implementarlo (hoy solo hay filtros por peso > 0 y combinaciones con percentiles, sin barrido de ε). Hace falta decidir cómo normalizar: min-max (lectura literal de las notas) o percentil (el de Ricardo). Propuesta (el usuario decide):
- Hay **dos ε distintos**: el del peso normalizado (en (0, 1)) y el de Hausdorff (en mm).
- **ε del peso:** con percentiles, ε = 0.01 solo descarta el 1 % más bajo; con min-max casi no descarta nada en SIFT2. En vez de fijar un valor, **barrer ε** (por ejemplo 0.01 a 0.9) y reportar, para cada método, cuántos hilos quedan y cuántos corresponden al GT. Comparar métodos con el **mismo número de hilos conservados** para que sea justo.
- **ε de Hausdorff: 5 mm (decidido el 2026-11-19)** (≈ 2.5 vóxeles de 2 mm, y el mismo valor de la MDF para poder comparar). Columna `etiqueta_5mm` de `out/hausdorff/hausdorff.csv`. Las distancias siguen guardadas por si se quiere mostrar el barrido: `hd_min` < 2, 3, 5, 7, 10 mm → 2.6 %, 13.0 %, 33.3 %, 46.0 %, 58.6 % de los hilos.

Evaluar contra el GT con `etiqueta_5mm` (Hausdorff); la etiqueta MDF ya no es la principal.

**Paso C (hecho el 2026-11-19): etiqueta por Hausdorff.** Resultado en `out/hausdorff/hausdorff.csv` (`hilo, hd_min, hd_dir_min, gt_hilo, etiqueta_5mm`). Cargar: `pd.read_csv("out/hausdorff/hausdorff.csv").etiqueta_5mm`. Se repartió entre 7 computadoras con `bash scripts/08_hausdorff.sh <bloque> 7`. Instrucciones: `docs/hausdorff_instrucciones.md`. Argumento para mostrar también MDF: `docs/etiqueta_hausdorff_vs_mdf.md`.

**Paso D: modelo.** `(x_S, x_L, x_C) → etiqueta`:
- Regresión logística como primera opción, y como comparación el **voto** (≥ 2 de 3 métodos) y el filtro simple por ε.
- Separar **entrenamiento y prueba** (p. ej. entrenar con una parte de los bloques de hilos y probar en otra, o validación cruzada) y reportar solo en la parte de prueba.
- Agregar la longitud del hilo como cuarta variable en una versión aparte, para ver cuánto aporta (sola da AUC 0.75 con la etiqueta MDF).

**Cuidados que ya conocemos** (detalle en `docs/conclusiones.md`): con la etiqueta MDF los pesos de COMMIT y SIFT2 ordenan *al revés* (AUC 0.42 y 0.35) y favorecen hilos cortos. Con Hausdorff puede cambiar: hay que comprobarlo antes de interpretar el modelo. Los extras (matrices 84 × 84, COMMIT2, etc.) están resumidos en `docs/resultados/extras.md`.

## 6. Dónde leer más

| Qué | Archivo |
|---|---|
| Mapa y entorno | `README.md` |
| Comandos paso a paso | `pipeline.md` |
| Notas de la junta | `docs/junta_17nov.md` |
| Hausdorff: reparto y comandos | `docs/hausdorff_instrucciones.md` |
| Hausdorff vs MDF | `docs/etiqueta_hausdorff_vs_mdf.md` |
| Resultados extra | `docs/resultados/extras.md` |
| Resultados y conclusiones hasta ahora | `docs/conclusiones.md` |
| Detalle por tema | `docs/resultados/` |
| Qué hace COMMIT y cómo se lee la matriz | `docs/explicacion_commit.md` |
| Reglas de trabajo y contrato de pesos | `docs/guia_equipo.md` |
| Cómo se calculan las métricas | `docs/metodologia_comparacion.md` |
| Lo que mandaron los otros equipos | `docs/equipos/` |

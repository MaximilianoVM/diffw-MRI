# Consideraciones para la normalización de Ricardo

Revisión del 2026-11-13 de `docs/Normalizacion Ricardo.md` contra los datos de este repo. **Conclusión: es factible.** Su ejemplo de la sección 4 da exactamente sus valores (0.33, 0.92, 0.25, 0.17, 0.83; se conservan las fibras 2 y 5). Lo que sigue son ajustes para que funcione con nuestros archivos.

## 1. Archivos de entrada (contrato del repo)

Todos los métodos pesan **el mismo tractograma**, `data/tracks_100k.tck` (100 000 hilos, `md5` `66ba3e6efe1fadf5b534d3947b2b138f`), y entregan un `.txt` con 100 000 pesos ≥ 0 en el orden del `.tck`.

| Método | Pesos | Estado |
|---|---|---|
| SIFT2 | `out/pesos_sift2.txt` | listo |
| COMMIT | `out/commit/pesos_commit.txt` | listo (corrido en la Mac) |
| COMMIT2 | `out/commit2/pesos_commit2.txt` | integrado (`scripts/06_commit2.sh`); falta el archivo de pesos |
| LiFE | `out/life/pesos_life.txt` | pendiente: su matriz actual es de otro tractograma |

Cargar con `np.loadtxt(f, comments="#").ravel()` (SIFT2 trae una cabecera `#`). Comprobar longitud 100 000 y orden, como pide Ricardo. `out/` y `data/` no se suben a Git; se comparten por Drive.

## 2. Ajustes que hay que decidir

1. **Un 0 no significa lo mismo en cada método.** COMMIT pone en 0 el 45 % de los hilos; SIFT2 no pone ninguno (0 de 100 000, pesos entre 0.19 y 3.7). Con el promedio de percentiles, SIFT2 nunca "elimina" un hilo y el umbral 0.5 pasa a decidirlo casi COMMIT. Opciones: (a) dejarlo así y decirlo; (b) para SIFT2 y LiFE tratar como "eliminado" el 45 % de menor peso (el mismo % que COMMIT); (c) usar solo el voto mayoritario con ese corte común.
2. **La longitud sesga los rangos.** Los pesos de COMMIT son por unidad de longitud y favorecen hilos cortos; SIFT2 tiene Spearman −0.41 con la longitud. Probar también COMMIT × longitud (`out/pesos_commit_x_long.txt`, ya lo genera `04_matrices.sh`).
3. **Elegir el umbral con el mismo GT con que se evalúa es optimista.** Declararlo en el informe, o elegir el umbral con la mitad de los haces y evaluar con la otra.
4. **Peso 0 = "eliminó"** es una hipótesis, no un hecho comprobado (decisión 3.5 de `aclaraciones_equipo.md`).

## 3. Lo que falta o no encaja

- Pide partir de `comparar_metodos.py` (segmentación por MDF, Dice): **no existe en el repo**. Hay que escribirlo o pedírselo a quien lo tenga.
- Habla de `.trk`; nosotros usamos `.tck` (`nibabel` lo lee; `load_tractogram` de DIPY también). Guardar la salida como `.tck` evita convertir.
- `dipy` ya está en `requirements.txt`; `matplotlib` no está en `environment.yml` (agregarlo con versión fija si se usa).
- El GT está en `data/GT/` (21 haces `.tck` y `all_tracks.tck`, ≈ 189 985 hilos). El MDF contra todo el GT hay que hacerlo por bloques.
- La etiqueta por haz (MDF < 5 mm al haz más cercano) es la misma que falta para evaluar hilo por hilo (decisión 3.4). Conviene hacerla una vez y que la usen todos.
- Las matrices 84 × 84 se comparan con la **diagonal en 0** (`np.fill_diagonal(M, 0)`); no aplica a esta normalización, que es por hilo.

## 4. Sobre `docs/Normalizacion.py`

No se usa para esto: normaliza matrices dividiendo entre el máximo, y en las matrices de LiFE ese máximo está en la diagonal (distorsiona RMSE y Frobenius). Es otro enfoque (matrices, no hilos).

## 5. Dónde dejar la implementación

Siguiendo `guia_equipo.md`: script en `scripts/` con el siguiente número libre (`07_...`), entrega `out/keep_<estrategia>.txt` (un 0 o 1 por hilo) y su sección en `pipeline.md` con comandos sueltos y "Se espera". Incluir el test del ejemplo (`test_normalizacion.py`).

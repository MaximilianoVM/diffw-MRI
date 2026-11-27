# Guía de trabajo del equipo

Objetivo: que SIFT2, COMMIT, LiFE, el etiquetado y la regla de decisión se puedan juntar sin retrabajo. Para eso todos trabajamos igual. **Lean esto completo antes de empezar.**

---

## 1. Reglas de trabajo

Antes de empezar, lean esta guía, `README.md` y `pipeline.md`.

1. Cualquiera puede modificar cualquier archivo del proyecto, aunque lo haya escrito otra persona, para que todo quede actualizado (documentos, estado, resultados, scripts); lo que se cambió se indica en el mensaje del commit.
2. No se cambian nombres de archivos de `out/` ni la estructura de carpetas.
3. Todo script va en `scripts/` y corre desde la raíz del proyecto con rutas relativas `data/` y `out/`.
4. Cada comando que se agregue a `pipeline.md` lleva una frase de explicación y el archivo que produce.
5. Antes de borrar, mover o sobrescribir cualquier archivo en `out/` o `data/`, se consulta con el equipo.
6. No se instalan paquetes fuera del entorno `dwmri`; si hace falta uno nuevo, se agrega a `environment.yml` con versión fija.
7. Los cálculos pesados (COMMIT, LiFE, tractografía) se coordinan antes de correrlos.
8. Se mantiene todo simple: menos archivos, menos carpetas, menos texto.

---

## 2. Estructura del repositorio (única, no se agregan carpetas)

```
README.md          qué es el proyecto y el mapa de carpetas
docs/interno/ACTUALIZACION.md   estado y cambios para quien se integra (se actualiza al terminar algo)
docs/              documentación: conclusiones, resultados/, equipos/, esta guía
pipeline.md        los pasos, comando por comando, explicados
environment.yml    entorno conda (MRtrix + Python)
data/              entrada, NO se modifica, NO se sube a Git
out/               todo lo generado, plano, NO se sube a Git
scripts/           01_... a NN_... y los .py de apoyo
```

`out/` es plano. Única subcarpeta permitida: `out/<metodo>/` para archivos intermedios pesados de un método (por ejemplo `out/commit/`).

---

## 3. Entorno

```bash
conda env create -f environment.yml
conda activate dwmri
mrconvert -version      # debe decir 3.0.8
python -c "import commit; print(commit.__version__)"   # 2.4.2
```

- Python **3.13** (AMICO/COMMIT no compilan con 3.14).
- Si necesitan una librería nueva (por ejemplo `dipy` para LiFE): agréguenla a `environment.yml` con versión fija y avisen al equipo.
- COMMIT necesita compilador. En Linux: `sudo apt install build-essential`.
- La ruta del proyecto **no debe tener acentos ni espacios** (COMMIT falla).

---

## 4. Archivos compartidos (los mismos para todos)

Los primeros pasos ya están hechos y todos parten de los mismos archivos. **No regeneren el tractograma.**

| Archivo | Qué es | Quién lo produce |
|---|---|---|
| `out/dwi.mif` | DWI con gradientes corregidos (eje `y` invertido) | `scripts/01_preprocess.sh` |
| `out/mask.mif` | máscara del cerebro | `01_preprocess.sh` |
| `out/fod.mif` | FOD (orientación de fibras) | `01_preprocess.sh` |
| `data/tracks_100k.tck` | **el tractograma oficial**, 100 000 hilos. Es una entrada: se pone en `data/` y no se regenera | se comparte por Drive (109 MB) |
| `out/longitudes.txt` | longitud en mm de cada hilo | `02_tractography.sh` |
| `out/pesos_sift2.txt` | pesos de SIFT2 | `02_tractography.sh` |

**Regla del eje `y`:** después del paso 1, **nunca** usen `-fslgrad` con el `.bvec` original. Usen siempre `out/dwi.mif`, que ya lleva los gradientes corregidos. Sin esa corrección los hilos salen cortados (≈ 42 mm en vez de ≈ 92 mm).

**Verificación de que van bien:** `tckstats data/tracks_100k.tck` debe dar media 92.13, mediana 95.21, desviación 40.65, `count 100000`.

---

## 5. El contrato de salida de cada método

Todos los métodos entregan **un archivo de pesos con el mismo formato**, para poder compararlos y combinarlos:

```
out/pesos_<metodo>.txt      # <metodo> = sift2 | commit | life
```

- Excepción: SIFT2 se llama `out/pesos_sift2.txt` y COMMIT queda en `out/commit/pesos_commit.txt` (así lo esperan los scripts `03` y `04`). LiFE entrega `out/life/pesos_life.txt` (lo espera `05_life.sh`). Los métodos nuevos usan `out/pesos_<metodo>.txt`.
- Exactamente **100 000 números**, uno por hilo, **en el mismo orden que `data/tracks_100k.tck`**.
- Todos ≥ 0 y sin `NaN`. Un peso 0 significa "el método descarta ese hilo".
- Debe poder leerse con `np.loadtxt("out/pesos_<metodo>.txt", comments="#").ravel()`. Una línea por hilo es lo preferido; `tcksift2` escribe todo en una sola línea con una cabecera `#`, y eso también se acepta.
- Si un método no devuelve 100 000 pesos (por ejemplo, porque elimina hilos), **rellenen con 0** o mapeen por índice, y escríbanlo en `pipeline.md`. Nunca alineen "a ojo".

**Comprobación que debe pasar cada método antes de entregar:**
```bash
python -c "
import numpy as np
w = np.loadtxt('out/pesos_<metodo>.txt', comments='#').ravel()
print(w.size, (w<0).sum(), np.isnan(w).sum(), (w==0).sum())
"
```
Debe imprimir `100000 0 0 <cuántos son cero>`.

**Matriz 84 × 84 de cada método:**
```bash
tck2connectome data/tracks_100k.tck data/Parcels_free.nii out/connectome_<metodo>.csv \
  -tck_weights_in out/pesos_<metodo>.txt -symmetric -zero_diagonal
python scripts/exportar_matriz84.py out/connectome_<metodo>.csv out/gt.csv out/matriz_<metodo>.xlsx
```
La región 15 no existe en la parcelación: su fila y columna quedan en 0 (es normal).

**Evaluación contra el ground truth:**
```bash
python scripts/evaluar_pesos.py <METODO> out/pesos_<metodo>.txt
```

---

## 6. Reparto de archivos (cada quien toca solo lo suyo)

| Parte | Quién | Archivos que crea o edita | Entrega |
|---|---|---|---|
| Preprocesamiento y SIFT2 | por decidir | `01_preprocess.sh`, `02_tractography.sh` | `out/pesos_sift2.txt` (ya hecho) |
| COMMIT | por decidir | `03_commit.sh`, `correr_commit.py` | `out/commit/pesos_commit.txt` |
| Matrices y evaluación | por decidir | `04_matrices.sh`, `exportar_matriz84.py`, `evaluar_pesos.py` | `out/matriz_*.xlsx` |
| LiFE | por decidir | `correr_life.py`, `05_life.sh` | `out/life/pesos_life.txt` |
| Etiqueta por haz | por decidir | `06_etiquetas.py` | `out/etiquetas.csv` |
| Regla de decisión | por decidir | `07_decision.py` | `out/keep_<estrategia>.txt` |

- `README.md`, `docs/interno/ACTUALIZACION.md`, `pipeline.md` y `environment.yml` son compartidos: se editan **solo para agregar su sección o su línea**, sin reescribir lo de los demás.
- Numeración de scripts: respeten los números de arriba. Si necesitan uno nuevo, el siguiente libre.

### Lo que le toca a cada método nuevo

**LiFE (DIPY).** Usa el tractograma oficial y `scripts/correr_life.py` (lee el `.bvec` crudo: en DIPY es correcto, la inversión de `y` solo hace falta al importar a MRtrix con `-fslgrad`). Entrega `out/life/pesos_life.txt`; `bash scripts/05_life.sh` hace el resto.

**Etiqueta por haz contra el GT.** Hoy `evaluar_pesos.py` marca un hilo como "bueno" si sus dos extremos caen en regiones que el GT conecta. Es débil: el 21 % de los hilos del propio GT no termina en ninguna región, y con esa etiqueta COMMIT da AUC 0.46 por hilo (0.83 por conexión). Hace falta una etiqueta por haz (21 haces en `data/GT/`), **la misma para los tres métodos**. Entrega `out/etiquetas.csv` con columnas `hilo, etiqueta (1 = válido, 0 = inválido), haz`, en el orden del `.tck`.

**Regla de decisión.** Combina `pesos_sift2.txt`, `pesos_commit.txt` y `pesos_life.txt` para decidir qué hilos conservar. Compara al menos 3 estrategias (por ejemplo: umbral por método, votación, promedio de rangos) usando `out/etiquetas.csv`. Entrega `out/keep_<estrategia>.txt` (un 0 o 1 por hilo) y una tabla de resultados en `pipeline.md`.

---

## 7. Cómo documentar (`pipeline.md`)

Cada sección sigue este formato:

1. Título del paso y qué script lo corre.
2. **Cada comando suelto**, en un bloque `bash`, con una frase debajo que diga qué hace y qué archivo sale. Quien lo lea debe poder escribirlo a mano sin entender el script.
3. Un "Se espera:" con los números de control (para saber si salió bien).
4. Las advertencias en una o dos líneas (RAM, rutas, errores conocidos).

Lo que **no** va: guías largas, teoría, planes, cronogramas.

Al terminar algo, actualicen `docs/interno/ACTUALIZACION.md` (tabla de pasos y pendiente) y agreguen una fila a la bitácora al final de `pipeline.md` con fecha y qué hicieron.

---

## 8. Git

```bash
git pull                          # al empezar
git status                        # revisa qué cambió
git add <solo tus archivos>       # NUNCA "git add ."
git commit -m "qué hiciste"
git push                          # al terminar
```

- `data/`, `out/` y `equipo_chat/` están en `.gitignore`: los datos pesados **no se suben**. Se comparten por Drive.
- Si aparece un conflicto en un archivo compartido, no lo resuelvan a ciegas: avisen.
- Un commit por cosa terminada, con un mensaje que diga qué hace, no "cambios".

---

## 9. Errores comunes

| Síntoma | Causa y solución |
|---|---|
| Hilos de ≈ 42 mm en vez de ≈ 92 mm, matriz con ≈ 21 % de conexiones reales | Usaron el `.bvec` original (`-fslgrad`). Usen `out/dwi.mif`. |
| `no peaks have been provided` (COMMIT) | Falta el archivo de picos; `correr_commit.py` ya lo genera con `sh2peaks`. |
| `Dictionary is outdated or not found` | `path_out` del diccionario y la carpeta que busca `Evaluation` deben coincidir. |
| `Killed` | Falta de RAM. Usen un subconjunto común: `tckedit data/tracks_100k.tck -number 20000 out/tracks_20k.tck` y corran los tres métodos sobre ese mismo archivo. |
| COMMIT falla sin mensaje claro | La ruta del proyecto tiene acentos o espacios. Muévanlo. |
| `No module named 'commit'` | No activaron `dwmri`. `conda activate dwmri`. |
| Número de pesos distinto de 100 000 | El método eliminó hilos. Rellenen con 0 según el índice original. |
| Resultados distintos a los de control | Generaron su propio `tracks_100k.tck` (`tckgen` es aleatorio). Usen el compartido. |

---

## 10. Lista de verificación antes de decir "terminé"

- [ ] El script corre desde la raíz con `conda activate dwmri`, sin rutas absolutas.
- [ ] Entrega `out/pesos_<metodo>.txt` con 100 000 pesos, ≥ 0, sin `NaN`.
- [ ] Generó su matriz 84 × 84 y pasó `exportar_matriz84.py`.
- [ ] `pipeline.md` tiene su sección: comandos sueltos, explicación, "Se espera".
- [ ] `docs/interno/ACTUALIZACION.md` y la bitácora actualizados.
- [ ] No agregó carpetas ni archivos fuera de la estructura.
- [ ] No subió `data/` ni `out/`.

# Qué hace COMMIT y cómo llegamos a la matriz

Este archivo explica la idea, no los comandos. Los comandos están en `pipeline.md`.

---

## 1. El problema que resuelve

Un tractograma de 100 000 hilos (streamlines) tiene muchos hilos **falsos**. La tractografía solo sigue la dirección de las fibras vóxel a vóxel y no sabe si el camino completo existe de verdad. Sale un montón de hilos plausibles, pero una parte no corresponde a ningún haz real.

COMMIT hace una pregunta distinta: **¿cuánto necesita cada hilo para explicar la señal de difusión que realmente medimos?** Los hilos que sirven para explicar la señal reciben un peso alto. Los que no aportan nada reciben peso 0.

---

## 2. Qué compara COMMIT (y qué papel tiene la máscara)

COMMIT **no compara con la máscara ni con el ground truth**. Compara contra **la señal medida**: `out/dwi.mif`, la imagen de difusión (1 imagen b0 + 64 direcciones, en cada vóxel).

```
señal medida en cada vóxel   ≈   suma de lo que aporta cada hilo   +   agua alrededor   +   agua libre
```

- **La máscara** solo dice en qué vóxeles trabajar: el cerebro. Fuera del cerebro (aire) solo hay ruido y no tiene sentido explicarlo. COMMIT construye el diccionario y hace el ajuste únicamente dentro de la máscara. Es un filtro de dónde, no la referencia con la que se compara.
- **El ground truth (`data/GT/`) no lo usa.** Se usa después, solo para evaluar qué tan bien quedó el resultado.

### Dónde se usa la máscara (y dónde no)

La máscara **nunca se compara con nada**: solo limita dónde se calcula.

| Paso | Cómo la usa |
|---|---|
| `dwi2response`, `dwi2fod` | estiman solo dentro del cerebro |
| `tckgen` | los hilos empiezan dentro (`-seed_image`) y no pueden salir (`-mask`) |
| `sh2peaks` | saca los picos solo dentro del cerebro |
| COMMIT (`trk2dictionary`) | construye el diccionario y ajusta solo en esos vóxeles |
| SIFT2 (`tcksift2`) | no recibe nuestra máscara; calcula una propia a partir de la FOD (`Creating homogeneous processing mask`) |
| `tck2connectome` | no la usa |

Con lo que sí se compara: COMMIT, contra la señal medida (`dwi.mif`); la evaluación final, contra el ground truth (`data/GT/`). No confundir con la parcelación (`data/Parcels_free.nii`), que son las 84 regiones que definen las filas y columnas de la matriz.

---

## 3. Cómo lo hace, paso a paso

COMMIT arma un modelo lineal. Cada hilo, en cada vóxel que cruza, deja una "huella" en la señal esperada:

1. **Hilo (compartimento intra-axonal, "Stick").** El agua dentro de un axón solo se mueve a lo largo de su dirección. Si un hilo cruza un vóxel con cierta dirección, produce una señal característica: baja mucho cuando el gradiente apunta a lo largo del hilo. Esa señal se multiplica por la **longitud del hilo dentro del vóxel** y por su peso `x_i`, que es la incógnita.
2. **Agua alrededor de los axones ("Zeppelin").** Se difunde más en la dirección de las fibras que en la perpendicular. Para su dirección usa los **picos de la FOD** (`sh2peaks`, hasta 3 por vóxel).
3. **Agua libre ("Ball").** Líquido cefalorraquídeo y materia gris, sin dirección preferida. Se usan dos difusividades: 1.7e-3 y 3.0e-3 mm²/s.

Todo eso forma una gran matriz `A` (el "diccionario": qué señal produce cada hilo y cada compartimento en cada vóxel). El problema queda así:

```
minimizar  || A · x  −  y ||²        con  x ≥ 0
```

- `y` es la señal medida (todos los vóxeles dentro de la máscara × 65 mediciones).
- `x` son los pesos: uno por hilo (100 000) más los de agua alrededor y agua libre.
- `x ≥ 0` porque un hilo no puede aportar señal negativa.
- Se resuelve con mínimos cuadrados no negativos (`mit.fit(tol_fun=1e-3, max_iter=1000)`).

El resultado interesante es `x` para los hilos. Es lo que guardamos en `pesos_commit.txt`: un peso por hilo, en el mismo orden que el `.tck`.

**Por qué salen muchos pesos en 0.** Con tantos hilos solapados, muchos son redundantes: la señal ya la explican otros. Al exigir `x ≥ 0` y minimizar el error, el ajuste "apaga" los que sobran. Salieron 44 780 de 100 000 (45 %).

**Cómo saber si el ajuste es bueno.** El NRMSE mide el error entre la señal medida y la que reconstruye el modelo. Dio 0.106 ± 0.039.

### Qué entra a COMMIT y de dónde sale cada cosa

| Entrada | Qué es | De dónde sale |
|---|---|---|
| Señal | `out/dwi.mif`: los 65 números de cada vóxel, lo que hay que explicar | los datos originales, con el eje `y` corregido |
| Hilos candidatos | `data/tracks_100k.tck`: 100 000 recorridos posibles | `tckgen`, a partir de la FOD |
| Picos de fibra | hasta 3 direcciones por vóxel | `sh2peaks`, a partir de la FOD |
| Máscara | en qué vóxeles ajustar | `dwi2mask` |
| Gradientes | dirección e intensidad de cada una de las 65 mediciones | `bvec` y `bval` (corregidos) |

**Salida:** `out/commit/pesos_commit.txt`, un peso por hilo, en el orden del `.tck`.

**Datos y estimados.** Solo la imagen es un dato (`dwi.mif`). La máscara, la respuesta, la FOD, los picos y el tractograma son estimados calculados a partir de ella.

### Qué son `bvec`, `bval` y FOD (para no confundirlos)

- **`bval` y `bvec` no son fibras.** Describen las **mediciones**: para cada una de las 65 imágenes, `bvec` dice en qué dirección se aplicó el gradiente y `bval` con qué intensidad (3000 en las 64 con gradiente, 0 en el b0). Son la tabla de cómo se tomó la imagen.
- **La imagen `dwi.mif`** guarda, en cada vóxel, 65 números: cuánta señal quedó en cada medición. Con ruido.
- **La FOD** (función de distribución de orientaciones de fibra) se calcula a partir de esos 65 números (`dwi2fod csd`). Dice, para cada vóxel, hacia dónde apuntan las fibras y con qué intensidad. Es un mapa de direcciones por vóxel; no hay conexiones entre vóxeles.
- **Los hilos** salen de `tckgen`: parte de puntos al azar dentro del cerebro y avanza vóxel a vóxel siguiendo las direcciones de la FOD. Cada recorrido es un hilo.

```
bvec + bval + imagen  ->  dwi.mif (65 números por vóxel)
dwi.mif               ->  FOD (direcciones por vóxel)
FOD                   ->  tckgen  ->  100 000 hilos candidatos
dwi.mif + hilos + FOD ->  COMMIT  ->  un peso por hilo
```

**Por qué hay más hilos de los que la imagen justifica.** La imagen no contiene hilos: contiene señal. Los hilos son una reconstrucción posible a partir de las direcciones locales, y `tckgen` produce muchos recorridos plausibles aunque una parte no corresponda a ningún haz real. COMMIT (y SIFT2, y LiFE) sirven para estimar cuáles se sostienen con la señal de la imagen y cuáles son redundantes o sobran. Por eso los pesos en 0 son los candidatos a descartar.

**COMMIT solo elige entre los hilos que se le dan.** No crea hilos nuevos ni corrige trayectorias. Si el tractograma no contiene un haz real, COMMIT no lo inventa. Por eso cualquier problema anterior (en la FOD o en el tractograma) llega hasta la matriz.

---

## 4. Por qué el peso de COMMIT va "por unidad de longitud"

Un hilo largo cruza más vóxeles y aporta más señal con el mismo peso. Para explicar la misma señal, a un hilo largo le basta un peso menor. Por eso, si sumamos pesos de COMMIT para armar la matriz, **las conexiones cortas pesan de más** y las largas de menos.

Multiplicar el peso por la longitud del hilo corrige eso (variante "COMMIT × longitud"). Está pendiente decidir cuál versión entregamos.

---

## 5. De los pesos a la matriz 84 × 84

`tck2connectome` hace esto:

1. Toma cada hilo y mira en qué región de `data/Parcels_free.nii` cae cada uno de sus **dos extremos**.
2. Si ambos extremos caen en regiones (por ejemplo la 12 y la 40), el hilo conecta ese par.
3. En la celda `(12, 40)` suma el peso del hilo. Con `-tck_weights_in` suma el peso de COMMIT; sin él, suma 1 por hilo (cuenta de hilos).
4. `-symmetric` repite el valor en `(40, 12)` y `-zero_diagonal` pone 0 donde una región se conecta consigo misma.

**La diagonal.** La celda `(i, i)` cuenta los hilos cuyos dos extremos caen en la misma región; no es una conexión entre regiones y no cambia las demás celdas. Las matrices que se entregaron sin `-zero_diagonal` (SIFT2 y LiFE de los equipos) la traen con valores. No hay que repetir nada: **al comparar se pone la diagonal en 0** (`np.fill_diagonal(M, 0)`), y solo importa si se suman totales o se normaliza por el máximo (el máximo cae en la diagonal).

Los hilos cuyos extremos no caen en ninguna región se descartan en este paso. La región 15 no existe en la parcelación, y por eso su fila y columna quedan en 0.

### Cómo leer la matriz

```
          R1   R2   R3  ...  R84
   R1      0   0.2  0     ...
   R2     0.2   0   1.3   ...
   ...
```

- **Filas y columnas:** son las 84 regiones de la parcelación (`R1` a `R84`). La fila `i` y la columna `i` son la misma región.
- **Una celda `(i, j)`:** cuánta evidencia hay de que la región `i` y la región `j` están conectadas por fibras. Es la suma de los pesos de COMMIT de todos los hilos que unen esas dos regiones.
- **Un valor alto:** muchos hilos, o hilos con mucho peso, unen esas regiones. Una conexión fuerte.
- **Un 0:** ningún hilo con peso une ese par. Para COMMIT, esas regiones no están conectadas.
- **Simétrica:** la celda `(i, j)` vale lo mismo que `(j, i)`, porque una conexión no tiene dirección.
- **Diagonal en 0:** una región no se conecta consigo misma.
- **Fila y columna 15 en 0:** esa región no existe en la parcelación.
- **Las unidades son relativas:** sirven para comparar celdas de la misma matriz, no son milímetros ni número de fibras. No se pueden comparar directamente con la matriz de otro método sin normalizar.
- **Para evaluarla:** se compara celda por celda con el conectoma del ground truth (`out/gt.csv`), que dice qué pares están realmente conectados (529).

---

## 6. Cómo llegamos a esto (la historia)

```
data/ (DWI + bval + bvec)
  │
  ├─ 1. Corregir gradientes: invertir el eje y   →  out/dwi.mif
  │       máscara, respuesta de una fibra, FOD   →  out/mask.mif, out/fod.mif
  │
  ├─ 2. Tractograma de 100 000 hilos (data/tracks_100k.tck, de la otra laptop de COMMIT)
  │       longitudes y SIFT2                      →  out/longitudes.txt, out/pesos_sift2.txt
  │
  ├─ 3. COMMIT (señal + hilos + picos + máscara)  →  out/commit/pesos_commit.txt
  │
  └─ 4. tck2connectome con esos pesos             →  matriz 84 × 84 (.xlsx)
                                                      │
                                      se compara con el GT (data/GT/) para evaluar
```

**Lo que cambió en la versión corregida.** La primera versión (de la otra laptop de COMMIT) usaba el `.bvec` tal cual y obtenía hilos cortos (≈ 42 mm de media). La versión corregida invierte el eje `y` de los gradientes (elegido con `dwigradcheck`) y los hilos pasan a ≈ 92 mm, mucho más cerca de los del ground truth.

**¿Por qué invertir un solo eje no es "simétrico"?** La señal de difusión sí es simétrica ante `g → −g` (invertir los tres ejes a la vez), pero invertir **solo `y`** es un espejo, no una rotación: una fibra que apunta en la dirección (1, 1, 0) pasaría a verse como (1, −1, 0). Solo las fibras paralelas a un eje, o contenidas en el plano x–z, quedan igual. Tampoco se nota en la FA, porque un espejo no cambia los valores propios del tensor; sí cambia sus direcciones.

**Qué está demostrado y qué no sobre `y`:**
- Demostrado (pruebas controladas, cambiando solo los gradientes): los hilos pasan de ≈ 36–42 mm a ≈ 92 mm, y la dirección principal del tensor concuerda mejor con la tangente de los hilos del GT (|cos| medio 0.40 → 0.64; el azar daría 0.5).
- **No demostrado:** que la mejora de la matriz (de 125 a 446 conexiones reales) se deba solo a `y`. En la versión corregida cambiaron **cuatro cosas a la vez** y no se probó cada una por separado:
  - el eje `y` invertido;
  - `fiber_shift=0.5`: MRtrix pone el centro del vóxel en 0 y COMMIT en 0.5;
  - `-mask` en `tckgen`: los hilos no pueden salir del cerebro;
  - Ball con dos difusividades en lugar de una.
- Para SIFT2 la corrección **casi no importa** (prueba del 2026-11-13: mismo tractograma, FOD con y sin `y` corregido; correlación de pesos por hilo 0.989 y de la matriz 0.9999). Para COMMIT y LiFE no se ha probado.

---

## 7. Qué dice el resultado (con los números de la otra laptop de COMMIT)

El ground truth tiene **529 conexiones reales** entre regiones.

| Matriz | Conexiones > 0 | GT recuperadas | Peso en conexiones reales |
|---|---|---|---|
| Versión anterior (sin invertir `y`) | 606 | 125 | 31 % |
| Sin pesos (cuenta de hilos) | 1322 | 460 | 81 % |
| SIFT2 | 1322 | 460 | 75 % |
| **COMMIT** | **1203** | **446** | **64 %** |
| COMMIT × longitud | 1203 | 446 | 79 % |

- La versión corregida recupera 446 conexiones reales contra 125 de la anterior, pero cambiaron cuatro cosas a la vez (ver sección 6), así que no se puede atribuir toda la mejora al eje `y`.
- COMMIT elimina 119 conexiones respecto al conteo sin pesos, y casi todas eran falsas (solo 14 estaban en el GT).
- **Aun así quedan ≈ 757 conexiones con peso que no existen en el GT** (63 % de las 1203). Ningún método por sí solo limpia el tractograma. Para eso se combinan COMMIT, SIFT2 y LiFE.

Cómo se ve la matriz: es escasa (35 % de las celdas con peso) y muy concentrada. El 10 % de las conexiones concentra el 88 % del peso, con unas pocas muy fuertes (R35–R84, R70–R72, R21–R23).

---

## 8. Límites y cuidados

- **Solo hay una shell (b = 3000).** Con una sola capa COMMIT separa peor los compartimentos (axón, alrededor, agua libre).
- **Peso 0 no significa "falso".** Significa que el hilo no hace falta para explicar la señal. Puede ser redundante y verdadero. Esto es una hipótesis aún sin comprobar.
- **Etiqueta por hilo débil.** Con la etiqueta actual de `evaluar_pesos.py` (por extremos), COMMIT da AUC 0.46 por hilo, igual que el azar, pero 0.83 por conexión. Falta una etiqueta por haz.
- **Los números son de la otra laptop de COMMIT.** En nuestro repo todavía no hemos corrido COMMIT ni generado la matriz.
- **COMMIT necesita bastante RAM** y falla (`Killed`) si no alcanza.

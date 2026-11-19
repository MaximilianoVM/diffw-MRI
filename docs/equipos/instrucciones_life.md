# LiFE sobre `tracks_100k.tck`: instrucciones para el equipo de LiFE

## Qué necesitamos y por qué

Para comparar LiFE con COMMIT y SIFT2, los tres métodos tienen que pesar **los mismos hilos**: el tractograma oficial `tracks_100k.tck`.

Las matrices que mandaron (`conn_life_full.csv`, `conn_raw_full.csv`) salen de otro tractograma, su `tracks.tck`. Se nota en su conteo crudo: 684 conexiones, contra las 1322 del oficial, y 18 564 hilos en la diagonal, contra 4 869. Ese tractograma se generó con `-fslgrad` y el `.bvec` original, y así los hilos salen cortados (≈ 40 mm en vez de 92 mm). Contra el ground truth, su matriz queda al nivel del azar (AUC 0.54).

**Su código de LiFE está bien.** El script de abajo es su mismo método (`FiberModel(gtab).fit(data, hilos, np.linalg.inv(img.affine))`, con el `.bvec` original, que para DIPY es correcto). Lo único que cambia es el tractograma.

Necesitamos tres cosas:

1. **`life_weights.txt`**: los 100 000 pesos β, uno por línea, en el orden de `tracks_100k.tck`. Es lo más importante: con esto comparamos los métodos hilo por hilo.
2. `conn_life_100k.csv`: la matriz 84 × 84 ponderada por LiFE, con `-symmetric -zero_diagonal`.
3. `conn_raw_100k.csv`: el conteo crudo, que sirve para confirmar que se usó el tractograma correcto.

El script hace todo y lo empaqueta en un solo archivo: `entrega_life_100k.tar.gz`.

---

## Paso 1. Bajar el tractograma oficial

Bajen `tracks_100k.tck` (109 MB) del Drive y pónganlo junto a sus datos:

```bash
mv /mnt/c/Users/<su_usuario>/Downloads/tracks_100k.tck ~/desafio/datos/dataset/DWIs/
md5sum ~/desafio/datos/dataset/DWIs/tracks_100k.tck
```

Debe dar **`66ba3e6efe1fadf5b534d3947b2b138f`**. Si da otro número, el archivo está incompleto: bájenlo otra vez.

## Paso 2. Copiar el script

Copien `life_para_equipo.sh` a `~/desafio/`, por ejemplo desde Descargas:

```bash
cp /mnt/c/Users/<su_usuario>/Downloads/life_para_equipo.sh ~/desafio/
```

El script usa estas rutas, que son las de sus documentos:

| Variable | Valor por omisión |
|---|---|
| `BASE` | `~/desafio/datos/dataset/DWIs` |
| `TCK` | `$BASE/tracks_100k.tck` |
| `DWI`, `BVAL`, `BVEC` | `$BASE/ISMRM_2023_b3000.{nii.gz,bval,bvec}` (el `.bvec` **original**) |
| `PARC` | `$BASE/../Parcels_free.nii` |
| `ENV_MRTRIX` / `ENV_PY` | entornos conda `dmri` / `pydmri` |
| `SALIDA` | `~/desafio/entrega_life_100k` |

Si algo está en otro lado, se puede cambiar al correrlo, por ejemplo: `PARC=/otra/ruta/Parcels_free.nii bash ~/desafio/life_para_equipo.sh`.

## Paso 3. Prueba rápida (1–2 minutos)

```bash
bash ~/desafio/life_para_equipo.sh --prueba
```

Revisa los archivos, el md5, que la media de los hilos sea ≈ 92.13 mm, que los entornos tengan MRtrix y DIPY, y corre LiFE con 2 000 hilos. Debe terminar con:

```
PRUEBA TERMINADA: todo funciona. Ahora corran sin --prueba
```

Si sale `[ERROR]`, el mensaje dice qué falta. Ver "Si algo falla" abajo.

## Paso 4. Corrida completa

```bash
bash ~/desafio/life_para_equipo.sh
```

Al final imprime la ruta del paquete:

```
LISTO. Manden este archivo al equipo de COMMIT:
   /home/<usuario>/desafio/entrega_life_100k.tar.gz
```

Para pasarlo a Windows: `cp ~/desafio/entrega_life_100k.tar.gz /mnt/c/Users/<su_usuario>/Downloads/`

## Paso 5. Mandar

Manden **`entrega_life_100k.tar.gz`**. Trae `life_weights.txt`, las dos matrices, `resumen.txt` y el log completo.

---

## Memoria (importante)

Con estos hilos, LiFE pide **≈ 20 GB entre RAM y swap**. Con su `tracks.tck` les pidió 7.7 GB, pero eran hilos de la mitad de largo, y la memoria crece con el número de puntos. El script revisa la memoria antes de empezar y se detiene si hay menos de 22 GB disponibles.

**WSL usa por omisión solo la mitad de la RAM de Windows.** Para darle más, creen o editen `C:\Users\<su_usuario>\.wslconfig` en Windows:

```ini
[wsl2]
memory=24GB
swap=16GB
```

Pongan en `memory` lo que su máquina tenga libre (deja unos 4 GB para Windows). Luego, en PowerShell, ejecuten `wsl --shutdown`, abran la terminal de nuevo y comprueben con `free -h`.

Si la máquina tiene 16 GB de RAM o menos, la corrida dependerá mucho de la swap y puede tardar horas. En una Mac de 16 GB se quedó esperando al disco y la detuvimos. Si tienen acceso a una máquina con 32 GB, úsenla. En una máquina con memoria suficiente, el ajuste debería tardar unos minutos: con 20 000 hilos tardó 21 s.

---

## Qué debe salir (para comprobar)

| Qué | Valor esperado |
|---|---|
| md5 de `tracks_100k.tck` | `66ba3e6efe1fadf5b534d3947b2b138f` |
| `tckstats` | count 100000, media ≈ 92.13 mm |
| `life_weights.txt` | 100 000 líneas, ningún negativo ni NaN |
| `conn_raw_100k.csv` | 1322 conexiones > 0 y 68 418 hilos asignados (el script lo comprueba) |
| `conn_life_100k.csv` | 84 × 84, simétrica, diagonal 0 |

## Si algo falla

| Mensaje | Qué hacer |
|---|---|
| `no encuentro ...` | ajusten la ruta con la variable correspondiente (tabla del paso 2) |
| `md5 ... debe ser 66ba3e...` | el `.tck` no es el oficial o está incompleto: bájenlo otra vez del Drive |
| `la media es ... debe ser ≈ 92.13` | no es el tractograma oficial |
| `no existe el entorno conda` | cambien `ENV_MRTRIX=` / `ENV_PY=` por los nombres de sus entornos (`conda env list`) |
| `no alcanza la memoria` | sección "Memoria" arriba. Se puede forzar con `FORZAR=1 bash ...`, bajo su riesgo |
| `Killed` / `LiFE no terminó` | se quedó sin memoria: sección "Memoria" |
| `el conteo no coincide` | las matrices no salieron del tractograma oficial: revisen `TCK` |

Para cualquier otra cosa, manden `~/desafio/entrega_life_100k/log_completo.txt` al equipo de COMMIT.

# LiFE sobre 100 000 streamlines — códigos

Secuencia completa, en orden. Ruta de trabajo:
`/home/jaziv/desafio/datos/dataset/DWIs/`

---

## 1. Tractograma (entorno `dmri`)

```bash
conda activate dmri
cd ~/desafio/datos/dataset/DWIs

dwi2response tournier ISMRM_2023_b3000.nii.gz response.txt \
  -fslgrad ISMRM_2023_b3000.bvec ISMRM_2023_b3000.bval \
  -mask ISMRM_2023_b3000_mask.nii -force

dwi2fod csd ISMRM_2023_b3000.nii.gz response.txt ODF.nii \
  -fslgrad ISMRM_2023_b3000.bvec ISMRM_2023_b3000.bval \
  -mask ISMRM_2023_b3000_mask.nii -force

tckgen -algorithm iFOD2 ODF.nii tracks.tck \
  -seed_image ISMRM_2023_b3000_mask.nii -select 100000 -force

ls -lh ODF.nii tracks.tck
```

Salidas: `ODF.nii` 151 MiB, `tracks.tck` 44 MiB.

---

## 2. Script de LiFE

```bash
cat > ~/desafio/analisis_life.py << 'EOF'
import numpy as np
import nibabel as nib
from nibabel.streamlines import load as load_tck
from dipy.io.gradients import read_bvals_bvecs
from dipy.core.gradients import gradient_table
from dipy.tracking.life import FiberModel

base = "/home/jaziv/desafio/datos/dataset/DWIs/"

img  = nib.load(base + "ISMRM_2023_b3000.nii.gz")
data = img.get_fdata(dtype=np.float32)
print("DWI:", data.shape)

bvals, bvecs = read_bvals_bvecs(base + "ISMRM_2023_b3000.bval",
                                base + "ISMRM_2023_b3000.bvec")
gtab = gradient_table(bvals, bvecs=bvecs)
print("b0:", int(gtab.b0s_mask.sum()), " direcciones DW:", int((~gtab.b0s_mask).sum()))

tck = load_tck(base + "tracks.tck")
sl  = list(tck.streamlines)
print("streamlines:", len(sl))

print("ajustando LiFE ...")
fit  = FiberModel(gtab).fit(data, sl, np.linalg.inv(img.affine))
beta = np.asarray(fit.beta)

np.savetxt(base + "life_weights.txt", beta)

print("beta  min/mediana/media/max: %.4g %.4g %.4g %.4g" %
      (beta.min(), np.median(beta), beta.mean(), beta.max()))
print("beta == 0: %d (%.2f%%)" % ((beta == 0).sum(), 100*np.mean(beta == 0)))
EOF
```

**El affine va invertido.** `np.linalg.inv(img.affine)`, no `img.affine`. DIPY
aplica el affine directamente a los streamlines y redondea el resultado para
usarlo como índice de vóxel; como los `.tck` están en coordenadas de mundo, pasar
el affine sin invertir produce
`IndexError: index 194 is out of bounds for axis 0 with size 90`.

---

## 3. Ejecutar

```bash
conda activate pydmri
/usr/bin/time -v python ~/desafio/analisis_life.py 2>&1 | tail -25
```

Antes conviene comprobar la memoria disponible, porque LiFE pide ~7.7 GB con
100 000 streamlines:

```bash
free -h
```

---

## 4. Estadísticas de los pesos

```bash
python -c "
import numpy as np
b=np.loadtxt('/home/jaziv/desafio/datos/dataset/DWIs/life_weights.txt')
print('n =', b.size)
print('min %.4g  mediana %.4g  media %.4g  max %.4g'%(b.min(),np.median(b),b.mean(),b.max()))
print('beta == 0: %d (%.2f%%)'%((b==0).sum(), 100*np.mean(b==0)))"
```

---

## 5. Matrices de conectividad (entorno `dmri`)

```bash
conda activate dmri
cd ~/desafio/datos/dataset/DWIs

tck2connectome tracks.tck ../Parcels_free.nii conn_life_full.csv \
  -tck_weights_in life_weights.txt -symmetric -force

tck2connectome tracks.tck ../Parcels_free.nii conn_raw_full.csv \
  -symmetric -force
```

`conn_life_full.csv` es la matriz ponderada por LiFE; `conn_raw_full.csv` es el
conteo crudo de los mismos streamlines, que sirve de control.

El aviso `The following nodes are missing from the parcellation image: 15` es
benigno: esa etiqueta no tiene vóxeles en la parcelación, así que su fila y su
columna quedan en cero.

---

## 6. Resumen de las matrices

```bash
conda activate pydmri
cd ~/desafio/datos/dataset/DWIs
python -c "
import numpy as np
A=np.loadtxt('conn_life_full.csv',delimiter=',')
B=np.loadtxt('conn_raw_full.csv',delimiter=',')
print('forma:', A.shape, '| simetrica:', np.allclose(A,A.T))
print('aristas  crudo: %d | LiFE: %d | eliminadas: %d'
      %((B>0).sum()//2,(A>0).sum()//2,(B>0).sum()//2-(A>0).sum()//2))
print('streamlines asignados: %d de 100000'%int(B.sum()//2))
print('peso total: %.4g'%(A.sum()/2))"
```

---

## 7. Figuras

```bash
cat > ~/desafio/figuras_life.py << 'EOF'
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

base = "/home/jaziv/desafio/datos/dataset/DWIs/"
b = np.loadtxt(base + "life_weights.txt")

fig, ax = plt.subplots(1, 2, figsize=(11, 4))
ax[0].hist(b, bins=80)
ax[0].set_xlabel("beta LiFE"); ax[0].set_ylabel("streamlines")
ax[0].set_title("Todos (n=%d)" % b.size)
ax[1].hist(b[b > 0], bins=80)
ax[1].set_xlabel("beta LiFE"); ax[1].set_ylabel("streamlines")
ax[1].set_title("Solo beta > 0 (n=%d)" % (b > 0).sum())
fig.tight_layout(); fig.savefig(base + "hist_life.png", dpi=150)

A = np.loadtxt(base + "conn_life_full.csv", delimiter=",")
B = np.loadtxt(base + "conn_raw_full.csv", delimiter=",")
fig, ax = plt.subplots(1, 2, figsize=(12, 5))
for a, M, t in zip(ax, (B, A), ("Conteo crudo", "Ponderada por LiFE")):
    im = a.imshow(np.log1p(M), cmap="magma")
    a.set_title(t + "\n(escala log1p)")
    a.set_xlabel("nodo"); a.set_ylabel("nodo")
    fig.colorbar(im, ax=a, fraction=0.046)
fig.tight_layout(); fig.savefig(base + "matriz_life.png", dpi=150)
print("figuras guardadas en", base)
EOF
```

```bash
conda activate pydmri
python ~/desafio/figuras_life.py
```

---

## 8. Pasar los resultados a Windows

```bash
cd ~/desafio/datos/dataset/DWIs
cp conn_life_full.csv conn_raw_full.csv life_weights.txt /mnt/c/Users/jaziv/Downloads/
cp hist_life.png matriz_life.png /mnt/c/Users/jaziv/Downloads/
```

Los CSV son 84×84 sin encabezados: la etiqueta de cada nodo es su posición, y la
fila y columna 15 están en cero. Si Excel está en español puede malinterpretar el
punto decimal; en ese caso abrirlos con Datos → Obtener datos → Desde archivo de
texto/CSV, eligiendo el punto como separador decimal.

---

## 9. Resultados obtenidos

Pesos de LiFE, 100 000 streamlines:

| Métrica | Valor |
|---|---|
| n | 100 000 |
| mínimo | 0 |
| mediana | 0.000561 |
| media | 0.001204 |
| máximo | 0.01474 |
| **beta = 0** | **38 643 (38.64 %)** |

Casi cuatro de cada diez streamlines no aportan nada a explicar la señal de
difusión medida.

Matrices: `conn_life_full.csv` y `conn_raw_full.csv`, ambas 84×84. El conteo de
aristas eliminadas **está pendiente de medir** con el comando de la sección 6.

---

## 10. Pendientes

1. Correr el resumen de la sección 6 para obtener el número de aristas que LiFE
   elimina respecto al conteo crudo.
2. Comparar contra el ground truth (`all_tracks.tck`, 189 985 streamlines):
   verificar si los streamlines más parecidos a los fascículos verdaderos reciben
   pesos altos.
3. Fijar el umbral de descarte. El criterio natural es `beta = 0`, que ya
   identifica 38 643 streamlines; si se quiere algo más estricto, usar un
   percentil de la distribución de pesos positivos.

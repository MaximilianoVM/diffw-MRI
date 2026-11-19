# Resultados extra (fuera del objetivo de la junta del 17 nov)

Lo que se hizo además del objetivo simple (`docs/junta_17nov.md`): matrices 84 × 84, COMMIT2 y el barrido de λ, la normalización por longitud, el análisis del eje `y` y la documentación de COMMIT. Es trabajo válido y quedó como material de apoyo. Cada sección dice qué se hizo, para qué, y qué dice; el detalle está en los archivos que se mencionan.

---

## 1. La matriz 84 × 84

**Qué es.** Una tabla de qué tan conectadas están las regiones del cerebro. Filas y columnas son las 84 regiones de `data/Parcels_free.nii` (la región 15 no existe y queda en 0). La celda `(i, j)` suma lo que aporta cada hilo que une la región `i` con la `j`. La matriz es simétrica y su diagonal se pone en 0.

**Cómo se arma.** Con `tck2connectome`. Cada hilo aporta: 1 en el **conteo** (sin pesos); el peso del método en SIFT2, COMMIT, COMMIT2 y LiFE (`-tck_weights_in`); o peso × longitud en "COMMIT × longitud".

**Para qué se hizo.** Fue la tarea original de COMMIT en el equipo: entregar la matriz de conectividad ponderada con los pesos de COMMIT (`pipeline.md`, pasos 3 y 4). Además da una forma barata de comparar métodos contra el GT, porque el GT también produce una matriz (hecha con sus hilos verdaderos): se ve cuántas conexiones reales recupera cada método.

**Qué dice.** GT: 529 conexiones reales de 3486 pares posibles. El tractograma sin pesos ya tiene 1322 conexiones y recupera 460.

| Matriz | Conexiones > 0 | Del GT | % peso en GT | AUC conexión | Pearson con GT |
|---|---|---|---|---|---|
| conteo (sin pesos) | 1322 | 460 | 80.5 | 0.857 | 0.894 |
| SIFT2 | 1322 | 460 | 74.6 | 0.850 | 0.795 |
| COMMIT | 1203 | 446 | 63.8 | 0.829 | 0.731 |
| COMMIT × longitud | 1203 | 446 | 79.0 | 0.846 | 0.881 |
| COMMIT2 (λ = 1e-2) | 86 | 70 | 91.9 | 0.564 | 0.788 |
| **LiFE** | 1168 | 442 | **90.7** | 0.851 | **0.923** |

- **LiFE es el único cuya matriz queda mejor que el conteo.** COMMIT y SIFT2 quedan peor; COMMIT solo se acerca al multiplicar por la longitud, porque su peso es por unidad de longitud y favorece hilos cortos.
- Una matriz solo dice qué regiones se conectan, no si cada hilo es correcto. Por eso funciona (AUC 0.83–0.85) donde por hilo casi no (ver `docs/conclusiones.md`).
- Detalle: `docs/resultados/matrices.md`, `docs/explicacion_commit.md` (sección 5), `docs/metodologia_comparacion.md` (las métricas).
- Entregable de COMMIT (Mac): `matriz_peso_commit_84x84_corregida.xlsx`.

---

## 2. COMMIT2 y el barrido de λ

**Qué es.** COMMIT con una penalización por grupos: los hilos que unen el mismo par de regiones forman un grupo y el ajuste prefiere apagar conexiones completas poco respaldadas por la señal. λ controla la fuerza. Código: `scripts/correr_commit2.py`, `scripts/06_commit2.sh`, `scripts/barrido_lambda_commit2.sh`.

**Qué dice.**

| | COMMIT | λ = 1e-4 | λ = 1e-3 | λ = 5e-3 | λ = 1e-2 |
|---|---|---|---|---|---|
| Peso = 0 | 44.8 % | 50.5 % | 51.0 % | 58.3 % | 63.1 % |
| Conexiones del GT (de 529) | 446 | 337 | 172 | 99 | 70 |
| Haces detectados (de 21) | 21 | 21 | 21 | 20 | 17 |
| % fibras falsas (sin filtrar: 45.2) | 48.7 | 41.7 | 31.2 | 25.0 | 21.2 |
| Dice (sin filtrar: 0.750) | 0.750 | 0.740 | 0.704 | 0.633 | 0.545 |

- λ es una perilla entre limpieza y cobertura: al subirlo bajan las falsas pero se pierden haces y conexiones reales.
- **COMMIT2 separa hilos buenos de malos** (AUC por hilo 0.68 con la etiqueta MDF), a diferencia de COMMIT (0.42). Además corrige el sesgo hacia hilos cortos.
- Sus pesos son los de `out/commit2/pesos_commit2.txt` (λ = 1e-2). El script original lo dejó a medias una compañera; lo terminamos nosotros.
- Detalle: `docs/resultados/commit2.md`.

---

## 3. Normalización de Ricardo y percentil por longitud

**Qué es.** Cada método usa otra escala, así que en vez del peso se usa el **lugar** del hilo dentro de su método (percentil de 0 a 1); se promedian y se filtra con un umbral. Variante nuestra: el percentil se calcula dentro de rangos de longitud (10 rangos), para quitar el efecto de la longitud. Código: `scripts/normalizacion_ricardo.py`, `scripts/07_normalizacion.sh`.

**Qué dice.**
- Con COMMIT + SIFT2 no mejora: el umbral óptimo es el mínimo (conservar casi todo) y subirlo aumenta las falsas (47 → 60 %).
- Por rango de longitud mejora el AUC del score en 0.07–0.09.
- La mejor combinación fue **COMMIT2 + LiFE** (percentil global, u = 0.1): 66 287 hilos, 21 haces, 33.8 % de falsas (sin filtrar: 45.2 %), Dice 0.736.
- Con el mismo número de hilos, COMMIT2 solo y LiFE solo ganan o empatan desde u = 0.3.
- Detalle: `docs/resultados/normalizacion.md`.

---

## 4. El eje `y`

**Qué es.** Con los gradientes tal cual (`-fslgrad` con el `.bvec` original) las direcciones salen incoherentes con el GT; invertir solo el eje `y` las arregla. Es un espejo, no una simetría de la señal.

**Qué dice.**
- **Demostrado:** cambia la tractografía (hilos de ≈ 36–42 mm a ≈ 92 mm; |cos| tensor–GT de 0.40 a 0.64).
- **SIFT2** casi no cambia (correlación de pesos 0.989, de la matriz 0.9999).
- **No demostrado:** cuánto de la mejora de COMMIT (125 → 446 conexiones) se debe a `y`; esa corrida cambió cuatro cosas a la vez. En LiFE, DIPY lee el `.bvec` crudo y es correcto.
- Detalle: `docs/explicacion_commit.md` (sección 6).

---

## 5. Documentación de COMMIT

`docs/explicacion_commit.md` explica qué hace COMMIT (modelo Stick-Zeppelin-Ball, mínimos cuadrados no negativos, no supervisado), qué papel tiene la máscara (solo restringe dónde se calcula), por qué su peso va por unidad de longitud y cómo se lee la matriz. Sirve para quien se integre.

---

## Para cerrar

Estos resultados sirven como contexto y **no son el objetivo**. Lo que sí pasa al nuevo enfoque: los vectores de pesos de cada método, la etiqueta MDF (como comparación, `docs/etiqueta_hausdorff_vs_mdf.md`) y la lección de que **la longitud pesa mucho** (una etiqueta o un modelo que no la considere puede engañar).

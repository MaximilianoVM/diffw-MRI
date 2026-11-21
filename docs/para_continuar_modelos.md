# Guía para continuar: aplicar modelos

Para quien se incorpora a la parte de **modelos**, sin necesidad de conocer el resto del proyecto ni de usar Git.
Tiempo de lectura: 10 minutos. Tiempo para tener algo corriendo: 5 minutos más.

---

## 1. El proyecto en un minuto
- Una resonancia de difusión de un cerebro **simulado** permite reconstruir fibras del cerebro. Cada fibra reconstruida es un **hilo** (una línea 3D). Tenemos **100 000 hilos**.
- Como el cerebro es simulado, existe una **lista de las fibras verdaderas** (el *ground truth*, GT). Por eso podemos saber, para cada hilo, **si es verdadero o falso**.
- Cuatro métodos (**SIFT2, COMMIT, LiFE, COMMIT2**) le asignan a cada hilo **un peso**: «qué tan creíble parece». Se usan para descartar los hilos con peso bajo.
- **El problema:** esos pesos, por separado, filtran mal (SIFT2 y COMMIT incluso empeoran el resultado).
- **Tu parte:** construir un **modelo** que combine los pesos de los 4 métodos (y lo que quieras) para predecir **si un hilo es verdadero**, y que filtre mejor que cada método por separado.

Ya hay un primer modelo (regresión logística) que sirve de punto de partida. Tu trabajo es **superarlo** con lo que se te ocurra.

---

## 2. Qué recibes: una sola tabla
`tabla_hilos.csv`: **100 000 filas (un hilo por fila) y 9 columnas**. Con eso basta; no hace falta correr nada más del proyecto.

| Columna | Qué es | ¿Entrada del modelo? |
|---|---|---|
| `hilo` | número del hilo (0–99 999) | no (es un identificador) |
| `longitud_mm` | largo del hilo en milímetros | sí (con cuidado, ver sección 6) |
| `SIFT2`, `COMMIT`, `LiFE`, `COMMIT2` | peso que cada método le da al hilo. **0 = el método lo eliminó** | **sí, son las entradas principales** |
| `hd_min_mm` | distancia del hilo al GT, en mm (vacío = más de 10 mm) | ❌ **NO** (ver abajo) |
| `etiqueta_5mm` | **la respuesta:** 1 = el hilo es verdadero (a menos de 5 mm del GT), 0 = falso | ❌ **NO** (es lo que se predice) |
| `conjunto` | `entrenamiento` o `prueba`: la mitad en la que se evalúa | sí, para separar los datos |

> ⚠️ **Nunca uses `hd_min_mm` ni `etiqueta_5mm` como entrada.** Son la respuesta misma. Un modelo que los use saldrá perfecto y no servirá para nada.

Un tercio de los hilos (33.3 %) son verdaderos. Los pesos de COMMIT y COMMIT2 tienen muchos ceros (45 % y 63 %); los de SIFT2 nunca son cero.

---

## 3. Qué hacer (libertad casi total)
**Objetivo:** un modelo que, dados los pesos de un hilo, diga qué tan probable es que sea verdadero, y que **ordene mejor** a los hilos que cada método solo.

Puedes usar el modelo que quieras: regresión, árboles, bosques, boosting, redes, combinaciones, transformaciones de los pesos (logaritmo, percentil, razones, productos, ceros como categoría…). Puedes incluir o no la longitud. Puedes crear tus propias columnas.
**No hay un método obligatorio.** Lo único que pedimos está en la sección 8.

### Empezar en 5 minutos
1. Instala Python 3 y las librerías (una vez): `pip install pandas scikit-learn numpy`
2. Pon `tabla_hilos.csv` y `ejemplo_modelo.py` en la misma carpeta.
3. Corre `python ejemplo_modelo.py`. Debe imprimir un AUC de **0.683** y las precisiones de abajo. Ese es el modelo de partida.
4. Abre `ejemplo_modelo.py`, cámbialo, y vuelve a correrlo.

---

## 4. Cómo saber si tu modelo es bueno
Dos medidas, ambas sobre los hilos de la mitad **`prueba`** (nunca entrenes con ellos):

- **AUC:** ¿el modelo pone los hilos verdaderos por encima de los falsos? **0.5 = azar, 1.0 = perfecto.**
- **Precisión al conservar n hilos:** te quedas con los n hilos de mayor puntaje; ¿qué % de ellos es verdadero? **Sin filtrar daría 33.3 %**; cuanto más alto, mejor.

### Qué hay que superar (mitad de prueba, etiqueta a 5 mm)
| Modelo | AUC | Precisión con 10 000 hilos | 25 000 | 50 000 |
|---|---|---|---|---|
| longitud sola | 0.649 | 31.1 % | 41.8 % | 42.1 % |
| COMMIT2 solo | 0.633 | 48.5 % | 52.3 % | 42.3 % |
| promedio de los 3 métodos del doctor (SIFT2+LiFE+COMMIT) | 0.486 | 30.0 % | 28.9 % | 32.7 % |
| logística, 3 métodos (SIFT2+LiFE+COMMIT) | 0.623 | 40.9 % | 42.9 % | 41.5 % |
| **logística, 4 métodos** (el ejemplo) | **0.683** | 45.5 % | 50.2 % | 45.9 % |
| logística, 4 métodos + longitud | 0.701 | 47.7 % | 47.9 % | 46.5 % |
| mínimo de percentiles LiFE+COMMIT2 (sin entrenar) | 0.630 | 54.3 % | 53.2 % | 41.4 % |

*Nota:* la fila «mínimo de percentiles» está medida sobre los 100 000 hilos (no solo la mitad de prueba) porque no se entrena. Y el ejemplo imprime las precisiones sobre los 100 000 hilos ya puntuados con el intercambio de mitades (45.0 / 50.3 / 46.0 %): por eso difieren unas décimas de la fila de la logística de 4 métodos (45.5 / 50.2 / 45.9 %), que es solo sobre `prueba`. El AUC sí se calcula sobre `prueba` y da 0.683.

Superar el AUC es bueno; **superar la precisión con pocos hilos (10 000–25 000) también**, y es lo más difícil.

---

## 5. Lo que ya sabemos (para no repetirlo)
- **SIFT2 y COMMIT, solos, están por debajo del azar** (AUC 0.43 y 0.45): dan pesos altos a hilos cortos, y los cortos casi nunca son verdaderos. Un modelo bueno les da **coeficiente negativo**.
- **LiFE y COMMIT2 sí aportan** (AUC 0.60 y 0.63). COMMIT2 es el mejor solo.
- **La longitud sola ya da AUC 0.65.** Por eso conviene reportar tu modelo **con y sin** la longitud: sin ella se ve cuánto aportan los pesos de verdad.
- **Promediar los 3 métodos del doctor empeora el resultado.** Un modelo supervisado sí logra aprovecharlos.
- **Hay un compromiso entre limpiar y no perder fibras** (sección siguiente).
- Una regresión logística es **lineal**. No se ha probado ningún modelo no lineal (árboles, boosting, redes): **ahí está la mayor oportunidad**, sobre todo en la interacción «peso × longitud» y en el significado de los ceros.

### El compromiso que importa (no solo el AUC)
Hay 21 haces (grupos de fibras) en el GT. Al filtrar, algunos haces pueden **perderse por completo**. Con 25 000 hilos conservados:
| Puntaje | % de hilos falsos | Haces recuperados (de 21) |
|---|---|---|
| mínimo LiFE + COMMIT2 | 46.8 % (el más limpio) | 14 |
| modelo con los 3 métodos del doctor | 57.4 % | 15 |
| LiFE solo | 58.9 % | 17 |
| COMMIT solo | 74.7 % | 20 |
| sin filtrar | 66.7 % | 20 |

Los modelos más precisos **pierden haces enteros** (BPS, Fornix, ICP) porque COMMIT2 les pone peso 0. Un modelo que sea **preciso y además conserve esos haces** sería un resultado muy valioso. Los hilos de esos haces están en la tabla: son hilos con `etiqueta_5mm = 1` y `COMMIT2 = 0`.


### Una propuesta: un modelo genético (lo mencionó el doctor)
No se ha probado nada de este tipo. Vale la pena porque ataca justo el compromiso de arriba. *(No sabemos exactamente qué quiso decir el doctor con «genético»; conviene preguntarle antes de invertir mucho tiempo. Esta es una lectura razonable.)*

- **Idea.** Un algoritmo genético mantiene una población de «reglas» candidatas; en cada generación se quedan las mejores (selección), se mezclan (cruce) y se alteran un poco (mutación). Una regla simple: *puntaje = a·log(SIFT2) + b·log(COMMIT) + c·log(LiFE) + d·log(COMMIT2) [+ e·longitud]*, y el **genoma** es el vector de coeficientes (a, b, c, d, e) más, si quieres, el umbral o el número de hilos a conservar.
- **Por qué encaja aquí.** La regresión logística optimiza una verosimilitud. Un algoritmo genético puede optimizar **directamente lo que nos importa**, aunque no sea derivable: el % de hilos falsos con n fijo, **el número de haces recuperados**, el Dice… Y con un enfoque multiobjetivo (por ejemplo NSGA-II) devuelve el **frente de compromiso**: toda la gama entre «tractograma muy limpio» y «no perder haces», que es la pregunta abierta de la sección anterior.
- **Variantes.** Programación genética (la regla es una fórmula que el algoritmo inventa a partir de los pesos, con +, ×, log…); o usar el algoritmo genético para escoger qué entradas y qué transformaciones usar.
- **Cómo empezar barato.** Con 4–5 coeficientes basta una evolución diferencial de `scipy.optimize.differential_evolution` (ya viene con scipy; sin instalar nada), o las librerías `DEAP` / `pymoo` para el caso multiobjetivo. Cada evaluación es contar aciertos sobre 50 000 hilos: milisegundos.
- **Cuidados.** La aptitud debe calcularse **solo con los hilos de `entrenamiento`** (un algoritmo genético sobreajusta con facilidad), y el resultado final se mide **una vez** en `prueba`. Compáralo siempre con la logística del ejemplo: un método «genético» no es mejor por serlo. Para medir haces recuperados hace falta saber a qué haz pertenece cada hilo; esa asignación existe (la calculó la Mac, `out/normalizacion/etiqueta_hausdorff.csv`) pero **no viene en la tabla**: pídela si la necesitas.

---

## 6. Ideas por probar (opcionales)
0. **Un modelo genético** (sección 5): coeficientes o fórmulas evolucionados para optimizar directamente haces recuperados / % de falsos.
1. Modelos no lineales: bosque aleatorio, gradient boosting (`HistGradientBoostingClassifier` entrena en segundos), una red pequeña.
2. Tratar el cero de COMMIT/COMMIT2/LiFE como información: columnas «peso > 0» además del peso.
3. Interacciones: `peso × longitud`, razones entre métodos, rangos (percentil) dentro de cada método.
4. Entrenar dándole más importancia a los hilos verdaderos de haces cortos, o dar un peso distinto a los falsos.
5. Probar otra definición de verdadero (distancia menor o mayor que 5 mm): `hd_min_mm` permite construir la etiqueta que quieras. Úsala solo **como respuesta**, nunca como entrada.
6. Probar un umbral de decisión distinto, o conservar un número fijo de hilos.

**Sobre la longitud:** un modelo que usa la longitud puede estar aprendiendo solo «hilo largo = verdadero». No está mal, pero hay que decirlo: reporta siempre el resultado con y sin ella.

---

## 7. Cómo evaluar sin engañarte
- Entrena **solo** con los hilos `entrenamiento` y mide con los `prueba`. Nunca ajustes decisiones (qué modelo, qué parámetros) mirando `prueba` muchas veces: si pruebas 50 variantes, la mejor se ve mejor de lo que es. Para ajustar parámetros, separa una parte de `entrenamiento`.
- El ejemplo hace además un intercambio de mitades (entrena con una, puntúa la otra, y viceversa). Así **cada hilo recibe un puntaje de un modelo que no lo vio**, y todos los hilos quedan puntuados de forma honesta; eso permite comparar el tractograma filtrado completo contra el GT.
- Es un solo cerebro simulado y un solo tractograma: no sabemos si lo que funciona aquí funciona en otros datos. Dilo en tus conclusiones.

---

## 8. Cómo entregar tu resultado (lo único que pedimos)
Manda dos cosas:
1. **`puntaje_<tu_modelo>.txt`**: un número por hilo, **100 000 líneas, en el mismo orden que la tabla** (`hilo` 0, 1, 2…), valores ≥ 0 (cuanto mayor, más probable que sea verdadero). El ejemplo ya genera uno (`puntaje_ejemplo.txt`).
2. **Una nota corta** (un párrafo, en un `.md` o en el mensaje): qué hiciste, qué entradas usaste, si usaste la longitud, y tus números de AUC y precisión en la mitad `prueba`.

Con ese archivo nosotros lo pasamos por la comparación de haces del tractograma completo (es un comando y tarda un minuto) y lo comparamos con los demás. **No tienes que tocar nada más del proyecto.**
Si usas Git, puedes subirlos directamente (sección 10); si no, mándalos por el grupo de WhatsApp (o por Drive).

### Las únicas reglas
1. **No uses** `hd_min_mm` ni `etiqueta_5mm` como entrada.
2. **Entrena solo con `entrenamiento`** y reporta en `prueba`.
3. **Si tu modelo usa la longitud, repórtalo también sin ella.**

Todo lo demás es libre.

---

## 9. Palabras que verás
- **Hilo / streamline:** una fibra reconstruida (una línea 3D).
- **GT (ground truth):** las fibras verdaderas del cerebro simulado.
- **Peso:** el número que un método le da a un hilo. 0 = lo eliminó.
- **Verdadero:** hilo a menos de 5 mm del GT (distancia de Hausdorff); es una aproximación y depende de ese 5.
- **AUC:** 0.5 = azar, 1 = perfecto. **Precisión:** % de verdaderos entre los hilos que conservas. **Tasa base:** 33.3 %, lo que obtendrías sin filtrar.
- **Haz:** un grupo de fibras con nombre (hay 21). **Dice:** qué tanto un haz recuperado se solapa con el real (0–1).

---

## 10. Si quieren integrarlo al repositorio (opcional; la puerta está abierta)
**No es obligatorio** y no hace falta para participar: la sección 8 basta. Pero si alguien tiene ganas, el proyecto está en un repositorio de Git y **es bienvenido a trabajar ahí**. Hay tres niveles, elige el que te acomode (y puedes cambiar después):

| Nivel | Qué haces | Qué necesitas |
|---|---|---|
| **1. Sin Git** | Entregas el puntaje y tu nota (sección 8) | nada |
| **2. Alguien sube por ti** | Mandas tu script y tu nota; otra persona los sube, y queda registrado con tu nombre | nada |
| **3. Integrado** | Trabajas dentro del repo y subes tus propios archivos | una cuenta de GitHub y pedir acceso en el grupo de WhatsApp |

### Nivel 3, paso a paso
1. El repositorio está en <https://github.com/MaximilianoVM/diffw-MRI>. Pide acceso de escritura en el grupo de WhatsApp, con tu usuario de GitHub (para poder subir; leer y descargar no lo necesita si el repo es público), y clónalo:
   ```
   git clone https://github.com/MaximilianoVM/diffw-MRI.git
   cd diffw-MRI
   ```
2. **Ya trae todo lo necesario**: la tabla (`out/modelos/tabla_hilos.csv`), los pesos de cada método, la etiqueta y los documentos. Se regenera con `python scripts/crear_tabla_modelos.py`. No tienes que correr los pasos 1–8 del proyecto.
3. Escribe tu modelo en **`scripts/modelo_<tu_nombre_o_idea>.py`**. Que lea la tabla con la ruta relativa `out/modelos/tabla_hilos.csv`, y que se pueda correr desde la raíz del proyecto. El `ejemplo_modelo.py` es un buen molde.
4. Escribe tu nota en **`docs/resultados/modelo_<tu_nombre_o_idea>.md`**: qué hiciste, qué entradas usaste, tus números en `prueba` (con y sin longitud), y cómo reproducirlo. En `pipeline.md` añade la línea del comando con una frase de explicación.
5. Sube tus cambios (una sola vez, antes de empezar, ejecuta `git config pull.rebase false`):
   ```
   git pull --no-rebase --no-edit        # trae lo último; hazlo siempre antes de subir
   git add scripts/modelo_xxx.py docs/resultados/modelo_xxx.md
   git commit -m "modelo xxx: qué hiciste, en una línea"
   git push
   ```
   - **Si `git push` dice «rejected»,** alguien subió algo mientras trabajabas: repite `git pull --no-rebase --no-edit` y luego `git push`. Es normal y no es un error.
   - **Si alguien más trabaja en otros archivos, no hay conflicto:** Git junta los cambios solo. Los conflictos solo aparecen si dos personas cambian **el mismo archivo en las mismas líneas**.
   - **Si Git dice `CONFLICT`:** no borres nada ni resuelvas a ciegas. Avisa en el grupo con el mensaje completo; es raro si cada quien trabaja en sus propios archivos.
   - Si algo sale raro con Git, **no pierdas tiempo**: manda los archivos por el grupo y alguien los sube (nivel 2).

### Reglas del repositorio (pocas)
- **Puedes modificar cualquier archivo** del proyecto, aunque lo haya escrito otra persona, para dejarlo actualizado; di qué cambiaste en el mensaje del commit. Si no estás seguro, pregunta.
- No cambies nombres ni muevas archivos de `out/`, ni la estructura de carpetas: otros scripts dependen de ellos. Antes de borrar o sobrescribir algo en `out/` o `data/`, pregunta.
- Sube solo código, `.md` y tablas pequeñas (menos de 5 MB). **No** subas tractogramas (`.tck`), cachés (`.npz`) ni los `puntaje_*.txt` (se regeneran con tu script).
- Cada script que corra desde la raíz con rutas relativas (`data/`, `out/`).

### Si usas un asistente de IA (Claude, etc.)
Puedes darle este texto: *«Lee `README.md`, `ACTUALIZACION.md` y `docs/para_continuar_modelos.md`. Mi tarea es construir un modelo que prediga `etiqueta_5mm` a partir de los pesos de `out/modelos/tabla_hilos.csv`. Reglas: no uses `hd_min_mm` ni `etiqueta_5mm` como entrada; entrena solo con `conjunto == "entrenamiento"` y reporta en `prueba`; si usas la longitud, reporta también sin ella; mi script va en `scripts/modelo_<nombre>.py` y mi nota en `docs/resultados/`; no hagas commit ni push sin que yo lo pida.»*

## 11. Si quieres profundizar (no es necesario para empezar)
El paquete incluye en `contexto/` tres documentos:
- `resumen_para_la_junta.md`: el estado completo del proyecto, fácil de leer.
- `modelo_y_normalizacion_hausdorff.md`: los modelos que ya se probaron, con todas las tablas.
- `tractograma_modelo_vs_gt.md`: la comparación de haces completa.

Si usas el repositorio completo (sección 10): `README.md` (mapa), `ACTUALIZACION.md` (estado), `docs/` (documentos) y `scripts/` (los pasos numerados 01–11). La tabla se regenera con `python scripts/crear_tabla_modelos.py`.

## 12. Si algo falla
- *El AUC del ejemplo no da 0.683:* revisa que `tabla_hilos.csv` esté completo (100 000 filas) y no lo hayas reordenado.
- *Memoria:* la tabla pesa 6 MB; cualquier laptop basta.
- *No entiendes algo:* pregunta en el grupo. Mejor preguntar que adivinar.

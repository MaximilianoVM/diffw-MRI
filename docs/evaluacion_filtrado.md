# Paso 10: evaluar cada método contra la etiqueta de Hausdorff

`bash scripts/10_evaluar.sh [E_mm=5]` → `out/evaluacion/{barrido_eps,mismo_n,auc}.csv` y un resumen en pantalla.
Solo numpy y pandas.

## Idea
- Etiqueta (paso 8): un hilo es **verdadero** si `hd_min < E` mm (por omisión 5); vacío = más de 10 mm = falso.
- Cada método (pasos 2, 3, 5, 6) da un peso por hilo; el paso 9 lo normaliza entre el máximo y filtra con ε.
- Este paso mide **si los hilos que el método conserva son los verdaderos**.

## Métricas
| Métrica | Pregunta que responde |
|---|---|
| precisión | de los hilos que conserva, ¿qué fracción es verdadera? (tasa base = 33.3 % si no filtra nada) |
| recall | de todos los hilos verdaderos, ¿qué fracción conserva? |
| F1 | resumen de los dos |
| lift | precisión / tasa base (1 = igual que no filtrar; >1 = filtra mejor que el azar) |
| AUC | ¿el peso, solo, ordena los hilos verdaderos por encima de los falsos? (0.5 = azar; <0.5 = al revés) |

Tres tablas: **(1)** barrido de ε sobre el peso normalizado; **(2)** mismo número de hilos conservados (los *n* de mayor peso),
que es la comparación justa entre métodos porque ε no significa lo mismo para todos; **(3)** AUC.
Se incluye la **longitud** del hilo como referencia («regla tonta»): un método debería superarla.

## Resultados (E = 5 mm; 33 349 hilos verdaderos, tasa base 33.3 %)
| Método | AUC |
|---|---|
| SIFT2 | 0.426 |
| COMMIT | 0.449 |
| LiFE | 0.601 |
| COMMIT2 | 0.634 |
| longitud sola | 0.652 |

Precisión conservando los *n* hilos de mayor peso:
| n | SIFT2 | COMMIT | LiFE | COMMIT2 | longitud |
|---|---|---|---|---|---|
| 10 000 | 13.4 % | 14.7 % | 42.9 % | 48.7 % | 31.7 % |
| 25 000 | 21.5 % | 25.3 % | 41.1 % | 52.5 % | 42.2 % |
| 50 000 | 28.7 % | 30.9 % | 40.8 % | 42.3 % | 42.4 % |

## Lectura
- **SIFT2 y COMMIT (sin regularización) están por debajo del azar** (AUC < 0.5): sus pesos más altos caen en hilos más falsos que
  la media. Filtrar con ellos empeora la proporción de verdaderos (con ε alto, lift < 1).
- **LiFE y COMMIT2 sí aportan** (AUC ≈ 0.60–0.63; lift hasta 1.2–1.6), con COMMIT2 mejor entre ~17 000 y 33 000 hilos conservados.
- **Ninguno supera de forma clara a la longitud sola** (AUC 0.652). Es coherente con el hallazgo previo con MDF (AUC por hilo:
  COMMIT 0.42, SIFT2 0.35, LiFE 0.66, COMMIT2 0.68, longitud 0.75). La etiqueta de Hausdorff da el mismo orden de métodos.
- Un ε fijo no es comparable entre métodos (con ε = 0.1: SIFT2 conserva 94 %, COMMIT 10 %, COMMIT2 0.6 %); por eso la tabla «mismo n».
- Esto solo evalúa **cada método por separado**. El modelo que combina los tres (paso 11) y la regla «≥ 2 de 3» son el siguiente paso.

## Cuidados
- El mismo vector sirve para entrenar y evaluar aquí **solo porque no hay entrenamiento** (se usa el peso tal cual). Cuando haya un modelo,
  hay que separar entrenamiento y prueba.
- Los pesos de COMMIT/COMMIT2 vienen de la Mac; se asume que están en el orden de `tracks_100k.tck` (tamaño correcto, no verificado de otra forma).

# Planificador TransMilenio — Proyecto final de Estructuras de Datos y Algoritmos

Es un motor en Python (carpeta `motor/`) que carga los tres CSV del profesor y responde consultas sobre la red de TransMilenio: estaciones, horarios, viajes y ranking. También permite editar la red, deshacer y rehacer, simular filas de abordaje y medir el rendimiento. La app (`app.py`) es una interfaz de consola que solo llama al motor.

Las estructuras de datos son propias: tabla hash, AVL, lista doblemente enlazada, pila, cola y montículo. De la biblioteca estándar solo se usan `csv` para leer archivos, `random` para las llegadas de la simulación y `time` para medir.

## Cómo ejecutar

Todo se corre desde la raíz del repositorio con Python 3.10 o superior.

```bash
python app.py                                  # la app
python -m unittest discover -s pruebas -v      # todas las pruebas (≈7 s)
python rendimiento.py                          # panel R11 (≈1 min) -> resultados_rendimiento.csv
```

## Estructura

```
datos/                 estaciones.csv, rutas.csv, horarios.csv (del profesor)
motor/
  __init__.py          expone Red
  red.py               Red: carga los 3 CSV y conecta R1–R10 (fachada del motor)
  tabla_hash.py        tabla hash con encadenamiento (R1, R5, R6, R7, R8)
  rangos.py            AVL de estaciones abiertas (R2, R3, R8)
  horarios.py          índice de horarios + merge sort + búsqueda binaria (R4)
  consultas.py         R1 estado, R2 autocompletar
  viajes.py            R5 planificador, R6 ranking
  edicion.py           R7 rutas como listas doblemente enlazadas
  estados.py           R8 cerrar / reabrir
  historial.py         R9 deshacer / rehacer con dos pilas
  simulacion.py        R10 fila de abordaje
  estructuras.py       Pila, Cola y Montículo propios
app.py                 interfaz de consola
rendimiento.py         panel de rendimiento R11 (todo el motor)
rendimiento_r3_r4.py   mediciones detalladas de R3 y R4
pruebas/               pruebas unitarias por requisito
```

> La carpeta `TransmilenioPlanner/` tiene la primera versión de R1 y R2 (búsqueda lineal y burbuja) y una copia de los datos. El motor ya no la usa: R1 y R2 viven ahora en `motor/consultas.py`. Se puede borrar cuando el grupo esté de acuerdo.

## Cómo se conectan las piezas

`Red` (en `motor/red.py`) es la única puerta de entrada al motor. Al cargar:

1. **Estaciones:** van a la tabla hash de estados (nombre → abierta) y al AVL de estaciones abiertas. Todas empiezan abiertas, porque el CSV no trae estado.
2. **Rutas:** cada ruta es una lista doblemente enlazada de paradas, guardada en una tabla hash (id → ruta).
3. **Horarios:** tabla hash (estación, ruta) → arreglo de minutos, ordenado con merge sort. En el CSV, unos 450 de los 1.927 pares vienen desordenados.
4. **Índices derivados**, que se actualizan con cada edición y cada deshacer/rehacer:
   - `rutas_por_estacion`: estación → rutas que paran ahí (lo usa R5).
   - `buses_por_estacion`: estación → buses al día que paran ahí (lo usa R6).

**Regla de estación cerrada (R8):** no aparece en R2, R3 ni R6. En R1 aparece como cerrada. R4 y R10 no la aceptan, y R5 no la usa para subir, bajar ni transbordar. Un bus sí pasa por ella sin detenerse, así que cuenta como parada recorrida.

**Nombres:** se normalizan a mayúsculas y espacios simples, así que `"  calle   26 "` equivale a `"CALLE 26"`.

---

## R1 — Estado de una estación

**Archivo:** `motor/consultas.py` (`estado`). Pruebas: `pruebas/test_r1_r2.py`.

- **Qué se hizo:** con el nombre exacto, responde `(existe, abierta)`. La app sugiere nombres con R2 cuando la estación no existe.
- **Qué se usó:** la tabla hash de estados de R8.
- **Considerado y descartado:** la primera versión recorría la lista de estaciones, que es O(n) por consulta. Otra opción era buscar en el AVL, que es O(log n) y no distingue "cerrada" de "no existe".
- **Big-O:** O(1) esperado. Aquí n son las estaciones, pero el costo no depende de n. Solo depende del largo del nombre, que está acotado.

## R2 — Autocompletar

**Archivo:** `motor/consultas.py` (`autocompletar`). Pruebas: `pruebas/test_r1_r2.py`.

- **Qué se hizo:** muestra hasta k estaciones abiertas que empiezan por el prefijo, en orden alfabético.
- **Qué se usó:** el AVL de estaciones abiertas de R3, recorrido en inorden con poda. Los nombres con un mismo prefijo forman un bloque contiguo en orden alfabético. Por eso solo se baja a la izquierda si el nodo no está antes del bloque, solo se va a la derecha si todavía no se pasó el bloque, y el recorrido para al juntar k nombres. Como R8 saca las cerradas del AVL, nunca aparecen.
- **Considerado y descartado:**
  - **Lista recorrida completa + burbuja** (primera versión): O(n + m²).
  - **Trie:** daría O(|p| + k), pero es una estructura más que habría que mantener sincronizada con cada cierre, reapertura y deshacer.
  - **Orden "natural"** (CALLE 19 antes que CALLE 100): el enunciado pide orden alfabético y R3 usa el mismo orden, así que se mantuvo el alfabético.
- **Big-O:** O(log n + k), con n = estaciones abiertas y k = resultados pedidos.

## R3 — Rango alfabético

**Archivo:** `motor/rangos.py`. El detalle está en [README_R3_R4.md](README_R3_R4.md).

- **Qué se hizo:** muestra las estaciones abiertas entre dos nombres, inclusive. Un rango invertido devuelve `[]`.
- **Qué se usó:** AVL de estaciones abiertas, recorrido en inorden con poda.
- **Considerado y descartado:** una lista ordenada con búsqueda binaria también consulta en O(log n + k), pero cada cierre o reapertura costaría O(n).
- **Big-O:** consulta O(log n + k), con n = estaciones abiertas y k = resultados. Abrir o cerrar cuesta O(log n).

## R4 — Próximo bus

**Archivo:** `motor/horarios.py`. El detalle está en [README_R3_R4.md](README_R3_R4.md).

- **Qué se hizo:** dada una estación, una ruta y una hora, devuelve la hora del siguiente bus. Incluye un bus a la hora exacta. Si no hay más ese día, devuelve `None`.
- **Qué se usó:** tabla hash (estación, ruta) → minutos ordenados con merge sort, y búsqueda binaria del primer horario mayor o igual a la hora pedida.
- **Integración:** `Red` primero revisa que la estación esté abierta y que la ruta todavía pare ahí. Si R7 quitó la parada, la respuesta es `None`.
- **Considerado y descartado:** escanear todos los horarios en cada consulta, que cuesta O(h).
- **Big-O:** O(log h + L), con h = horarios del par y L = paradas de la ruta (la revisión de R7). La carga cuesta O(H + Σ hᵢ log hᵢ).

## R5 — Planificador de viajes

**Archivo:** `motor/viajes.py` (`planificar`). Pruebas: `pruebas/test_r5_r6.py`.

- **Qué se hizo:** busca el viaje directo o con un transbordo que recorre **menos paradas**. Dice qué ruta tomar, dónde bajarse y dónde cambiar, y muestra las estaciones de cada tramo. Si hay empate en paradas, prefiere el directo.
- **Cómo funciona:**
  1. **Desde el origen:** recorre hacia adelante cada ruta que para en el origen. Para cada estación alcanzada guarda, en una tabla hash, la menor cantidad de paradas y la ruta que la logra.
  2. **Hacia el destino:** hace lo mismo hacia atrás desde el destino, con las rutas que paran ahí.
  3. **Directo:** si el destino aparece en la tabla del origen, hay viaje directo.
  4. **Transbordo:** para cada estación abierta *s* que está en las dos tablas con rutas distintas, el total es paradas(origen→s) + paradas(s→destino). Se queda el menor. Si en *s* la mejor ruta de los dos lados es la misma, ya existe un directo igual o mejor, así que no se pierde ningún óptimo.
- **Qué se usó:** las listas doblemente enlazadas de R7 (se recorre `sig` hacia adelante y `ant` hacia atrás), el índice `rutas_por_estacion` y tablas hash propias.
- **Considerado y descartado:**
  - **Probar todos los pares de rutas:** cuesta O(R_total² · L). Se dejó solo como verificador en las pruebas: `optimo_fuerza_bruta` compara el resultado en 49 pares reales.
  - **BFS sobre un grafo de estaciones:** minimiza paradas pero no controla el número de transbordos. Habría que hacer BFS sobre estados (estación, ruta), que es más complejo de lo que pide "máximo un transbordo".
  - **Minimizar transbordos antes que paradas:** el enunciado pide menos paradas.
- **Supuestos:** las rutas tienen sentido, así que solo se avanza en el orden del CSV. Origen igual a destino, o una estación inexistente o cerrada, devuelve `None`.
- **Big-O:** O(R·L) esperado, con R = rutas que paran en el origen o el destino y L = paradas por ruta (≤ 33 en los datos). No depende del total de estaciones n, como muestra el panel R11.

## R6 — Ranking de estaciones

**Archivo:** `motor/viajes.py` (`ranking`). Pruebas: `pruebas/test_r5_r6.py`.

- **Qué se hizo:** muestra las k estaciones abiertas por donde pasan más buses al día. "Buses al día" es el número de filas de `horarios.csv` de esa estación, sumando solo las rutas que hoy paran ahí. Con empate, va primero el nombre alfabéticamente menor.
- **Qué se usó:**
  - El índice `buses_por_estacion`, calculado al cargar. Se actualiza en O(1) esperado cuando R7 agrega o quita una parada, y también al deshacer o rehacer.
  - Un **montículo de tamaño k** con la peor de las elegidas en la raíz. Cada estación se compara con la raíz y, si es mejor, la reemplaza.
- **Considerado y descartado:**
  - **Ordenar todas las estaciones:** O(n log n).
  - **Recalcular los conteos en cada consulta recorriendo los horarios:** O(H).
  - **Montículo de las n estaciones y extraer k:** O(n + k log n), pero usa O(n) de memoria extra.
- **Big-O:** O(n log k), con n = estaciones y k = tamaño del ranking. Memoria extra O(k).

## R7 — Agregar parada, quitar parada y recorrido

**Archivo:** `motor/edicion.py`. El detalle está en [Readme_R7_R8.md](Readme_R7_R8.md).

- **Qué se usó:** una lista doblemente enlazada por ruta, en una tabla hash. Cada edición devuelve un registro que R9 guarda.
- **Integración:** `Red` actualiza `rutas_por_estacion` y `buses_por_estacion` en cada edición, deshacer y rehacer.
- **Big-O:** agregar, quitar y recorrido cuestan O(L), con L = paradas de la ruta. Revertir y rehacer cuestan O(1) más la actualización de índices, que es O(R_e) con R_e = rutas de esa estación.

## R8 — Cerrar y reabrir estaciones

**Archivo:** `motor/estados.py`. El detalle está en [Readme_R7_R8.md](Readme_R7_R8.md).

- **Qué se usó:** tabla hash de estados y AVL de abiertas. Cerrar saca la estación del AVL y reabrir la vuelve a meter.
- **Big-O:** consultar cuesta O(1) esperado. Cerrar y reabrir cuestan O(log n), con n = estaciones abiertas.

## R9 — Deshacer y rehacer

**Archivo:** `motor/historial.py` y `motor/estructuras.py` (`Pila`). Pruebas: `pruebas/test_r9_r10.py`.

- **Qué se hizo:** deshace y rehace cualquier cierre, reapertura, parada agregada o parada quitada, en orden LIFO.
- **Cómo funciona:**
  - Dos pilas propias, implementadas con nodos enlazados.
  - Cada acción válida apila su registro en "deshacer" y vacía "rehacer", porque una acción nueva invalida el futuro.
  - Deshacer aplica el inverso del registro (`revertir` de R7 o R8), actualiza los índices de `Red` y pasa el registro a "rehacer". Rehacer hace lo contrario.
  - Una acción que falla con `ValueError` no se registra.
  - Si revertir falla, la pila queda intacta, porque se lee la cima antes de desapilar.
- **Considerado y descartado:**
  - **Guardar una copia de toda la red en cada acción:** O(n + P) de tiempo y memoria por acción.
  - **Una sola lista con un cursor:** funciona, pero el enunciado pide pilas, y dos pilas hacen explícita la regla de vaciar "rehacer".
  - **Pila sobre la lista de Python:** se prefirió la pila enlazada para que cada operación sea O(1) sin depender del redimensionamiento de la lista.
- **Big-O:** apilar y desapilar cuestan O(1). Un deshacer o rehacer completo cuesta O(log n) si es un cierre o reapertura (n = estaciones abiertas), y O(1) + O(R_e) si es una edición de ruta.

## R10 — Simulación de la fila de abordaje

**Archivo:** `motor/simulacion.py` y `motor/estructuras.py` (`Cola`). Pruebas: `pruebas/test_r9_r10.py`.

- **Qué se hizo:** simula la fila de una estación entre dos horas.
  - **Buses:** salen a las horas reales de `horarios.csv` para la ruta elegida, o cada N minutos si no se da ruta.
  - **Pasajeros:** llegan al azar (proceso de Poisson con semilla, así que el resultado es reproducible) y hacen fila. Cada bus sube hasta `cupo` pasajeros en orden de llegada (FIFO).
  - **Reporte:** pasajeros, abordados, los que siguen en fila, espera promedio y máxima, fila más larga y detalle por bus.
- **Qué se usó:** una cola enlazada propia y una mezcla de dos secuencias ordenadas (llegadas y salidas), como en el paso de mezcla de merge sort.
- **Considerado y descartado:**
  - **Simular minuto a minuto:** O(T · P) y depende de la resolución del tiempo.
  - **Lista de Python con `pop(0)`:** cada desencolar costaría O(P).
  - **Cola de prioridad de eventos:** O((P + B) log(P + B)). No hace falta, porque llegadas y salidas ya vienen ordenadas.
- **Big-O:** O(P + B), con P = pasajeros y B = buses de la ventana. Cada pasajero entra y sale de la cola una vez. Obtener las salidas de la ruta cuesta O(log h) con búsqueda binaria.

## R11 — Panel de rendimiento

**Archivo:** `rendimiento.py`. Los resultados se guardan en `resultados_rendimiento.csv`. Para R3 y R4 por separado está `rendimiento_r3_r4.py`.

- **Qué se hizo:**
  - Genera redes sintéticas de n = 500, 1000, 2000 y 4000 estaciones con la misma densidad: n/4 rutas, 12 paradas por ruta y 24 buses por parada.
  - Mide cada operación del motor como el mínimo de 7 tandas, con el recolector de basura apagado, y calcula el factor tiempo(2n) / tiempo(n).
  - Aparte, duplica h para R4 y P para R10, que son las variables de las que dependen.
  - Las operaciones que modifican la red se miden junto con su inverso (por ejemplo, agregar + deshacer) para que la red no cambie de tamaño entre repeticiones.
- **Cómo leer el factor:** ≈1,0 significa O(1) o "no depende de n"; ≈1,05–1,15 significa O(log n); ≈2,0 significa lineal.

Resultados en un portátil con Python 3.14 (factor al pasar de n a 2n):

| Operación | Big-O | 500→1000 | 1000→2000 | 2000→4000 |
|---|---|---|---|---|
| Carga de los 3 CSV | O(H log h), H ∝ n | 1,90 | 1,98 | 1,81 |
| R1 estado | O(1) | 0,99 | 1,00 | 0,98 |
| R2 autocompletar (k=5) | O(log n + k) | 1,04 | 0,99 | 1,07 |
| R3 rango (k=4) | O(log n + k) | 0,97 | 1,04 | 1,06 |
| R4 próximo bus | O(log h + L) | 0,98 | 0,99 | 1,00 |
| R5 viaje | O(R·L) | 1,30 | 0,96 | 0,85 |
| R6 ranking (k=10) | O(n log k) | **1,99** | **2,00** | **2,01** |
| R7 recorrido / agregar / quitar | O(L) | ≈1,0 | ≈1,0 | ≈1,0 |
| R8 cerrar + reabrir | O(log n) | 0,94 | 1,08 | 1,02 |
| R9 deshacer + rehacer | O(log n) | 0,91 | 1,16 | 1,00 |

| Variable duplicada | Operación | Factores |
|---|---|---|
| h: 1000 → 16000 | R4 | 1,04 · 1,05 · 1,02 · 1,03 (logarítmico) |
| P: 2000 → 32000 | R10 | 2,03 · 2,04 · 2,00 · 2,04 (lineal) |

**Lectura:**
- R6 y la carga crecen linealmente con n, como se esperaba.
- R1, R4, R5 y R7 no dependen de n.
- R2, R3, R8 y R9 son O(log n): con n ≤ 4000 el árbol tiene a lo sumo unos 14 niveles, así que el crecimiento casi no se nota.
- R5 varía entre tamaños porque R·L depende de cuántas rutas pasan por el origen y el destino elegidos al azar, no de n.

## Pruebas

En `pruebas/` hay 41 pruebas:

- `test_r1_r2.py`: R1 y R2, con fuerza bruta para el autocompletar.
- `test_r3_r4.py`: R3 y R4.
- `test_r5_r6.py`: R5 contra un óptimo de fuerza bruta y R6 contra ordenar todo.
- `test_r7.py` y `test_r8.py`: R7 y R8.
- `test_r9_r10.py`: pilas, colas, montículo, deshacer/rehacer mezclando los cuatro tipos de acción, y la simulación.

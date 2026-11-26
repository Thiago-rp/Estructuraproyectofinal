# R7 y R8 — Edición de la red

Ejecutar desde la raíz: `python -m unittest pruebas.test_r7 pruebas.test_r8 -v`.

Todos los datos (estaciones, rutas, horarios) salen de los CSV del profesor en `datos/`.

---

## R7 — Agregar parada, quitar parada y recorrido

**Archivos:** `motor/edicion.py` (rutas) y `motor/tabla_hash.py` (tabla hash propia). Pruebas: `pruebas/test_r7.py`.

### Qué se hizo
- Cada ruta de `rutas.csv` se carga como una lista doblemente enlazada de paradas, respetando la columna `orden`.
- Las rutas se guardan en una tabla hash propia (id de ruta → ruta), con encadenamiento y expansión al pasar de factor de carga 0,75.
- `agregar_parada(ruta, antes, despues, nueva)` inserta una estación entre dos paradas consecutivas.
- `quitar_parada(ruta, estacion)` quita una parada.
- `recorrido(ruta)` devuelve la lista de paradas de ida (cabeza a cola) y de vuelta (cola a cabeza), siguiendo los punteros `sig` y `ant`.
- Al cargar, se verifica que cada estación de `rutas.csv` exista en `estaciones.csv`, y solo se pueden agregar estaciones que estén en ese archivo.
- Cada edición devuelve un registro (`('agregar_parada', ruta, nodo)` o `('quitar_parada', ruta, nodo)`). `revertir` y `rehacer` lo aplican en sentido inverso o directo, para que R9 los use con sus pilas.

### Qué se usó
Lista doblemente enlazada, tabla hash propia con encadenamiento, y el módulo `csv` solo para leer archivos.

### Qué se consideró y se descartó
- **Arreglo (lista de Python) por ruta:** insertar o quitar en medio obliga a desplazar elementos, y para recorrer al revés habría que invertirlo. Con la lista doblemente enlazada, enlazar y desenlazar un nodo ya localizado es O(1) y recorrer al revés es seguir `ant`.
- **Lista simplemente enlazada:** no permite recorrer en sentido contrario ni desenlazar un nodo sin volver a buscar su anterior.
- **Tabla hash de paradas dentro de cada ruta** para buscar en O(1): se descartó porque las rutas tienen entre 3 y 33 paradas, y mantener un índice por ruta con cada edición y cada deshacer agrega complejidad que no se justifica.
- **Inventar horarios para una parada nueva:** se descartó porque todos los datos deben salir de los CSV. La parada nueva queda sin horarios en esa ruta, y `proximo_bus` para ese par devuelve `None`. Si se vuelve a agregar una estación que ya estaba en la ruta en `rutas.csv`, se recuperan sus horarios originales.

### Supuestos
- `antes` y `despues` deben existir en la ruta y ser consecutivas, en ese orden.
- La estación nueva debe existir en `estaciones.csv` y no estar ya en esa ruta.
- Una ruta debe conservar al menos 2 paradas.
- "Recorrido en ambos sentidos" se interpreta como ida y vuelta de la misma ruta (cabeza a cola y cola a cabeza).
- Los errores se informan con `ValueError` y un mensaje claro.
- `revertir` solo es válido en orden inverso al de las ediciones (LIFO), que es lo que garantiza una pila.

### Big-O
En R7, **n = número de paradas de la ruta** editada (en los datos, n ≤ 33).

| Operación | Costo | Por qué |
|---|---|---|
| Cargar rutas | O(R) esperado | R = filas de `rutas.csv`; cada fila se procesa en O(1) esperado |
| Buscar una ruta por id | O(1) esperado | tabla hash |
| `agregar_parada` | O(n) | tres búsquedas lineales en la ruta (antes, después, duplicado) y enlace O(1) |
| `quitar_parada` | O(n) | una búsqueda lineal y desenlace O(1) |
| `recorrido` | O(n) | se recorre la ruta una vez en cada sentido |
| `revertir` / `rehacer` | O(1) esperado | solo se enlaza o desenlaza el nodo guardado (más buscar la ruta) |

Memoria: O(R) para las paradas más la tabla hash.

---

## R8 — Cerrar y reabrir estaciones

**Archivos:** `motor/estados.py` y `motor/tabla_hash.py`. Pruebas: `pruebas/test_r8.py`.

### Qué se hizo
- Una tabla hash propia guarda el estado de cada estación (nombre → abierta o cerrada). Al cargar `estaciones.csv`, todas empiezan abiertas.
- `cerrar(nombre)` y `reabrir(nombre)` cambian el estado y mantienen al día el AVL de estaciones abiertas de R3 (`IndiceRangos.cerrar` / `abrir`). Así una estación cerrada deja de aparecer en los rangos sin modificar el archivo de R3.
- `abierta(nombre)` dice si una estación existe y está abierta. `puede_usar(nombre)` es la regla para subir, bajar y hacer transbordo: solo se puede en estaciones abiertas.
- Cada acción devuelve un registro (`('cerrar', nombre)` o `('reabrir', nombre)`). `revertir` y `rehacer` lo aplican para que R9 los use con sus pilas.

### Qué se usó
Tabla hash propia (la misma de R7) y el AVL de R3.

### Qué se consideró y se descartó
- **Borrar la estación de las estructuras al cerrarla:** se pierde su información y reabrir exigiría reconstruirla. Se guarda un estado y se conserva la estación.
- **Búsqueda lineal del estado en una lista de estaciones** (como se hacía en la primera versión de R1): cuesta O(n) por consulta. La tabla hash lo baja a O(1) esperado.
- **Usar solo el AVL para saber si una estación está abierta:** consultar costaría O(log n) y no distinguiría entre una estación cerrada y una que no existe. La tabla hash sí lo distingue.
- **Una bandera de cerrada dentro de cada nodo del AVL:** las búsquedas de rango tendrían que recorrer nodos cerrados. Sacar la estación del AVL deja el rango en O(log n + k).

### Supuestos
- Un bus sigue pasando por una estación cerrada, pero no se detiene en ella.
- Cerrar una estación que ya está cerrada, reabrir una que ya está abierta, o usar un nombre que no está en `estaciones.csv` produce `ValueError`.

### Big-O
En R8, **n = número de estaciones abiertas** (las que están en el AVL) y **E = estaciones de `estaciones.csv`**.

| Operación | Costo | Por qué |
|---|---|---|
| Cargar estaciones | O(E log E) esperado | E inserciones en la tabla (O(1) esperado cada una) y en el AVL (O(log n) cada una) |
| `abierta` / `puede_usar` / `existe` | O(1) esperado | consulta a la tabla hash |
| `cerrar` | O(log n) | consulta O(1) esperado en la tabla y eliminación en el AVL |
| `reabrir` | O(log n) | consulta O(1) esperado en la tabla e inserción en el AVL |
| `revertir` / `rehacer` | O(log n) | un cambio de estado en la tabla y en el AVL |

Memoria: O(E).

---

## Integración con el resto del motor

`motor/red.py` (`Red`) conecta R7 y R8 con el resto. La app y el panel solo llaman a `Red`.

- **R9 (deshacer y rehacer):** `Red` guarda en las pilas de `motor/historial.py` cada registro que devuelven `agregar_parada`, `quitar_parada`, `cerrar` y `reabrir`. Deshacer y rehacer llaman a `revertir` o `rehacer` del objeto que creó el registro, en orden LIFO.
- **R1, R2, R3, R5 y R6:** usan `EstadoEstaciones` y el AVL de abiertas. Una estación cerrada sale como cerrada en R1, no aparece en R2, R3 ni R6, y en R5 no se usa para subir, bajar ni transbordar.
- **R4 y R6:** cuando una parada sale o entra a una ruta (también al deshacer o rehacer), `Red` actualiza `rutas_por_estacion` y `buses_por_estacion`, y `proximo_bus` responde `None` si la ruta ya no para en esa estación.
- **R11:** `rendimiento.py` mide agregar, quitar, cerrar y reabrir junto con su inverso, para que la red no cambie de tamaño.

### Ejemplo de uso

```python
# Uso directo de las clases de R7 y R8 (en la app todo pasa por motor.Red)
from motor.edicion import RedRutas
from motor.estados import EstadoEstaciones
from motor.rangos import IndiceRangos

rutas = RedRutas()
rutas.cargar_estaciones("datos/estaciones.csv")
rutas.cargar("datos/rutas.csv")

indice = IndiceRangos()
estados = EstadoEstaciones(indice)
estados.cargar("datos/estaciones.csv")

reg = rutas.agregar_parada("1-1", "UNIVERSIDADES", "RECINTO FERIAL", "CAN")
ida, vuelta = rutas.recorrido("1-1")
rutas.revertir(reg)

reg = estados.cerrar("CALLE 26")
estados.revertir(reg)
```

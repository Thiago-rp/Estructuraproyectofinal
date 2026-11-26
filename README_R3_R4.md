# R3 y R4 — Rangos y horarios

Ejecutar desde la raíz: `python -m unittest discover -s pruebas -v`.

## R3
AVL de estaciones abiertas, recorrido inorden con poda de subárboles. Consulta O(log n + k), n estaciones abiertas, k resultados; abrir/cerrar O(log n). Alternativa: lista ordenada con búsqueda binaria y consulta O(log n + k), pero inserción/eliminación O(n). El AVL evita ese coste. Se asumen nombres normalizados y límites inclusivos; rango invertido devuelve [].

## R4
Tabla hash propia con encadenamiento y expansión; cada par estación/ruta tiene un arreglo de minutos ordenado mediante merge sort propio. Búsqueda binaria del primer horario >= consulta. Consulta del índice O(log h) esperado para nombres de longitud acotada, h horarios del par; peor caso O(p + log h), p pares. `Red.proximo_bus` añade dos comprobaciones: que la estación esté abierta (tabla hash de estados, O(1) esperado) y que la ruta siga parando ahí (búsqueda en la lista de la ruta, O(L)). En total cuesta O(log h + L). Carga de H horarios: O(H + sum(h_i log h_i)) esperado, memoria O(H+p). Alternativa descartada: escanear horarios O(h) por consulta. Se conservan horas superiores a 23:59 como parte del día de servicio; no hay salto automático al siguiente día. Sin resultado devuelve None. Se incluye el bus a la hora exacta.

## Integración

- `motor/red.py` (`Red`) usa `IndiceRangos` como índice único de estaciones abiertas: R2 (autocompletar) y R3 lo recorren, y R8 lo actualiza al cerrar, reabrir, deshacer y rehacer.
- `Red.proximo_bus` revisa primero que la estación esté abierta (R8) y que la ruta siga parando ahí (R7). Si no, devuelve `None` sin consultar `IndiceHorarios`.
- `IndiceHorarios` también lo usan R6 (`buses`: buses al día por par) y R10 (`horarios`: salidas reales de una ruta).
- La carga se hace una sola vez al crear `Red`, y `agregar` no se vuelve a llamar después de `preparar`.
- `rendimiento_r3_r4.py` mide R3 y R4 con n = h. El panel completo de R11 está en `rendimiento.py`.

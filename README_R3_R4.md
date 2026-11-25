# R3 y R4 — Rangos y horarios

Ejecutar desde la raíz: `python -m unittest discover -s pruebas -v`.

## R3
AVL de estaciones abiertas, recorrido inorden con poda de subárboles. Consulta O(log n + k), n estaciones abiertas, k resultados; abrir/cerrar O(log n). Alternativa: lista ordenada con búsqueda binaria y consulta O(log n + k), pero inserción/eliminación O(n). El AVL evita ese coste. Se asumen nombres normalizados y límites inclusivos; rango invertido devuelve [].

## R4
Tabla hash propia con encadenamiento y expansión; cada par estación/ruta tiene un arreglo de minutos ordenado mediante merge sort propio. Búsqueda binaria del primer horario >= consulta. Consulta del índice O(log h) esperado para nombres de longitud acotada, h horarios del par; peor caso O(p + log h), p pares. La Red de ejemplo añade comprobación AVL O(log n), n estaciones abiertas, y comprobación hash del par vigente. El grupo puede usar su tabla hash de estados de R1 para hacer esa comprobación en O(1) esperado. Carga de H horarios: O(H + sum(h_i log h_i)) esperado, memoria O(H+p). Alternativa descartada: escanear horarios O(h) por consulta. Se conservan horas superiores a 23:59 como parte del día de servicio; no hay salto automático al siguiente día. Sin resultado devuelve None. Se incluye el bus a la hora exacta.

## Integración
Copiar rangos.py y horarios.py al motor grupal; red.py y __init__.py aquí son exclusivamente de demostración, no reemplazar los del grupo. Incorporar la carga y los métodos rango/proximo_bus a Red existente. Coordinar con R2 para compartir el AVL si conviene; con R8/R9 para invocar cerrar/abrir en el índice tras cada cambio, incluso deshacer y rehacer. Coordinar R7 para que el índice de pares vigentes refleje ediciones de rutas y acordar el tratamiento de horarios de nuevas paradas; el ejemplo solo carga pares iniciales. No llamar agregar en IndiceHorarios después de preparar sin reordenar. Verificar el enunciado escrito (no adjunto) para formatos de retorno, límites, normalización y reglas de horas. No se implementa el resto del motor, ni el panel R11 grupal.

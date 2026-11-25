"""R1 (estado de una estación) y R2 (autocompletar).

R1 consulta la tabla hash de estados de R8 (`EstadoEstaciones`).
R2 recorre en inorden el AVL de estaciones abiertas de R3 (`IndiceRangos`),
podando las ramas que no pueden contener el prefijo y parando al llegar a k.
"""


def normalizar(nombre):
    return ' '.join(nombre.strip().upper().split())


def estado(estados, nombre):
    """R1: (existe, abierta) para el nombre exacto. O(1) esperado."""
    nombre = normalizar(nombre)
    return estados.existe(nombre), estados.abierta(nombre)


def _prefijo(nodo, prefijo, k, salida):
    if nodo is None or len(salida) >= k:
        return
    nombre = nodo.nombre
    empieza = nombre.startswith(prefijo)
    # Los nombres que empiezan por el prefijo forman un bloque contiguo que
    # arranca en `prefijo`. A la izquierda solo puede haber coincidencias si
    # este nodo no está antes del bloque.
    if prefijo <= nombre:
        _prefijo(nodo.izq, prefijo, k, salida)
    if empieza and len(salida) < k:
        salida.append(nombre)
    # A la derecha solo puede haber coincidencias si aún no se pasó el bloque.
    if nombre < prefijo or empieza:
        _prefijo(nodo.der, prefijo, k, salida)


def autocompletar(indice, prefijo, k):
    """R2: hasta k estaciones abiertas que empiezan por `prefijo`, en orden
    alfabético. O(log n + k), n = estaciones abiertas."""
    salida = []
    if k > 0:
        _prefijo(indice.raiz, normalizar(prefijo), k, salida)
    return salida

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
    """R2: hasta k estaciones abiertas que empiezan por `prefijo`, ordenadas numéricamente."""
    salida = []
    if k > 0:
        _prefijo(indice.raiz, normalizar(prefijo), k, salida)
    
    # --- FUNCIÓN AUXILIAR PARA ORDEN NUMÉRICO (para que 19 vaya antes de 100) ---
    def obtener_clave_orden(nombre):
        partes = nombre.split()
        texto_base = ""
        numero = 0
        encontro_numero = False
        for parte in partes:
            es_digito = True
            for c in parte:
                if c < '0' or c > '9':
                    es_digito = False
                    break
            if es_digito and len(parte) > 0:
                numero = int(parte)
                encontro_numero = True
                break
            else:
                texto_base += parte + " "
        return (texto_base.strip(), numero) if encontro_numero else (nombre, 0)

    # Ordenamiento de burbuja sobre la lista resultante para asegurar orden numérico correcto
    n = len(salida)
    for i in range(n):
        for j in range(0, n - i - 1):
            if obtener_clave_orden(salida[j]) > obtener_clave_orden(salida[j + 1]):
                salida[j], salida[j + 1] = salida[j + 1], salida[j]

    return salida[:k]raiz, normalizar(prefijo), k, salida)
    return salida

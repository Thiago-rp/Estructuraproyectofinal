"""R5 (planificador de viajes) y R6 (ranking de estaciones)."""
from motor.tabla_hash import TablaHash
from motor.estructuras import Monticulo


class Tramo:
    def __init__(self, ruta, sube, baja, paradas, estaciones):
        self.ruta = ruta
        self.sube = sube
        self.baja = baja
        self.paradas = paradas          # paradas recorridas en este tramo
        self.estaciones = estaciones    # de `sube` a `baja`, ambas incluidas

    def __repr__(self):
        return f'Tramo({self.ruta}: {self.sube} -> {self.baja}, {self.paradas} paradas)'


class Viaje:
    def __init__(self, tramos):
        self.tramos = tramos
        self.paradas = sum(t.paradas for t in tramos)
        self.transbordos = len(tramos) - 1

    @property
    def directo(self):
        return self.transbordos == 0

    def __repr__(self):
        return f'Viaje({self.tramos}, total={self.paradas})'


def _alcance(rutas, ids_rutas, estacion, hacia_adelante):
    """Desde `estacion`, recorre cada ruta que pasa por ella (hacia adelante
    para el origen, hacia atrás para el destino) y guarda, por estación
    alcanzada, la menor cantidad de paradas y la ruta que la logra.
    O(R·L): R rutas que pasan por la estación, L paradas por ruta."""
    mejor = TablaHash()     # estación -> [paradas, id_ruta]
    vistas = []             # para poder recorrer las claves de `mejor`
    for id_ruta in ids_rutas:
        nodo = rutas.rutas.obtener(id_ruta).buscar(estacion)
        if nodo is None:
            continue
        paradas = 0
        nodo = nodo.sig if hacia_adelante else nodo.ant
        while nodo is not None:
            paradas += 1
            actual = mejor.obtener(nodo.estacion)
            if actual is None:
                mejor.poner(nodo.estacion, [paradas, id_ruta])
                vistas.append(nodo.estacion)
            elif paradas < actual[0]:
                actual[0], actual[1] = paradas, id_ruta
            nodo = nodo.sig if hacia_adelante else nodo.ant
    return mejor, vistas


def _tramo(rutas, id_ruta, sube, baja):
    nodo = rutas.rutas.obtener(id_ruta).buscar(sube)
    estaciones = [nodo.estacion]
    while nodo.estacion != baja:
        nodo = nodo.sig
        estaciones.append(nodo.estacion)
    return Tramo(id_ruta, sube, baja, len(estaciones) - 1, estaciones)


def planificar(rutas, rutas_por_estacion, estados, origen, destino):
    """R5: viaje directo o con un transbordo que recorre menos paradas.

    Solo se sube, se baja y se transborda en estaciones abiertas; un bus sí
    pasa por estaciones cerradas (cuentan como paradas recorridas). Con
    empate en paradas se prefiere el viaje directo. Devuelve None si no hay
    viaje posible. O(R·L) esperado.
    """
    if origen == destino or not estados.abierta(origen) or not estados.abierta(destino):
        return None
    desde_origen, vistas = _alcance(rutas, rutas_por_estacion.obtener(origen) or [], origen, True)
    hasta_destino, _ = _alcance(rutas, rutas_por_estacion.obtener(destino) or [], destino, False)

    mejor_total, mejor_plan = None, None
    directo = desde_origen.obtener(destino)
    if directo is not None:
        mejor_total, mejor_plan = directo[0], (directo[1], None, None)

    for s in vistas:
        if s == destino or s == origen or not estados.abierta(s):
            continue
        a, b = desde_origen.obtener(s), hasta_destino.obtener(s)
        # Si es la misma ruta, ya existe el viaje directo con igual o menos paradas.
        if b is None or a[1] == b[1]:
            continue
        total = a[0] + b[0]
        if mejor_total is None or total < mejor_total:
            mejor_total, mejor_plan = total, (a[1], s, b[1])

    if mejor_plan is None:
        return None
    r1, transbordo, r2 = mejor_plan
    if transbordo is None:
        return Viaje([_tramo(rutas, r1, origen, destino)])
    return Viaje([_tramo(rutas, r1, origen, transbordo),
                  _tramo(rutas, r2, transbordo, destino)])


def _peor(a, b):
    """a va más abajo en el ranking que b: menos buses, o empate y nombre mayor."""
    return a[1] < b[1] or (a[1] == b[1] and a[0] > b[0])


def ranking(estaciones, conteos, estados, k):
    """R6: las k estaciones abiertas por donde pasan más buses al día.

    Montículo de tamaño k con la peor de las elegidas en la raíz: cada
    estación se compara con la raíz y, si es mejor, la reemplaza.
    O(n log k), n = estaciones. Devuelve [(nombre, buses), ...] de mayor a menor.
    """
    if k <= 0:
        return []
    monticulo = Monticulo(_peor)
    for nombre in estaciones:
        if not estados.abierta(nombre):
            continue
        candidato = (nombre, conteos.obtener(nombre) or 0)
        if len(monticulo) < k:
            monticulo.insertar(candidato)
        elif _peor(monticulo.raiz(), candidato):
            monticulo.reemplazar_raiz(candidato)
    salida = []
    while len(monticulo):
        salida.append(monticulo.extraer())
    salida.reverse()
    return salida

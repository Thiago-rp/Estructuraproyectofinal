"""Red: punto de entrada del motor. Carga los 3 CSV y conecta R1–R10.

La app (app.py) y el panel de rendimiento (rendimiento.py) solo llaman a
los métodos de esta clase.
"""
import csv
from pathlib import Path

from motor.tabla_hash import TablaHash
from motor.rangos import IndiceRangos
from motor.horarios import IndiceHorarios, minutos, formato, limite_inferior
from motor.estados import EstadoEstaciones
from motor.edicion import RedRutas
from motor.historial import Historial
from motor import consultas, viajes, simulacion

normalizar = consultas.normalizar


def _filas(ruta_csv):
    with open(ruta_csv, encoding='utf-8', newline='') as f:
        lector = csv.reader(f)
        next(lector, None)          # encabezado
        for fila in lector:
            if fila and fila[0].strip():
                yield [c.strip() for c in fila]


class Red:
    def __init__(self, carpeta='datos'):
        carpeta = Path(carpeta)
        est_csv = str(carpeta / 'estaciones.csv')
        rutas_csv = str(carpeta / 'rutas.csv')
        horarios_csv = str(carpeta / 'horarios.csv')

        # Estaciones: tabla hash de estados (R1, R8) + AVL de abiertas (R2, R3).
        self.estaciones = [fila[0] for fila in _filas(est_csv)]
        self.rangos = IndiceRangos()
        self.estados = EstadoEstaciones(self.rangos)
        self.estados.cargar(est_csv)

        # Rutas: listas doblemente enlazadas en una tabla hash (R5, R7).
        self.rutas = RedRutas()
        self.rutas.cargar_estaciones(est_csv)
        self.rutas.cargar(rutas_csv)
        self.ids_rutas = []
        for id_ruta, _ in self.rutas.rutas.elementos():
            self.ids_rutas.append(id_ruta)

        # Horarios: tabla hash (estación, ruta) -> minutos ordenados (R4, R6, R10).
        self.horarios = IndiceHorarios()
        for ruta, estacion, hora in _filas(horarios_csv):
            self.horarios.agregar(estacion, ruta, hora)
        self.horarios.preparar()

        # Índices derivados que se mantienen al editar rutas:
        #   rutas_por_estacion: estación -> [ids de ruta que paran ahí] (R5)
        #   buses_por_estacion: estación -> buses al día que paran ahí  (R6)
        self.rutas_por_estacion = TablaHash()
        self.buses_por_estacion = TablaHash()
        for nombre in self.estaciones:
            self.rutas_por_estacion.poner(nombre, [])
            self.buses_por_estacion.poner(nombre, 0)
        for id_ruta in self.ids_rutas:
            nodo = self.rutas.rutas.obtener(id_ruta).cabeza
            while nodo:
                self._parada_entra(id_ruta, nodo.estacion)
                nodo = nodo.sig

        self.historial = Historial(self._revertir, self._rehacer)

    # ------------------------------------------------------------ índices
    def _parada_entra(self, id_ruta, estacion):
        self.rutas_por_estacion.obtener(estacion).append(id_ruta)
        actual = self.buses_por_estacion.obtener(estacion)
        self.buses_por_estacion.poner(estacion, actual + self.horarios.buses(estacion, id_ruta))

    def _parada_sale(self, id_ruta, estacion):
        self.rutas_por_estacion.obtener(estacion).remove(id_ruta)
        actual = self.buses_por_estacion.obtener(estacion)
        self.buses_por_estacion.poner(estacion, actual - self.horarios.buses(estacion, id_ruta))

    def _ruta_existe(self, id_ruta):
        return self.rutas.rutas.obtener(id_ruta) is not None

    # ------------------------------------------------------------ R1, R2, R3
    def estado(self, nombre):
        """R1: (existe, abierta). O(1) esperado."""
        return consultas.estado(self.estados, nombre)

    def autocompletar(self, prefijo, k=5):
        """R2: hasta k estaciones abiertas con ese prefijo. O(log n + k)."""
        return consultas.autocompletar(self.rangos, prefijo, k)

    def rango(self, desde, hasta):
        """R3: estaciones abiertas entre dos nombres (inclusive). O(log n + k)."""
        return self.rangos.rango(normalizar(desde), normalizar(hasta))

    # ------------------------------------------------------------ R4
    def proximo_bus(self, estacion, ruta, hora):
        """R4: hora 'HH:MM' del siguiente bus de `ruta` en `estacion` a
        partir de `hora` (inclusive), o None. O(log h + L)."""
        estacion, ruta = normalizar(estacion), normalizar(ruta)
        if not self.estados.abierta(estacion):
            return None
        r = self.rutas.rutas.obtener(ruta)
        if r is None or r.buscar(estacion) is None:   # parada quitada en R7
            return None
        return self.horarios.proximo_bus(estacion, ruta, hora)

    # ------------------------------------------------------------ R5, R6
    def viaje(self, origen, destino):
        """R5: Viaje (directo o con un transbordo) con menos paradas, o None."""
        return viajes.planificar(self.rutas, self.rutas_por_estacion, self.estados,
                                 normalizar(origen), normalizar(destino))

    def ranking(self, k=10):
        """R6: [(estación, buses al día)] de las k abiertas con más buses. O(n log k)."""
        return viajes.ranking(self.estaciones, self.buses_por_estacion, self.estados, k)

    # ------------------------------------------------------------ R7
    def agregar_parada(self, ruta, antes, despues, nueva):
        registro = self.rutas.agregar_parada(normalizar(ruta), normalizar(antes),
                                             normalizar(despues), normalizar(nueva))
        self._aplicar_indices(('rutas', registro), adelante=True)
        self.historial.registrar(('rutas', registro))
        return registro

    def quitar_parada(self, ruta, estacion):
        registro = self.rutas.quitar_parada(normalizar(ruta), normalizar(estacion))
        self._aplicar_indices(('rutas', registro), adelante=True)
        self.historial.registrar(('rutas', registro))
        return registro

    def recorrido(self, ruta):
        """R7: (ida, vuelta) de la ruta. O(L)."""
        return self.rutas.recorrido(normalizar(ruta))

    def rutas_de(self, estacion):
        """Rutas que paran hoy en la estación. O(1) esperado."""
        return list(self.rutas_por_estacion.obtener(normalizar(estacion)) or [])

    # ------------------------------------------------------------ R8
    def cerrar(self, nombre):
        registro = self.estados.cerrar(normalizar(nombre))
        self.historial.registrar(('estados', registro))
        return registro

    def reabrir(self, nombre):
        registro = self.estados.reabrir(normalizar(nombre))
        self.historial.registrar(('estados', registro))
        return registro

    # ------------------------------------------------------------ R9
    def _aplicar_indices(self, accion, adelante):
        origen, registro = accion
        if origen != 'rutas':
            return
        tipo, id_ruta, nodo = registro
        entra = (tipo == 'agregar_parada') == adelante
        if entra:
            self._parada_entra(id_ruta, nodo.estacion)
        else:
            self._parada_sale(id_ruta, nodo.estacion)

    def _revertir(self, accion):
        origen, registro = accion
        (self.rutas if origen == 'rutas' else self.estados).revertir(registro)
        self._aplicar_indices(accion, adelante=False)

    def _rehacer(self, accion):
        origen, registro = accion
        (self.rutas if origen == 'rutas' else self.estados).rehacer(registro)
        self._aplicar_indices(accion, adelante=True)

    def deshacer(self):
        """R9: deshace la última acción. Devuelve su descripción o None."""
        accion = self.historial.deshacer()
        return describir(accion) if accion else None

    def rehacer(self):
        """R9: rehace la última acción deshecha. Devuelve su descripción o None."""
        accion = self.historial.rehacer()
        return describir(accion) if accion else None

    # ------------------------------------------------------------ R10
    def simular_fila(self, estacion, ruta=None, desde='06:00', hasta='08:00',
                     pasajeros_por_minuto=5, cupo=100, intervalo=None, semilla=1):
        """R10: simula la fila de abordaje entre `desde` y `hasta`.

        Si se da `ruta`, los buses salen a las horas reales de horarios.csv;
        si no, salen cada `intervalo` minutos. O(P + B + log h).
        """
        estacion = normalizar(estacion)
        if not self.estados.abierta(estacion):
            raise ValueError(f'{estacion} no existe o está cerrada')
        inicio, fin = minutos(desde), minutos(hasta)
        if fin <= inicio:
            raise ValueError('La hora final debe ser posterior a la inicial')
        if ruta is not None:
            ruta = normalizar(ruta)
            r = self.rutas.rutas.obtener(ruta)
            if r is None or r.buscar(estacion) is None:
                raise ValueError(f'La ruta {ruta} no para en {estacion}')
            todas = self.horarios.horarios(estacion, ruta)
            salidas = todas[limite_inferior(todas, inicio):limite_inferior(todas, fin + 1)]
        else:
            if not intervalo or intervalo <= 0:
                raise ValueError('Sin ruta hay que dar un intervalo en minutos')
            salidas = list(range(inicio, fin + 1, intervalo))
        llegadas = simulacion.generar_llegadas(inicio, fin, pasajeros_por_minuto, semilla)
        return simulacion.simular(llegadas, salidas, cupo)


def describir(accion):
    origen, registro = accion
    if origen == 'estados':
        tipo, nombre = registro
        return f'{tipo} {nombre}'
    tipo, id_ruta, nodo = registro
    return f'{tipo.replace("_", " ")} {nodo.estacion} en la ruta {id_ruta}'


__all__ = ['Red', 'formato', 'minutos']

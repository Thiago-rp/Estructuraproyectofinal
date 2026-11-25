import csv
from motor.tabla_hash import TablaHash


class Parada:
    def __init__(self, estacion):
        self.estacion = estacion
        self.ant = None
        self.sig = None


class Ruta:
    def __init__(self, id_ruta):
        self.id = id_ruta
        self.cabeza = None
        self.cola = None
        self.largo = 0

    def agregar_al_final(self, estacion):
        nodo = Parada(estacion)
        nodo.ant = self.cola
        if self.cola:
            self.cola.sig = nodo
        else:
            self.cabeza = nodo
        self.cola = nodo
        self.largo += 1

    def buscar(self, estacion):
        n = self.cabeza
        while n:
            if n.estacion == estacion:
                return n
            n = n.sig
        return None

    def _desenlazar(self, nodo):
        if nodo.ant:
            nodo.ant.sig = nodo.sig
        else:
            self.cabeza = nodo.sig
        if nodo.sig:
            nodo.sig.ant = nodo.ant
        else:
            self.cola = nodo.ant
        self.largo -= 1

    def _enlazar(self, nodo):
        if nodo.ant:
            nodo.ant.sig = nodo
        else:
            self.cabeza = nodo
        if nodo.sig:
            nodo.sig.ant = nodo
        else:
            self.cola = nodo
        self.largo += 1

    def recorrido(self):
        ida, vuelta = [], []
        n = self.cabeza
        while n:
            ida.append(n.estacion)
            n = n.sig
        n = self.cola
        while n:
            vuelta.append(n.estacion)
            n = n.ant
        return ida, vuelta


class RedRutas:
    def __init__(self):
        self.rutas = TablaHash()
        self.estaciones = TablaHash()  

    def cargar_estaciones(self, estaciones_csv):
        with open(estaciones_csv, encoding='utf-8', newline='') as f:
            primera = True
            for fila in csv.reader(f):
                if primera:
                    primera = False
                    continue
                if len(fila) > 0 and fila[0].strip() != '':
                    self.estaciones.poner(fila[0].strip(), True)

    def cargar(self, ruta_csv):
        with open(ruta_csv, encoding='utf-8', newline='') as f:
            lector = csv.reader(f)
            primera = True
            for fila in lector:
                if primera:
                    primera = False
                    continue
                if len(fila) < 3:
                    continue
                id_ruta, orden, estacion = fila[0].strip(), int(fila[1]), fila[2].strip()
                ruta = self.rutas.obtener(id_ruta)
                if ruta is None:
                    ruta = Ruta(id_ruta)
                    self.rutas.poner(id_ruta, ruta)
                if self.estaciones.obtener(estacion) is None:
                    raise ValueError(f'{estacion} (ruta {id_ruta}) no está en estaciones.csv')
                if orden != ruta.largo + 1:
                    raise ValueError(f'Orden inesperado en {id_ruta}: {orden}')
                ruta.agregar_al_final(estacion)

    def _ruta(self, id_ruta):
        ruta = self.rutas.obtener(id_ruta)
        if ruta is None:
            raise ValueError(f'La ruta {id_ruta} no existe')
        return ruta

    def agregar_parada(self, id_ruta, antes, despues, nueva):
        ruta = self._ruta(id_ruta)
        a, b = ruta.buscar(antes), ruta.buscar(despues)
        if a is None or b is None:
            raise ValueError('Las dos paradas deben existir en la ruta')
        if a.sig is not b:
            raise ValueError(f'{antes} y {despues} no son consecutivas (en ese orden)')
        if self.estaciones.obtener(nueva) is None:
            raise ValueError(f'{nueva} no existe en estaciones.csv')
        if ruta.buscar(nueva) is not None:
            raise ValueError(f'{nueva} ya está en la ruta {id_ruta}')
        nodo = Parada(nueva)
        nodo.ant, nodo.sig = a, b
        ruta._enlazar(nodo)
        return ('agregar_parada', id_ruta, nodo)

    def quitar_parada(self, id_ruta, estacion):
        ruta = self._ruta(id_ruta)
        nodo = ruta.buscar(estacion)
        if nodo is None:
            raise ValueError(f'{estacion} no está en la ruta {id_ruta}')
        if ruta.largo <= 2:
            raise ValueError('Una ruta debe tener al menos 2 paradas')
        ruta._desenlazar(nodo)
        return ('quitar_parada', id_ruta, nodo)

    def recorrido(self, id_ruta):
        return self._ruta(id_ruta).recorrido()

    def revertir(self, registro):
        tipo, id_ruta, nodo = registro
        ruta = self._ruta(id_ruta)
        if tipo == 'agregar_parada':
            ruta._desenlazar(nodo)
        else:
            ruta._enlazar(nodo)

    def rehacer(self, registro):
        tipo, id_ruta, nodo = registro
        ruta = self._ruta(id_ruta)
        if tipo == 'agregar_parada':
            ruta._enlazar(nodo)
        else:
            ruta._desenlazar(nodo)

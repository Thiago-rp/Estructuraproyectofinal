import csv
from motor.tabla_hash import TablaHash


class EstadoEstaciones:
    def __init__(self, indice_rangos=None):
        self.estado = TablaHash()
        self.indice = indice_rangos

    def cargar(self, estaciones_csv):
        with open(estaciones_csv, encoding='utf-8', newline='') as f:
            primera = True
            for fila in csv.reader(f):
                if primera:
                    primera = False
                    continue
                if len(fila) > 0 and fila[0].strip() != '':
                    self._poner(fila[0].strip(), True)

    def _poner(self, nombre, abierta):
        self.estado.poner(nombre, abierta)
        if self.indice is not None:
            if abierta:
                self.indice.abrir(nombre)
            else:
                self.indice.cerrar(nombre)

    def existe(self, nombre):
        return self.estado.obtener(nombre) is not None

    def abierta(self, nombre):
        return self.estado.obtener(nombre) is True

    def puede_usar(self, nombre):
        return self.abierta(nombre)

    def cerrar(self, nombre):
        if not self.existe(nombre):
            raise ValueError(f'{nombre} no existe en estaciones.csv')
        if not self.abierta(nombre):
            raise ValueError(f'{nombre} ya está cerrada')
        self._poner(nombre, False)
        return ('cerrar', nombre)

    def reabrir(self, nombre):
        if not self.existe(nombre):
            raise ValueError(f'{nombre} no existe en estaciones.csv')
        if self.abierta(nombre):
            raise ValueError(f'{nombre} ya está abierta')
        self._poner(nombre, True)
        return ('reabrir', nombre)

    def revertir(self, registro):
        tipo, nombre = registro
        self._poner(nombre, tipo == 'cerrar') 
    def rehacer(self, registro):
        tipo, nombre = registro
        self._poner(nombre, tipo == 'reabrir')

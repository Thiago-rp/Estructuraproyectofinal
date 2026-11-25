"""R10: simulación de la fila de abordaje en hora pico.

Los pasajeros llegan a la estación y hacen fila (cola FIFO). Cada bus sale a
su hora, se suben hasta `cupo` pasajeros en orden de llegada y el resto
sigue esperando el siguiente bus.
"""
import random
from motor.estructuras import Cola


class ResultadoSimulacion:
    def __init__(self):
        self.pasajeros = 0          # llegaron durante la ventana
        self.abordaron = 0
        self.quedan_en_fila = 0     # siguen esperando al pasar el último bus
        self.espera_total = 0.0
        self.espera_maxima = 0.0
        self.fila_maxima = 0
        self.buses = []             # [(minuto_salida, suben, fila_que_queda)]

    @property
    def espera_promedio(self):
        return self.espera_total / self.abordaron if self.abordaron else 0.0


def generar_llegadas(desde, hasta, por_minuto, semilla=1):
    """Llegadas aleatorias (proceso de Poisson) entre `desde` y `hasta`
    (minutos del día), con `por_minuto` pasajeros en promedio. O(P)."""
    if por_minuto <= 0:
        return []
    azar = random.Random(semilla)
    llegadas = []
    t = desde + azar.expovariate(por_minuto)
    while t < hasta:
        llegadas.append(t)
        t += azar.expovariate(por_minuto)
    return llegadas


def simular(llegadas, salidas, cupo):
    """`llegadas` y `salidas` en minutos, ordenadas de menor a mayor.

    Recorre los dos arreglos a la vez como una mezcla de eventos: antes de
    cada salida encola a todos los que llegaron hasta ese momento y luego
    sube hasta `cupo` pasajeros desde el frente de la fila.
    O(P + B), P = pasajeros, B = buses: cada pasajero entra y sale de la
    cola una sola vez y cada bus se procesa una vez.
    """
    if cupo <= 0:
        raise ValueError('El cupo debe ser mayor que 0')
    fila = Cola()
    r = ResultadoSimulacion()
    r.pasajeros = len(llegadas)
    i = 0
    for salida in salidas:
        while i < len(llegadas) and llegadas[i] <= salida:
            fila.encolar(llegadas[i])
            i += 1
        if fila.tamano > r.fila_maxima:
            r.fila_maxima = fila.tamano
        suben = 0
        while suben < cupo and not fila.vacia():
            espera = salida - fila.desencolar()
            r.espera_total += espera
            if espera > r.espera_maxima:
                r.espera_maxima = espera
            suben += 1
        r.abordaron += suben
        r.buses.append((salida, suben, fila.tamano))
    r.quedan_en_fila = fila.tamano + (len(llegadas) - i)
    return r

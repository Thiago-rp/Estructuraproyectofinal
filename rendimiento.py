"""R11: panel de rendimiento de todo el motor.

Genera redes sintéticas de tamaño n, 2n, 4n... con la misma "densidad"
(paradas por ruta, rutas por estación y buses por parada constantes), mide
cada operación del motor y muestra cuánto crece el tiempo al duplicar n.

Cómo leer el factor (tiempo con 2n / tiempo con n):
    ~1.0  -> O(1) u operación que no depende de n
    ~1.1  -> O(log n)
    ~2.0  -> O(n)  (u O(n log k) con k fijo)

Además mide R4 duplicando h (horarios del par) y R10 duplicando P
(pasajeros), que son las variables de las que dependen esas operaciones.

Ejecutar desde la raíz: python rendimiento.py   (tarda unos 2 minutos)
Guarda los resultados en resultados_rendimiento.csv
"""
import csv
import gc
import random
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter_ns

from motor import Red
from motor.horarios import IndiceHorarios
from motor.simulacion import simular

TAMANOS = (500, 1000, 2000, 4000)
PARADAS_POR_RUTA = 12
ESTACIONES_POR_RUTA = 4      # m = n / 4 rutas  -> ~3 rutas por estación
BUSES_POR_PARADA = 24


def nombre(i):
    return f'ESTACION {i:06d}'


def crear_red(carpeta, n, semilla=42):
    azar = random.Random(semilla)
    carpeta = Path(carpeta)
    with (carpeta / 'estaciones.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['nombre'])
        for i in range(n):
            w.writerow([nombre(i)])
    rutas = []
    for r in range(n // ESTACIONES_POR_RUTA):
        paradas = azar.sample(range(n), PARADAS_POR_RUTA)
        rutas.append((f'R{r}', paradas))
    # Las rutas R0 y R1 comparten una estación para que R5 tenga transbordo.
    rutas[1][1][3] = rutas[0][1][6]
    with (carpeta / 'rutas.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['ruta', 'orden', 'estacion'])
        for id_ruta, paradas in rutas:
            for orden, e in enumerate(paradas, 1):
                w.writerow([id_ruta, orden, nombre(e)])
    with (carpeta / 'horarios.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['ruta', 'estacion', 'hora'])
        for id_ruta, paradas in rutas:
            for j, e in enumerate(paradas):
                for b in range(BUSES_POR_PARADA):
                    t = (300 + b * 40 + j * 2) % 1440
                    w.writerow([id_ruta, nombre(e), f'{t // 60:02d}:{t % 60:02d}'])
    return rutas


def medir(funcion, repeticiones=2000, tandas=7):
    """Tiempo promedio por llamada en microsegundos (us).

    Se toma el mínimo de varias tandas con el recolector de basura apagado:
    el mínimo es la medición menos afectada por otros procesos del equipo.
    """
    for _ in range(50):
        funcion()
    tiempos = []
    gc.collect()
    gc.disable()
    try:
        for _ in range(tandas):
            inicio = perf_counter_ns()
            for _ in range(repeticiones):
                funcion()
            tiempos.append((perf_counter_ns() - inicio) / repeticiones / 1000)
    finally:
        gc.enable()
    return min(tiempos)


def operaciones(red, rutas, n):
    """Cada operación es una función sin argumentos que deja la red igual."""
    r0, p0 = rutas[0]
    r1, p1 = rutas[1]
    medio = n // 2
    fuera_de_r0 = next(nombre(i) for i in range(n) if i not in p0)
    a, b = nombre(p0[2]), nombre(p0[3])
    cerrable = nombre(p0[5])

    def r7_agregar():
        red.agregar_parada(r0, a, b, fuera_de_r0)
        red.deshacer()

    def r7_quitar():
        red.quitar_parada(r0, a)
        red.deshacer()

    def r8():
        red.cerrar(cerrable)
        red.reabrir(cerrable)

    # R9 se mide después de R8: deshace y rehace la última acción de la pila.
    def r9():
        red.deshacer()
        red.rehacer()

    ops = [
        ('R1 estado', 'O(1)', lambda: red.estado(nombre(medio))),
        ('R2 autocompletar k=5', 'O(log n + k)', lambda: red.autocompletar(nombre(medio)[:-2], 5)),
        ('R3 rango k=4', 'O(log n + k)', lambda: red.rango(nombre(medio), nombre(medio + 3))),
        ('R4 próximo bus', 'O(log h + L)', lambda: red.proximo_bus(nombre(p0[4]), r0, '12:00')),
        ('R5 viaje', 'O(R·L)', lambda: red.viaje(nombre(p0[0]), nombre(p1[-1]))),
        ('R6 ranking k=10', 'O(n log k)', lambda: red.ranking(10)),
        ('R7 recorrido', 'O(L)', lambda: red.recorrido(r0)),
        ('R7 agregar + deshacer', 'O(L)', r7_agregar),
        ('R7 quitar + deshacer', 'O(L)', r7_quitar),
        ('R8 cerrar + reabrir', 'O(log n)', r8),
        ('R9 deshacer + rehacer', 'O(log n)', r9),
    ]
    return ops


def panel_red():
    filas = []
    previos = {}
    for n in TAMANOS:
        with TemporaryDirectory() as carpeta:
            rutas = crear_red(carpeta, n)
            inicio = perf_counter_ns()
            red = Red(carpeta)
            carga = (perf_counter_ns() - inicio) / 1000
        resultados = [('Carga de los 3 CSV', 'O(H log h)', carga)]
        for etiqueta, cota, f in operaciones(red, rutas, n):
            resultados.append((etiqueta, cota, medir(f, repeticiones=200 if 'R6' in etiqueta else 2000)))
        print(f'\n--- n = {n} estaciones, {len(rutas)} rutas, '
              f'{len(rutas) * PARADAS_POR_RUTA * BUSES_POR_PARADA} horarios ---')
        for etiqueta, cota, us in resultados:
            factor = us / previos[etiqueta] if etiqueta in previos else None
            previos[etiqueta] = us
            print(f'{etiqueta:<24} {cota:<13} {us:12.2f} us   '
                  f'{"x%.2f" % factor if factor else ""}')
            filas.append(['red', etiqueta, cota, n, round(us, 3), round(factor, 3) if factor else ''])
    return filas


def panel_variables():
    filas = []
    print('\n--- R4 duplicando h (horarios del par estación-ruta) ---')
    anterior = None
    for h in (1000, 2000, 4000, 8000, 16000):
        indice = IndiceHorarios()
        for i in range(h):
            t = (i * 7) % (h * 2)
            indice.agregar('A', 'R', f'{t // 60:02d}:{t % 60:02d}')
        indice.preparar()
        us = medir(lambda: indice.proximo_bus('A', 'R', '05:00'), repeticiones=5000)
        factor = us / anterior if anterior else None
        anterior = us
        print(f'h = {h:6d}  R4 {us:8.2f} us  {"x%.2f" % factor if factor else ""}')
        filas.append(['h', 'R4 próximo bus', 'O(log h)', h, round(us, 3), round(factor, 3) if factor else ''])

    print('\n--- R10 duplicando P (pasajeros) y B (buses) ---')
    anterior = None
    for p in (2000, 4000, 8000, 16000, 32000):
        llegadas = [i * 0.5 for i in range(p)]
        salidas = list(range(0, p // 2 + 1, 5))
        us = medir(lambda: simular(llegadas, salidas, 30), repeticiones=5, tandas=5)
        factor = us / anterior if anterior else None
        anterior = us
        print(f'P = {p:6d}  R10 {us:10.1f} us  {"x%.2f" % factor if factor else ""}')
        filas.append(['P', 'R10 simular fila', 'O(P + B)', p, round(us, 3), round(factor, 3) if factor else ''])
    return filas


def ejecutar():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    filas = panel_red() + panel_variables()
    with open('resultados_rendimiento.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['experimento', 'operacion', 'cota', 'tamano', 'microsegundos', 'factor_vs_anterior'])
        w.writerows(filas)
    print('\nGuardado: resultados_rendimiento.csv')


if __name__ == '__main__':
    ejecutar()

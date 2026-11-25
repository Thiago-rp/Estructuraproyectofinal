"""Mediciones R11 de R3/R4. Colocar en la raíz del proyecto."""
import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter_ns
from statistics import median
from motor import Red


def crear_red(carpeta, n):
    carpeta = Path(carpeta)
    with (carpeta / 'estaciones.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['nombre'])
        for i in range(n):
            w.writerow([f'ESTACION {i:08d}'])
    with (carpeta / 'rutas.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['ruta', 'orden', 'estacion'])
        for i in range(n):
            w.writerow(['R1', i+1, f'ESTACION {i:08d}'])
    with (carpeta / 'horarios.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['ruta', 'estacion', 'hora'])
        for i in range(n):
            t = (i*2) % 1440
            w.writerow(['R1', 'ESTACION 00000000', f'{t//60:02d}:{t%60:02d}'])


def medir(funcion, repeticiones=3000, tandas=5):
    for _ in range(100):
        funcion()
    tiempos = []
    for _ in range(tandas):
        inicio = perf_counter_ns()
        for _ in range(repeticiones):
            funcion()
        tiempos.append((perf_counter_ns()-inicio)/repeticiones/1000)
    return median(tiempos)


def ejecutar():
    resultados = []
    anterior = None
    for n in (256, 512, 1024, 2048, 4096, 8192):
        with TemporaryDirectory() as carpeta:
            crear_red(carpeta, n)
            red = Red(str(carpeta))
            r3 = lambda: red.rango(f'ESTACION {n//2:08d}', f'ESTACION {n//2+3:08d}')
            r4 = lambda: red.proximo_bus('ESTACION 00000000', 'R1', '06:01')
            assert len(r3()) == 4
            assert r4() == '06:02'
            a, b = medir(r3), medir(r4)
            resultados.append([n, n, 4, a, b, a/anterior[0] if anterior else '', b/anterior[1] if anterior else ''])
            anterior = (a,b)
            print(f'n=h={n:5d} | R3: {a:8.3f} us | R4: {b:8.3f} us')
    with open('resultados_r3_r4.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['n_estaciones','h_horarios','k_resultados','r3_us','r4_us','factor_r3','factor_r4'])
        w.writerows(resultados)
    print('Guardado: resultados_r3_r4.csv')
    return resultados


if __name__ == '__main__':
    ejecutar()

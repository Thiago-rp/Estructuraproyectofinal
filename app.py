"""App de consola del planificador de TransMilenio.

Solo lee lo que escribe el usuario, llama al motor y muestra el resultado.
Ejecutar desde la raíz del proyecto: python app.py
"""
import sys
from pathlib import Path
from motor import Red
from motor.horarios import formato

DATOS = Path(__file__).resolve().parent / 'datos'

MENU = """
================= TransMilenio =================
 Consultas            1. Estado de una estación (R1)
                      2. Autocompletar (R2)
 Rangos y horarios    3. Estaciones en un rango (R3)
                      4. Próximo bus (R4)
 Viajes y ranking     5. Planear un viaje (R5)
                      6. Estaciones con más buses (R6)
 Edición de la red    7. Ver recorrido de una ruta (R7)
                      8. Agregar parada (R7)
                      9. Quitar parada (R7)
                     10. Cerrar estación (R8)
                     11. Reabrir estación (R8)
 Historial           12. Deshacer (R9)
                     13. Rehacer (R9)
 Simulación          14. Fila de abordaje en hora pico (R10)
                      0. Salir
================================================"""


def pedir(texto, defecto=None):
    valor = input(f'{texto}{f" [{defecto}]" if defecto else ""}: ').strip()
    return valor if valor else defecto


def pedir_entero(texto, defecto):
    valor = pedir(texto, defecto)
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValueError(f'"{valor}" no es un número entero')


def paradas(n):
    return f'{n} parada' if n == 1 else f'{n} paradas'


def sugerir(red, nombre):
    """Si la estación no existe, muestra sugerencias con R2."""
    existe, _ = red.estado(nombre)
    if not existe:
        opciones = red.autocompletar(nombre[:3], 5)
        if opciones:
            print('  ¿Quisiste decir?: ' + ', '.join(opciones))


def r1(red):
    nombre = pedir('Nombre exacto de la estación')
    existe, abierta = red.estado(nombre)
    if not existe:
        print('  La estación no existe.')
        sugerir(red, nombre)
    else:
        print(f'  Existe y está {"ABIERTA" if abierta else "CERRADA"}.')


def r2(red):
    prefijo = pedir('Prefijo (por ejemplo CAL)')
    k = pedir_entero('¿Cuántas como máximo?', 5)
    res = red.autocompletar(prefijo, k)
    print('  ' + (', '.join(res) if res else 'No hay estaciones abiertas con ese prefijo.'))


def r3(red):
    desde = pedir('Desde', 'CALLE 26')
    hasta = pedir('Hasta', 'CALLE 80')
    res = red.rango(desde, hasta)
    print(f'  {len(res)} estaciones: ' + (', '.join(res) if res else '(ninguna)'))


def r4(red):
    estacion = pedir('Estación')
    rutas = red.rutas_de(estacion)
    if rutas:
        print('  Rutas que paran ahí: ' + ', '.join(rutas))
    ruta = pedir('Ruta')
    hora = pedir('Hora (HH:MM)', '07:00')
    res = red.proximo_bus(estacion, ruta, hora)
    if res:
        print(f'  El próximo bus de la ruta {ruta.upper()} pasa a las {res}.')
    else:
        print('  No hay más buses (o la estación está cerrada, o la ruta no para ahí).')
        sugerir(red, estacion)


def r5(red):
    origen = pedir('Origen')
    destino = pedir('Destino')
    v = red.viaje(origen, destino)
    if v is None:
        print('  No hay viaje directo ni con un transbordo (revisa que ambas estén abiertas).')
        sugerir(red, origen)
        sugerir(red, destino)
        return
    print(f'  {"Viaje directo" if v.directo else "Viaje con 1 transbordo"}: {paradas(v.paradas)} en total')
    for i, t in enumerate(v.tramos, 1):
        print(f'   {i}. Tome la ruta {t.ruta} en {t.sube} y bájese en {t.baja} ({paradas(t.paradas)})')
        print('      ' + ' -> '.join(t.estaciones))
    if not v.directo:
        print(f'  Transbordo en: {v.tramos[0].baja}')


def r6(red):
    k = pedir_entero('¿Cuántas estaciones?', 10)
    for i, (nombre, buses) in enumerate(red.ranking(k), 1):
        print(f'  {i:3d}. {nombre:<28} {buses:6d} buses al día')


def r7_ver(red):
    ruta = pedir('Ruta', '1-3')
    ida, vuelta = red.recorrido(ruta)
    print('  Ida:    ' + ' -> '.join(ida))
    print('  Vuelta: ' + ' -> '.join(vuelta))


def r7_agregar(red):
    ruta = pedir('Ruta')
    print('  Recorrido actual: ' + ' -> '.join(red.recorrido(ruta)[0]))
    antes = pedir('Parada anterior')
    despues = pedir('Parada siguiente')
    nueva = pedir('Estación nueva')
    red.agregar_parada(ruta, antes, despues, nueva)
    print('  Listo: ' + ' -> '.join(red.recorrido(ruta)[0]))


def r7_quitar(red):
    ruta = pedir('Ruta')
    print('  Recorrido actual: ' + ' -> '.join(red.recorrido(ruta)[0]))
    estacion = pedir('Parada a quitar')
    red.quitar_parada(ruta, estacion)
    print('  Listo: ' + ' -> '.join(red.recorrido(ruta)[0]))


def r8_cerrar(red):
    red.cerrar(pedir('Estación a cerrar'))
    print('  Estación cerrada.')


def r8_reabrir(red):
    red.reabrir(pedir('Estación a reabrir'))
    print('  Estación reabierta.')


def r9_deshacer(red):
    hecho = red.deshacer()
    print(f'  Deshecho: {hecho}' if hecho else '  No hay nada para deshacer.')


def r9_rehacer(red):
    hecho = red.rehacer()
    print(f'  Rehecho: {hecho}' if hecho else '  No hay nada para rehacer.')


def r10(red):
    estacion = pedir('Estación', 'PORTAL NORTE')
    rutas = red.rutas_de(estacion)
    if rutas:
        print('  Rutas que paran ahí: ' + ', '.join(rutas))
    ruta = pedir('Ruta (vacío = buses cada N minutos)', '')
    intervalo = None
    if not ruta:
        ruta = None
        intervalo = pedir_entero('Cada cuántos minutos sale un bus', 5)
    desde = pedir('Desde (HH:MM)', '06:00')
    hasta = pedir('Hasta (HH:MM)', '08:00')
    tasa = float(pedir('Pasajeros que llegan por minuto (promedio)', '8'))
    cupo = pedir_entero('Cupo de cada bus', 80)
    r = red.simular_fila(estacion, ruta, desde, hasta, tasa, cupo, intervalo)
    print(f'  Buses: {len(r.buses)} | Llegaron: {r.pasajeros} | Abordaron: {r.abordaron} '
          f'| Siguen en fila: {r.quedan_en_fila}')
    print(f'  Espera promedio: {r.espera_promedio:.1f} min | Espera máxima: {r.espera_maxima:.1f} min '
          f'| Fila más larga: {r.fila_maxima}')
    for salida, suben, quedan in r.buses[:12]:
        print(f'   {formato(int(salida))}  suben {suben:4d}  quedan {quedan:4d}')
    if len(r.buses) > 12:
        print(f'   ... ({len(r.buses) - 12} buses más)')


ACCIONES = {
    '1': r1, '2': r2, '3': r3, '4': r4, '5': r5, '6': r6, '7': r7_ver,
    '8': r7_agregar, '9': r7_quitar, '10': r8_cerrar, '11': r8_reabrir,
    '12': r9_deshacer, '13': r9_rehacer, '14': r10,
}


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print('Cargando datos...')
    red = Red(str(DATOS))
    print(f'{len(red.estaciones)} estaciones y {len(red.ids_rutas)} rutas cargadas.')
    while True:
        print(MENU)
        opcion = input('Opción: ').strip()
        if opcion == '0':
            break
        accion = ACCIONES.get(opcion)
        if accion is None:
            print('  Opción no válida.')
            continue
        try:
            accion(red)
        except ValueError as e:
            print(f'  Error: {e}')
        except (EOFError, KeyboardInterrupt):
            break


if __name__ == '__main__':
    main()

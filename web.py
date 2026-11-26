from pathlib import Path
from flask import Flask, jsonify, render_template, request
from motor import Red
from motor.horarios import formato

DATOS = Path(__file__).resolve().parent / 'datos'

app = Flask(__name__)
red = Red(str(DATOS))


def _nombre_estacion(est):
    if isinstance(est, str):
        return est
    return getattr(est, 'nombre', None) or getattr(est, 'id', str(est))


def _lista_estaciones_limpia():
    """Devuelve solo las estaciones (nombre y estado) sin dibujar rutas."""
    raw = red.estaciones
    if isinstance(raw, dict):
        items = list(raw.keys())
    else:
        items = list(raw)

    resultado = []
    for item in items:
        nombre = _nombre_estacion(item)
        existe, abierta = red.estado(nombre)
        if existe:
            resultado.append({
                'nombre': nombre,
                'abierta': bool(abierta),
            })
    resultado.sort(key=lambda x: x['nombre'])
    return resultado


def _resumen_red():
    estaciones = _lista_estaciones_limpia()
    abiertas = sum(1 for e in estaciones if e['abierta'])
    return {
        'total_estaciones': len(estaciones),
        'estaciones_abiertas': abiertas,
        'total_rutas': len(red.ids_rutas),
    }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/estado-red')
def api_estado_red():
    return jsonify({
        'resumen': _resumen_red(),
        'estaciones': _lista_estaciones_limpia(),
    })


@app.route('/api/autocompletar')
def api_autocompletar():
    q = request.args.get('q', '').strip()
    limite = int(request.args.get('limite', 8))
    if not q:
        estaciones = [e['nombre'] for e in _lista_estaciones_limpia() if e['abierta']]
        return jsonify({'sugerencias': estaciones[:limite]})
    return jsonify({'sugerencias': red.autocompletar(q, limite)})


@app.route('/api/estacion')
def api_estacion():
    nombre = request.args.get('nombre', '').strip()
    existe, abierta = red.estado(nombre)
    if not existe:
        sugerencias = red.autocompletar(nombre[:3], 5) if nombre else []
        return jsonify({'existe': False, 'sugerencias': sugerencias}), 404
    rutas = red.rutas_de(nombre)
    return jsonify({
        'existe': True,
        'nombre': nombre,
        'abierta': bool(abierta),
        'rutas': rutas,
    })


@app.route('/api/rango')
def api_rango():
    desde = request.args.get('desde', 'CALLE 26').strip()
    hasta = request.args.get('hasta', 'CALLE 80').strip()
    estaciones = red.rango(desde, hasta)
    return jsonify({'estaciones': estaciones})


@app.route('/api/proximo-bus')
def api_proximo_bus():
    estacion = request.args.get('estacion', '').strip()
    ruta = request.args.get('ruta', '').strip()
    hora = request.args.get('hora', '07:00').strip()
    rutas_disponibles = red.rutas_de(estacion)
    llegada = red.proximo_bus(estacion, ruta, hora)
    return jsonify({
        'llegada': llegada,
        'rutas_disponibles': rutas_disponibles,
    })


@app.route('/api/viaje')
def api_viaje():
    origen = request.args.get('origen', '').strip()
    destino = request.args.get('destino', '').strip()
    v = red.viaje(origen, destino)
    if v is None:
        return jsonify({
            'encontrado': False,
            'mensaje': 'No hay viaje directo ni con un transbordo (verifica que ambas estaciones estén abiertas).',
            'sugerencias_origen': red.autocompletar(origen[:3], 4) if origen else [],
            'sugerencias_destino': red.autocompletar(destino[:3], 4) if destino else [],
        })

    tramos = []
    estaciones_recorrido = []
    for t in v.tramos:
        est_tramo = list(t.estaciones)
        for e in est_tramo:
            if not estaciones_recorrido or estaciones_recorrido[-1] != e:
                estaciones_recorrido.append(e)
        tramos.append({
            'ruta': t.ruta,
            'sube': t.sube,
            'baja': t.baja,
            'paradas': t.paradas,
            'estaciones': est_tramo,
        })

    return jsonify({
        'encontrado': True,
        'directo': bool(v.directo),
        'paradas': v.paradas,
        'transbordo': None if v.directo else v.tramos[0].baja,
        'tramos': tramos,
        'estaciones_recorrido': estaciones_recorrido,
    })


@app.route('/api/ranking')
def api_ranking():
    top = int(request.args.get('top', 10))
    datos = [{'nombre': nombre, 'buses': buses} for nombre, buses in red.ranking(top)]
    return jsonify({'ranking': datos})


@app.route('/api/recorrido')
def api_recorrido():
    ruta = request.args.get('ruta', '').strip()
    ida, vuelta = red.recorrido(ruta)
    return jsonify({'ida': list(ida), 'vuelta': list(vuelta)})


@app.route('/api/parada/agregar', methods=['POST'])
def api_agregar_parada():
    data = request.get_json(force=True)
    red.agregar_parada(
        data['ruta'].strip(),
        data['antes'].strip(),
        data['despues'].strip(),
        data['nueva'].strip(),
    )
    return jsonify({'ok': True, 'resumen': _resumen_red(), 'estaciones': _lista_estaciones_limpia()})


@app.route('/api/parada/quitar', methods=['POST'])
def api_quitar_parada():
    data = request.get_json(force=True)
    red.quitar_parada(data['ruta'].strip(), data['estacion'].strip())
    return jsonify({'ok': True, 'resumen': _resumen_red(), 'estaciones': _lista_estaciones_limpia()})


@app.route('/api/estacion/estado', methods=['POST'])
def api_cambiar_estado():
    data = request.get_json(force=True)
    nombre = data['nombre'].strip()
    abrir = bool(data.get('abierta', False))
    if abrir:
        red.reabrir(nombre)
    else:
        red.cerrar(nombre)
    return jsonify({'ok': True, 'resumen': _resumen_red(), 'estaciones': _lista_estaciones_limpia()})


@app.route('/api/historial/<accion>', methods=['POST'])
def api_historial(accion):
    if accion == 'deshacer':
        hecho = red.deshacer()
    elif accion == 'rehacer':
        hecho = red.rehacer()
    else:
        return jsonify({'ok': False, 'error': 'Acción no válida'}), 400
    return jsonify({
        'ok': True,
        'hecho': hecho,
        'resumen': _resumen_red(),
        'estaciones': _lista_estaciones_limpia(),
    })


@app.route('/api/simulacion', methods=['POST'])
def api_simulacion():
    data = request.get_json(force=True)
    estacion = data.get('estacion', 'PORTAL NORTE').strip()
    ruta_raw = (data.get('ruta') or '').strip()
    ruta = ruta_raw if ruta_raw else None
    intervalo = None if ruta else int(data.get('intervalo', 5))
    desde = data.get('desde', '06:00').strip()
    hasta = data.get('hasta', '08:00').strip()
    tasa = float(data.get('tasa', 8))
    cupo = int(data.get('cupo', 80))

    r = red.simular_fila(estacion, ruta, desde, hasta, tasa, cupo, intervalo)
    buses_fmt = [
        {
            'hora': formato(int(salida)),
            'suben': int(suben),
            'quedan': int(quedan),
        }
        for salida, suben, quedan in r.buses[:15]
    ]
    return jsonify({
        'total_buses': len(r.buses),
        'pasajeros': r.pasajeros,
        'abordaron': r.abordaron,
        'quedan_en_fila': r.quedan_en_fila,
        'espera_promedio': round(float(r.espera_promedio), 1),
        'espera_maxima': round(float(r.espera_maxima), 1),
        'fila_maxima': r.fila_maxima,
        'buses': buses_fmt,
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
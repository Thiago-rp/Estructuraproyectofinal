import unittest
from pathlib import Path
from motor import Red

DATOS = Path(__file__).resolve().parents[1] / 'datos'


def optimo_fuerza_bruta(red, origen, destino):
    """Menor número de paradas probando todas las rutas y transbordos. Lento a propósito."""
    if not (red.estados.abierta(origen) and red.estados.abierta(destino)) or origen == destino:
        return None
    recorridos = {r: red.recorrido(r)[0] for r in red.ids_rutas}
    mejor = None
    for r1, p1 in recorridos.items():
        if origen not in p1:
            continue
        i = p1.index(origen)
        if destino in p1[i + 1:]:
            d = p1.index(destino) - i
            mejor = d if mejor is None else min(mejor, d)
        for j in range(i + 1, len(p1)):
            s = p1[j]
            if s == destino or not red.estados.abierta(s):
                continue
            for r2, p2 in recorridos.items():
                if r2 == r1 or s not in p2:
                    continue
                q = p2.index(s)
                if destino in p2[q + 1:]:
                    d = (j - i) + (p2.index(destino) - q)
                    mejor = d if mejor is None else min(mejor, d)
    return mejor


class PruebasR5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.red = Red(str(DATOS))

    def verificar_viaje(self, v, origen, destino):
        self.assertEqual(v.tramos[0].sube, origen)
        self.assertEqual(v.tramos[-1].baja, destino)
        self.assertLessEqual(v.transbordos, 1)
        for t in v.tramos:
            ida = self.red.recorrido(t.ruta)[0]
            i, j = ida.index(t.sube), ida.index(t.baja)
            self.assertEqual(ida[i:j + 1], t.estaciones)
            self.assertEqual(j - i, t.paradas)
            self.assertTrue(self.red.estados.abierta(t.sube))
            self.assertTrue(self.red.estados.abierta(t.baja))
        if v.transbordos:
            self.assertEqual(v.tramos[0].baja, v.tramos[1].sube)
            self.assertNotEqual(v.tramos[0].ruta, v.tramos[1].ruta)

    def test_directo(self):
        v = self.red.viaje('PORTAL USME', 'MOLINOS')
        self.assertTrue(v.directo)
        self.assertEqual(v.paradas, 1)

    def test_transbordo(self):
        v = self.red.viaje('PORTAL USME', 'PORTAL SUBA')
        self.verificar_viaje(v, 'PORTAL USME', 'PORTAL SUBA')
        self.assertEqual(v.paradas, optimo_fuerza_bruta(self.red, 'PORTAL USME', 'PORTAL SUBA'))

    def test_contra_fuerza_bruta(self):
        nombres = self.red.estaciones
        pares = [(nombres[i], nombres[(i * 37 + 11) % len(nombres)]) for i in range(0, len(nombres), 3)]
        for o, d in pares:
            v = self.red.viaje(o, d)
            esperado = optimo_fuerza_bruta(self.red, o, d)
            if esperado is None:
                self.assertIsNone(v, (o, d))
            else:
                self.assertIsNotNone(v, (o, d))
                self.verificar_viaje(v, o, d)
                self.assertEqual(v.paradas, esperado, (o, d))

    def test_respeta_cerradas(self):
        self.red.cerrar('CALLE 40 S.')
        try:
            v = self.red.viaje('PORTAL USME', 'PORTAL SUBA')
            self.verificar_viaje(v, 'PORTAL USME', 'PORTAL SUBA')
            self.assertNotEqual(v.tramos[0].baja, 'CALLE 40 S.')
            self.assertEqual(v.paradas, optimo_fuerza_bruta(self.red, 'PORTAL USME', 'PORTAL SUBA'))
            self.assertIsNone(self.red.viaje('CALLE 40 S.', 'PORTAL SUBA'))
            self.assertIsNone(self.red.viaje('PORTAL SUBA', 'CALLE 40 S.'))
        finally:
            self.red.deshacer()

    def test_invalidos(self):
        self.assertIsNone(self.red.viaje('NO EXISTE', 'PORTAL SUBA'))
        self.assertIsNone(self.red.viaje('PORTAL SUBA', 'PORTAL SUBA'))


class PruebasR6(unittest.TestCase):
    def setUp(self):
        self.red = Red(str(DATOS))

    def test_top(self):
        top = self.red.ranking(3)
        self.assertEqual(top, [('RICAURTE', 4446), ('PORTAL NORTE', 3282), ('BANDERAS', 3038)])

    def test_contra_ordenar_todo(self):
        conteo = {n: self.red.buses_por_estacion.obtener(n) for n in self.red.estaciones}
        esperado = sorted(conteo.items(), key=lambda x: (-x[1], x[0]))
        self.assertEqual(self.red.ranking(len(esperado)), esperado)
        self.assertEqual(self.red.ranking(500), esperado)
        self.assertEqual(self.red.ranking(0), [])
        total = sum(conteo.values())
        self.assertEqual(total, 140492)   # filas de horarios.csv

    def test_omite_cerradas(self):
        self.red.cerrar('RICAURTE')
        self.assertEqual(self.red.ranking(1)[0][0], 'PORTAL NORTE')
        self.red.deshacer()
        self.assertEqual(self.red.ranking(1)[0][0], 'RICAURTE')

    def test_refleja_edicion_de_rutas(self):
        antes = self.red.buses_por_estacion.obtener('UNIVERSIDADES')
        quitados = self.red.horarios.buses('UNIVERSIDADES', '1-1')
        self.red.quitar_parada('1-1', 'UNIVERSIDADES')
        self.assertEqual(self.red.buses_por_estacion.obtener('UNIVERSIDADES'), antes - quitados)
        self.red.deshacer()
        self.assertEqual(self.red.buses_por_estacion.obtener('UNIVERSIDADES'), antes)


if __name__ == '__main__':
    unittest.main()

import unittest
from pathlib import Path
from motor import Red
from motor.estructuras import Pila, Cola, Monticulo
from motor.simulacion import simular, generar_llegadas

DATOS = Path(__file__).resolve().parents[1] / 'datos'


class PruebasEstructuras(unittest.TestCase):
    def test_pila(self):
        p = Pila()
        for i in range(5):
            p.apilar(i)
        self.assertEqual([p.desapilar() for _ in range(5)], [4, 3, 2, 1, 0])
        self.assertTrue(p.vacia())
        with self.assertRaises(IndexError):
            p.desapilar()

    def test_cola(self):
        c = Cola()
        for i in range(5):
            c.encolar(i)
        self.assertEqual([c.desencolar() for _ in range(3)], [0, 1, 2])
        c.encolar(9)
        self.assertEqual([c.desencolar() for _ in range(3)], [3, 4, 9])
        self.assertTrue(c.vacia())
        with self.assertRaises(IndexError):
            c.desencolar()

    def test_monticulo(self):
        m = Monticulo(lambda a, b: a < b)
        for x in [5, 3, 8, 1, 9, 2, 7]:
            m.insertar(x)
        self.assertEqual([m.extraer() for _ in range(7)], [1, 2, 3, 5, 7, 8, 9])


class PruebasR9(unittest.TestCase):
    def setUp(self):
        self.red = Red(str(DATOS))

    def foto(self):
        return (self.red.recorrido('1-3'), self.red.estado('CALLE 26'), self.red.estado('MODELIA'),
                self.red.ranking(5), self.red.rutas_de('AGUAS'))

    def test_deshacer_rehacer_mezclado(self):
        f0 = self.foto()
        self.red.cerrar('CALLE 26')
        f1 = self.foto()
        self.red.quitar_parada('1-3', 'MODELIA')
        f2 = self.foto()
        self.red.agregar_parada('1-3', 'NORMANDIA', 'AV. ROJAS', 'AGUAS')
        f3 = self.foto()
        self.red.cerrar('MODELIA')
        f4 = self.foto()
        self.assertIn('1-3', self.red.rutas_de('AGUAS'))

        for esperado in (f3, f2, f1, f0):
            self.assertIsNotNone(self.red.deshacer())
            self.assertEqual(self.foto(), esperado)
        self.assertIsNone(self.red.deshacer())

        for esperado in (f1, f2, f3, f4):
            self.assertIsNotNone(self.red.rehacer())
            self.assertEqual(self.foto(), esperado)
        self.assertIsNone(self.red.rehacer())

    def test_accion_nueva_borra_rehacer(self):
        self.red.cerrar('CALLE 26')
        self.red.deshacer()
        self.assertTrue(self.red.historial.puede_rehacer())
        self.red.cerrar('CALLE 34')
        self.assertFalse(self.red.historial.puede_rehacer())
        self.assertIsNone(self.red.rehacer())
        self.assertEqual(self.red.estado('CALLE 26'), (True, True))

    def test_error_no_se_registra(self):
        with self.assertRaises(ValueError):
            self.red.cerrar('NO EXISTE')
        with self.assertRaises(ValueError):
            self.red.quitar_parada('1-1', 'NO EXISTE')
        self.assertFalse(self.red.historial.puede_deshacer())

    def test_reabrir_y_rango(self):
        self.red.cerrar('CALLE 26')
        self.red.reabrir('CALLE 26')
        self.red.deshacer()          # deshace la reapertura -> cerrada
        self.assertNotIn('CALLE 26', self.red.rango('CALLE 22', 'CALLE 34'))
        self.assertIsNone(self.red.proximo_bus('CALLE 26', '6-1', '10:00'))
        self.red.deshacer()          # deshace el cierre -> abierta
        self.assertIn('CALLE 26', self.red.rango('CALLE 22', 'CALLE 34'))
        self.assertIsNotNone(self.red.proximo_bus('CALLE 26', '6-1', '10:00'))

    def test_proximo_bus_tras_quitar_parada(self):
        self.assertIsNotNone(self.red.proximo_bus('RECINTO FERIAL', '1-1', '10:00'))
        self.red.quitar_parada('1-1', 'RECINTO FERIAL')
        self.assertIsNone(self.red.proximo_bus('RECINTO FERIAL', '1-1', '10:00'))
        self.red.deshacer()
        self.assertIsNotNone(self.red.proximo_bus('RECINTO FERIAL', '1-1', '10:00'))


class PruebasR10(unittest.TestCase):
    def test_fifo_y_cupo(self):
        r = simular([0, 1, 2, 3, 4], [5, 10], cupo=2)
        self.assertEqual(r.buses, [(5, 2, 3), (10, 2, 1)])
        self.assertEqual(r.abordaron, 4)
        self.assertEqual(r.quedan_en_fila, 1)
        # FIFO: suben 0,1 a las 5 y 2,3 a las 10 -> esperas 5,4,8,7
        self.assertEqual(r.espera_total, 24)
        self.assertEqual(r.espera_maxima, 8)
        self.assertEqual(r.fila_maxima, 5)

    def test_llegan_despues_del_ultimo_bus(self):
        r = simular([1, 20], [5], cupo=10)
        self.assertEqual(r.abordaron, 1)
        self.assertEqual(r.quedan_en_fila, 1)

    def test_llegadas_reproducibles(self):
        a = generar_llegadas(360, 480, 5, semilla=7)
        self.assertEqual(a, generar_llegadas(360, 480, 5, semilla=7))
        self.assertEqual(a, sorted(a))
        self.assertTrue(all(360 <= t < 480 for t in a))
        self.assertTrue(400 < len(a) < 800)

    def test_con_datos_reales(self):
        red = Red(str(DATOS))
        r = red.simular_fila('PORTAL NORTE', 'B10-2', '06:00', '08:00', pasajeros_por_minuto=8, cupo=80)
        self.assertGreater(len(r.buses), 0)
        self.assertTrue(all(360 <= b[0] <= 480 for b in r.buses))
        self.assertEqual(r.abordaron + r.quedan_en_fila, r.pasajeros)
        r2 = red.simular_fila('PORTAL NORTE', None, '06:00', '07:00', 5, 50, intervalo=10)
        self.assertEqual([b[0] for b in r2.buses], list(range(360, 421, 10)))
        with self.assertRaises(ValueError):
            red.simular_fila('PORTAL NORTE', '1-1')      # 1-1 no para en Portal Norte
        red.cerrar('PORTAL NORTE')
        with self.assertRaises(ValueError):
            red.simular_fila('PORTAL NORTE', 'B10-2')


if __name__ == '__main__':
    unittest.main()

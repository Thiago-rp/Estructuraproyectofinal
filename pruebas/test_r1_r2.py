import unittest
from pathlib import Path
from motor import Red
from motor.rangos import IndiceRangos
from motor.consultas import autocompletar

DATOS = Path(__file__).resolve().parents[1] / 'datos'


class PruebasR1R2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.red = Red(str(DATOS))

    def test_r1_estado(self):
        self.assertEqual(self.red.estado('CALLE 26'), (True, True))
        self.assertEqual(self.red.estado('  calle   26 '), (True, True))  # se normaliza
        self.assertEqual(self.red.estado('NO EXISTE'), (False, False))
        self.red.cerrar('CALLE 26')
        try:
            self.assertEqual(self.red.estado('CALLE 26'), (True, False))
        finally:
            self.red.deshacer()

    def test_r2_orden_y_limite(self):
        self.assertEqual(self.red.autocompletar('CAL', 3), ['CALLE 100', 'CALLE 106', 'CALLE 127'])
        todas = self.red.autocompletar('CALLE', 100)
        self.assertEqual(todas, sorted(todas))
        self.assertTrue(all(n.startswith('CALLE') for n in todas))
        esperadas = [n for n in self.red.estaciones if n.startswith('CALLE')]
        self.assertEqual(len(todas), len(esperadas))

    def test_r2_bordes(self):
        self.assertEqual(self.red.autocompletar('ZZZ', 5), [])
        self.assertEqual(self.red.autocompletar('CAL', 0), [])
        self.assertEqual(self.red.autocompletar('portal s', 5), ['PORTAL SUBA', 'PORTAL SUR'])
        self.assertEqual(len(self.red.autocompletar('', 7)), 7)

    def test_r2_omite_cerradas(self):
        self.red.cerrar('CALLE 106')
        try:
            self.assertEqual(self.red.autocompletar('CALLE 1', 3), ['CALLE 100', 'CALLE 127', 'CALLE 142'])
        finally:
            self.red.deshacer()
        self.assertIn('CALLE 106', self.red.autocompletar('CALLE 1', 3))

    def test_r2_contra_fuerza_bruta(self):
        indice = IndiceRangos()
        nombres = ['AB', 'ABC', 'ABD', 'AC', 'B', 'BA', 'A', 'ABCD', 'C']
        for n in nombres:
            indice.abrir(n)
        for p in ['', 'A', 'AB', 'ABC', 'B', 'C', 'D', 'AA']:
            for k in range(0, 10):
                esperado = sorted(n for n in nombres if n.startswith(p))[:k]
                self.assertEqual(autocompletar(indice, p, k), esperado, (p, k))


if __name__ == '__main__':
    unittest.main()

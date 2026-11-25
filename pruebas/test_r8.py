import unittest
from pathlib import Path
from motor.estados import EstadoEstaciones
from motor.rangos import IndiceRangos

DATOS = Path(__file__).resolve().parents[1] / 'datos'


class PruebasR8(unittest.TestCase):
    def setUp(self):
        self.indice = IndiceRangos()
        self.estados = EstadoEstaciones(self.indice)
        self.estados.cargar(str(DATOS / 'estaciones.csv'))

    def test_todas_abiertas_al_inicio(self):
        self.assertTrue(self.estados.abierta('CALLE 26'))
        self.assertTrue(self.estados.puede_usar('CALLE 26'))
        self.assertFalse(self.estados.existe('NO EXISTE'))
        self.assertFalse(self.estados.abierta('NO EXISTE'))

    def test_cerrar_la_saca_del_rango(self):
        self.assertIn('CALLE 26', self.indice.rango('CALLE 22', 'CALLE 34'))
        self.estados.cerrar('CALLE 26')
        self.assertFalse(self.estados.abierta('CALLE 26'))
        self.assertFalse(self.estados.puede_usar('CALLE 26'))
        self.assertNotIn('CALLE 26', self.indice.rango('CALLE 22', 'CALLE 34'))

    def test_reabrir_la_devuelve(self):
        self.estados.cerrar('CALLE 26')
        self.estados.reabrir('CALLE 26')
        self.assertTrue(self.estados.puede_usar('CALLE 26'))
        self.assertIn('CALLE 26', self.indice.rango('CALLE 22', 'CALLE 34'))

    def test_errores(self):
        with self.assertRaises(ValueError):
            self.estados.cerrar('NO EXISTE')
        with self.assertRaises(ValueError):
            self.estados.reabrir('CALLE 26')      
        self.estados.cerrar('CALLE 26')
        with self.assertRaises(ValueError):
            self.estados.cerrar('CALLE 26')       

    def test_revertir_rehacer(self):
        r1 = self.estados.cerrar('CALLE 26')
        r2 = self.estados.cerrar('CALLE 34')
        self.estados.revertir(r2)
        self.assertTrue(self.estados.abierta('CALLE 34'))
        self.assertFalse(self.estados.abierta('CALLE 26'))
        self.estados.revertir(r1)
        self.assertIn('CALLE 26', self.indice.rango('CALLE 22', 'CALLE 34'))
        self.estados.rehacer(r1)
        self.assertNotIn('CALLE 26', self.indice.rango('CALLE 22', 'CALLE 34'))

    def test_sin_indice(self):
        e = EstadoEstaciones()
        e.cargar(str(DATOS / 'estaciones.csv'))
        e.cerrar('AGUAS')
        self.assertFalse(e.abierta('AGUAS'))


if __name__ == '__main__':
    unittest.main()

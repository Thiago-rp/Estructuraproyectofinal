import unittest
from pathlib import Path
from motor import Red
from motor.rangos import IndiceRangos
from motor.horarios import IndiceHorarios

class Pruebas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.red = Red(str(Path(__file__).resolve().parents[1] / 'datos'))

    def test_rango_real(self):
        self.assertIn('AGUAS', self.red.rango('AGUAS', 'ALCALA'))
        self.assertEqual(self.red.rango('ALCALA', 'AGUAS'), [])

    def test_avl(self):
        a = IndiceRangos()
        for nombre in ['D', 'C', 'B', 'A', 'E', 'F']:
            a.abrir(nombre)
        self.assertEqual(a.rango('B', 'E'), ['B','C','D','E'])
        a.cerrar('C')
        self.assertEqual(a.rango('B', 'E'), ['B','D','E'])
        a.abrir('C')
        self.assertEqual(a.rango('C', 'C'), ['C'])

    def test_horarios(self):
        a = IndiceHorarios()
        for h in ['25:10','09:30','08:00','09:00']:
            a.agregar('A','1',h)
        a.preparar()
        self.assertEqual(a.proximo_bus('A','1','09:00'), '09:00')
        self.assertEqual(a.proximo_bus('A','1','09:01'), '09:30')
        self.assertEqual(a.proximo_bus('A','1','24:00'), '25:10')
        self.assertIsNone(a.proximo_bus('A','1','26:00'))
        self.assertIsNone(a.proximo_bus('A','2','09:00'))

    def test_bus_real(self):
        self.assertEqual(self.red.proximo_bus('UNIVERSIDADES','1-1','09:57'), '09:57')
        self.assertIsNone(self.red.proximo_bus('NO EXISTE','1-1','09:57'))

if __name__ == '__main__':
    unittest.main()

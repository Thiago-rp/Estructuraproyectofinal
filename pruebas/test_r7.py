import unittest
from pathlib import Path
from motor.edicion import RedRutas

DATOS = Path(__file__).resolve().parents[1] / 'datos'


class PruebasR7(unittest.TestCase):
    def setUp(self):
        self.red = RedRutas()
        self.red.cargar_estaciones(str(DATOS / 'estaciones.csv'))
        self.red.cargar(str(DATOS / 'rutas.csv'))

    def test_carga(self):
        ida, vuelta = self.red.recorrido('1-1')
        self.assertEqual(ida, ['UNIVERSIDADES', 'RECINTO FERIAL', 'EL TIEMPO - MALOKA', 'PORTAL ELDORADO'])
        self.assertEqual(vuelta, ida[::-1])

    def test_agregar_en_medio_y_extremos(self):
        self.red.agregar_parada('1-1', 'UNIVERSIDADES', 'RECINTO FERIAL', 'CAN')
        ida, vuelta = self.red.recorrido('1-1')
        self.assertEqual(ida[:3], ['UNIVERSIDADES', 'CAN', 'RECINTO FERIAL'])
        self.assertEqual(vuelta, ida[::-1])

    def test_errores(self):
        with self.assertRaises(ValueError):   
            self.red.agregar_parada('1-1', 'UNIVERSIDADES', 'PORTAL ELDORADO', 'CAN')
        with self.assertRaises(ValueError):  
            self.red.agregar_parada('1-1', 'UNIVERSIDADES', 'RECINTO FERIAL', 'PORTAL ELDORADO')
        with self.assertRaises(ValueError):   
            self.red.agregar_parada('1-1', 'UNIVERSIDADES', 'RECINTO FERIAL', 'ESTACION FALSA')
        with self.assertRaises(ValueError):  
            self.red.recorrido('99-9')

    def test_quitar_y_extremos(self):
        self.red.quitar_parada('1-1', 'UNIVERSIDADES')     
        self.red.quitar_parada('1-1', 'PORTAL ELDORADO')    
        ida, vuelta = self.red.recorrido('1-1')
        self.assertEqual(ida, ['RECINTO FERIAL', 'EL TIEMPO - MALOKA'])
        with self.assertRaises(ValueError):                 
            self.red.quitar_parada('1-1', 'RECINTO FERIAL')

    def test_revertir_rehacer_lifo(self):
        original = self.red.recorrido('1-3')
        r1 = self.red.quitar_parada('1-3', 'MODELIA')
        r2 = self.red.quitar_parada('1-3', 'PORTAL ELDORADO')
        r3 = self.red.agregar_parada('1-3', 'NORMANDIA', 'AV. ROJAS', 'AGUAS')
        editado = self.red.recorrido('1-3')
        for r in (r3, r2, r1):
            self.red.revertir(r)
        self.assertEqual(self.red.recorrido('1-3'), original)
        for r in (r1, r2, r3):
            self.red.rehacer(r)
        self.assertEqual(self.red.recorrido('1-3'), editado)


if __name__ == '__main__':
    unittest.main()

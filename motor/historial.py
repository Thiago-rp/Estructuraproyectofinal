"""R9: deshacer y rehacer con dos pilas.

Cada acción que cambia la red (cerrar, reabrir, agregar parada, quitar
parada) se guarda como un registro en la pila de deshacer. Deshacer saca el
último, aplica su inverso y lo pasa a la pila de rehacer. Rehacer hace lo
contrario. Una acción nueva vacía la pila de rehacer, porque la historia
"futura" ya no es válida.
"""
from motor.estructuras import Pila


class Historial:
    def __init__(self, revertir, rehacer):
        self._revertir = revertir    # función que aplica el inverso de un registro
        self._rehacer = rehacer      # función que vuelve a aplicar un registro
        self.por_deshacer = Pila()
        self.por_rehacer = Pila()

    def registrar(self, registro):
        """O(1)."""
        self.por_deshacer.apilar(registro)
        self.por_rehacer.vaciar()

    def puede_deshacer(self):
        return not self.por_deshacer.vacia()

    def puede_rehacer(self):
        return not self.por_rehacer.vacia()

    def deshacer(self):
        """Devuelve el registro deshecho o None si no hay nada.
        O(1) más el costo de revertir la acción."""
        if self.por_deshacer.vacia():
            return None
        registro = self.por_deshacer.cima()
        self._revertir(registro)            # si falla, la pila queda intacta
        self.por_deshacer.desapilar()
        self.por_rehacer.apilar(registro)
        return registro

    def rehacer(self):
        """Devuelve el registro rehecho o None si no hay nada.
        O(1) más el costo de volver a aplicar la acción."""
        if self.por_rehacer.vacia():
            return None
        registro = self.por_rehacer.cima()
        self._rehacer(registro)
        self.por_rehacer.desapilar()
        self.por_deshacer.apilar(registro)
        return registro

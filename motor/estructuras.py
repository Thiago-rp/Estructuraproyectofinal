"""Estructuras propias de apoyo: pila (R9), cola (R10) y montículo (R6)."""


class _Nodo:
    def __init__(self, valor, sig=None):
        self.valor = valor
        self.sig = sig


class Pila:
    """Pila con nodos enlazados (LIFO). apilar, desapilar y cima son O(1)."""

    def __init__(self):
        self._cima = None
        self.tamano = 0

    def vacia(self):
        return self._cima is None

    def apilar(self, valor):
        self._cima = _Nodo(valor, self._cima)
        self.tamano += 1

    def desapilar(self):
        if self._cima is None:
            raise IndexError('Pila vacía')
        valor = self._cima.valor
        self._cima = self._cima.sig
        self.tamano -= 1
        return valor

    def cima(self):
        if self._cima is None:
            raise IndexError('Pila vacía')
        return self._cima.valor

    def vaciar(self):
        self._cima = None
        self.tamano = 0


class Cola:
    """Cola con nodos enlazados (FIFO). encolar, desencolar y frente son O(1)."""

    def __init__(self):
        self._frente = None
        self._final = None
        self.tamano = 0

    def vacia(self):
        return self._frente is None

    def encolar(self, valor):
        nodo = _Nodo(valor)
        if self._final is None:
            self._frente = nodo
        else:
            self._final.sig = nodo
        self._final = nodo
        self.tamano += 1

    def desencolar(self):
        if self._frente is None:
            raise IndexError('Cola vacía')
        valor = self._frente.valor
        self._frente = self._frente.sig
        if self._frente is None:
            self._final = None
        self.tamano -= 1
        return valor

    def frente(self):
        if self._frente is None:
            raise IndexError('Cola vacía')
        return self._frente.valor


class Monticulo:
    """Montículo binario sobre un arreglo.

    `menor(a, b)` dice si `a` debe quedar más cerca de la raíz que `b`.
    insertar y extraer son O(log m), raiz es O(1), con m elementos.
    """

    def __init__(self, menor):
        self.datos = []
        self.menor = menor

    def __len__(self):
        return len(self.datos)

    def raiz(self):
        return self.datos[0]

    def insertar(self, valor):
        d = self.datos
        d.append(valor)
        i = len(d) - 1
        while i > 0:
            padre = (i - 1) // 2
            if self.menor(d[i], d[padre]):
                d[i], d[padre] = d[padre], d[i]
                i = padre
            else:
                break

    def extraer(self):
        d = self.datos
        if not d:
            raise IndexError('Montículo vacío')
        raiz = d[0]
        ultimo = d.pop()
        if d:
            d[0] = ultimo
            i, n = 0, len(d)
            while True:
                izq, der, menor = 2 * i + 1, 2 * i + 2, i
                if izq < n and self.menor(d[izq], d[menor]):
                    menor = izq
                if der < n and self.menor(d[der], d[menor]):
                    menor = der
                if menor == i:
                    break
                d[i], d[menor] = d[menor], d[i]
                i = menor
        return raiz

    def reemplazar_raiz(self, valor):
        """Saca la raíz y mete `valor` en un solo paso. O(log m)."""
        raiz = self.extraer()
        self.insertar(valor)
        return raiz

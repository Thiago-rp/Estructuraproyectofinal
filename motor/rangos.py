"""R3: índice AVL de estaciones abiertas."""
class Nodo:
    def __init__(self, nombre):
        self.nombre = nombre
        self.izq = self.der = None
        self.altura = 1


def altura(n):
    return n.altura if n else 0


def actualizar(n):
    a, b = altura(n.izq), altura(n.der)
    n.altura = 1 + (a if a > b else b)


def derecha(n):
    p = n.izq
    n.izq = p.der
    p.der = n
    actualizar(n)
    actualizar(p)
    return p


def izquierda(n):
    p = n.der
    n.der = p.izq
    p.izq = n
    actualizar(n)
    actualizar(p)
    return p


def balancear(n):
    actualizar(n)
    f = altura(n.izq) - altura(n.der)
    if f > 1:
        if altura(n.izq.izq) < altura(n.izq.der):
            n.izq = izquierda(n.izq)
        return derecha(n)
    if f < -1:
        if altura(n.der.der) < altura(n.der.izq):
            n.der = derecha(n.der)
        return izquierda(n)
    return n


def insertar(n, nombre):
    if n is None:
        return Nodo(nombre)
    if nombre < n.nombre:
        n.izq = insertar(n.izq, nombre)
    elif nombre > n.nombre:
        n.der = insertar(n.der, nombre)
    else:
        return n
    return balancear(n)


def eliminar(n, nombre):
    if n is None:
        return None
    if nombre < n.nombre:
        n.izq = eliminar(n.izq, nombre)
    elif nombre > n.nombre:
        n.der = eliminar(n.der, nombre)
    else:
        if n.izq is None:
            return n.der
        if n.der is None:
            return n.izq
        sucesor = n.der
        while sucesor.izq:
            sucesor = sucesor.izq
        n.nombre = sucesor.nombre
        n.der = eliminar(n.der, sucesor.nombre)
    return balancear(n)


def recolectar(n, desde, hasta, salida):
    if n is None:
        return
    if desde < n.nombre:
        recolectar(n.izq, desde, hasta, salida)
    if desde <= n.nombre <= hasta:
        salida.append(n.nombre)
    if n.nombre < hasta:
        recolectar(n.der, desde, hasta, salida)


class IndiceRangos:
    def __init__(self):
        self.raiz = None

    def abrir(self, nombre):
        self.raiz = insertar(self.raiz, nombre)

    def cerrar(self, nombre):
        self.raiz = eliminar(self.raiz, nombre)

    def abierta(self, nombre):
        n = self.raiz
        while n:
            if nombre == n.nombre:
                return True
            n = n.izq if nombre < n.nombre else n.der
        return False

    def rango(self, desde, hasta):
        salida = []
        if desde <= hasta:
            recolectar(self.raiz, desde, hasta, salida)
        return salida

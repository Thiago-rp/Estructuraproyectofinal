class TablaHash:
    def __init__(self):
        self.cubetas = [[] for _ in range(16)]
        self.cantidad = 0

    def _pos(self, clave):
        h = 0
        for c in clave:
            h = (h * 131 + ord(c)) % 4294967291
        return h % len(self.cubetas)

    def _entrada(self, clave):
        for e in self.cubetas[self._pos(clave)]:
            if e[0] == clave:
                return e
        return None

    def _ampliar(self):
        anteriores = self.cubetas
        self.cubetas = [[] for _ in range(len(anteriores) * 2)]
        for cubeta in anteriores:
            for e in cubeta:
                self.cubetas[self._pos(e[0])].append(e)

    def obtener(self, clave):
        """Valor asociado o None. O(1) esperado."""
        e = self._entrada(clave)
        return e[1] if e else None

    def poner(self, clave, valor):
        """Inserta o actualiza. O(1) amortizado esperado."""
        e = self._entrada(clave)
        if e:
            e[1] = valor
            return
        if (self.cantidad + 1) * 4 > len(self.cubetas) * 3:
            self._ampliar()
        self.cubetas[self._pos(clave)].append([clave, valor])
        self.cantidad += 1

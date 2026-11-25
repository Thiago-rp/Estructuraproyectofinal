"""R4: tabla hash propia y búsqueda binaria de horarios."""

def minutos(hora):
    h, m = hora.split(':')
    h, m = int(h), int(m)
    if h < 0 or not 0 <= m < 60:
        raise ValueError('Hora inválida')
    return h * 60 + m


def formato(t):
    return f'{t // 60:02d}:{t % 60:02d}'


def merge_sort(a):
    if len(a) <= 1:
        return a
    medio = len(a) // 2
    izq, der = merge_sort(a[:medio]), merge_sort(a[medio:])
    salida = []
    i = j = 0
    while i < len(izq) and j < len(der):
        if izq[i] <= der[j]:
            salida.append(izq[i]); i += 1
        else:
            salida.append(der[j]); j += 1
    salida.extend(izq[i:])
    salida.extend(der[j:])
    return salida


def limite_inferior(a, objetivo):
    izq, der = 0, len(a)
    while izq < der:
        medio = (izq + der) // 2
        if a[medio] < objetivo:
            izq = medio + 1
        else:
            der = medio
    return izq


class IndiceHorarios:
    def __init__(self):
        self.cubetas = [[] for _ in range(16)]
        self.cantidad = 0

    def _pos(self, estacion, ruta):
        h = 0
        for c in estacion + '\x00' + ruta:
            h = (h * 131 + ord(c)) % 4294967291
        return h % len(self.cubetas)

    def _buscar(self, estacion, ruta):
        for entrada in self.cubetas[self._pos(estacion, ruta)]:
            if entrada[0] == estacion and entrada[1] == ruta:
                return entrada
        return None

    def _ampliar(self):
        anteriores = self.cubetas
        self.cubetas = [[] for _ in range(len(anteriores) * 2)]
        for cubeta in anteriores:
            for entrada in cubeta:
                self.cubetas[self._pos(entrada[0], entrada[1])].append(entrada)

    def agregar(self, estacion, ruta, hora):
        # Solo durante la carga, antes de preparar().
        t = minutos(hora)
        entrada = self._buscar(estacion, ruta)
        if entrada is None:
            if (self.cantidad + 1) * 4 > len(self.cubetas) * 3:
                self._ampliar()
            entrada = [estacion, ruta, []]
            self.cubetas[self._pos(estacion, ruta)].append(entrada)
            self.cantidad += 1
        entrada[2].append(t)

    def preparar(self):
        for cubeta in self.cubetas:
            for entrada in cubeta:
                entrada[2] = merge_sort(entrada[2])

    def proximo_bus(self, estacion, ruta, hora):
        entrada = self._buscar(estacion, ruta)
        if entrada is None:
            return None
        a = entrada[2]
        i = limite_inferior(a, minutos(hora))
        return formato(a[i]) if i < len(a) else None

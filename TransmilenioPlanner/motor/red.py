import csv

class RedTransmilenio:
    def __init__(self):
        # Estructura basada en listas de listas [codigo, nombre, estado]
        self.estaciones = []

    def cargar_estaciones(self, ruta_csv):
        # Carga las estaciones desde el archivo CSV
        try:
            with open(ruta_csv, mode='r', encoding='utf-8') as archivo:
                lector = csv.reader(archivo)
                siguiente_es_encabezado = True

                for fila in lector:
                    if siguiente_es_encabezado:
                        siguiente_es_encabezado = False
                        continue  # Salta la cabecera 'nombre'

                    if len(fila) > 0 and fila[0].strip() != "":
                        nombre = fila[0].strip()
                        codigo = "EST_" + nombre[:3].upper()
                        estado = 'ABIERTA'
                        self.estaciones.append([codigo, nombre, estado])

            print(f"¡Estaciones cargadas con éxito! Total: {len(self.estaciones)}")
        except Exception as e:
            print(f"Error al cargar las estaciones: {e}")

    # ===============
    # Buscar Estación

    def buscar_estacion(self, nombre_buscado):
        # Busca una estación por nombre exacto (Búsqueda lineal - O(n))
        nombre_buscado = nombre_buscado.strip().upper()

        for est in self.estaciones:
            if est[1].upper() == nombre_buscado:
                return (True, est[2] == 'ABIERTA')

        return (False, False)

    def _obtener_clave_orden(self, nombre):

        # Separa el texto del número (CALLE 19 antes de CALLE 100)

        partes = nombre.split()
        texto_base = ""
        numero = 0
        encontro_numero = False

        for parte in partes:
            # Verificamos manualmente si la parte es un número entero
            es_digito = True
            if len(parte) == 0:
                es_digito = False
            else:
                for c in parte:
                    if c < '0' or c > '9':
                        es_digito = False
                        break

            if es_digito:
                numero = int(parte)
                encontro_numero = True
                break
            else:
                texto_base += parte + " "

        if encontro_numero:
            return (texto_base.strip(), numero)
        else:
            return (nombre, 0)

    # =============
    # Autocompletar

    def autocompletar(self, prefijo, k):

        prefijo = prefijo.strip().upper()
        sugerencias = []

        # Filtrar estaciones abiertas que inician con el prefijo
        for est in self.estaciones:
            nombre = est[1].upper()
            if est[2] == 'ABIERTA' and nombre.startswith(prefijo):

                # Verificación manual de duplicados
                ya_esta = False
                for s in sugerencias:
                    if s == nombre:
                        ya_esta = True
                        break

                if not ya_esta:
                    sugerencias.append(nombre)

        # Ordenar con burbuja usando la clave numérica/alfabética
        n = len(sugerencias)
        for i in range(n):
            for j in range(0, n - i - 1):
                clave_j = self._obtener_clave_orden(sugerencias[j])
                clave_siguiente = self._obtener_clave_orden(sugerencias[j + 1])

                if clave_j > clave_siguiente:
                    # Intercambio de elementos adyacentes
                    sugerencias[j], sugerencias[j + 1] = sugerencias[j + 1], sugerencias[j]

        # Retornar máximo 'k' elementos usando slicing
        return sugerencias[:k]

if __name__ == "__main__":
    red = RedTransmilenio()
    red.cargar_estaciones("../data/estaciones.csv")

    print("\n--- PRUEBAS DE AUTOCOMPLETAR ---")
    sugerencias_cal = red.autocompletar("CAL", 15)
    print("Autocompletar 'CAL':", sugerencias_cal)
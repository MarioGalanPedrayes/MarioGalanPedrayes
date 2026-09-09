"""
Conversor de unidades: longitud, peso y temperatura.
Versión de consola: autocontenida, sin dependencias externas,
sin acceso a red ni a ficheros del sistema.
"""

# Factores de conversión a una unidad base por categoría.
LONGITUD_A_METROS = {
    "m": 1.0,
    "km": 1000.0,
    "cm": 0.01,
    "mm": 0.001,
    "milla": 1609.344,
    "pie": 0.3048,
    "pulgada": 0.0254,
}

PESO_A_KG = {
    "kg": 1.0,
    "g": 0.001,
    "mg": 0.000001,
    "libra": 0.45359237,
    "onza": 0.028349523125,
}


def convertir_longitud(valor, desde, hasta):
    metros = valor * LONGITUD_A_METROS[desde]
    return metros / LONGITUD_A_METROS[hasta]


def convertir_peso(valor, desde, hasta):
    kg = valor * PESO_A_KG[desde]
    return kg / PESO_A_KG[hasta]


def _a_celsius(valor, unidad):
    if unidad == "C":
        return valor
    if unidad == "F":
        return (valor - 32) * 5 / 9
    if unidad == "K":
        return valor - 273.15
    raise ValueError(f"Unidad de temperatura desconocida: {unidad}")


def _desde_celsius(valor_c, unidad):
    if unidad == "C":
        return valor_c
    if unidad == "F":
        return valor_c * 9 / 5 + 32
    if unidad == "K":
        return valor_c + 273.15
    raise ValueError(f"Unidad de temperatura desconocida: {unidad}")


def convertir_temperatura(valor, desde, hasta):
    celsius = _a_celsius(valor, desde)
    return _desde_celsius(celsius, hasta)


CATEGORIAS = {
    "1": ("Longitud", LONGITUD_A_METROS, convertir_longitud),
    "2": ("Peso", PESO_A_KG, convertir_peso),
    "3": ("Temperatura", {"C": None, "F": None, "K": None}, convertir_temperatura),
}


def elegir_categoria():
    print("Categorías disponibles:")
    for clave, (nombre, _, _) in CATEGORIAS.items():
        print(f"  {clave}) {nombre}")
    while True:
        opcion = input("Elige una categoría: ").strip()
        if opcion in CATEGORIAS:
            return CATEGORIAS[opcion]
        print("Opción no válida, inténtalo de nuevo.")


def elegir_unidad(mensaje, unidades):
    lista = list(unidades.keys())
    print(f"{mensaje} ({', '.join(lista)}):")
    while True:
        unidad = input("> ").strip()
        if unidad in unidades:
            return unidad
        print("Unidad no reconocida, inténtalo de nuevo.")


def leer_valor():
    while True:
        entrada = input("Valor a convertir: ").strip().replace(",", ".")
        try:
            return float(entrada)
        except ValueError:
            print("Escribe un número válido.")


def main():
    print("=== Conversor de unidades ===\n")
    nombre_categoria, unidades, funcion = elegir_categoria()
    print()
    desde = elegir_unidad("Unidad de origen", unidades)
    hasta = elegir_unidad("Unidad de destino", unidades)
    valor = leer_valor()

    resultado = funcion(valor, desde, hasta)
    print(f"\n{valor} {desde} = {resultado:.4f} {hasta} ({nombre_categoria})")


if __name__ == "__main__":
    main()

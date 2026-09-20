"""
Sumatorio de horas, minutos, segundos y milisegundos.
Versión de consola: autocontenida, sin dependencias externas,
sin acceso a red ni a ficheros del sistema.
"""


def duracion_a_ms(horas, minutos, segundos, milisegundos):
    return ((horas * 3600 + minutos * 60 + segundos) * 1000) + milisegundos


def normalizar(total_ms):
    milisegundos = total_ms % 1000
    total_s = total_ms // 1000
    segundos = total_s % 60
    total_m = total_s // 60
    minutos = total_m % 60
    horas = total_m // 60
    return horas, minutos, segundos, milisegundos


def sumar_duraciones(duraciones):
    total_ms = sum(duracion_a_ms(*d) for d in duraciones)
    return normalizar(total_ms)


def formatear(horas, minutos, segundos, milisegundos):
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}.{milisegundos:03d}"


def leer_entero(mensaje, minimo=0, maximo=None):
    while True:
        entrada = input(mensaje).strip()
        if not entrada.isdigit():
            print("Escribe un número entero válido.")
            continue
        valor = int(entrada)
        if valor < minimo or (maximo is not None and valor > maximo):
            print(f"El valor debe estar entre {minimo} y {maximo}.")
            continue
        return valor


def leer_duracion(indice):
    print(f"\n--- Duración {indice} ---")
    horas = leer_entero("Horas: ")
    minutos = leer_entero("Minutos (0-59): ", 0, 59)
    segundos = leer_entero("Segundos (0-59): ", 0, 59)
    milisegundos = leer_entero("Milisegundos (0-999): ", 0, 999)
    return (horas, minutos, segundos, milisegundos)


def main():
    print("=== Sumatorio de duraciones ===")
    print("Introduce cuántas duraciones quieres sumar.\n")

    cantidad = leer_entero("¿Cuántas duraciones vas a sumar? ", 1)

    duraciones = [leer_duracion(i + 1) for i in range(cantidad)]

    print("\n--- Duraciones introducidas ---")
    for i, d in enumerate(duraciones, start=1):
        print(f"{i}. {formatear(*d)}")

    horas, minutos, segundos, milisegundos = sumar_duraciones(duraciones)
    total_ms = sum(duracion_a_ms(*d) for d in duraciones)

    print("\n=== Resultado ===")
    print(f"Total: {formatear(horas, minutos, segundos, milisegundos)}")
    print(f"({total_ms} milisegundos en total, {total_ms / 1000:.3f} segundos)")


if __name__ == "__main__":
    main()

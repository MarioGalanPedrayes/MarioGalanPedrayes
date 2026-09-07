import math

G = 9.81  # aceleración de la gravedad (m/s^2)


def tiro_parabolico(velocidad, angulo_grados):
    """
    Calcula el alcance, la altura máxima y el tiempo de vuelo
    de un proyectil lanzado con una velocidad inicial y un ángulo dados,
    ignorando la resistencia del aire.
    """
    angulo_rad = math.radians(angulo_grados)

    tiempo_vuelo = (2 * velocidad * math.sin(angulo_rad)) / G
    altura_maxima = (velocidad ** 2) * (math.sin(angulo_rad) ** 2) / (2 * G)
    alcance = (velocidad ** 2) * math.sin(2 * angulo_rad) / G

    return {
        "tiempo_vuelo": tiempo_vuelo,
        "altura_maxima": altura_maxima,
        "alcance": alcance,
    }


def trayectoria(velocidad, angulo_grados, num_puntos=40):
    """Devuelve una lista de puntos (x, y) de la trayectoria, para poder dibujarla."""
    angulo_rad = math.radians(angulo_grados)
    resultado = tiro_parabolico(velocidad, angulo_grados)
    t_total = resultado["tiempo_vuelo"]

    puntos = []
    for i in range(num_puntos + 1):
        t = (t_total / num_puntos) * i
        x = velocidad * math.cos(angulo_rad) * t
        y = velocidad * math.sin(angulo_rad) * t - 0.5 * G * t ** 2
        puntos.append((x, max(y, 0)))

    return puntos


if __name__ == "__main__":
    v0 = float(input("Velocidad inicial (m/s): "))
    angulo = float(input("Ángulo de lanzamiento (grados): "))

    r = tiro_parabolico(v0, angulo)

    print(f"\nTiempo de vuelo: {r['tiempo_vuelo']:.2f} s")
    print(f"Altura máxima:   {r['altura_maxima']:.2f} m")
    print(f"Alcance:         {r['alcance']:.2f} m")

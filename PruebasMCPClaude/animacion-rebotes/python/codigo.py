"""
Animación de una pelota rebotando (gravedad + rebote), dibujada
frame a frame como arte ASCII en la terminal.
Versión de consola: autocontenida, sin dependencias externas,
sin acceso a red ni a ficheros del sistema.
"""

import os
import time

ANCHO = 30
ALTO = 15
GRAVEDAD = 0.12
REBOTE = 0.85
NUM_FRAMES = 120
PAUSA_SEGUNDOS = 0.05


def limpiar_pantalla():
    os.system("cls" if os.name == "nt" else "clear")


def avanzar(x, y, vx, vy):
    vy += GRAVEDAD
    x += vx
    y += vy

    if x < 0:
        x = 0
        vx = -vx * REBOTE
    elif x > ANCHO - 1:
        x = ANCHO - 1
        vx = -vx * REBOTE

    if y < 0:
        y = 0
        vy = -vy * REBOTE
    elif y > ALTO - 1:
        y = ALTO - 1
        vy = -vy * REBOTE

    return x, y, vx, vy


def dibujar_frame(x, y, numero_frame):
    col = round(x)
    fila = round(y)

    lineas = []
    lineas.append(f"Frame {numero_frame}/{NUM_FRAMES}")
    lineas.append("+" + "-" * ANCHO + "+")
    for f in range(ALTO):
        if f == fila:
            linea = " " * col + "o" + " " * (ANCHO - col - 1)
        else:
            linea = " " * ANCHO
        lineas.append("|" + linea + "|")
    lineas.append("+" + "-" * ANCHO + "+")

    print("\n".join(lineas))


def main():
    x, y = 2.0, 0.0
    vx, vy = 0.6, 0.0

    for frame in range(1, NUM_FRAMES + 1):
        limpiar_pantalla()
        dibujar_frame(x, y, frame)
        x, y, vx, vy = avanzar(x, y, vx, vy)
        time.sleep(PAUSA_SEGUNDOS)

    print("\n=== Animación terminada ===")


if __name__ == "__main__":
    main()

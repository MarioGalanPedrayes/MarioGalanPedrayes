"""Piedra, papel o tijeras: toda la lógica del juego en Python.

La página web solo muestra los botones y el marcador; quien decide la jugada
del ordenador y quién gana es este archivo.
"""
import json
import random

OPCIONES = ["piedra", "papel", "tijeras"]

# Cada opción vence a la que tiene como valor.
VENCE_A = {"piedra": "tijeras", "papel": "piedra", "tijeras": "papel"}

marcador = {"jugador": 0, "ordenador": 0, "empates": 0}


def resolver(jugador, ordenador):
    """Devuelve 'jugador', 'ordenador' o 'empate' según las dos jugadas."""
    if jugador == ordenador:
        return "empate"
    if VENCE_A[jugador] == ordenador:
        return "jugador"
    return "ordenador"


def jugar(eleccion):
    """Juega una ronda: el ordenador elige al azar y se actualiza el marcador."""
    if eleccion not in OPCIONES:
        return json.dumps({"error": "Opción no válida"})
    ordenador = random.choice(OPCIONES)
    ganador = resolver(eleccion, ordenador)
    if ganador == "empate":
        marcador["empates"] += 1
    else:
        marcador[ganador] += 1
    return json.dumps({
        "jugador": eleccion,
        "ordenador": ordenador,
        "ganador": ganador,
        "marcador": marcador,
    })


def reiniciar():
    """Pone el marcador a cero."""
    for clave in marcador:
        marcador[clave] = 0
    return json.dumps(marcador)


if __name__ == "__main__":
    # Prueba rápida en tu ordenador: python codigo.py
    for _ in range(5):
        print(jugar(random.choice(OPCIONES)))

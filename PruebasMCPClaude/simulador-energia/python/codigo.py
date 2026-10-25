"""Simulador de energía potencial y cinética con un péndulo.

Toda la física está aquí. La página (JavaScript) solo dibuja lo que devuelve
avanzar() y pasa los valores de los deslizadores a iniciar().

Fórmulas (altura h medida desde el punto más bajo):
    h  = L * (1 - cos(theta))
    v  = L * omega
    Ep = m * g * h
    Ec = 1/2 * m * v^2
Sin rozamiento, Ep + Ec se mantiene constante (conservación de la energía).
"""
import json
import math

G = 9.81  # gravedad en m/s^2

estado = {}


def iniciar(masa, longitud, angulo_grados, rozamiento):
    """Prepara el péndulo soltándolo en reposo desde el ángulo indicado."""
    estado.clear()
    estado.update({
        "m": float(masa),
        "L": float(longitud),
        "theta": math.radians(float(angulo_grados)),
        "omega": 0.0,
        "roce": float(rozamiento),
    })
    estado["e0"] = estado["m"] * G * estado["L"] * (1 - math.cos(estado["theta"]))
    return medir()


def medir():
    """Calcula alturas, velocidad y energías del estado actual."""
    m, L = estado["m"], estado["L"]
    theta, omega = estado["theta"], estado["omega"]
    h = L * (1 - math.cos(theta))
    v = L * omega
    ep = m * G * h
    ec = 0.5 * m * v * v
    return json.dumps({
        "theta": theta,
        "h": h,
        "v": abs(v),
        "ep": ep,
        "ec": ec,
        "total": ep + ec,
        "e0": estado["e0"],
    })


def avanzar(dt, pasos=20):
    """Avanza la simulación dt segundos, dividido en 'pasos' pequeños."""
    h_paso = dt / pasos
    L = estado["L"]
    for _ in range(pasos):
        # Aceleración angular: gravedad + rozamiento (proporcional a la velocidad)
        alfa = -(G / L) * math.sin(estado["theta"]) - estado["roce"] * estado["omega"]
        estado["omega"] += alfa * h_paso          # primero la velocidad...
        estado["theta"] += estado["omega"] * h_paso  # ...luego la posición
    return medir()


if __name__ == "__main__":
    # Prueba en tu ordenador: python codigo.py  (5 s simulados, sin rozamiento)
    iniciar(1.0, 2.0, 60, 0.0)
    for segundo in range(1, 6):
        d = json.loads(avanzar(1.0, 1000))
        print(f"t={segundo}s  Ep={d['ep']:.2f} J  Ec={d['ec']:.2f} J  total={d['total']:.2f} J")

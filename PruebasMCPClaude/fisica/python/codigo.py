"""Choques entre dos carritos en una pista recta (1 dimensión).

Toda la física está aquí; la página solo dibuja lo que devuelve avanzar().

Fórmulas del choque, con coeficiente de restitución e (0 = totalmente
inelástico, 1 = totalmente elástico):
    v1' = (m1*v1 + m2*v2 + m2*e*(v2 - v1)) / (m1 + m2)
    v2' = (m1*v1 + m2*v2 + m1*e*(v1 - v2)) / (m1 + m2)
El momento p = m*v total se conserva SIEMPRE; la energía cinética solo si e = 1.
"""
import json

estado = {}


def ancho(m):
    """Tamaño visual del carrito (en metros): crece con la masa."""
    return 0.4 + 0.08 * m


def momento(m1, v1, m2, v2):
    return m1 * v1 + m2 * v2


def energia(m1, v1, m2, v2):
    return 0.5 * m1 * v1 ** 2 + 0.5 * m2 * v2 ** 2


def resolver_choque(m1, v1, m2, v2, e):
    """Devuelve las velocidades de los dos carritos justo después del choque."""
    total = m1 + m2
    p = m1 * v1 + m2 * v2
    return (p + m2 * e * (v2 - v1)) / total, (p + m1 * e * (v1 - v2)) / total


def iniciar(m1, v1, m2, v2, e):
    """Coloca el carrito 1 a la izquierda (x=2 m) y el 2 a la derecha (x=8 m)."""
    estado.clear()
    estado.update({"m1": float(m1), "v1": float(v1), "x1": 2.0,
                   "m2": float(m2), "v2": float(v2), "x2": 8.0,
                   "e": float(e), "choque": None})
    # Habrá choque solo si el de la izquierda va más rápido que el de la derecha
    estado["habra_choque"] = estado["v1"] > estado["v2"]
    return datos()


def datos():
    s = estado
    return json.dumps({
        "x1": s["x1"], "x2": s["x2"], "v1": s["v1"], "v2": s["v2"],
        "w1": ancho(s["m1"]), "w2": ancho(s["m2"]),
        "p": momento(s["m1"], s["v1"], s["m2"], s["v2"]),
        "ec": energia(s["m1"], s["v1"], s["m2"], s["v2"]),
        "habra_choque": s["habra_choque"],
        "choque": s["choque"],
        "fuera": s["x1"] < -1 or s["x1"] > 11 or s["x2"] < -1 or s["x2"] > 11,
    })


def avanzar(dt):
    """Mueve los carritos dt segundos y resuelve el choque si se tocan."""
    s = estado
    s["x1"] += s["v1"] * dt
    s["x2"] += s["v2"] * dt
    se_tocan = s["x1"] + ancho(s["m1"]) / 2 >= s["x2"] - ancho(s["m2"]) / 2
    se_acercan = s["v1"] > s["v2"]
    if se_tocan and se_acercan:
        antes = {"p": momento(s["m1"], s["v1"], s["m2"], s["v2"]),
                 "ec": energia(s["m1"], s["v1"], s["m2"], s["v2"]),
                 "v1": s["v1"], "v2": s["v2"]}
        s["v1"], s["v2"] = resolver_choque(s["m1"], s["v1"], s["m2"], s["v2"], s["e"])
        despues = {"p": momento(s["m1"], s["v1"], s["m2"], s["v2"]),
                   "ec": energia(s["m1"], s["v1"], s["m2"], s["v2"]),
                   "v1": s["v1"], "v2": s["v2"]}
        s["choque"] = {"antes": antes, "despues": despues}
    return datos()


if __name__ == "__main__":
    # Prueba en tu ordenador: python codigo.py
    for e in (1.0, 0.5, 0.0):
        iniciar(2.0, 3.0, 1.0, -1.0, e)
        d = json.loads(avanzar(0.0001))
        while d["choque"] is None:
            d = json.loads(avanzar(0.01))
        c = d["choque"]
        print(f"e={e}: p {c['antes']['p']:.2f} -> {c['despues']['p']:.2f} | "
              f"Ec {c['antes']['ec']:.2f} -> {c['despues']['ec']:.2f} J")

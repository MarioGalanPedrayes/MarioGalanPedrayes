"""MANECILLA: lógica de un juego de un solo toque (Python 3, sin dependencias).

Una aguja gira sin parar por una esfera de reloj. En la esfera hay un sector
marcado: hay que pulsar justo cuando la aguja está dentro. Si aciertas, el
sector salta a otro sitio, la aguja va un poco más rápido y el sector se
estrecha. Si fallas o se acaba el tiempo del sector, pierdes una vida.

Reglas:
  - 3 vidas. Cada 8 aciertos recuperas una (máximo 3).
  - Acierto = 10 puntos. Acierto perfecto (centro del sector) = 20 puntos.
  - Combo: aciertos seguidos. Multiplicador x1 (1-4), x2 (5-9), x3 (10-14),
    x4 (15-19) y x5 (20 o más). Un fallo pone el combo a cero.
  - Cada 5 aciertos la aguja cambia de sentido.
  - La dificultad sube durante los primeros 20 aciertos (velocidad, anchura y
    tiempo disponible) y luego se queda fija: a partir de ahí solo cuenta la
    pericia y la resistencia.

La página (script.js) mide el tiempo, dibuja el estado y avisa a Python de cada
pulsación. Todas las reglas están en este archivo y las funciones públicas
devuelven texto JSON.
"""
import json

VIDAS_MAX = 3
VEL_INICIAL, VEL_MAX = 150.0, 270.0          # grados por segundo
ANCHO_INICIAL, ANCHO_MIN = 70.0, 28.0        # grados del sector
TIEMPO_INICIAL, TIEMPO_MIN = 4.5, 2.5        # segundos para acertar cada sector
FRACCION_PERFECTO = 0.2                      # perfecto = dentro del 40 % central
TOLERANCIA = 2.0                             # grados de margen en los bordes
DT_MAX = 0.05                                # una pestaña dormida no quita vidas
_M32 = 0xFFFFFFFF


class Generador:
    """Generador pseudoaleatorio de 32 bits (mulberry32, dominio público)."""

    def __init__(self, semilla):
        self.estado = int(semilla) & _M32

    def siguiente(self):
        """Número decimal en [0, 1)."""
        self.estado = (self.estado + 0x6D2B79F5) & _M32
        t = self.estado
        t = ((t ^ (t >> 15)) * (1 | t)) & _M32
        t = ((t + (((t ^ (t >> 7)) * (61 | t)) & _M32)) & _M32) ^ t
        return ((t ^ (t >> 14)) & _M32) / 4294967296


def parametros(aciertos):
    """Velocidad, anchura del sector y tiempo disponible según los aciertos."""
    vel = min(VEL_MAX, VEL_INICIAL + 6.0 * aciertos)
    ancho = max(ANCHO_MIN, ANCHO_INICIAL - 2.1 * aciertos)
    tiempo = max(TIEMPO_MIN, TIEMPO_INICIAL - 0.1 * aciertos)
    return vel, ancho, tiempo


def _diferencia(a, b):
    """Diferencia angular con signo, entre -180 y 180."""
    return ((a - b + 180.0) % 360.0) - 180.0


def multiplicador(combo):
    return 1 + min(combo // 5, 4)


# --------------------------------------------------------------------------
# Estado de la partida
# --------------------------------------------------------------------------
P = {}


def _nuevo_objetivo():
    vel, ancho, tiempo = parametros(P["aciertos"])
    P["vel"], P["ancho"], P["tmax"], P["tiempo"] = vel, ancho, tiempo, tiempo
    desplazamiento = 60.0 + P["rng"].siguiente() * 240.0   # siempre por delante
    P["centro"] = (P["angulo"] + P["dir"] * desplazamiento) % 360.0


def _json():
    p = P
    return json.dumps({
        "estado": p["estado"],
        "angulo": round(p["angulo"], 2),
        "dir": p["dir"],
        "centro": round(p["centro"], 2),
        "ancho": round(p["ancho"], 2),
        "tiempo_frac": round(max(0.0, p["tiempo"] / p["tmax"]), 3),
        "vidas": p["vidas"],
        "vidas_max": VIDAS_MAX,
        "puntos": p["puntos"],
        "combo": p["combo"],
        "mult": multiplicador(p["combo"]),
        "aciertos": p["aciertos"],
        "perfectos": p["perfectos"],
        "fallos": p["fallos"],
        "mejor_combo": p["mejor_combo"],
        "vel": p["vel"],
        "evento": p["evento"],
        "evento_n": p["evento_n"],
        "ganado": p["ganado"],
        "vida_extra": p["vida_extra"],
    })


def _evento(nombre, ganado=0, vida_extra=False):
    P["evento"] = nombre
    P["evento_n"] += 1
    P["ganado"] = ganado
    P["vida_extra"] = vida_extra


def nueva_partida(semilla):
    P.clear()
    P.update(
        rng=Generador(semilla), estado="listo", angulo=0.0, dir=1,
        vidas=VIDAS_MAX, puntos=0, combo=0, mejor_combo=0, aciertos=0,
        perfectos=0, fallos=0, evento=None, evento_n=0, ganado=0,
        vida_extra=False, centro=0.0, ancho=ANCHO_INICIAL, vel=VEL_INICIAL,
        tmax=TIEMPO_INICIAL, tiempo=TIEMPO_INICIAL,
    )
    _nuevo_objetivo()
    return _json()


def estado():
    return _json()


def _fallar(motivo):
    P["vidas"] -= 1
    P["combo"] = 0
    P["fallos"] += 1
    _evento(motivo)
    if P["vidas"] <= 0:
        P["estado"] = "fin"
    else:
        _nuevo_objetivo()


def avanzar(segundos):
    """Hace pasar el tiempo (solo si se está jugando)."""
    if P["estado"] != "jugando":
        return _json()
    dt = min(max(float(segundos), 0.0), DT_MAX)
    P["angulo"] = (P["angulo"] + P["dir"] * P["vel"] * dt) % 360.0
    P["tiempo"] -= dt
    if P["tiempo"] <= 0:
        _fallar("tiempo")
    return _json()


def tocar():
    """Pulsación del jugador: empieza la partida o intenta parar la aguja."""
    if P["estado"] == "listo":
        P["estado"] = "jugando"
        return _json()
    if P["estado"] != "jugando":
        return _json()
    distancia = abs(_diferencia(P["angulo"], P["centro"]))
    if distancia <= P["ancho"] / 2.0 + TOLERANCIA:
        perfecto = distancia <= P["ancho"] * FRACCION_PERFECTO
        P["aciertos"] += 1
        P["combo"] += 1
        P["mejor_combo"] = max(P["mejor_combo"], P["combo"])
        ganado = (20 if perfecto else 10) * multiplicador(P["combo"])
        P["puntos"] += ganado
        if perfecto:
            P["perfectos"] += 1
        vida_extra = False
        if P["aciertos"] % 8 == 0 and P["vidas"] < VIDAS_MAX:
            P["vidas"] += 1
            vida_extra = True
        if P["aciertos"] % 5 == 0:
            P["dir"] = -P["dir"]
        _evento("perfecto" if perfecto else "acierto", ganado, vida_extra)
        _nuevo_objetivo()
    else:
        _fallar("fallo")
    return _json()


# --------------------------------------------------------------------------
# Resultado, texto para compartir y estadísticas
# --------------------------------------------------------------------------
def _miles(n):
    return "{:,}".format(int(n)).replace(",", ".")


def texto_compartir():
    """Resumen de la partida terminada (vacío si aún se está jugando)."""
    if P.get("estado") != "fin":
        return ""
    return "\n".join([
        "MANECILLA · %s puntos" % _miles(P["puntos"]),
        "%d aciertos (%d perfectos) · %d fallos" % (P["aciertos"], P["perfectos"], P["fallos"]),
        "Combo máximo: %d" % P["mejor_combo"],
    ])


def registrar_partida(estadisticas_json, puntos, aciertos, perfectos, mejor_combo):
    """Suma una partida terminada a las estadísticas guardadas."""
    e = {"partidas": 0, "mejor": 0, "mejor_combo": 0, "aciertos": 0, "perfectos": 0}
    try:
        guardadas = json.loads(estadisticas_json)
        if isinstance(guardadas, dict):
            for clave in e:
                valor = guardadas.get(clave, 0)
                e[clave] = int(valor) if isinstance(valor, (int, float)) and valor >= 0 else 0
    except (ValueError, TypeError):
        pass
    puntos, aciertos = max(0, int(puntos)), max(0, int(aciertos))
    perfectos, mejor_combo = max(0, int(perfectos)), max(0, int(mejor_combo))
    e["nuevo_record"] = puntos > e["mejor"]
    e["partidas"] += 1
    e["mejor"] = max(e["mejor"], puntos)
    e["mejor_combo"] = max(e["mejor_combo"], mejor_combo)
    e["aciertos"] += aciertos
    e["perfectos"] += perfectos
    return json.dumps(e)

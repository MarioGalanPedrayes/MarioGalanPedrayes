"""FAROS DE NIEBLA: lógica del juego (Python 3, sin dependencias externas).

Hay un código oculto de 4 faros. Cada faro tiene uno de 6 símbolos y ningún
símbolo se repite. Tienes 7 intentos para descubrirlo. Tras cada intento
recibes dos números:
  - exactos:     símbolos correctos que están en su sitio.
  - desplazados: símbolos correctos que están en otro sitio.
Además dispones de 3 sondas: preguntas si un símbolo está en el código o no.
Cada sonda que uses resta puntos.

El reto diario usa la fecha como semilla, así que todo el mundo recibe el mismo
código el mismo día. Para que el resultado sea idéntico en cualquier versión de
Python, el generador de números aleatorios está escrito aquí (no usa `random`).

Toda la lógica vive en este archivo. La página (script.js) solo dibuja y llama
a las funciones públicas, que devuelven texto JSON.
"""
import json
from datetime import date, timedelta

NUM_SIMBOLOS = 6
LONGITUD = 4
MAX_INTENTOS = 7
MAX_SONDAS = 3
NOMBRES = ["Círculo", "Rombo", "Triángulo", "Cuadrado", "Estrella", "Cruz"]

_M32 = 0xFFFFFFFF


class Generador:
    """Generador pseudoaleatorio de 32 bits (algoritmo mulberry32, dominio público)."""

    def __init__(self, semilla):
        self.estado = int(semilla) & _M32

    def siguiente(self):
        """Devuelve un número decimal en [0, 1)."""
        self.estado = (self.estado + 0x6D2B79F5) & _M32
        t = self.estado
        t = ((t ^ (t >> 15)) * (1 | t)) & _M32
        t = ((t + (((t ^ (t >> 7)) * (61 | t)) & _M32)) & _M32) ^ t
        return ((t ^ (t >> 14)) & _M32) / 4294967296


def crear_codigo(semilla):
    """Baraja los 6 símbolos (Fisher-Yates) y se queda con los 4 primeros."""
    gen = Generador(semilla)
    simbolos = list(range(NUM_SIMBOLOS))
    for i in range(len(simbolos) - 1, 0, -1):
        j = int(gen.siguiente() * (i + 1))
        simbolos[i], simbolos[j] = simbolos[j], simbolos[i]
    return simbolos[:LONGITUD]


def evaluar(codigo, intento):
    """Compara un intento con el código. Ambos tienen símbolos sin repetir."""
    exactos = sum(1 for a, b in zip(codigo, intento) if a == b)
    en_comun = len(set(codigo) & set(intento))
    return exactos, en_comun - exactos


# --------------------------------------------------------------------------
# Estado de la partida actual
# --------------------------------------------------------------------------
PARTIDA = {}


def _puntuacion():
    if PARTIDA.get("estado") != "ganada":
        return 0
    bruto = 1000 - 100 * (len(PARTIDA["intentos"]) - 1) - 120 * len(PARTIDA["sondas"])
    return max(50, bruto)


def _estado_json(error=None):
    p = PARTIDA
    terminada = p["estado"] != "jugando"
    datos = {
        "modo": p["modo"],
        "semilla": p["semilla"],
        "longitud": LONGITUD,
        "max_intentos": MAX_INTENTOS,
        "max_sondas": MAX_SONDAS,
        "intentos": p["intentos"],
        "sondas": p["sondas"],
        "sondas_restantes": MAX_SONDAS - len(p["sondas"]),
        "estado": p["estado"],
        "puntos": _puntuacion(),
        "codigo": p["codigo"] if terminada else None,
        "error": error,
    }
    return json.dumps(datos, ensure_ascii=False)


def nueva_partida(semilla, modo):
    """Empieza una partida. modo: 'diario' o 'practica'."""
    semilla = int(semilla)
    PARTIDA.clear()
    PARTIDA.update(
        semilla=semilla,
        modo="diario" if modo == "diario" else "practica",
        codigo=crear_codigo(semilla),
        intentos=[],
        sondas=[],
        estado="jugando",
    )
    return _estado_json()


def restaurar(semilla, modo, intentos_json, sondas_json):
    """Reconstruye una partida guardada repitiendo sus intentos y sondas."""
    nueva_partida(semilla, modo)
    try:
        intentos = json.loads(intentos_json)
        sondas = json.loads(sondas_json)
    except ValueError:
        return nueva_partida(semilla, modo)
    for simbolo in sondas:
        usar_sonda(simbolo)
    for intento in intentos:
        enviar_intento(json.dumps(intento))
    return _estado_json()


def _validar_intento(intento):
    if len(intento) != LONGITUD:
        return "Coloca los %d símbolos antes de probar." % LONGITUD
    if any(s < 0 or s >= NUM_SIMBOLOS for s in intento):
        return "Hay un símbolo que no existe."
    if len(set(intento)) != LONGITUD:
        return "Cada símbolo solo puede aparecer una vez."
    return None


def enviar_intento(intento_json):
    """Evalúa un intento (lista JSON de 4 números del 0 al 5)."""
    if PARTIDA.get("estado") != "jugando":
        return _estado_json("La partida ya ha terminado.")
    try:
        intento = [int(s) for s in json.loads(intento_json)]
    except (ValueError, TypeError):
        return _estado_json("Intento no válido.")
    problema = _validar_intento(intento)
    if problema:
        return _estado_json(problema)
    exactos, desplazados = evaluar(PARTIDA["codigo"], intento)
    PARTIDA["intentos"].append(
        {"intento": intento, "exactos": exactos, "desplazados": desplazados}
    )
    if exactos == LONGITUD:
        PARTIDA["estado"] = "ganada"
    elif len(PARTIDA["intentos"]) >= MAX_INTENTOS:
        PARTIDA["estado"] = "perdida"
    return _estado_json()


def usar_sonda(simbolo):
    """Gasta una sonda: dice si el símbolo está en el código (sin decir dónde)."""
    if PARTIDA.get("estado") != "jugando":
        return _estado_json("La partida ya ha terminado.")
    try:
        simbolo = int(simbolo)
    except (ValueError, TypeError):
        return _estado_json("Símbolo no válido.")
    if simbolo < 0 or simbolo >= NUM_SIMBOLOS:
        return _estado_json("Ese símbolo no existe.")
    if len(PARTIDA["sondas"]) >= MAX_SONDAS:
        return _estado_json("No te quedan sondas.")
    if any(s["simbolo"] == simbolo for s in PARTIDA["sondas"]):
        return _estado_json("Ya has sondeado ese símbolo.")
    PARTIDA["sondas"].append(
        {"simbolo": simbolo, "presente": simbolo in PARTIDA["codigo"]}
    )
    return _estado_json()


# --------------------------------------------------------------------------
# Resultado para compartir y estadísticas
# --------------------------------------------------------------------------
def compartir_texto():
    """Resumen en emojis, sin revelar el código (vacío si aún se está jugando)."""
    p = PARTIDA
    if not p or p["estado"] == "jugando":
        return ""
    if p["modo"] == "diario":
        s = str(p["semilla"])
        etiqueta = "Reto %s-%s-%s" % (s[:4], s[4:6], s[6:8])
    else:
        etiqueta = "Práctica"
    n = len(p["intentos"])
    resultado = ("%d/%d" % (n, MAX_INTENTOS)) if p["estado"] == "ganada" else "X/%d" % MAX_INTENTOS
    k = len(p["sondas"])
    cabecera = "FAROS DE NIEBLA · %s · %s · %d sonda%s" % (
        etiqueta, resultado, k, "" if k == 1 else "s")
    filas = []
    for i in p["intentos"]:
        vacios = LONGITUD - i["exactos"] - i["desplazados"]
        filas.append("🟡" * i["exactos"] + "⚪" * i["desplazados"] + "⚫" * vacios)
    return "\n".join([cabecera] + filas)


def actualizar_estadisticas(estadisticas_json, fecha_iso, ganada, puntos):
    """Suma una partida del reto diario y recalcula la racha de victorias.

    La racha son los días seguidos ganados: si ayer ganaste, hoy suma uno;
    si falta algún día o pierdes, vuelve a empezar.
    """
    e = {
        "jugadas": 0,
        "ganadas": 0,
        "racha": 0,
        "mejor_racha": 0,
        "mejor_puntuacion": 0,
        "ultima_victoria": None,
    }
    try:
        guardadas = json.loads(estadisticas_json)
        if isinstance(guardadas, dict):
            e.update(guardadas)
    except (ValueError, TypeError):
        pass
    e["jugadas"] += 1
    if ganada:
        e["ganadas"] += 1
        ayer = (date.fromisoformat(fecha_iso) - timedelta(days=1)).isoformat()
        e["racha"] = e["racha"] + 1 if e["ultima_victoria"] == ayer else 1
        e["ultima_victoria"] = fecha_iso
        e["mejor_racha"] = max(e["mejor_racha"], e["racha"])
        e["mejor_puntuacion"] = max(e["mejor_puntuacion"], int(puntos))
    else:
        e["racha"] = 0
    return json.dumps(e)

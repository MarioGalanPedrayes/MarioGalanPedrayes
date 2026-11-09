"""MONTAÑA DE XANAS: lógica del juego (Python 3, sin dependencias externas).

Aventura 2D vista desde arriba. Recorres una montaña con una aldea, un prado,
un bosque y una gruta. En la hierba alta te salen al paso criaturas del folclore
(todas inventadas aquí). No se las vence: se las TRANQUILIZA en un duelo por
turnos, o se les hace una OFRENDA, y se hacen amigas. El objetivo es completar
el registro de 12 especies.

Reglas del duelo:

  - Tres elementos que se ganan en círculo: Bosque gana a Roca, Roca gana a
    Niebla y Niebla gana a Bosque. Ventaja = x1,5 de efecto; desventaja = x0,67.
  - Cada criatura tiene tres gestos según su elemento: uno básico, uno fuerte
    (pocos usos) y uno de resguardo que reduce a la mitad el siguiente golpe.
  - El "ánimo" es la vida. Si el ánimo de la criatura salvaje llega a 0 se
    tranquiliza y se hace amiga. Si el de la tuya llega a 0, se cansa y entra
    otra; si se cansan todas, vuelves a la fuente de la aldea sin perder nada.
  - Ofrenda: cuesta 1 ofrenda y la criatura la acepta con más probabilidad
    cuanto menos ánimo le queda. Siempre se puede ganar sin ofrendas.
  - Se puede huir o cambiar de criatura (cambiar gasta el turno).

Cada día hay un VISITANTE en el claro de la cumbre, igual para todos (la fecha
es la semilla). Hacerse amiga de él cuenta para la racha de días.

Toda la lógica vive en este archivo. Para que el azar sea idéntico en cualquier
versión de Python, el generador pseudoaleatorio está escrito aquí (no usa
`random`). script.js solo dibuja y llama a las funciones públicas, que
devuelven texto JSON (salvo `semilla_del_dia`, `racha_vigente`, `guardar` y
`compartir_texto`).
"""
import json
from datetime import date, timedelta

_M32 = 0xFFFFFFFF
ANCHO, ALTO = 34, 26
MAX_EQUIPO = 3
NIVEL_MAX = 12
OFRENDAS_INICIO = 6
OFRENDAS_MAX = 12
INICIO = (16, 22)
CLARO = (16, 3)
VIDA_ENCUENTRO = 0.22          # probabilidad de encuentro en hierba alta
PASOS_SIN_ENCUENTRO = 3        # pasos de gracia tras cada encuentro
PROB_HUIR = 0.75

ELEMENTOS = ["Bosque", "Roca", "Niebla"]
ZONAS = ["Prado", "Bosque", "Gruta"]
NIVELES_ZONA = [(2, 4), (4, 6), (6, 8)]
NIVEL_VISITANTE = 7

# (nombre, poder, usos). Poder 0 = resguardo.
GESTOS = [
    [("Zarcillo", 12, 25), ("Raigambre", 18, 5), ("Resguardo de hojas", 0, 4)],
    [("Cabezazo", 12, 25), ("Derrumbe", 18, 5), ("Coraza de piedra", 0, 4)],
    [("Soplo", 12, 25), ("Bruma densa", 18, 5), ("Velo de niebla", 0, 4)],
]
USOS_MAX = [25, 5, 4]

# ---------------------------------------------------------------- especies
# id, nombre, elemento, zona, ánimo base, fuerza base, color, forma, descripción
_DATOS = [
    (0, "Trasguín", 0, 0, 22, 9, "#6b8f3a", "duende", "Un duende pequeño que cambia las cosas de sitio cuando nadie mira."),
    (1, "Guirrio", 1, 0, 26, 8, "#8d8a80", "guijarro", "Un guijarro redondo que rueda cuesta abajo solo por diversión."),
    (2, "Nubecilla", 2, 0, 20, 10, "#b8c4cf", "nube", "Un jirón de niebla que se ha quedado dormido en el prado."),
    (3, "Abeyín", 0, 0, 21, 10, "#d9b44a", "luz", "Una chispa amarilla que zumba entre las flores."),
    (4, "Busgosín", 0, 1, 28, 9, "#4f7a3b", "seta", "Espíritu del bosque con sombrero de seta y paso silencioso."),
    (5, "Raigal", 1, 1, 30, 8, "#7a5a3a", "raiz", "Una raíz vieja que ha aprendido a caminar."),
    (6, "Ñublín", 2, 1, 24, 11, "#9fb3c8", "gota", "Una gota de rocío del tamaño de una manzana."),
    (7, "Culebrín", 1, 1, 27, 10, "#a0763c", "serpiente", "Serpiente pequeña que guarda un tesoro diminuto."),
    (8, "Mineru", 1, 2, 34, 9, "#5b6470", "piedra", "Minero de bigotes de musgo que habla con las paredes."),
    (9, "Eco", 2, 2, 26, 12, "#7d6fa8", "eco", "Una voz sin dueño que repite lo que oye."),
    (10, "Musgón", 0, 2, 30, 10, "#3f6b4a", "musgo", "Un montón de musgo con muchas ganas de crecer."),
    (11, "Xaniella", 2, 2, 30, 12, "#5f9fb5", "xana", "La pequeña xana de la gruta, guardiana de la fuente escondida."),
]
ESPECIES = [{"id": i, "nombre": n, "elem": e, "zona": z, "hp": h, "atk": a,
             "color": c, "forma": f, "desc": d} for i, n, e, z, h, a, c, f, d in _DATOS]
N_ESPECIES = len(ESPECIES)

# --------------------------------------------------------------------- mapa
SUELO = set(".,pbcFD")      # casillas que se pueden pisar
NOMBRE_CASILLA = {".": "camino", ",": "césped", "p": "hierba alta", "b": "maleza del bosque",
                  "c": "musgo de la gruta", "F": "la fuente", "D": "el claro del visitante"}


def _construir_mapa():
    g = [["T"] * ANCHO for _ in range(ALTO)]

    def rect(x0, y0, x1, y1, ch):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                g[y][x] = ch

    rect(12, 19, 21, 24, ",")                     # aldea
    rect(4, 10, 29, 17, ",")                      # prado
    rect(2, 2, 13, 8, ",")                        # bosque
    rect(20, 2, 31, 8, ",")                       # gruta
    rect(14, 2, 18, 4, ",")                       # claro de la cumbre
    # Árboles y rocas sueltos (patrón fijo, nunca dos juntos, para no encerrar casillas).
    for y in range(ALTO):
        for x in range(ANCHO):
            if g[y][x] != ",":
                continue
            if 4 <= x <= 29 and 10 <= y <= 17 and (x * 3 + y * 7) % 11 == 0:
                g[y][x] = "T"
            elif x <= 13 and y <= 8 and (x * 5 + y * 11) % 9 == 0:
                g[y][x] = "T"
            elif x >= 20 and y <= 8 and (x * 5 + y * 11) % 9 == 0:
                g[y][x] = "#"
    # Parches de hierba alta (x0, y0, x1, y1): solo sobre césped libre.
    parches = [("p", (5, 11, 9, 13)), ("p", (11, 10, 14, 12)), ("p", (10, 14, 14, 16)),
               ("p", (18, 11, 22, 13)), ("p", (18, 15, 23, 17)), ("p", (25, 15, 29, 17)),
               ("p", (5, 15, 8, 17)), ("p", (24, 10, 29, 11)),
               ("b", (3, 3, 6, 5)), ("b", (8, 2, 12, 4)), ("b", (3, 7, 7, 8)), ("b", (9, 6, 13, 8)),
               ("c", (21, 3, 24, 5)), ("c", (26, 2, 30, 4)), ("c", (22, 7, 26, 8)), ("c", (28, 6, 31, 8))]
    for ch, (x0, y0, x1, y1) in parches:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if g[y][x] == ",":
                    g[y][x] = ch
    rect(24, 12, 27, 14, "W")                     # estanque
    for (x, y) in [(13, 20), (14, 20), (19, 20), (20, 20)]:
        g[y][x] = "H"
    for y in range(4, 25):                        # camino central
        g[y][16] = "."
    g[9][8] = "."                                 # enlace prado-bosque
    g[9][26] = "."                                # enlace prado-gruta
    g[8][8] = "."
    g[8][26] = "."
    g[22][18] = "F"                               # fuente de la aldea
    g[CLARO[1]][CLARO[0]] = "D"
    return ["".join(f) for f in g]


MAPA = _construir_mapa()


def _zona_nombre(x, y):
    if y >= 18:
        return "Aldea"
    if y <= 8:
        if x <= 14:
            return "Bosque"
        if x >= 19:
            return "Gruta"
        return "Cumbre"
    return "Prado"


def _lugar(x, y):
    return "%s, %s" % (_zona_nombre(x, y), NOMBRE_CASILLA.get(MAPA[y][x], "terreno"))


# ------------------------------------------------- generador aleatorio
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


def semilla_del_dia(fecha_iso):
    """Convierte una fecha ISO ("2026-11-08") en una semilla de 32 bits (hash FNV-1a)."""
    h = 0x811C9DC5
    for b in ("xanas:" + str(fecha_iso)).encode("utf-8"):
        h = ((h ^ b) * 0x01000193) & _M32
    return h


def _visitante_del_dia(fecha_iso):
    return int(Generador(semilla_del_dia(fecha_iso)).siguiente() * N_ESPECIES)


def _azar():
    """Siguiente número del generador de la partida (su estado se guarda)."""
    g = Generador(_s["rng"])
    v = g.siguiente()
    _s["rng"] = g.estado
    return v


# ------------------------------------------------------------ criaturas
def _hp_max(c):
    return ESPECIES[c["e"]]["hp"] + 4 * (c["n"] - 1)


def _atk(c):
    return ESPECIES[c["e"]]["atk"] * (1 + 0.08 * (c["n"] - 1))


def _crear(esp, nivel):
    c = {"e": esp, "n": nivel, "xp": 0, "hp": 0, "pp": list(USOS_MAX)}
    c["hp"] = _hp_max(c)
    return c


def _ventaja(att, defe):
    """1,5 si el elemento atacante gana; 0,67 si pierde; 1 si no."""
    if (att + 1) % 3 == defe:
        return 1.5
    if (defe + 1) % 3 == att:
        return 0.67
    return 1.0


def _nombre(c):
    return ESPECIES[c["e"]]["nombre"]


def _vista(c, idx=None):
    return {"id": idx, "e": c["e"], "nombre": _nombre(c), "elem": ESPECIES[c["e"]]["elem"],
            "n": c["n"], "xp": c["xp"], "xp_sig": 10 * c["n"], "hp": c["hp"], "hp_max": _hp_max(c),
            "pp": list(c["pp"])}


def _curar_todo():
    for c in _s["criaturas"]:
        c["hp"] = _hp_max(c)
        c["pp"] = list(USOS_MAX)


def _dar_xp(c, cantidad, msgs):
    if c["n"] >= NIVEL_MAX:
        return
    c["xp"] += cantidad
    while c["n"] < NIVEL_MAX and c["xp"] >= 10 * c["n"]:
        c["xp"] -= 10 * c["n"]
        c["n"] += 1
        c["hp"] = min(_hp_max(c), c["hp"] + _hp_max(c) // 4)
        msgs.append("¡%s sube al nivel %d!" % (_nombre(c), c["n"]))
    if c["n"] >= NIVEL_MAX:
        c["xp"] = 0


# -------------------------------------------------------------- partida
_s = None


def _nuevo_estado(semilla=1):
    return {"fase": "inicio", "x": INICIO[0], "y": INICIO[1], "dir": "N",
            "criaturas": [], "equipo": [], "registro": [0] * N_ESPECIES,
            "ofrendas": OFRENDAS_INICIO, "pasos": 0, "desde_enc": 0,
            "rng": int(semilla) & _M32, "duelo": None, "log": [],
            "dia": {"fecha": "", "visitante": 0, "hecho": False}, "duelos": 0}


def _completo():
    return all(r == 2 for r in _s["registro"])


def _estado(error=None, nuevos=None):
    s = _s
    x, y = s["x"], s["y"]
    d = {
        "fase": s["fase"], "x": x, "y": y, "dir": s["dir"], "lugar": _lugar(x, y), "casilla": MAPA[y][x],
        "equipo": [_vista(s["criaturas"][i], i) for i in s["equipo"]],
        "reserva": [_vista(c, i) for i, c in enumerate(s["criaturas"]) if i not in s["equipo"]],
        "registro": list(s["registro"]), "amigas": sum(1 for r in s["registro"] if r == 2),
        "vistas": sum(1 for r in s["registro"] if r >= 1), "total": N_ESPECIES, "completo": _completo(),
        "ofrendas": s["ofrendas"], "ofrendas_max": OFRENDAS_MAX, "pasos": s["pasos"], "duelos": s["duelos"],
        "dia": {"fecha": s["dia"]["fecha"], "hecho": s["dia"]["hecho"],
                "visitante": s["dia"]["visitante"] if s["registro"][s["dia"]["visitante"]] >= 1 else -1},
        "log": s["log"][-8:], "nuevos": nuevos or [],
    }
    if error:
        d["error"] = error
    du = s["duelo"]
    if du:
        w = du["salvaje"]
        d["duelo"] = {"salvaje": _vista(w), "activo": du["activo"], "debe_cambiar": du["debe_cambiar"],
                      "escudo_j": du["escudo_j"], "escudo_s": du["escudo_s"], "visitante": du["visitante"],
                      "zona": du["zona"], "prob_ofrenda": int(round(_prob_ofrenda(w) * 100)),
                      "gestos": [{"nombre": n, "poder": p, "usos_max": u} for n, p, u in GESTOS[
                          ESPECIES[s["criaturas"][s["equipo"][du["activo"]]]["e"]]["elem"]]]}
    return json.dumps(d)


def _log(msgs, texto):
    msgs.append(texto)
    _s["log"].append(texto)
    del _s["log"][:-30]


def datos_estaticos():
    """Mapa, especies, elementos y gestos: no cambian durante la partida."""
    return json.dumps({"ancho": ANCHO, "alto": ALTO, "mapa": MAPA, "especies": ESPECIES,
                       "elementos": ELEMENTOS, "zonas": ZONAS, "gestos": GESTOS,
                       "inicio": list(INICIO), "claro": list(CLARO)})


def nueva_partida(semilla=1):
    """Empieza de cero: hay que elegir criatura inicial."""
    global _s
    _s = _nuevo_estado(semilla)
    return _estado()


def elegir_inicial(i):
    """Elige la primera amiga: 0 Trasguín (Bosque), 1 Guirrio (Roca), 2 Nubecilla (Niebla)."""
    s = _s
    if s["fase"] != "inicio":
        return _estado("Ya has elegido a tu primera amiga.")
    try:
        i = int(i)
    except (ValueError, TypeError):
        return _estado("Elección no válida.")
    if i not in (0, 1, 2):
        return _estado("Elección no válida.")
    msgs = []
    s["criaturas"].append(_crear(i, 3))
    s["equipo"] = [0]
    s["registro"][i] = 2
    s["fase"] = "mundo"
    _log(msgs, "%s decide acompañarte por la montaña. Busca criaturas en la hierba alta." % ESPECIES[i]["nombre"])
    return _estado(None, msgs)


def fijar_dia(fecha_iso):
    """Indica la fecha de hoy. Si cambia el día, aparece un visitante nuevo en el claro."""
    s = _s
    try:
        date.fromisoformat(fecha_iso)
    except (ValueError, TypeError):
        return _estado("Fecha no válida.")
    if s["dia"]["fecha"] != fecha_iso:
        s["dia"] = {"fecha": fecha_iso, "visitante": _visitante_del_dia(fecha_iso), "hecho": False}
    return _estado()


# ---------------------------------------------------------------- mundo
_DIRS = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "O": (-1, 0)}


def _salvaje_de_zona(zona):
    pool = [e for e in ESPECIES if e["zona"] == zona]
    esp = pool[int(_azar() * len(pool))]["id"]
    lo, hi = NIVELES_ZONA[zona]
    return _crear(esp, lo + int(_azar() * (hi - lo + 1)))


def _empezar_duelo(salvaje, zona, visitante, msgs):
    s = _s
    activo = next((p for p, i in enumerate(s["equipo"]) if s["criaturas"][i]["hp"] > 0), 0)
    s["duelo"] = {"salvaje": salvaje, "activo": activo, "debe_cambiar": False,
                  "escudo_j": False, "escudo_s": False, "visitante": visitante, "zona": zona}
    s["fase"] = "duelo"
    s["desde_enc"] = 0
    s["registro"][salvaje["e"]] = max(s["registro"][salvaje["e"]], 1)


def mover(direccion):
    """Da un paso (N, S, E u O). Puede provocar un encuentro o curar en la fuente."""
    s = _s
    if s["fase"] != "mundo":
        return _estado("Ahora no puedes caminar.")
    if direccion not in _DIRS:
        return _estado("Dirección no válida.")
    dx, dy = _DIRS[direccion]
    s["dir"] = direccion
    nx, ny = s["x"] + dx, s["y"] + dy
    if not (0 <= nx < ANCHO and 0 <= ny < ALTO) or MAPA[ny][nx] not in SUELO:
        return _estado()
    s["x"], s["y"] = nx, ny
    s["pasos"] += 1
    s["desde_enc"] += 1
    msgs = []
    c = MAPA[ny][nx]
    if c == "F":
        falta = any(x["hp"] < _hp_max(x) for x in s["criaturas"]) or s["ofrendas"] < 3
        _curar_todo()
        s["ofrendas"] = max(s["ofrendas"], 3)
        _log(msgs, "Bebéis de la fuente: tu equipo descansa del todo." if falta else "Agua fresca. Todos estáis bien.")
    elif c == "D":
        if not s["dia"]["hecho"] and s["dia"]["fecha"]:
            esp = s["dia"]["visitante"]
            _empezar_duelo(_crear(esp, NIVEL_VISITANTE), 2, True, msgs)
            _log(msgs, "¡El visitante del día te estaba esperando en el claro!")
        else:
            _log(msgs, "El claro está en calma. Vuelve mañana: llegará otro visitante.")
    elif c in "pbc" and s["desde_enc"] >= PASOS_SIN_ENCUENTRO and _azar() < VIDA_ENCUENTRO:
        zona = "pbc".index(c)
        _empezar_duelo(_salvaje_de_zona(zona), zona, False, msgs)
        _log(msgs, "¡Algo se mueve entre la hierba!")
    return _estado(None, msgs)


def poner_en_equipo(idx_criatura, posicion):
    """Mete a una criatura de la reserva en el equipo (sustituye a la de esa posición)."""
    s = _s
    if s["fase"] != "mundo":
        return _estado("Solo puedes cambiar el equipo caminando por el mundo.")
    try:
        idx, pos = int(idx_criatura), int(posicion)
    except (ValueError, TypeError):
        return _estado("Elección no válida.")
    if not (0 <= idx < len(s["criaturas"])) or idx in s["equipo"]:
        return _estado("Esa criatura ya está en el equipo.")
    if pos < len(s["equipo"]):
        if pos < 0:
            return _estado("Posición no válida.")
        s["equipo"][pos] = idx
    elif pos == len(s["equipo"]) and pos < MAX_EQUIPO:
        s["equipo"].append(idx)
    else:
        return _estado("Posición no válida.")
    return _estado()


def quitar_del_equipo(posicion):
    """Manda una criatura del equipo a la reserva (siempre queda al menos una)."""
    s = _s
    if s["fase"] != "mundo":
        return _estado("Solo puedes cambiar el equipo caminando por el mundo.")
    try:
        pos = int(posicion)
    except (ValueError, TypeError):
        return _estado("Elección no válida.")
    if len(s["equipo"]) <= 1 or not (0 <= pos < len(s["equipo"])):
        return _estado("El equipo necesita al menos una criatura.")
    s["equipo"].pop(pos)
    return _estado()


# ---------------------------------------------------------------- duelo
def _prob_ofrenda(w):
    ratio = w["hp"] / _hp_max(w)
    return min(0.9, 0.25 + 0.65 * (1 - ratio))


def _golpe(att, gesto, defe, escudo):
    """Daño de un gesto de ataque. Devuelve (daño, multiplicador)."""
    _, poder, _ = GESTOS[ESPECIES[att["e"]]["elem"]][gesto]
    mult = _ventaja(ESPECIES[att["e"]]["elem"], ESPECIES[defe["e"]]["elem"])
    v = 0.9 + 0.2 * _azar()
    d = poder * _atk(att) / 10 * mult * v
    if escudo:
        d /= 2
    return max(1, int(round(d))), mult


def _usar(att, gesto, defe, escudo_def, msgs, es_mio):
    """Un gesto de `att` contra `defe`. Devuelve True si activa el resguardo propio."""
    nombre, poder, _ = GESTOS[ESPECIES[att["e"]]["elem"]][gesto]
    att["pp"][gesto] -= 1
    if poder == 0:
        _log(msgs, "%s usa %s: se prepara para el siguiente golpe." % (_nombre(att), nombre))
        return True
    dmg, mult = _golpe(att, gesto, defe, escudo_def)
    defe["hp"] = max(0, defe["hp"] - dmg)
    extra = " Es muy eficaz." if mult > 1 else (" No es muy eficaz." if mult < 1 else "")
    amort = " El resguardo lo amortigua." if escudo_def else ""
    _log(msgs, "%s usa %s y resta %d de ánimo a %s.%s%s" % (_nombre(att), nombre, dmg, _nombre(defe), extra, amort))
    return False


def _final_duelo(msgs, extra_ofrendas=1):
    s = _s
    s["duelo"] = None
    s["fase"] = "mundo"
    s["duelos"] += 1
    s["ofrendas"] = min(OFRENDAS_MAX, s["ofrendas"] + extra_ofrendas)
    for c in s["criaturas"]:
        c["pp"] = list(USOS_MAX)


def _amistad(msgs, por_ofrenda):
    s = _s
    du = s["duelo"]
    w = du["salvaje"]
    esp = w["e"]
    activa = s["criaturas"][s["equipo"][du["activo"]]]
    if s["registro"][esp] == 2:
        _log(msgs, "%s ya es tu amiga. Acepta el gesto y se marcha en paz." % _nombre(w))
    else:
        nueva = {"e": esp, "n": w["n"], "xp": 0, "hp": 0, "pp": list(USOS_MAX)}
        nueva["hp"] = _hp_max(nueva)
        s["criaturas"].append(nueva)
        if len(s["equipo"]) < MAX_EQUIPO:
            s["equipo"].append(len(s["criaturas"]) - 1)
            _log(msgs, "¡%s se hace amiga tuya y se une al equipo!" % _nombre(w))
        else:
            _log(msgs, "¡%s se hace amiga tuya! Se queda en la reserva." % _nombre(w))
        s["registro"][esp] = 2
    if du["visitante"]:
        s["dia"]["hecho"] = True
        _log(msgs, "Has recibido al visitante del día.")
    _dar_xp(activa, w["n"] * 4 + 4, msgs)
    _final_duelo(msgs)
    if _completo():
        _log(msgs, "¡Has completado el registro de la montaña: 12 de 12!")


def _derrota(msgs):
    s = _s
    _log(msgs, "Todas tus criaturas están cansadas. Vuelves a la fuente de la aldea y descansáis; no se pierde nada.")
    s["x"], s["y"] = INICIO
    _final_duelo(msgs, 0)
    _curar_todo()
    s["ofrendas"] = max(s["ofrendas"], 3)


def _turno_salvaje(msgs):
    """La criatura salvaje responde y se comprueba si la tuya se cansa."""
    s = _s
    du = s["duelo"]
    w = du["salvaje"]
    mia = s["criaturas"][s["equipo"][du["activo"]]]
    r = _azar()
    if w["hp"] < _hp_max(w) * 0.4 and w["pp"][2] > 0 and not du["escudo_s"] and r < 0.3:
        gesto = 2
    elif w["pp"][1] > 0 and r < 0.4:
        gesto = 1
    else:
        gesto = 0
    if _usar(w, gesto, mia, du["escudo_j"], msgs, False):
        du["escudo_s"] = True
    else:
        du["escudo_j"] = False
    if mia["hp"] <= 0:
        _log(msgs, "%s se cansa." % _nombre(mia))
        if any(s["criaturas"][i]["hp"] > 0 for i in s["equipo"]):
            du["debe_cambiar"] = True
            _log(msgs, "Elige a otra criatura del equipo.")
        else:
            _derrota(msgs)


def accion(tipo, arg=0):
    """Acción de duelo: 'atacar' (arg = gesto 0-2), 'ofrecer', 'cambiar' (arg = posición) o 'huir'."""
    s = _s
    if s["fase"] != "duelo":
        return _estado("No hay ningún encuentro.")
    du = s["duelo"]
    w = du["salvaje"]
    msgs = []
    try:
        arg = int(arg)
    except (ValueError, TypeError):
        arg = -1
    if du["debe_cambiar"] and tipo != "cambiar":
        return _estado("Tu criatura está cansada: elige a otra del equipo.")
    mia = s["criaturas"][s["equipo"][du["activo"]]]

    if tipo == "atacar":
        if not (0 <= arg <= 2):
            return _estado("Gesto no válido.")
        if mia["pp"][arg] <= 0:
            return _estado("Ese gesto ya no tiene usos en este encuentro.")
        if _usar(mia, arg, w, du["escudo_s"], msgs, True):
            du["escudo_j"] = True
        else:
            du["escudo_s"] = False
        if w["hp"] <= 0:
            _log(msgs, "%s se tranquiliza." % _nombre(w))
            _amistad(msgs, False)
        else:
            _turno_salvaje(msgs)
    elif tipo == "ofrecer":
        if s["ofrendas"] <= 0:
            return _estado("No te quedan ofrendas.")
        s["ofrendas"] -= 1
        if _azar() < _prob_ofrenda(w):
            _log(msgs, "Le ofreces una ofrenda y %s la acepta." % _nombre(w))
            _amistad(msgs, True)
        else:
            _log(msgs, "%s olisquea la ofrenda, pero todavía no se fía." % _nombre(w))
            _turno_salvaje(msgs)
    elif tipo == "cambiar":
        if not (0 <= arg < len(s["equipo"])) or arg == du["activo"]:
            return _estado("Elige a otra criatura del equipo.")
        if s["criaturas"][s["equipo"][arg]]["hp"] <= 0:
            return _estado("Esa criatura está cansada.")
        forzado = du["debe_cambiar"]
        du["activo"] = arg
        du["debe_cambiar"] = False
        du["escudo_j"] = False
        _log(msgs, "%s entra en el duelo." % _nombre(s["criaturas"][s["equipo"][arg]]))
        if not forzado:
            _turno_salvaje(msgs)
    elif tipo == "huir":
        if _azar() < PROB_HUIR:
            _log(msgs, "Escapas entre la hierba.")
            _final_duelo(msgs, 0)
        else:
            _log(msgs, "No consigues escapar.")
            _turno_salvaje(msgs)
    else:
        return _estado("Acción no válida.")
    return _estado(None, msgs)


# ------------------------------------------------------ guardado
def guardar():
    """Partida en texto JSON. Si hay un duelo en marcha, no se guarda (la criatura se va)."""
    d = dict(_s)
    d["duelo"] = None
    if d["fase"] == "duelo":
        d["fase"] = "mundo"
    return json.dumps(d)


def _entero(v, lo, hi, por_defecto):
    if isinstance(v, bool) or not isinstance(v, int):
        return por_defecto
    return max(lo, min(hi, v))


def restaurar(raw, semilla=1):
    """Carga una partida guardada. Todo se comprueba: un guardado dañado no rompe nada."""
    global _s
    nuevo = _nuevo_estado(semilla)
    try:
        d = json.loads(raw)
    except (ValueError, TypeError):
        _s = nuevo
        return _estado("El guardado no era válido: empiezas de nuevo.")
    if not isinstance(d, dict):
        _s = nuevo
        return _estado("El guardado no era válido: empiezas de nuevo.")
    criaturas = []
    lista = d.get("criaturas")
    for c in (lista if isinstance(lista, list) else [])[:60]:
        if not isinstance(c, dict):
            continue
        e = c.get("e")
        if isinstance(e, bool) or not isinstance(e, int) or not (0 <= e < N_ESPECIES):
            continue
        n = _entero(c.get("n"), 1, NIVEL_MAX, 0)
        if n < 1:
            continue
        nc = {"e": e, "n": n, "xp": _entero(c.get("xp"), 0, 10 * n, 0), "hp": 0, "pp": list(USOS_MAX)}
        nc["hp"] = _entero(c.get("hp"), 0, _hp_max(nc), _hp_max(nc))
        criaturas.append(nc)
    if not criaturas:
        _s = nuevo
        _s["rng"] = _entero(d.get("rng"), 0, _M32, nuevo["rng"])
        return _estado()
    equipo = []
    for i in d.get("equipo") if isinstance(d.get("equipo"), list) else []:
        if isinstance(i, int) and not isinstance(i, bool) and 0 <= i < len(criaturas) and i not in equipo:
            equipo.append(i)
    equipo = equipo[:MAX_EQUIPO] or [0]
    nuevo["criaturas"], nuevo["equipo"], nuevo["fase"] = criaturas, equipo, "mundo"
    registro = d.get("registro") if isinstance(d.get("registro"), list) else []
    for i in range(N_ESPECIES):
        nuevo["registro"][i] = _entero(registro[i], 0, 2, 0) if i < len(registro) else 0
    for c in criaturas:
        nuevo["registro"][c["e"]] = 2
    x, y = _entero(d.get("x"), 0, ANCHO - 1, INICIO[0]), _entero(d.get("y"), 0, ALTO - 1, INICIO[1])
    if MAPA[y][x] not in SUELO:
        x, y = INICIO
    nuevo["x"], nuevo["y"] = x, y
    nuevo["dir"] = d.get("dir") if d.get("dir") in _DIRS else "N"
    nuevo["ofrendas"] = _entero(d.get("ofrendas"), 0, OFRENDAS_MAX, OFRENDAS_INICIO)
    registro_msgs = d.get("log") if isinstance(d.get("log"), list) else []
    nuevo["log"] = [m[:200] for m in registro_msgs if isinstance(m, str)][-30:]
    nuevo["pasos"] = _entero(d.get("pasos"), 0, 10 ** 9, 0)
    nuevo["duelos"] = _entero(d.get("duelos"), 0, 10 ** 9, 0)
    nuevo["rng"] = _entero(d.get("rng"), 0, _M32, 1)
    dia = d.get("dia") if isinstance(d.get("dia"), dict) else {}
    fecha = dia.get("fecha") if isinstance(dia.get("fecha"), str) else ""
    try:
        if fecha:
            date.fromisoformat(fecha)
    except ValueError:
        fecha = ""
    nuevo["dia"] = {"fecha": fecha, "visitante": _visitante_del_dia(fecha) if fecha else 0,
                    "hecho": bool(dia.get("hecho")) and bool(fecha)}
    _s = nuevo
    if all(criaturas[i]["hp"] <= 0 for i in equipo):
        _curar_todo()
    return _estado()


# ------------------------------------------------- compartir y estadísticas
_EMOJI_ELEM = ["🟩", "🟫", "🟦"]


def compartir_texto():
    """Resultado para compartir sin spoilers: solo el color del elemento de cada amiga."""
    s = _s
    if s is None or s["fase"] == "inicio":
        return ""
    casillas = "".join(_EMOJI_ELEM[ESPECIES[i]["elem"]] if s["registro"][i] == 2 else "⬜" for i in range(N_ESPECIES))
    amigas = sum(1 for r in s["registro"] if r == 2)
    lineas = ["MONTAÑA DE XANAS · " + (s["dia"]["fecha"] or "sin fecha"),
              "Registro %d/%d: %s" % (amigas, N_ESPECIES, casillas),
              "Visitante del día: " + ("recibido ✔" if s["dia"]["hecho"] else "aún sin recibir")]
    return "\n".join(lineas)


def _leer_estadisticas(estadisticas_json):
    e = {"completados": 0, "racha": 0, "mejor_racha": 0, "ultimo_dia": None}
    try:
        guardadas = json.loads(estadisticas_json)
        if isinstance(guardadas, dict):
            for clave in ("completados", "racha", "mejor_racha"):
                v = guardadas.get(clave)
                e[clave] = max(0, v) if isinstance(v, int) and not isinstance(v, bool) else 0
            ultimo = guardadas.get("ultimo_dia")
            if isinstance(ultimo, str):
                date.fromisoformat(ultimo)
                e["ultimo_dia"] = ultimo
    except (ValueError, TypeError):
        pass
    return e


def actualizar_estadisticas(estadisticas_json, fecha_iso):
    """Suma un visitante del día recibido. La racha son los días seguidos con visitante
    recibido; si falta un día vuelve a empezar. Recibirlo dos veces el mismo día no suma."""
    e = _leer_estadisticas(estadisticas_json)
    try:
        hoy = date.fromisoformat(fecha_iso)
    except (ValueError, TypeError):
        return json.dumps(e)
    if e["ultimo_dia"] == hoy.isoformat():
        return json.dumps(e)
    ayer = (hoy - timedelta(days=1)).isoformat()
    e["racha"] = e["racha"] + 1 if e["ultimo_dia"] == ayer else 1
    e["mejor_racha"] = max(e["mejor_racha"], e["racha"])
    e["completados"] += 1
    e["ultimo_dia"] = hoy.isoformat()
    return json.dumps(e)


def racha_vigente(estadisticas_json, hoy_iso):
    """Racha que hay que mostrar hoy: sigue viva si el último visitante fue hoy o ayer."""
    e = _leer_estadisticas(estadisticas_json)
    try:
        hoy = date.fromisoformat(hoy_iso)
    except (ValueError, TypeError):
        return e["racha"]
    ayer = (hoy - timedelta(days=1)).isoformat()
    return e["racha"] if e["ultimo_dia"] in (hoy.isoformat(), ayer) else 0


_s = _nuevo_estado()

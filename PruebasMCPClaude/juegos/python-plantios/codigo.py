"""PLANTÍOS: lógica del juego (Python 3, sin dependencias externas).

Un plantío es un terreno donde se planta y se injerta. Recibes piezas de una
en una y las colocas en el huerto; cuando tres o más piezas iguales quedan
juntas, se fusionan en una de nivel superior. Hay que criar una pieza de nivel
objetivo (por ejemplo, un pumar) antes de que el huerto se llene.

Reglas:

  - Las piezas son de seis niveles: semilla (1), brote (2), plantón (3),
    manzano (4), pumar (5) y pumarada (6). Se ve la pieza actual y las dos
    siguientes.
  - Colocar: eliges una casilla vacía para la pieza actual. Si tras colocarla
    forma con sus vecinas (arriba, abajo, izquierda, derecha) un grupo de 3 o
    más piezas iguales, todo el grupo se fusiona en UNA pieza de nivel
    superior en la casilla donde la pusiste. Con 5 o más piezas el salto es de
    dos niveles ("injerto doble"). La nueva pieza puede fusionarse a su vez con
    otras (cadena).
  - Savia: pieza comodín. Cuenta como cualquier nivel para formar el grupo y
    se gasta en la fusión. Si no hay grupo, se queda esperando en el huerto.
  - Piedras: ocupan casilla. Se deshacen solas cuando una fusión ocurre pegada
    a ellas.
  - Cesto: guarda una pieza. Una vez por turno puedes cambiar la pieza actual
    por la del cesto (si está vacío, la actual se guarda y llega la siguiente).
  - Ganas al criar una pieza del nivel objetivo. Pierdes si el huerto se llena.

Cada partida se comprueba con un jugador automático (un "bot" de una jugada de
anticipación): solo se acepta si logra ganarla, y los turnos que gasta son la
referencia para las estrellas. El reto diario usa la fecha como semilla, así
que todo el mundo recibe la misma sucesión de piezas y piedras el mismo día.
Para que el resultado sea idéntico en cualquier versión de Python, el
generador de números aleatorios está escrito aquí (no usa `random`).

Toda la lógica vive en este archivo. La página (script.js) solo dibuja y llama
a las funciones públicas, que devuelven texto JSON (salvo `semilla_del_dia`,
`racha_vigente` y `compartir_texto`).
"""
import json
from datetime import date, timedelta

MAX_NIVEL = 6
SAVIA = 8
PIEDRA = 9
PISTAS_MAX = 3
INTENTOS_GENERACION = 12
LIMITE_TURNOS = 400

# Catálogo de piezas. La forma se dibuja con CSS, así que cada nivel se
# distingue por su forma y su número, no solo por el color.
# "cuadro" es el emoji que se usa en el texto para compartir.
PIEZAS = {
    1: {"nombre": "semilla", "forma": "circulo", "color": "#a9a16b", "tinta": "#1f2933", "cuadro": "🌱"},
    2: {"nombre": "brote", "forma": "gota", "color": "#7fa650", "tinta": "#1f2933", "cuadro": "🌿"},
    3: {"nombre": "plantón", "forma": "triangulo", "color": "#3f8a5a", "tinta": "#ffffff", "cuadro": "🪴"},
    4: {"nombre": "manzano", "forma": "rombo", "color": "#2f6f73", "tinta": "#ffffff", "cuadro": "🌳"},
    5: {"nombre": "pumar", "forma": "estrella", "color": "#8b4a7a", "tinta": "#ffffff", "cuadro": "🌸"},
    6: {"nombre": "pumarada", "forma": "cruz", "color": "#a83b2c", "tinta": "#ffffff", "cuadro": "🍎"},
}
CUADRO_VACIO = "⬜"
CUADRO_PIEDRA = "🪨"
CUADRO_SAVIA = "💧"

# filas, columnas, piedras, nivel objetivo, probabilidad de savia y pesos de
# los niveles 1, 2 y 3 al repartir piezas normales.
NIVELES = {
    "facil": {"nombre": "Cuadro", "filas": 5, "cols": 5, "piedras": 0, "objetivo": 4,
              "savia": 0.10, "pesos": (70, 30, 0)},
    "normal": {"nombre": "Huerto", "filas": 5, "cols": 5, "piedras": 3, "objetivo": 5,
               "savia": 0.05, "pesos": (62, 28, 10)},
    "dificil": {"nombre": "Pumarada", "filas": 5, "cols": 5, "piedras": 4, "objetivo": 5,
                "savia": 0.0, "pesos": (60, 30, 10)},
}
NIVEL_DIARIO = "normal"
NIVEL_PRACTICA = "normal"

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


def semilla_del_dia(fecha_iso):
    """Convierte una fecha ISO ("2026-11-09") en una semilla de 32 bits (hash FNV-1a)."""
    h = 0x811C9DC5
    for b in ("plantios:" + str(fecha_iso)).encode("utf-8"):
        h = ((h ^ b) * 0x01000193) & _M32
    return h


# ------------------------------------------------------------------ reglas
# El huerto es una lista plana de filas*cols casillas: 0 vacía, 1..6 nivel de
# la pieza, SAVIA (8) o PIEDRA (9). La casilla (fila, col) es fila*cols + col.

_VECINOS = {}


def _vecinos(filas, cols):
    """Vecinas ortogonales de cada casilla (se calculan una vez por tamaño)."""
    clave = (filas, cols)
    if clave not in _VECINOS:
        todas = []
        for i in range(filas * cols):
            f, c = divmod(i, cols)
            v = []
            if f > 0:
                v.append(i - cols)
            if f < filas - 1:
                v.append(i + cols)
            if c > 0:
                v.append(i - 1)
            if c < cols - 1:
                v.append(i + 1)
            todas.append(tuple(v))
        _VECINOS[clave] = tuple(todas)
    return _VECINOS[clave]


def _grupo(tab, vec, i, nivel):
    """Casillas conectadas con la i formadas por piezas de ese nivel o savia."""
    visto = {i}
    pila = [i]
    while pila:
        x = pila.pop()
        for y in vec[x]:
            if y not in visto and (tab[y] == nivel or tab[y] == SAVIA):
                visto.add(y)
                pila.append(y)
    return visto


def _fusionar(tab, vec, i, objetivo):
    """Aplica las fusiones en cadena que provoca la pieza recién puesta en i.
    Modifica `tab` y devuelve la lista de fusiones (la última puede alcanzar
    el objetivo, y entonces no se sigue)."""
    eventos = []
    while True:
        v = tab[i]
        if v == SAVIA:
            candidatos = range(MAX_NIVEL - 1, 0, -1)   # la savia elige el nivel más alto posible
        elif 1 <= v < MAX_NIVEL:
            candidatos = (v,)
        else:
            break
        elegido = None
        for nivel in candidatos:
            g = _grupo(tab, vec, i, nivel)
            if len(g) >= 3:
                elegido = (nivel, g)
                break
        if elegido is None:
            break
        nivel, g = elegido
        n = len(g)
        nuevo = min(MAX_NIVEL, nivel + (2 if n >= 5 else 1))
        piedras = set()
        for x in g:
            tab[x] = 0
            for y in vec[x]:
                if tab[y] == PIEDRA:
                    piedras.add(y)
        for y in piedras:
            tab[y] = 0
        tab[i] = nuevo
        eventos.append({"casilla": i, "desde": nivel, "hasta": nuevo, "n": n, "piedras": len(piedras)})
        if nuevo >= objetivo:
            break
    return eventos


def _poner(tab, vec, i, pieza, objetivo):
    """Devuelve (huerto nuevo, fusiones) tras poner la pieza en la casilla i."""
    nuevo = list(tab)
    nuevo[i] = pieza
    return nuevo, _fusionar(nuevo, vec, i, objetivo)


def _alcanzado(tab, objetivo):
    return any(1 <= x <= MAX_NIVEL and x >= objetivo for x in tab)


# ------------------------------------------------------------- generación

def _pieza(semilla, k, cfg):
    """Pieza número k de la sucesión: depende solo de la semilla y de k, así
    que se puede calcular cualquiera sin repetir las anteriores."""
    g = Generador((semilla ^ ((k + 1) * 0x9E3779B1)) & _M32)
    g.siguiente()
    if g.siguiente() < cfg["savia"]:
        return SAVIA
    pesos = cfg["pesos"]
    u = g.siguiente() * sum(pesos)
    acumulado = 0
    for nivel, p in enumerate(pesos, 1):
        acumulado += p
        if u < acumulado:
            return nivel
    return 1


def _piedras(semilla, cfg):
    casillas = list(range(cfg["filas"] * cfg["cols"]))
    g = Generador(semilla ^ 0xA5A5A5A5)
    for i in range(len(casillas) - 1, 0, -1):
        j = int(g.siguiente() * (i + 1))
        casillas[i], casillas[j] = casillas[j], casillas[i]
    return sorted(casillas[:cfg["piedras"]])


def _inicial(semilla, cfg):
    """Estado de partida: huerto con piedras, pieza actual, cesto vacío."""
    tab = [0] * (cfg["filas"] * cfg["cols"])
    for i in _piedras(semilla, cfg):
        tab[i] = PIEDRA
    return {
        "tab": tab,
        "actual": _pieza(semilla, 0, cfg),
        "idx": 1,              # índice de la próxima pieza que saldrá
        "cesto": None,
        "cambio_usado": False,
        "turnos": 0,
    }


# --------------------------------------------------------------- el bot

def _valor(tab, vec):
    """Cuánto vale un huerto para el bot: casillas libres y piezas iguales
    juntas (que están cerca de fusionarse)."""
    v = 0.0
    for i, x in enumerate(tab):
        if x == 0:
            v += 5.0
        elif x == SAVIA:
            v += 2.0
        elif x <= MAX_NIVEL:
            for y in vec[i]:
                if y > i and tab[y] == x:
                    v += 2.0 + 0.5 * x
    return v


def _opciones(est, cfg, semilla):
    """Acciones posibles: [(tipo, pieza que se pondrá, cesto resultante, idx resultante)]."""
    ops = [("poner", est["actual"], est["cesto"], est["idx"])]
    if not est["cambio_usado"]:
        if est["cesto"] is not None:
            ops.append(("cesto", est["cesto"], est["actual"], est["idx"]))
        else:
            ops.append(("cesto", _pieza(semilla, est["idx"], cfg), est["actual"], est["idx"] + 1))
    return ops


def _mejor_colocacion(tab, vec, pieza, objetivo):
    """Mejor casilla para una pieza: (valor, casilla, huerto resultante)."""
    mejor = None
    for i, x in enumerate(tab):
        if x != 0:
            continue
        nuevo, ev = _poner(tab, vec, i, pieza, objetivo)
        if _alcanzado(nuevo, objetivo):
            return 1e9, i, nuevo
        val = _valor(nuevo, vec)
        if mejor is None or val > mejor[0]:
            mejor = (val, i, nuevo)
    return mejor


def _decidir(est, cfg, semilla, profundidad=1):
    """Elige la mejor acción del bot. Con profundidad 2 mira también cómo
    colocaría la pieza siguiente. Devuelve (tipo, casilla) o None si el
    huerto está lleno."""
    vec = _vecinos(cfg["filas"], cfg["cols"])
    objetivo = cfg["objetivo"]
    mejor = None
    for tipo, pieza, cesto, idx in _opciones(est, cfg, semilla):
        for i, x in enumerate(est["tab"]):
            if x != 0:
                continue
            nuevo, ev = _poner(est["tab"], vec, i, pieza, objetivo)
            if _alcanzado(nuevo, objetivo):
                return (tipo, i)
            val = _valor(nuevo, vec)
            if profundidad >= 2 and 0 in nuevo:
                siguiente = _pieza(semilla, idx, cfg)
                m = _mejor_colocacion(nuevo, vec, siguiente, objetivo)
                if m is not None:
                    val = m[0]
            if mejor is None or val > mejor[0]:
                mejor = (val, tipo, i)
    return None if mejor is None else (mejor[1], mejor[2])


def _aplicar_accion(est, cfg, semilla, tipo, casilla):
    """Aplica al estado `est` (modificándolo) una colocación, con o sin cambio
    previo con el cesto. Devuelve las fusiones que hubo."""
    vec = _vecinos(cfg["filas"], cfg["cols"])
    if tipo == "cesto":
        _cambiar_cesto(est, semilla, cfg)
    nuevo, ev = _poner(est["tab"], vec, casilla, est["actual"], cfg["objetivo"])
    est["tab"] = nuevo
    est["actual"] = _pieza(semilla, est["idx"], cfg)
    est["idx"] += 1
    est["cambio_usado"] = False
    est["turnos"] += 1
    return ev


def _cambiar_cesto(est, semilla, cfg):
    """Cambia la pieza actual por la del cesto (o la guarda si está vacío)."""
    if est["cesto"] is None:
        est["cesto"] = est["actual"]
        est["actual"] = _pieza(semilla, est["idx"], cfg)
        est["idx"] += 1
    else:
        est["cesto"], est["actual"] = est["actual"], est["cesto"]
    est["cambio_usado"] = True


def _copiar(est):
    c = dict(est)
    c["tab"] = list(est["tab"])
    return c


def jugar_bot(semilla, nivel, profundidad=1):
    """Partida completa del bot. Devuelve (ganó, turnos). Se usa para
    comprobar que una semilla se puede ganar y para fijar la referencia."""
    cfg = NIVELES[nivel]
    est = _inicial(semilla, cfg)
    while est["turnos"] < LIMITE_TURNOS:
        accion = _decidir(est, cfg, semilla, profundidad)
        if accion is None:
            return False, est["turnos"]
        _aplicar_accion(est, cfg, semilla, accion[0], accion[1])
        if _alcanzado(est["tab"], cfg["objetivo"]):
            return True, est["turnos"]
    return False, est["turnos"]


def _generar(semilla, nivel):
    """Busca una semilla efectiva que el bot gane. Devuelve (efectiva, referencia)."""
    for intento in range(INTENTOS_GENERACION):
        efectiva = (semilla + intento * 0x9E3779B9) & _M32
        gano, turnos = jugar_bot(efectiva, nivel)
        if gano:
            return efectiva, turnos
    return semilla, None


def estrellas(turnos, referencia, pistas=0):
    """3 estrellas hasta un 15 % por encima de la referencia, 2 hasta un 50 %,
    1 si se completa. Con pistas usadas el máximo es 2."""
    if referencia is None:
        e = 1
    elif turnos * 20 <= referencia * 23:
        e = 3
    elif turnos * 2 <= referencia * 3:
        e = 2
    else:
        e = 1
    return min(e, 2) if pistas else e


# ------------------------------------------------------------ partida

_p = None


def _nueva(semilla, modo, etiqueta, nivel):
    global _p
    if modo == "diario":
        nivel = NIVEL_DIARIO
    elif nivel not in NIVELES:
        nivel = NIVEL_PRACTICA
    semilla = int(semilla) & _M32
    cfg = NIVELES[nivel]
    efectiva, referencia = _generar(semilla, nivel)
    est = _inicial(efectiva, cfg)
    _p = {
        "semilla": semilla,
        "efectiva": efectiva,
        "modo": "diario" if modo == "diario" else "practica",
        "etiqueta": etiqueta,
        "nivel": nivel,
        "referencia": referencia,
        "est": est,
        "historial": [],      # acciones: ["p", casilla] (colocar) o ["g"] (cambiar con el cesto)
        "pila": [],           # estados anteriores para deshacer
        "pistas": 0,
        "estado": "jugando",
        "ultimo": [],
    }


def _previsiones(p):
    """Para cada casilla vacía, qué nivel tendría la última pieza fusionada si
    se pusiera ahí la pieza actual (0 si no hay fusión)."""
    cfg = NIVELES[p["nivel"]]
    est = p["est"]
    vec = _vecinos(cfg["filas"], cfg["cols"])
    res = []
    for i, x in enumerate(est["tab"]):
        if x != 0:
            res.append(0)
            continue
        _, ev = _poner(est["tab"], vec, i, est["actual"], cfg["objetivo"])
        res.append(ev[-1]["hasta"] if ev else 0)
    return res


def _estado_json(error=None, pista=None):
    p = _p
    est = p["est"]
    cfg = NIVELES[p["nivel"]]
    jugando = p["estado"] == "jugando"
    siguientes = [_pieza(p["efectiva"], est["idx"] + k, cfg) for k in range(2)]
    d = {
        "semilla": p["semilla"],
        "modo": p["modo"],
        "etiqueta": p["etiqueta"],
        "nivel": p["nivel"],
        "nivel_nombre": cfg["nombre"],
        "filas": cfg["filas"],
        "cols": cfg["cols"],
        "objetivo": cfg["objetivo"],
        "piezas": {str(k): {c: v[c] for c in ("nombre", "forma", "color", "tinta")} for k, v in PIEZAS.items()},
        "codigos": {"savia": SAVIA, "piedra": PIEDRA},
        "tab": list(est["tab"]),
        "actual": est["actual"],
        "siguientes": siguientes,
        "cesto": est["cesto"],
        "puede_cambiar": jugando and not est["cambio_usado"],
        "turnos": est["turnos"],
        "referencia": p["referencia"],
        "estado": p["estado"],
        "estrellas": estrellas(est["turnos"], p["referencia"], p["pistas"]) if p["estado"] == "completada" else 0,
        "puede_deshacer": bool(p["pila"]),
        "previsiones": _previsiones(p) if jugando else [],
        "ultimo": p["ultimo"],
        "historial": p["historial"],
        "pistas": p["pistas"],
        "pistas_max": PISTAS_MAX,
        "pista": pista,
        "mayor": max([x for x in est["tab"] if 1 <= x <= MAX_NIVEL] or [0]),
    }
    if error:
        d["error"] = error
    return json.dumps(d)


def nueva_partida(semilla, modo, etiqueta="", nivel=""):
    """Empieza una partida. `modo` es "diario" o "practica"."""
    _nueva(semilla, modo, etiqueta, nivel)
    return _estado_json()


def _guardar_pila(p):
    est = p["est"]
    p["pila"].append((_copiar(est), p["estado"]))


def _jugada(p, tipo, casilla):
    """Aplica una acción del jugador ya validada. Devuelve las fusiones."""
    cfg = NIVELES[p["nivel"]]
    _guardar_pila(p)
    ev = _aplicar_accion(p["est"], cfg, p["efectiva"], tipo, casilla)
    p["historial"].append(["p", casilla])
    p["ultimo"] = ev
    if _alcanzado(p["est"]["tab"], cfg["objetivo"]):
        p["estado"] = "completada"
    elif 0 not in p["est"]["tab"]:
        p["estado"] = "perdida"
    return ev


def _colocar(casilla):
    p = _p
    if p["estado"] != "jugando":
        return "La partida ya ha terminado. Puedes deshacer o empezar otra."
    cfg = NIVELES[p["nivel"]]
    try:
        casilla = int(casilla)
    except (ValueError, TypeError):
        return "Casilla no válida."
    if not 0 <= casilla < cfg["filas"] * cfg["cols"]:
        return "Casilla no válida."
    if p["est"]["tab"][casilla] != 0:
        return "Esa casilla está ocupada."
    _jugada(p, "poner", casilla)
    return None


def colocar(fila, col):
    """Pone la pieza actual en la casilla (fila, col), contando desde 0."""
    cols = NIVELES[_p["nivel"]]["cols"]
    try:
        fila, col = int(fila), int(col)
    except (ValueError, TypeError):
        return _estado_json("Casilla no válida.")
    if not (0 <= fila < NIVELES[_p["nivel"]]["filas"] and 0 <= col < cols):
        return _estado_json("Casilla no válida.")
    return _estado_json(_colocar(fila * cols + col))


def cambiar():
    """Cambia la pieza actual por la del cesto (o la guarda si está vacío).
    Solo una vez por turno; no cuenta como turno."""
    p = _p
    if p["estado"] != "jugando":
        return _estado_json("La partida ya ha terminado.")
    est = p["est"]
    if est["cambio_usado"]:
        return _estado_json("Ya has usado el cesto en este turno: coloca la pieza.")
    _guardar_pila(p)
    _cambiar_cesto(est, p["efectiva"], NIVELES[p["nivel"]])
    p["historial"].append(["g"])
    p["ultimo"] = []
    return _estado_json()


def deshacer():
    """Deshace la última acción (colocación o cambio de cesto)."""
    p = _p
    if not p["pila"]:
        return _estado_json("No hay nada que deshacer.")
    est, estado = p["pila"].pop()
    p["est"] = est
    p["estado"] = estado
    p["historial"].pop()
    p["ultimo"] = []
    return _estado_json()


def reiniciar():
    """Vuelve a empezar la misma partida (mismas piezas y piedras)."""
    p = _p
    cfg = NIVELES[p["nivel"]]
    p["est"] = _inicial(p["efectiva"], cfg)
    p["historial"] = []
    p["pila"] = []
    p["pistas"] = 0
    p["estado"] = "jugando"
    p["ultimo"] = []
    return _estado_json()


def restaurar(semilla, modo, etiqueta, nivel, historial_json, pistas=0):
    """Reconstruye una partida repitiendo las acciones guardadas."""
    _nueva(semilla, modo, etiqueta, nivel)
    p = _p
    try:
        acciones = json.loads(historial_json)
    except (ValueError, TypeError):
        acciones = []
    if isinstance(acciones, list):
        for a in acciones:
            if p["estado"] != "jugando":
                break
            try:
                tipo = a[0]
                if tipo == "g":
                    if p["est"]["cambio_usado"]:
                        break
                    _guardar_pila(p)
                    _cambiar_cesto(p["est"], p["efectiva"], NIVELES[p["nivel"]])
                    p["historial"].append(["g"])
                elif tipo == "p":
                    casilla = int(a[1])
                    if not 0 <= casilla < len(p["est"]["tab"]) or p["est"]["tab"][casilla] != 0:
                        break
                    _jugada(p, "poner", casilla)
                else:
                    break
            except (IndexError, TypeError, ValueError, KeyError):
                break
    p["ultimo"] = []
    p["pistas"] = min(PISTAS_MAX, _entero(pistas))
    return _estado_json()


def pista():
    """Pide una pista: la mejor acción según el bot, mirando también la pieza
    siguiente. Gasta una de las 3 pistas."""
    p = _p
    if p["estado"] != "jugando":
        return _estado_json("La partida ya ha terminado.")
    if p["pistas"] >= PISTAS_MAX:
        return _estado_json("Ya has usado las %d pistas." % PISTAS_MAX)
    cfg = NIVELES[p["nivel"]]
    accion = _decidir(p["est"], cfg, p["efectiva"], 2)
    if accion is None:
        return _estado_json("No hay ninguna jugada posible.")
    tipo, casilla = accion
    p["pistas"] += 1
    return _estado_json(pista={
        "tipo": "cesto" if tipo == "cesto" else "colocar",
        "fila": casilla // cfg["cols"],
        "col": casilla % cfg["cols"],
    })


def compartir_texto():
    """Resultado para compartir sin spoilers: no enseña las piezas que te
    tocaron, solo el huerto al terminar. Devuelve "" si no se ha completado."""
    p = _p
    if p is None or p["estado"] != "completada":
        return ""
    cfg = NIVELES[p["nivel"]]
    est = p["est"]
    est_n = estrellas(est["turnos"], p["referencia"], p["pistas"])
    lineas = [
        "PLANTÍOS · " + (p["etiqueta"] or "práctica"),
        "★" * est_n + "☆" * (3 - est_n) + " · %s criado en %d turnos (referencia %s)" % (
            PIEZAS[cfg["objetivo"]]["nombre"], est["turnos"],
            p["referencia"] if p["referencia"] is not None else "–"),
    ]
    for f in range(cfg["filas"]):
        fila = ""
        for c in range(cfg["cols"]):
            x = est["tab"][f * cfg["cols"] + c]
            if x == 0:
                fila += CUADRO_VACIO
            elif x == PIEDRA:
                fila += CUADRO_PIEDRA
            elif x == SAVIA:
                fila += CUADRO_SAVIA
            else:
                fila += PIEZAS[x]["cuadro"]
        lineas.append(fila)
    if p["pistas"]:
        lineas.append("💡 %d %s" % (p["pistas"], "pista" if p["pistas"] == 1 else "pistas"))
    return "\n".join(lineas)


# ------------------------------------------------------------ estadísticas

def _entero(valor):
    try:
        return max(0, int(valor))
    except (ValueError, TypeError):
        return 0


def _leer_estadisticas(estadisticas_json):
    e = {"completados": 0, "racha": 0, "mejor_racha": 0, "tres_estrellas": 0, "ultimo_dia": None}
    try:
        guardadas = json.loads(estadisticas_json)
        if isinstance(guardadas, dict):
            for clave in ("completados", "racha", "mejor_racha", "tres_estrellas"):
                e[clave] = _entero(guardadas.get(clave))
            ultimo = guardadas.get("ultimo_dia")
            if isinstance(ultimo, str):
                date.fromisoformat(ultimo)
                e["ultimo_dia"] = ultimo
    except (ValueError, TypeError):
        pass
    return e


def actualizar_estadisticas(estadisticas_json, fecha_iso, turnos, estrellas_ganadas):
    """Suma un reto diario completado. La racha son los días seguidos con el
    reto completado: si ayer lo hiciste, hoy suma uno; si falta algún día,
    vuelve a empezar. Completar dos veces el mismo día no suma."""
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
    if int(estrellas_ganadas) >= 3:
        e["tres_estrellas"] += 1
    e["ultimo_dia"] = hoy.isoformat()
    return json.dumps(e)


def racha_vigente(estadisticas_json, hoy_iso):
    """Racha que hay que mostrar hoy: sigue viva si el último reto fue hoy o ayer."""
    e = _leer_estadisticas(estadisticas_json)
    try:
        hoy = date.fromisoformat(hoy_iso)
    except (ValueError, TypeError):
        return e["racha"]
    ayer = (hoy - timedelta(days=1)).isoformat()
    return e["racha"] if e["ultimo_dia"] in (hoy.isoformat(), ayer) else 0

"""CORRADA: puzle de acorralar a un ternero en un prado de casillas hexagonales.

Toda la logica del juego esta en este archivo. Las funciones publicas devuelven
texto JSON para que script.js (Pyodide) solo tenga que dibujarlo.

Reglas en una linea: cada turno pones UNA piedra en una casilla libre y despues
el ternero da un paso hacia la salida (el borde del prado) mas cercana. Si no le
queda camino hasta el borde, lo has acorralado y ganas; si pisa el borde, escapa.

El ternero no tiene azar escondido: sigue siempre un camino de longitud minima
y, cuando hay varios iguales, elige uno con un generador (mulberry32) que sale de
la semilla de la partida y del numero de turno. Asi la partida entera depende solo
de la semilla y de la lista de piedras puestas, y deshacer es repetir la lista.
"""
import json
from collections import deque
from datetime import date

M32 = 0xFFFFFFFF

NIVELES = {
    # nombre, filas, columnas, piedras iniciales, piedras extra sobre el 150 % de la referencia
    "facil": {"nombre": "Prau", "filas": 9, "cols": 9, "piedras": 13, "extra": 3},
    "normal": {"nombre": "Corral", "filas": 11, "cols": 11, "piedras": 15, "extra": 2},
    "dificil": {"nombre": "Pumarada", "filas": 11, "cols": 11, "piedras": 10, "extra": 1},
}

LIBRE, PIEDRA, PUESTA = 0, 1, 2  # codigos de casilla que ve la interfaz
MAX_PISTAS = 3


# ---------------------------------------------------------------- azar determinista
class Mulberry:
    """mulberry32: generador de 32 bits identico en cualquier version de Python."""

    def __init__(self, semilla):
        self.a = semilla & M32

    def siguiente(self):
        self.a = (self.a + 0x6D2B79F5) & M32
        t = self.a
        t = ((t ^ (t >> 15)) * (t | 1)) & M32
        t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & M32)) & M32
        return ((t ^ (t >> 14)) & M32) / 4294967296.0

    def entero(self, n):
        return int(self.siguiente() * n)


def fnv1a(texto):
    """Hash FNV-1a de 32 bits: convierte la fecha del dia en una semilla."""
    h = 0x811C9DC5
    for b in texto.encode("utf-8"):
        h = ((h ^ b) * 0x01000193) & M32
    return h


def semilla_de_fecha(iso):
    return fnv1a("corrada-" + iso)


def _azar_turno(semilla, turno):
    return Mulberry((semilla * 2654435761 + turno * 40503 + 12345) & M32)


# ---------------------------------------------------------------- geometria hexagonal
_CACHE_GEO = {}


def geometria(filas, cols):
    """Vecinos y casillas del borde. Filas impares desplazadas media casilla a la derecha."""
    clave = (filas, cols)
    if clave in _CACHE_GEO:
        return _CACHE_GEO[clave]
    vec = []
    for f in range(filas):
        for c in range(cols):
            if f % 2 == 0:
                cand = [(f, c - 1), (f, c + 1), (f - 1, c - 1), (f - 1, c), (f + 1, c - 1), (f + 1, c)]
            else:
                cand = [(f, c - 1), (f, c + 1), (f - 1, c), (f - 1, c + 1), (f + 1, c), (f + 1, c + 1)]
            vec.append([ff * cols + cc for ff, cc in cand if 0 <= ff < filas and 0 <= cc < cols])
    borde = [f * cols + c for f in range(filas) for c in range(cols)
             if f in (0, filas - 1) or c in (0, cols - 1)]
    _CACHE_GEO[clave] = (vec, borde)
    return vec, borde


def distancias(libre, vec, borde):
    """Pasos que le faltan a cada casilla para llegar al borde (-1 si no puede)."""
    d = [-1] * len(libre)
    cola = deque()
    for i in borde:
        if libre[i]:
            d[i] = 0
            cola.append(i)
    while cola:
        i = cola.popleft()
        for j in vec[i]:
            if libre[j] and d[j] < 0:
                d[j] = d[i] + 1
                cola.append(j)
    return d


def pasos_posibles(libre, vec, d, ternero):
    return [j for j in vec[ternero] if libre[j] and d[j] == d[ternero] - 1]


def camino_corto(libre, vec, d, ternero):
    """Casillas por las que podria pasar el ternero en un camino de longitud minima."""
    if d[ternero] < 0:
        return []
    visto = {ternero}
    cola = deque([ternero])
    while cola:
        i = cola.popleft()
        if d[i] == 0:
            continue
        for j in pasos_posibles(libre, vec, d, i):
            if j not in visto:
                visto.add(j)
                cola.append(j)
    return sorted(visto)


# ---------------------------------------------------------------- simulacion de una partida
def simular(cfg, piedras0, ternero0, semilla, acciones):
    """Repite la partida desde el principio con la lista de piedras puestas.

    Devuelve un diccionario con el estado final. Las acciones no validas se ignoran
    (cuentan en 'rechazadas'), de modo que una lista antigua nunca rompe la partida.
    """
    filas, cols = cfg["filas"], cfg["cols"]
    vec, borde = geometria(filas, cols)
    n = filas * cols
    libre = [True] * n
    for i in piedras0:
        libre[i] = False
    ternero = ternero0
    turno = 0
    puestas = {}          # casilla -> numero de turno en el que la pusiste
    rastro = [ternero]
    resultado, motivo = "jugando", ""
    validas = []
    rechazadas = 0
    presupuesto = cfg["presupuesto"]
    for a in acciones:
        if resultado != "jugando":
            rechazadas += 1
            continue
        if not isinstance(a, int) or a < 0 or a >= n or not libre[a] or a == ternero:
            rechazadas += 1
            continue
        libre[a] = False
        turno += 1
        puestas[a] = turno
        validas.append(a)
        d = distancias(libre, vec, borde)
        if d[ternero] < 0:
            resultado, motivo = "ganada", "El ternero se ha quedado sin camino hasta el borde: acorralado."
            break
        opciones = pasos_posibles(libre, vec, d, ternero)
        ternero = opciones[_azar_turno(semilla, turno).entero(len(opciones))]
        rastro.append(ternero)
        if ternero in borde:
            resultado, motivo = "perdida", "El ternero ha llegado al borde y se ha escapado del prado."
            break
        if turno >= presupuesto:
            resultado, motivo = "perdida", "Te has quedado sin piedras y el ternero sigue suelto."
            break
    return {"libre": libre, "ternero": ternero, "turno": turno, "puestas": puestas,
            "rastro": rastro, "resultado": resultado, "motivo": motivo,
            "validas": validas, "rechazadas": rechazadas}


# ---------------------------------------------------------------- jugador automatico
def _evaluar(libre, vec, borde, ternero, c, turno, semilla):
    """Pone una piedra en c y mueve al ternero. Devuelve (estado, nueva_libre, nuevo_ternero)."""
    libre2 = libre[:]
    libre2[c] = False
    d = distancias(libre2, vec, borde)
    if d[ternero] < 0:
        return "atrapa", libre2, ternero, d
    opciones = pasos_posibles(libre2, vec, d, ternero)
    t2 = opciones[_azar_turno(semilla, turno + 1).entero(len(opciones))]
    if t2 in borde:
        return "escapa", libre2, t2, d
    return "sigue", libre2, t2, d


def _candidatas(libre, vec, ternero, radio):
    """Casillas libres a menos de 'radio' pasos del ternero (sin atravesar piedras)."""
    dist = {ternero: 0}
    cola = deque([ternero])
    while cola:
        i = cola.popleft()
        if dist[i] >= radio:
            continue
        for j in vec[i]:
            if libre[j] and j not in dist:
                dist[j] = dist[i] + 1
                cola.append(j)
    return [i for i in dist if i != ternero]


def _buscar(libre, vec, borde, ternero, turno, semilla, prof, ancho, radio):
    """Busca una piedra que gane en 'prof' jugadas. Devuelve (casilla, jugadas) o (None, None)."""
    puntuadas = []
    for c in _candidatas(libre, vec, ternero, radio):
        est, libre2, t2, d = _evaluar(libre, vec, borde, ternero, c, turno, semilla)
        if est == "atrapa":
            return c, 1
        if est == "escapa":
            continue
        d2 = distancias(libre2, vec, borde)
        vias = len(pasos_posibles(libre2, vec, d2, t2))
        puntuadas.append((-d2[t2], vias, c, libre2, t2))
    if prof <= 1:
        return None, None
    puntuadas.sort(key=lambda x: (x[0], x[1], x[2]))
    mejor = (None, None)
    for _, _, c, libre2, t2 in puntuadas[:ancho]:
        _, n = _buscar(libre2, vec, borde, t2, turno + 1, semilla, prof - 1, ancho, radio)
        if n is not None and (mejor[1] is None or n + 1 < mejor[1]):
            mejor = (c, n + 1)
    return mejor


def _mejor_por_heuristica(libre, vec, borde, ternero, turno, semilla):
    """Si no hay jugada ganadora a la vista: la que mas aleja al ternero de la salida."""
    mejor = None
    for c in _candidatas(libre, vec, ternero, 6):
        est, libre2, t2, d = _evaluar(libre, vec, borde, ternero, c, turno, semilla)
        if est == "escapa":
            continue
        d2 = distancias(libre2, vec, borde)
        vias = len(pasos_posibles(libre2, vec, d2, t2))
        clave = (-d2[t2], vias, c)
        if mejor is None or clave < mejor[0]:
            mejor = (clave, c)
    return None if mejor is None else mejor[1]


def jugada_del_bot(cfg, piedras0, ternero0, semilla, acciones, prof=2, ancho=5, radio=4):
    """Casilla que pondria el jugador automatico despues de las 'acciones' dadas."""
    s = simular(cfg, piedras0, ternero0, semilla, acciones)
    if s["resultado"] != "jugando":
        return None
    vec, borde = geometria(cfg["filas"], cfg["cols"])
    c, _ = _buscar(s["libre"], vec, borde, s["ternero"], s["turno"], semilla, prof, ancho, radio)
    if c is None:
        c = _mejor_por_heuristica(s["libre"], vec, borde, s["ternero"], s["turno"], semilla)
    return c


def _partida_del_bot(cfg, piedras0, ternero0, semilla, tope=40):
    acciones = []
    for _ in range(tope):
        c = jugada_del_bot(cfg, piedras0, ternero0, semilla, acciones)
        if c is None:
            return False, len(acciones), acciones
        acciones.append(c)
        s = simular(dict(cfg, presupuesto=tope + 5), piedras0, ternero0, semilla, acciones)
        if s["resultado"] == "ganada":
            return True, len(acciones), acciones
        if s["resultado"] == "perdida":
            return False, len(acciones), acciones
    return False, len(acciones), acciones


# ---------------------------------------------------------------- generacion de partidas
_CACHE_PARTIDAS = {}


def crear_partida(semilla, nivel):
    """Elige piedras iniciales y comprueba con el jugador automatico que la partida se gana.

    Si el jugador automatico no la gana, se prueba una semilla cercana (siempre la misma
    para la misma semilla de entrada). Devuelve un diccionario con todo lo necesario.
    """
    clave = (semilla & M32, nivel)
    if clave in _CACHE_PARTIDAS:
        return _CACHE_PARTIDAS[clave]
    base = NIVELES[nivel]
    filas, cols = base["filas"], base["cols"]
    vec, borde = geometria(filas, cols)
    ternero0 = (filas // 2) * cols + cols // 2
    prohibidas = set(vec[ternero0]) | {ternero0}
    for intento in range(300):
        efectiva = (semilla + intento * 7919) & M32
        rng = Mulberry(efectiva)
        piedras0 = set()
        while len(piedras0) < base["piedras"]:
            c = rng.entero(filas * cols)
            if c not in prohibidas:
                piedras0.add(c)
        libre = [i not in piedras0 for i in range(filas * cols)]
        d = distancias(libre, vec, borde)
        if d[ternero0] < 2:
            continue
        cfg = dict(base, presupuesto=99)
        gana, n, sol = _partida_del_bot(cfg, piedras0, ternero0, efectiva)
        if not gana:
            continue
        ref = n
        presupuesto = -(-ref * 3 // 2) + base["extra"]
        res = {"cfg": dict(base, presupuesto=presupuesto), "piedras0": sorted(piedras0),
               "ternero0": ternero0, "semilla": efectiva, "ref": ref, "intentos": intento + 1,
               "solucion": sol}
        _CACHE_PARTIDAS[clave] = res
        return res
    raise RuntimeError("no se ha podido crear una partida ganable")


def jugar_bot(semilla, nivel="normal"):
    """Para probar en el ordenador: (gana, piedras usadas) del jugador automatico."""
    p = crear_partida(semilla, nivel)
    s = simular(p["cfg"], p["piedras0"], p["ternero0"], p["semilla"], p["solucion"])
    return s["resultado"] == "ganada", len(p["solucion"])


# ---------------------------------------------------------------- estado que ve la interfaz
JUEGO = {"modo": "practica", "nivel": "normal", "semilla": 1, "fecha": "", "acciones": [],
         "pistas": 0, "partida": None}


def _estrellas(usadas, ref, pistas):
    if usadas <= -(-ref * 115 // 100):
        e = 3
    elif usadas <= -(-ref * 3 // 2):
        e = 2
    else:
        e = 1
    return min(e, 2) if pistas > 0 else e


def _estado(pista=None, error=""):
    j = JUEGO
    p = j["partida"]
    cfg = p["cfg"]
    s = simular(cfg, p["piedras0"], p["ternero0"], p["semilla"], j["acciones"])
    filas, cols = cfg["filas"], cfg["cols"]
    vec, borde = geometria(filas, cols)
    celdas = []
    for i in range(filas * cols):
        if i in s["puestas"]:
            celdas.append(PUESTA)
        elif not s["libre"][i]:
            celdas.append(PIEDRA)
        else:
            celdas.append(LIBRE)
    d = distancias(s["libre"], vec, borde)
    dt = d[s["ternero"]]
    estrellas = _estrellas(s["turno"], p["ref"], j["pistas"]) if s["resultado"] == "ganada" else 0
    return json.dumps({
        "filas": filas, "cols": cols, "nivel": j["nivel"], "nombre_nivel": cfg["nombre"],
        "modo": j["modo"], "fecha": j["fecha"], "semilla": j["semilla"],
        "celdas": celdas, "turnos_piedra": {str(k): v for k, v in s["puestas"].items()},
        "borde": borde, "ternero": s["ternero"], "rastro": s["rastro"],
        "distancia": dt, "camino": camino_corto(s["libre"], vec, d, s["ternero"]) if s["resultado"] == "jugando" else [],
        "usadas": s["turno"], "presupuesto": cfg["presupuesto"], "restantes": cfg["presupuesto"] - s["turno"],
        "ref": p["ref"], "resultado": s["resultado"], "motivo": s["motivo"], "estrellas": estrellas,
        "pistas": j["pistas"], "max_pistas": MAX_PISTAS, "pista": pista,
        "acciones": s["validas"], "puede_deshacer": len(s["validas"]) > 0 and s["resultado"] != "perdida_x",
        "error": error,
    }, ensure_ascii=False)


def nueva(modo, nivel, semilla_o_fecha):
    """modo 'diario' (semilla_o_fecha = 'AAAA-MM-DD', nivel Corral) o 'practica' (semilla numerica)."""
    if modo == "diario":
        nivel = "normal"
        semilla = semilla_de_fecha(str(semilla_o_fecha))
        JUEGO["fecha"] = str(semilla_o_fecha)
    else:
        if nivel not in NIVELES:
            nivel = "normal"
        semilla = int(semilla_o_fecha) & M32
        JUEGO["fecha"] = ""
    JUEGO.update(modo=modo, nivel=nivel, semilla=semilla, acciones=[], pistas=0,
                 partida=crear_partida(semilla, nivel))
    return _estado()


def reconstruir(modo, nivel, semilla_o_fecha, acciones_json, pistas):
    """Vuelve a una partida guardada repitiendo sus piedras."""
    nueva(modo, nivel, semilla_o_fecha)
    p = JUEGO["partida"]
    s = simular(p["cfg"], p["piedras0"], p["ternero0"], p["semilla"], json.loads(acciones_json))
    JUEGO["acciones"] = s["validas"]
    JUEGO["pistas"] = max(0, min(MAX_PISTAS, int(pistas)))
    return _estado()


def colocar(i):
    p = JUEGO["partida"]
    s = simular(p["cfg"], p["piedras0"], p["ternero0"], p["semilla"], JUEGO["acciones"])
    if s["resultado"] != "jugando":
        return _estado(error="La partida ya ha terminado.")
    i = int(i)
    if i == s["ternero"]:
        return _estado(error="Ahi esta el ternero: no se puede poner una piedra encima.")
    if i < 0 or i >= len(s["libre"]) or not s["libre"][i]:
        return _estado(error="Esa casilla ya tiene una piedra.")
    JUEGO["acciones"].append(i)
    return _estado()


def deshacer():
    if JUEGO["acciones"]:
        JUEGO["acciones"].pop()
    return _estado()


def reiniciar():
    JUEGO["acciones"] = []
    JUEGO["pistas"] = 0
    return _estado()


def pista():
    p = JUEGO["partida"]
    s = simular(p["cfg"], p["piedras0"], p["ternero0"], p["semilla"], JUEGO["acciones"])
    if s["resultado"] != "jugando":
        return _estado()
    if JUEGO["pistas"] >= MAX_PISTAS:
        return _estado(error="Ya has gastado las 3 pistas.")
    c = jugada_del_bot(p["cfg"], p["piedras0"], p["ternero0"], p["semilla"], JUEGO["acciones"])
    if c is None:
        return _estado(error="No se me ocurre ninguna casilla que ayude desde aqui.")
    JUEGO["pistas"] += 1
    return _estado(pista=c)


# ---------------------------------------------------------------- compartir y racha
def compartir():
    """Texto para pegar en cualquier sitio: nota y mapa final, sin decir como ganar."""
    j = JUEGO
    p = j["partida"]
    s = simular(p["cfg"], p["piedras0"], p["ternero0"], p["semilla"], j["acciones"])
    cfg = p["cfg"]
    filas, cols = cfg["filas"], cfg["cols"]
    if s["resultado"] == "ganada":
        e = _estrellas(s["turno"], p["ref"], j["pistas"])
        nota = "★" * e + "☆" * (3 - e) + f" acorralado con {s['turno']} piedras (referencia {p['ref']})"
    else:
        nota = f"se escapó tras {s['turno']} piedras"
    titulo = f"CORRADA {j['fecha']}" if j["modo"] == "diario" else f"CORRADA · {cfg['nombre']}"
    lineas = [titulo, nota]
    for f in range(filas):
        fila = ""
        for c in range(cols):
            i = f * cols + c
            if i == s["ternero"]:
                fila += "🐮"
            elif i in s["puestas"]:
                fila += "🟫"
            elif not s["libre"][i]:
                fila += "⬛"
            else:
                fila += "⬜"
        lineas.append((" " if f % 2 else "") + fila)
    return "\n".join(lineas)


def racha(fechas_json, hoy_iso):
    """Racha actual y mejor racha a partir de las fechas (ISO) de retos diarios ganados."""
    dias = sorted({date.fromisoformat(f).toordinal() for f in json.loads(fechas_json)})
    hoy = date.fromisoformat(hoy_iso).toordinal()
    mejor = actual = 0
    previo = None
    for d in dias:
        actual = actual + 1 if previo is not None and d == previo + 1 else 1
        mejor = max(mejor, actual)
        previo = d
    conjunto = set(dias)
    cuenta = 0
    d = hoy if hoy in conjunto else hoy - 1
    while d in conjunto:
        cuenta += 1
        d -= 1
    return json.dumps({"actual": cuenta, "mejor": mejor, "total": len(dias)})


def leyenda():
    return json.dumps({"niveles": {k: {"nombre": v["nombre"], "filas": v["filas"], "cols": v["cols"],
                                       "piedras": v["piedras"]} for k, v in NIVELES.items()}})

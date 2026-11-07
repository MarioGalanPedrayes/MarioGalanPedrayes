"""TROJES: lógica del juego (Python 3, sin dependencias externas).

Un troje es el compartimento de madera donde se guarda la cosecha. Tienes
varios trojes con productos mezclados (manzanas, castañas, maíz...) y tienes
que dejar cada producto junto, sellado en su propio troje.

Reglas:

  - Cada troje cabe CAPACIDAD (4) fichas, apiladas de abajo arriba. Solo se
    puede coger la ficha de arriba (con las iguales que tenga pegadas debajo).
  - Mover: eliges un troje de origen y uno de destino. Se pasan al destino
    las fichas iguales de arriba del origen que quepan. El destino tiene que
    estar vacío o tener arriba una ficha igual. Cuenta como un movimiento.
  - Un troje lleno de fichas iguales se SELLA solo: ya no se toca más.
  - Candado (solo en difícil): un troje empieza cerrado, ni se puede coger de
    él ni poner en él, hasta que selles el primer troje.
  - Se gana cuando todos los trojes están vacíos o sellados.

Cada partida se genera repartiendo las fichas al azar y comprobando con un
solucionador que tiene salida; la longitud de la solución que encuentra es la
referencia de movimientos (no tiene por qué ser el mínimo absoluto). El reto
diario usa la fecha como semilla: todo el mundo recibe el mismo reparto el
mismo día. Para que el resultado sea idéntico en cualquier versión de Python,
el generador de números aleatorios está escrito aquí (no usa `random`).

Toda la lógica vive en este archivo. La página (script.js) solo dibuja y llama
a las funciones públicas, que devuelven texto JSON (salvo `semilla_del_dia`,
`racha_vigente` y `compartir_texto`).
"""
import heapq
import json
from datetime import date, timedelta

CAPACIDAD = 4
PISTAS_MAX = 3
LIMITE_NODOS = 60000     # tope de estados que explora el solucionador al generar
LIMITE_PISTA = 40000     # tope al calcular una pista a mitad de partida
PESO = 2.0               # A* ponderado: busca rápido a cambio de no garantizar el mínimo

# Catálogo de productos. La forma se dibuja con CSS, así que cada producto se
# distingue por su forma y no solo por el color. "cuadro" es para compartir.
CLASES = [
    {"nombre": "manzana", "forma": "circulo", "color": "#b3402f", "tinta": "#ffffff", "cuadro": "🟥"},
    {"nombre": "castaña", "forma": "triangulo", "color": "#7b4a21", "tinta": "#ffffff", "cuadro": "🟫"},
    {"nombre": "maíz", "forma": "cuadrado", "color": "#e0b422", "tinta": "#1f2933", "cuadro": "🟨"},
    {"nombre": "faba", "forma": "rombo", "color": "#2f7d4f", "tinta": "#ffffff", "cuadro": "🟩"},
    {"nombre": "arándano", "forma": "estrella", "color": "#3a5da8", "tinta": "#ffffff", "cuadro": "🟦"},
    {"nombre": "remolacha", "forma": "cruz", "color": "#8c3f86", "tinta": "#ffffff", "cuadro": "🟪"},
]

# productos distintos, trojes vacíos, si hay candado y movimientos mínimos de referencia
DIFICULTADES = {
    "facil": {"nombre": "Fácil", "clases": 4, "vacios": 2, "candado": False, "minimo": 8},
    "normal": {"nombre": "Normal", "clases": 5, "vacios": 2, "candado": False, "minimo": 12},
    "dificil": {"nombre": "Difícil", "clases": 6, "vacios": 2, "candado": True, "minimo": 18},
}
DIFICULTAD_DIARIA = "dificil"
DIFICULTAD_PRACTICA = "normal"

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
    """Convierte una fecha ISO ("2026-11-06") en una semilla de 32 bits (hash FNV-1a)."""
    h = 0x811C9DC5
    for b in ("trojes:" + str(fecha_iso)).encode("utf-8"):
        h = ((h ^ b) * 0x01000193) & _M32
    return h


def _mezclar(lista, gen):
    """Baraja la lista en el sitio (Fisher-Yates)."""
    for i in range(len(lista) - 1, 0, -1):
        j = int(gen.siguiente() * (i + 1))
        lista[i], lista[j] = lista[j], lista[i]


# ------------------------------------------------------------------ reglas
# Un estado es una tupla de trojes; cada troje es una tupla de productos
# (números) de abajo arriba. El candado es el índice del troje cerrado o None.

def _sellado(troje):
    """Un troje lleno de fichas iguales está sellado."""
    return len(troje) == CAPACIDAD and troje.count(troje[0]) == CAPACIDAD


def _candado_activo(trojes, candado):
    """El candado sigue cerrado mientras no haya ningún troje sellado."""
    return candado is not None and not any(_sellado(t) for t in trojes)


def _ganada(trojes):
    return all(not t or _sellado(t) for t in trojes)


def _grupo_superior(troje):
    """Cuántas fichas iguales hay pegadas en lo alto del troje."""
    k = 1
    while k < len(troje) and troje[-1 - k] == troje[-1]:
        k += 1
    return k


def _motivo(trojes, candado, origen, destino):
    """Devuelve (n, None) con las fichas que se moverían, o (0, texto) si no se puede."""
    total = len(trojes)
    if not (0 <= origen < total and 0 <= destino < total):
        return 0, "Ese troje no existe."
    if origen == destino:
        return 0, "Elige otro troje como destino."
    cerrado = candado if _candado_activo(trojes, candado) else None
    if origen == cerrado or destino == cerrado:
        return 0, "Ese troje tiene candado: se abre cuando selles el primer troje."
    to, td = trojes[origen], trojes[destino]
    if not to:
        return 0, "Ese troje está vacío."
    if _sellado(to) or _sellado(td):
        return 0, "Un troje sellado ya no se toca."
    libre = CAPACIDAD - len(td)
    if libre == 0:
        return 0, "El troje de destino está lleno."
    if td and td[-1] != to[-1]:
        return 0, "Solo puedes poner una ficha sobre otra igual o en un troje vacío."
    k = _grupo_superior(to)
    if not td and k == len(to):
        return 0, "Pasar un grupo entero a un troje vacío no cambia nada."
    return min(k, libre), None


def _movimientos(trojes, candado):
    """Todos los movimientos legales como lista de (origen, destino, fichas).
    Es la versión rápida de _motivo para el solucionador y debe dar lo mismo."""
    cerrado = candado if _candado_activo(trojes, candado) else None
    res = []
    for o, to in enumerate(trojes):
        if not to or o == cerrado or len(to) == CAPACIDAD and _sellado(to):
            continue
        arriba = to[-1]
        k = _grupo_superior(to)
        entero = k == len(to)
        for d, td in enumerate(trojes):
            if d == o or d == cerrado or len(td) == CAPACIDAD:
                continue
            if td:
                if td[-1] != arriba:
                    continue
            elif entero:
                continue
            res.append((o, d, min(k, CAPACIDAD - len(td))))
    return res


def _mover_fichas(trojes, origen, destino, n):
    """Devuelve el estado tras pasar n fichas de origen a destino (sin validar)."""
    ficha = trojes[origen][-1]
    nuevo = list(trojes)
    nuevo[origen] = trojes[origen][:-n]
    nuevo[destino] = trojes[destino] + (ficha,) * n
    return tuple(nuevo)


def _aplicar(trojes, candado, origen, destino):
    """Valida y aplica un movimiento. Lanza ValueError con el motivo si no se puede."""
    n, motivo = _motivo(trojes, candado, origen, destino)
    if motivo:
        raise ValueError(motivo)
    return _mover_fichas(trojes, origen, destino, n)


# ------------------------------------------------------------ solucionador

def _heuristica(trojes):
    """Fichas que están encima de otra distinta (hay que moverlas al menos una vez)."""
    h = 0
    for t in trojes:
        if not t:
            continue
        k = 1
        while k < len(t) and t[k] == t[0]:
            k += 1
        h += len(t) - k
    return h


def _clave(trojes, candado):
    """Identifica un estado ignorando el orden de los trojes (salvo el cerrado con candado)."""
    if _candado_activo(trojes, candado):
        resto = sorted(t for i, t in enumerate(trojes) if i != candado)
        return (trojes[candado], tuple(resto))
    return (None, tuple(sorted(trojes)))


def _resolver(trojes, candado, limite=LIMITE_NODOS, peso=PESO):
    """Busca una lista de movimientos [(origen, destino), ...] que gane desde
    `trojes` (A* ponderado). Devuelve [] si ya está ganada y None si no la
    encuentra dentro del límite de estados."""
    inicio = tuple(tuple(t) for t in trojes)
    if _ganada(inicio):
        return []
    nodos = [(inicio, -1, None, 0)]          # (estado, padre, movimiento, g)
    visto = {_clave(inicio, candado): 0}
    abiertos = [(peso * _heuristica(inicio), 0, 0)]
    orden = 0
    expandidos = 0
    while abiertos and expandidos < limite:
        _, _, idx = heapq.heappop(abiertos)
        estado, _, _, g = nodos[idx]
        if visto.get(_clave(estado, candado), g) < g:
            continue                          # ya se llegó aquí por un camino más corto
        expandidos += 1
        for o, d, n in _movimientos(estado, candado):
            nuevo = _mover_fichas(estado, o, d, n)
            g2 = g + 1
            clave = _clave(nuevo, candado)
            if clave in visto and visto[clave] <= g2:
                continue
            visto[clave] = g2
            nodos.append((nuevo, idx, (o, d), g2))
            if _ganada(nuevo):
                camino = []
                i = len(nodos) - 1
                while nodos[i][1] != -1:
                    camino.append(nodos[i][2])
                    i = nodos[i][1]
                camino.reverse()
                return camino
            orden += 1
            heapq.heappush(abiertos, (g2 + peso * _heuristica(nuevo), orden, len(nodos) - 1))
    return None


# ------------------------------------------------------------ generación

def _reparto_basico(k):
    """Reparto fijo y desordenado (cuadrado latino) por si el azar no diera uno válido."""
    return tuple(tuple((i + j) % k for j in range(CAPACIDAD)) for i in range(k))


def _generar(semilla, dificultad):
    """Devuelve (trojes, candado, referencia) de una partida con solución."""
    cfg = DIFICULTADES[dificultad]
    k = cfg["clases"]
    gen = Generador(semilla)
    mejor = None
    for _ in range(80):
        fichas = [c for c in range(k) for _ in range(CAPACIDAD)]
        _mezclar(fichas, gen)
        llenos = tuple(tuple(fichas[i * CAPACIDAD:(i + 1) * CAPACIDAD]) for i in range(k))
        if any(len(set(t)) == 1 for t in llenos):
            continue                          # un troje ya hecho de salida no tiene gracia
        candado = int(gen.siguiente() * k) if cfg["candado"] else None
        trojes = llenos + ((),) * cfg["vacios"]
        solucion = _resolver(trojes, candado)
        if solucion is None:
            continue
        if len(solucion) >= cfg["minimo"]:
            return trojes, candado, len(solucion)
        if mejor is None or len(solucion) > mejor[2]:
            mejor = (trojes, candado, len(solucion))
    if mejor:
        return mejor
    trojes = _reparto_basico(k) + ((),) * cfg["vacios"]
    candado = 0 if cfg["candado"] else None
    solucion = _resolver(trojes, candado)
    return trojes, candado, len(solucion) if solucion else cfg["minimo"]


def estrellas(movimientos, referencia, pistas=0):
    """3 estrellas hasta un 25 % por encima de la referencia, 2 hasta un 75 %,
    1 si se completa. Con pistas usadas el máximo es 2."""
    if movimientos <= referencia * 5 // 4:
        e = 3
    elif movimientos <= referencia * 7 // 4:
        e = 2
    else:
        e = 1
    return min(e, 2) if pistas else e


# ------------------------------------------------------------ partida

_p = None


def _nueva(semilla, modo, etiqueta, dificultad):
    global _p
    if modo == "diario":
        dificultad = DIFICULTAD_DIARIA
    elif dificultad not in DIFICULTADES:
        dificultad = DIFICULTAD_PRACTICA
    semilla = int(semilla) & _M32
    trojes, candado, referencia = _generar(semilla, dificultad)
    _p = {
        "semilla": semilla,
        "modo": "diario" if modo == "diario" else "practica",
        "etiqueta": etiqueta,
        "dificultad": dificultad,
        "inicial": trojes,
        "trojes": trojes,
        "candado": candado,
        "referencia": referencia,
        "historial": [],
        "pila": [],
        "pistas": 0,
        "estado": "jugando",
    }


def _estado_json(error=None, pista=None):
    p = _p
    trojes = p["trojes"]
    cfg = DIFICULTADES[p["dificultad"]]
    movs = len(p["historial"])
    jugando = p["estado"] == "jugando"
    d = {
        "semilla": p["semilla"],
        "modo": p["modo"],
        "etiqueta": p["etiqueta"],
        "dificultad": p["dificultad"],
        "dificultad_nombre": cfg["nombre"],
        "capacidad": CAPACIDAD,
        "clases": [{k: c[k] for k in ("nombre", "forma", "color", "tinta")} for c in CLASES[:cfg["clases"]]],
        "trojes": [list(t) for t in trojes],
        "sellados": [bool(t) and _sellado(t) for t in trojes],
        "n_sellados": sum(1 for t in trojes if t and _sellado(t)),
        "total_clases": cfg["clases"],
        "candado": p["candado"],
        "candado_cerrado": _candado_activo(trojes, p["candado"]),
        "movimientos": movs,
        "referencia": p["referencia"],
        "estado": p["estado"],
        "estrellas": estrellas(movs, p["referencia"], p["pistas"]) if p["estado"] == "completada" else 0,
        "puede_deshacer": movs > 0 and jugando,
        "sin_movimientos": jugando and not _movimientos(trojes, p["candado"]),
        "historial": p["historial"],
        "pistas": p["pistas"],
        "pistas_max": PISTAS_MAX,
        "pista": pista,
    }
    if error:
        d["error"] = error
    return json.dumps(d)


def nueva_partida(semilla, modo, etiqueta="", dificultad=""):
    """Empieza una partida. modo: "diario" (siempre difícil) o "practica"
    (dificultad "facil", "normal" o "dificil")."""
    _nueva(semilla, modo, etiqueta, dificultad)
    return _estado_json()


def restaurar(semilla, modo, etiqueta, dificultad, historial_json, pistas=0):
    """Reconstruye una partida guardada repitiendo sus movimientos. Si el
    guardado no es válido, devuelve la partida desde cero."""
    _nueva(semilla, modo, etiqueta, dificultad)
    try:
        historial = json.loads(historial_json)
        if not isinstance(historial, list):
            raise ValueError("historial no es una lista")
        for o, d in historial:
            if _p["estado"] != "jugando":
                raise ValueError("movimientos después de terminar")
            _mover(int(o), int(d))
        _p["pistas"] = min(PISTAS_MAX, max(0, int(pistas)))
    except (ValueError, TypeError):
        _nueva(semilla, modo, etiqueta, dificultad)
    return _estado_json()


def _mover(origen, destino):
    """Aplica un movimiento a la partida. Lanza ValueError si no es válido."""
    p = _p
    if p["estado"] != "jugando":
        raise ValueError("La partida ya ha terminado.")
    nuevo = _aplicar(p["trojes"], p["candado"], origen, destino)
    p["pila"].append(p["trojes"])
    p["trojes"] = nuevo
    p["historial"].append([origen, destino])
    if _ganada(nuevo):
        p["estado"] = "completada"


def mover(origen, destino):
    """Pasa fichas del troje `origen` al troje `destino` (índices desde 0, de izquierda a derecha)."""
    if _p is None:
        return json.dumps({"error": "No hay partida en curso."})
    try:
        _mover(int(origen), int(destino))
    except (ValueError, TypeError) as e:
        return _estado_json(str(e))
    return _estado_json()


def deshacer():
    """Deshace el último movimiento (los movimientos ya hechos se siguen contando como pasos del historial solo mientras existan)."""
    if _p is None:
        return json.dumps({"error": "No hay partida en curso."})
    if _p["estado"] != "jugando":
        return _estado_json("La partida ya ha terminado.")
    if not _p["historial"]:
        return _estado_json("No hay nada que deshacer.")
    _p["historial"].pop()
    _p["trojes"] = _p["pila"].pop()
    return _estado_json()


def reiniciar():
    """Vuelve al reparto inicial y borra el historial. Las pistas gastadas no se recuperan."""
    if _p is None:
        return json.dumps({"error": "No hay partida en curso."})
    _p["trojes"] = _p["inicial"]
    _p["historial"] = []
    _p["pila"] = []
    _p["estado"] = "jugando"
    return _estado_json()


def pista():
    """Calcula con el solucionador un buen primer movimiento desde la posición
    actual. Gasta una de las 3 pistas y no cuenta como movimiento."""
    if _p is None:
        return json.dumps({"error": "No hay partida en curso."})
    p = _p
    if p["estado"] != "jugando":
        return _estado_json("La partida ya ha terminado.")
    if p["pistas"] >= PISTAS_MAX:
        return _estado_json("Ya has usado las %d pistas." % PISTAS_MAX)
    solucion = _resolver(p["trojes"], p["candado"], limite=LIMITE_PISTA)
    if not solucion:
        return _estado_json("No encuentro salida desde aquí: deshaz algunos movimientos.")
    p["pistas"] += 1
    return _estado_json(None, {"origen": solucion[0][0], "destino": solucion[0][1]})


# ------------------------------------------------- compartir y estadísticas

def _eventos():
    """Repite el historial y devuelve (orden en que se sellaron los productos,
    movimiento en que se abrió el candado o None)."""
    p = _p
    trojes = p["inicial"]
    orden, abierto, hechos = [], None, set()
    for numero, (o, d) in enumerate(p["historial"], 1):
        trojes = _aplicar(trojes, p["candado"], o, d)
        for j, t in enumerate(trojes):
            if t and _sellado(t) and j not in hechos:
                hechos.add(j)
                orden.append(t[0])
                if abierto is None:
                    abierto = numero
    return orden, abierto


def compartir_texto():
    """Resultado para compartir sin spoilers: no enseña el reparto, solo en qué
    orden sellaste los productos. Devuelve "" si la partida no está completada."""
    p = _p
    if p is None or p["estado"] != "completada":
        return ""
    movs = len(p["historial"])
    est = estrellas(movs, p["referencia"], p["pistas"])
    orden, abierto = _eventos()
    lineas = [
        "TROJES · " + (p["etiqueta"] or "práctica"),
        "★" * est + "☆" * (3 - est) + " · %d movimientos (referencia %d)" % (movs, p["referencia"]),
        "Sellos: " + "".join(CLASES[c]["cuadro"] for c in orden),
    ]
    if p["candado"] is not None and abierto is not None:
        lineas.append("Candado abierto en el movimiento %d" % abierto)
    if p["pistas"]:
        lineas.append("💡 %d %s" % (p["pistas"], "pista" if p["pistas"] == 1 else "pistas"))
    return "\n".join(lineas)


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


def actualizar_estadisticas(estadisticas_json, fecha_iso, movimientos, estrellas_ganadas):
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

"""TARIMA: lógica del juego (Python 3, sin dependencias externas).

Una tarima es el suelo de tablas sobre el que se trabaja. Aquí es un suelo de
8 × 8 casillas que hay que ir cubriendo con piezas de tablas. Cada lote trae
tres piezas; las colocas donde quepan, sin girarlas. Cuando una fila o una
columna queda completa se «despeja» y deja sitio para más.

Reglas:

  - El suelo tiene 8 × 8 casillas. Empieza con algunos nudos (casillas ya
    ocupadas) repartidos al azar; un nudo cuenta como casilla llena y se
    despeja igual que las demás cuando su fila o su columna se completa.
  - Cada lote son 3 piezas. Se pueden colocar en cualquier orden. Una pieza
    no se puede girar. Debe caber entera en casillas libres.
  - Al colocar, toda fila o columna completa se despeja a la vez. Una pieza
    puede completar varias líneas de golpe (una fila y una columna a la vez
    cuentan como dos líneas).
  - Se ve el lote siguiente antes de empezar a colocarlo.
  - La partida dura un número fijo de lotes (5 o 6 según el nivel). Hay que
    despejar al menos las líneas del OBJETIVO. Si ninguna de las piezas que
    quedan en el lote cabe en el suelo, la partida termina.
  - Puntos (solo para comparar): una casilla por cada casilla cubierta, 10 por
    línea al cuadrado en cada jugada que despeja y un extra de 5 por cada
    jugada seguida que despeja ("racha de jugadas").

Cada partida se comprueba con un jugador automático (una búsqueda en haz con
varias jugadas de anticipación): el objetivo se fija por debajo de lo que ese
jugador consigue, así que siempre se puede cumplir, y las líneas que despeja
son la referencia para las estrellas. El reto diario usa la fecha como semilla,
de modo que todo el mundo recibe los mismos nudos y las mismas piezas el mismo
día. Para que el resultado sea idéntico en cualquier versión de Python, el
generador de números aleatorios está escrito aquí (no usa `random`).

Toda la lógica vive en este archivo. La página (script.js) solo dibuja y llama
a las funciones públicas, que devuelven texto JSON (salvo `semilla_del_dia`,
`racha_vigente` y `compartir_texto`).
"""
import json
from datetime import date, timedelta

N = 8
CASILLAS = N * N
NUDO = 2
PISTAS_MAX = 3
INTENTOS_GENERACION = 16
ANCHO_BUSQUEDA = 60
ANCHO_PISTA = 20
_M32 = 0xFFFFFFFF
_TODO = (1 << CASILLAS) - 1

# lotes, nudos de partida, mínimo de líneas que debe lograr el jugador
# automático para aceptar una partida y qué parte de lo que logra se exige
# como objetivo.
NIVELES = {
    "facil": {"nombre": "Tablón", "lotes": 6, "nudos": 6, "minimo": 7, "fraccion": 0.55},
    "normal": {"nombre": "Entarimado", "lotes": 6, "nudos": 10, "minimo": 6, "fraccion": 0.7},
    "dificil": {"nombre": "Parqué", "lotes": 5, "nudos": 14, "minimo": 5, "fraccion": 0.8},
}
NIVEL_DIARIO = "normal"
NIVEL_PRACTICA = "normal"
FRACCION_DOS_ESTRELLAS = 0.85

CUADRO_VACIO = "⬜"
CUADRO_TABLA = "🟫"
CUADRO_NUDO = "🪵"

_pop = int.bit_count if hasattr(int, "bit_count") else (lambda x: bin(x).count("1"))


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
    """Convierte una fecha ISO ("2026-11-20") en una semilla de 32 bits (hash FNV-1a)."""
    h = 0x811C9DC5
    for b in ("tarima:" + str(fecha_iso)).encode("utf-8"):
        h = ((h ^ b) * 0x01000193) & _M32
    return h


# ------------------------------------------------------------------ piezas
# Cada pieza es un conjunto de casillas (fila, columna) con la esquina superior
# izquierda en (0, 0). Las orientaciones distintas son piezas distintas: no se
# pueden girar al jugar. (nombre, casillas, ¿tiene imagen en espejo?, peso)
_BASES = [
    ("punto", [(0, 0)], False, 3),
    ("par", [(0, 0), (0, 1)], False, 8),
    ("tres", [(0, 0), (0, 1), (0, 2)], False, 8),
    ("cuatro", [(0, 0), (0, 1), (0, 2), (0, 3)], False, 5),
    ("cinco", [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)], False, 3),
    ("cuadrado", [(0, 0), (0, 1), (1, 0), (1, 1)], False, 7),
    ("cuadrado grande", [(r, c) for r in range(3) for c in range(3)], False, 2),
    ("rectangulo", [(r, c) for r in range(2) for c in range(3)], False, 4),
    ("esquina", [(0, 0), (1, 0), (1, 1)], False, 8),
    ("ele", [(0, 0), (1, 0), (2, 0), (2, 1)], True, 6),
    ("te", [(0, 0), (0, 1), (0, 2), (1, 1)], False, 5),
    ("zeta", [(0, 1), (0, 2), (1, 0), (1, 1)], True, 4),
    ("esquina grande", [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)], False, 2),
]


def _normalizar(celdas):
    mf = min(f for f, c in celdas)
    mc = min(c for f, c in celdas)
    return tuple(sorted((f - mf, c - mc) for f, c in celdas))


def _orientaciones(celdas, espejo):
    vistas = []
    formas = [list(celdas)]
    if espejo:
        formas.append([(f, -c) for f, c in celdas])
    for forma in formas:
        actual = forma
        for _ in range(4):
            n = _normalizar(actual)
            if n not in vistas:
                vistas.append(n)
            actual = [(c, -f) for f, c in actual]
    return vistas


def _mascara(f0, c0, celdas):
    """Máscaras de una pieza puesta con su esquina en (f0, c0): una por filas
    y otra por columnas (el tablero "traspuesto"), o None si se sale."""
    m = tm = 0
    for f, c in celdas:
        ff, cc = f0 + f, c0 + c
        if ff >= N or cc >= N:
            return None
        m |= 1 << (ff * N + cc)
        tm |= 1 << (cc * N + ff)
    return m, tm


PIEZAS = {}          # id -> {"base", "celdas", "alto", "ancho"}
_POR_BASE = []       # (peso, [ids]) en el orden de _BASES
_POS = {}            # id -> [(fila, col, máscara, máscara_traspuesta)]
_POSD = {}           # id -> {(fila, col): (máscara, máscara_traspuesta)}


def _construir_catalogo():
    ident = 0
    for nombre, celdas, espejo, peso in _BASES:
        ids = []
        for forma in _orientaciones(celdas, espejo):
            ident += 1
            alto = max(f for f, c in forma) + 1
            ancho = max(c for f, c in forma) + 1
            PIEZAS[ident] = {"base": nombre, "celdas": [list(x) for x in forma], "alto": alto, "ancho": ancho}
            lista = []
            for f0 in range(N - alto + 1):
                for c0 in range(N - ancho + 1):
                    m, tm = _mascara(f0, c0, forma)
                    lista.append((f0, c0, m, tm))
            _POS[ident] = lista
            _POSD[ident] = {(f, c): (m, tm) for f, c, m, tm in lista}
            ids.append(ident)
        _POR_BASE.append((peso, ids))


_construir_catalogo()
_PESO_TOTAL = sum(p for p, _ in _POR_BASE)

# Máscaras de líneas: _RB/_CB sobre el tablero por filas, _RT/_CT sobre el
# traspuesto (casilla (f, c) es el bit f*8+c en uno y c*8+f en el otro).
_RB = [255 << (N * f) for f in range(N)]
_CB = [sum(1 << (N * f + c) for f in range(N)) for c in range(N)]
_RT = [sum(1 << (N * c + f) for c in range(N)) for f in range(N)]
_CT = [255 << (N * c) for c in range(N)]
_COL0 = _CB[0]
_COL7 = _CB[N - 1]
_FILA0 = _RB[0]
_FILA7 = _RB[N - 1]

# Valor de una línea según cuántas casillas lleva: crece rápido, así que el
# jugador automático prefiere completar líneas antes que repartir casillas.
_VALOR_LINEA = [k * k if k < N else 0 for k in range(N + 1)]


def _id_pieza(semilla, k):
    """Pieza número k de una partida. Sale solo de la semilla y de k, así que
    se puede conocer cualquiera sin repetir las anteriores y deshacer nunca
    cambia lo que viene."""
    g = Generador((int(semilla) ^ ((k + 1) * 0x9E3779B1)) & _M32)
    g.siguiente()
    g.siguiente()
    x = g.siguiente() * _PESO_TOTAL
    acumulado = 0
    ids = _POR_BASE[-1][1]
    for peso, lista in _POR_BASE:
        acumulado += peso
        if x < acumulado:
            ids = lista
            break
    return ids[int(g.siguiente() * len(ids)) % len(ids)]


def _lote(semilla, j):
    return [_id_pieza(semilla, 3 * j + i) for i in range(3)]


# ------------------------------------------------------------------- reglas
# El suelo es un entero de 64 bits: la casilla (fila, col) es el bit fila*8+col.
# Se guarda también el suelo traspuesto para leer las columnas con la misma
# operación que las filas.

def _bits_a_lista(m):
    return [i for i in range(CASILLAS) if (m >> i) & 1]


def _nudos_iniciales(semilla, cfg):
    g = Generador((int(semilla) ^ 0x5DEECE66) & _M32)
    orden = list(range(CASILLAS))
    for i in range(CASILLAS - 1):
        j = i + int(g.siguiente() * (CASILLAS - i))
        orden[i], orden[j] = orden[j], orden[i]
    b = tm = 0
    por_fila = [0] * N
    por_col = [0] * N
    puestos = 0
    for casilla in orden:
        if puestos >= cfg["nudos"]:
            break
        f, c = divmod(casilla, N)
        if por_fila[f] >= N - 1 or por_col[c] >= N - 1:
            continue
        b |= 1 << casilla
        tm |= 1 << (c * N + f)
        por_fila[f] += 1
        por_col[c] += 1
        puestos += 1
    return b, tm


def _poner_y_despejar(b, t, m, tm):
    """Pone una pieza (sus máscaras) y despeja las líneas completas.
    Devuelve (suelo, traspuesto, filas, columnas, casillas despejadas)."""
    b |= m
    t |= tm
    filas = [f for f in range(N) if (b >> (N * f)) & 255 == 255]
    cols = [c for c in range(N) if (t >> (N * c)) & 255 == 255]
    despejadas = 0
    if filas or cols:
        cb = ct = 0
        for f in filas:
            cb |= _RB[f]
            ct |= _RT[f]
        for c in cols:
            cb |= _CB[c]
            ct |= _CT[c]
        despejadas = b & cb
        b &= ~cb
        t &= ~ct
    return b, t, filas, cols, despejadas


def _cabe(b, pid):
    for _f, _c, m, _tm in _POS[pid]:
        if not (b & m):
            return True
    return False


def _nuevo_estado(semilla, cfg):
    b, t = _nudos_iniciales(semilla, cfg)
    return {"b": b, "t": t, "nudos": b, "lote": 0, "usadas": 0, "lineas": 0,
            "puntos": 0, "racha": 0, "mejor_racha": 0, "colocadas": 0,
            "por_lote": [0] * cfg["lotes"], "ultimo": None}


def _copiar(est):
    c = dict(est)
    c["por_lote"] = list(est["por_lote"])
    return c


def _aplicar(est, semilla, cfg, slot, fila, col):
    """Aplica una colocación a `est`. Devuelve None si va bien o un texto de
    error (y no cambia nada)."""
    if est["lote"] >= cfg["lotes"]:
        return "La partida ya ha terminado."
    if not isinstance(slot, int) or slot < 0 or slot > 2:
        return "Esa pieza no existe."
    if (est["usadas"] >> slot) & 1:
        return "Esa pieza ya está colocada."
    pid = _lote(semilla, est["lote"])[slot]
    if (fila, col) not in _POSD[pid]:
        return "La pieza se sale del suelo."
    m, tm = _POSD[pid][(fila, col)]
    if est["b"] & m:
        return "La pieza no cabe: hay casillas ocupadas."
    b, t, filas, cols, despejadas = _poner_y_despejar(est["b"], est["t"], m, tm)
    n = len(filas) + len(cols)
    puntos = len(PIEZAS[pid]["celdas"])
    if n:
        est["racha"] += 1
        puntos += 10 * n * n + 5 * est["racha"]
    else:
        est["racha"] = 0
    est["mejor_racha"] = max(est["mejor_racha"], est["racha"])
    est["puntos"] += puntos
    est["lineas"] += n
    est["por_lote"][est["lote"]] += n
    est["b"], est["t"] = b, t
    est["nudos"] &= b
    est["colocadas"] += 1
    est["usadas"] |= 1 << slot
    est["ultimo"] = {"slot": slot, "pieza": _bits_a_lista(m), "filas": filas, "cols": cols,
                     "despejadas": _bits_a_lista(despejadas), "puntos": puntos}
    if est["usadas"] == 7:
        est["lote"] += 1
        est["usadas"] = 0
    return None


def _terminada(est, semilla, cfg):
    """None si se sigue jugando; "lotes" si se han colocado todos los lotes y
    "sin_sitio" si ninguna de las piezas que quedan cabe."""
    if est["lote"] >= cfg["lotes"]:
        return "lotes"
    ids = _lote(semilla, est["lote"])
    for slot in range(3):
        if not (est["usadas"] >> slot) & 1 and _cabe(est["b"], ids[slot]):
            return None
    return "sin_sitio"


# -------------------------------------------------------- jugador automático
# Búsqueda en haz: en cada paso se guardan los mejores `ancho` suelos según las
# líneas ya despejadas y una estimación de lo "ordenado" que queda el suelo.

def _huecos_sueltos(b):
    vacio = ~b & _TODO
    arriba = ((b << N) | _FILA0) & _TODO
    abajo = (b >> N) | _FILA7
    izq = ((b << 1) | _COL0) & _TODO
    der = (b >> 1) | _COL7
    return _pop(vacio & arriba & abajo & izq & der)


def _valor(b, t):
    v = 0
    for f in range(N):
        v += _VALOR_LINEA[_pop((b >> (N * f)) & 255)]
    for c in range(N):
        v += _VALOR_LINEA[_pop((t >> (N * c)) & 255)]
    return v - 9 * _huecos_sueltos(b)


def _plan_bot(b, t, usadas0, lineas0, lotes_ids, ancho):
    """Busca la secuencia de colocaciones que más líneas despeja.

    `lotes_ids` son las piezas de los lotes que quedan, empezando por el actual
    (del que ya pueden estar usadas las de la máscara `usadas0`). Devuelve
    (líneas, [(slot, fila, col), ...]) con la mejor secuencia encontrada."""
    estados = [(0, b, t, lineas0, usadas0, None)]
    mejor = (lineas0, None)
    for k, ids in enumerate(lotes_ids):
        for _paso in range(3):
            nuevos = {}
            for clave, sb, st, lin, usadas, plan in estados:
                if usadas == 7:
                    nuevos[(sb, 7, lin)] = (clave, sb, st, lin, usadas, plan)
                    continue
                hubo = False
                vistos = set()
                for slot in range(3):
                    if (usadas >> slot) & 1 or ids[slot] in vistos:
                        continue
                    vistos.add(ids[slot])
                    for f, c, m, tm in _POS[ids[slot]]:
                        if sb & m:
                            continue
                        hubo = True
                        nb, nt, fl, cl, _d = _poner_y_despejar(sb, st, m, tm)
                        lin2 = lin + len(fl) + len(cl)
                        clave2 = lin2 * 10000 + _valor(nb, nt)
                        u2 = usadas | (1 << slot)
                        llave = (nb, u2, lin2)
                        previo = nuevos.get(llave)
                        if previo is None or previo[0] < clave2:
                            nuevos[llave] = (clave2, nb, nt, lin2, u2, (plan, (slot, f, c)))
                if not hubo and lin >= mejor[0]:
                    mejor = (lin, plan)
            if not nuevos:
                estados = []
                break
            ordenados = sorted(nuevos.values(), key=lambda e: -e[0])
            estados = ordenados[:ancho]
        # fin del lote: las piezas del siguiente empiezan sin usar
        estados = [(cl, sb, st, lin, 0, plan) for cl, sb, st, lin, _u, plan in estados]
        if k == len(lotes_ids) - 1:
            for _cl, _sb, _st, lin, _u, plan in estados:
                if lin >= mejor[0]:
                    mejor = (lin, plan)
    secuencia = []
    plan = mejor[1]
    while plan is not None:
        plan, accion = plan
        secuencia.append(accion)
    secuencia.reverse()
    return mejor[0], secuencia


_REFERENCIAS = {}


def _simular(semilla, cfg, secuencia):
    """Repite una secuencia con las reglas reales y devuelve (estado, error)."""
    est = _nuevo_estado(semilla, cfg)
    for slot, f, c in secuencia:
        error = _aplicar(est, semilla, cfg, slot, f, c)
        if error:
            return est, error
    return est, None


def _referencia(semilla, nivel):
    """Líneas que despeja el jugador automático en esa partida (repitiendo su
    secuencia con las reglas reales, para no fiarse de su cuenta)."""
    clave = (int(semilla), nivel)
    if clave in _REFERENCIAS:
        return _REFERENCIAS[clave]
    cfg = NIVELES[nivel]
    est0 = _nuevo_estado(semilla, cfg)
    lotes = [_lote(semilla, j) for j in range(cfg["lotes"])]
    _lin, secuencia = _plan_bot(est0["b"], est0["t"], 0, 0, lotes, ANCHO_BUSQUEDA)
    est, error = _simular(semilla, cfg, secuencia)
    ref = 0 if error else est["lineas"]
    _REFERENCIAS[clave] = ref
    return ref


def _objetivo(referencia, nivel):
    return max(3, int(referencia * NIVELES[nivel]["fraccion"]))


def _generar(semilla, nivel):
    """Busca una partida que el jugador automático despeje con holgura.
    Devuelve (semilla efectiva, referencia, objetivo)."""
    cfg = NIVELES[nivel]
    mejor = None
    for intento in range(INTENTOS_GENERACION):
        s = (int(semilla) + intento * 0x9E3779B1) & _M32
        ref = _referencia(s, nivel)
        if mejor is None or ref > mejor[1]:
            mejor = (s, ref)
        if ref >= cfg["minimo"]:
            return s, ref, _objetivo(ref, nivel)
    return mejor[0], mejor[1], _objetivo(mejor[1], nivel)


def jugar_bot(semilla, nivel="normal"):
    """Devuelve (JSON) si el jugador automático cumple el objetivo de esa
    partida y cuántas líneas despeja. Sirve para comprobar el generador."""
    if nivel not in NIVELES:
        nivel = NIVEL_PRACTICA
    s, ref, obj = _generar(semilla, nivel)
    return json.dumps({"semilla_efectiva": s, "lineas": ref, "objetivo": obj, "gana": ref >= obj})


def estrellas(lineas, referencia, objetivo, pistas=0):
    """0 si no se llega al objetivo; 1 si se llega; 2 si además se despeja el
    85 % de la referencia; 3 si se iguala o supera. Con pistas, máximo 2."""
    if lineas < objetivo:
        return 0
    n = 1
    if referencia and lineas >= -(-int(referencia * 100 * FRACCION_DOS_ESTRELLAS) // 100):
        n = 2
    if referencia and lineas >= referencia:
        n = 3
    if pistas:
        n = min(n, 2)
    return n


# ------------------------------------------------------------ partida actual
_p = None


def _nueva(semilla, modo, etiqueta, nivel):
    if nivel not in NIVELES:
        nivel = NIVEL_PRACTICA
    efectiva, ref, obj = _generar(semilla, nivel)
    cfg = NIVELES[nivel]
    return {"semilla": int(semilla), "efectiva": efectiva, "modo": modo, "etiqueta": etiqueta,
            "nivel": nivel, "cfg": cfg, "referencia": ref, "objetivo": obj,
            "est": _nuevo_estado(efectiva, cfg), "historial": [], "pistas": 0}


def _forma(pid):
    d = PIEZAS[pid]
    return {"id": pid, "celdas": d["celdas"], "alto": d["alto"], "ancho": d["ancho"],
            "pivote": [d["alto"] // 2, d["ancho"] // 2], "nombre": d["base"]}


def _estado_json(error=None, pista=None):
    p = _p
    est = p["est"]
    cfg = p["cfg"]
    fin = _terminada(est, p["efectiva"], cfg)
    if fin is None:
        estado = "jugando"
    else:
        estado = "completada" if est["lineas"] >= p["objetivo"] else "perdida"
    tab = []
    for i in range(CASILLAS):
        if not (est["b"] >> i) & 1:
            tab.append(0)
        elif (est["nudos"] >> i) & 1:
            tab.append(NUDO)
        else:
            tab.append(1)
    bandeja = []
    siguiente = []
    if est["lote"] < cfg["lotes"]:
        ids = _lote(p["efectiva"], est["lote"])
        for slot in range(3):
            usada = bool((est["usadas"] >> slot) & 1)
            d = _forma(ids[slot])
            d["slot"] = slot
            d["usada"] = usada
            d["cabe"] = (not usada) and _cabe(est["b"], ids[slot])
            bandeja.append(d)
        if est["lote"] + 1 < cfg["lotes"]:
            siguiente = [_forma(x) for x in _lote(p["efectiva"], est["lote"] + 1)]
    n_est = estrellas(est["lineas"], p["referencia"], p["objetivo"], p["pistas"]) if estado == "completada" else 0
    return json.dumps({
        "error": error,
        "pista": pista,
        "estado": estado,
        "motivo_fin": fin,
        "estrellas": n_est,
        "modo": p["modo"],
        "etiqueta": p["etiqueta"],
        "nivel": p["nivel"],
        "nivel_nombre": cfg["nombre"],
        "filas": N,
        "cols": N,
        "codigos": {"nudo": NUDO},
        "tab": tab,
        "bandeja": bandeja,
        "siguiente": siguiente,
        "lote": min(est["lote"] + 1, cfg["lotes"]),
        "lotes": cfg["lotes"],
        "lineas": est["lineas"],
        "objetivo": p["objetivo"],
        "referencia": p["referencia"],
        "puntos": est["puntos"],
        "racha": est["racha"],
        "mejor_racha": est["mejor_racha"],
        "colocadas": est["colocadas"],
        "por_lote": est["por_lote"],
        "ultimo": est["ultimo"],
        "pistas": p["pistas"],
        "pistas_max": PISTAS_MAX,
        "puede_deshacer": bool(p["historial"]),
        "historial": [list(a) for a in p["historial"]],
    })


def nueva_partida(semilla, modo, etiqueta="", nivel=""):
    """Empieza una partida. `modo` es "diario" o "practica"."""
    global _p
    _p = _nueva(int(semilla), modo, etiqueta, nivel)
    return _estado_json()


def _reconstruir(p):
    est = _nuevo_estado(p["efectiva"], p["cfg"])
    buenas = []
    for slot, f, c in p["historial"]:
        if _aplicar(est, p["efectiva"], p["cfg"], slot, f, c) is None:
            buenas.append((slot, f, c))
    p["est"] = est
    p["historial"] = buenas


def colocar(slot, fila, col):
    """Coloca la pieza `slot` (0 a 2) del lote actual con su esquina superior
    izquierda en (fila, col)."""
    p = _p
    if _terminada(p["est"], p["efectiva"], p["cfg"]) is not None:
        return _estado_json("La partida ya ha terminado.")
    copia = _copiar(p["est"])
    try:
        slot, fila, col = int(slot), int(fila), int(col)
    except (ValueError, TypeError):
        return _estado_json("Jugada no válida.")
    error = _aplicar(copia, p["efectiva"], p["cfg"], slot, fila, col)
    if error:
        return _estado_json(error)
    p["est"] = copia
    p["historial"].append((slot, fila, col))
    return _estado_json()


def vista_previa(slot, fila, col):
    """Qué pasaría al colocar la pieza `slot` con su esquina en (fila, col),
    sin cambiar nada: si cabe, qué casillas ocuparía y qué líneas despejaría."""
    p = _p
    est = p["est"]
    cfg = p["cfg"]
    res = {"valida": False, "celdas": [], "filas": [], "cols": [], "motivo": ""}
    try:
        slot, fila, col = int(slot), int(fila), int(col)
    except (ValueError, TypeError):
        res["motivo"] = "Jugada no válida."
        return json.dumps(res)
    if est["lote"] >= cfg["lotes"] or slot < 0 or slot > 2 or (est["usadas"] >> slot) & 1:
        res["motivo"] = "Esa pieza no está disponible."
        return json.dumps(res)
    pid = _lote(p["efectiva"], est["lote"])[slot]
    if (fila, col) not in _POSD[pid]:
        res["motivo"] = "Se sale del suelo."
        return json.dumps(res)
    m, tm = _POSD[pid][(fila, col)]
    res["celdas"] = _bits_a_lista(m)
    if est["b"] & m:
        res["motivo"] = "Hay casillas ocupadas."
        return json.dumps(res)
    _b, _t, filas, cols, _d = _poner_y_despejar(est["b"], est["t"], m, tm)
    res.update({"valida": True, "filas": filas, "cols": cols})
    return json.dumps(res)


def deshacer():
    """Quita la última colocación."""
    p = _p
    if not p["historial"]:
        return _estado_json("No hay nada que deshacer.")
    p["historial"].pop()
    _reconstruir(p)
    return _estado_json()


def reiniciar():
    """Vuelve al principio de la misma partida (los mismos nudos y piezas)."""
    p = _p
    p["historial"] = []
    p["pistas"] = 0
    p["est"] = _nuevo_estado(p["efectiva"], p["cfg"])
    return _estado_json()


def restaurar(semilla, modo, etiqueta, nivel, historial_json, pistas=0):
    """Reconstruye una partida repitiendo las jugadas guardadas."""
    global _p
    _p = _nueva(int(semilla), modo, etiqueta, nivel)
    try:
        acciones = json.loads(historial_json)
    except (ValueError, TypeError):
        acciones = []
    if isinstance(acciones, list):
        for a in acciones:
            if not (isinstance(a, (list, tuple)) and len(a) == 3):
                continue
            try:
                slot, f, c = int(a[0]), int(a[1]), int(a[2])
            except (ValueError, TypeError):
                continue
            if _terminada(_p["est"], _p["efectiva"], _p["cfg"]) is not None:
                break
            if _aplicar(_p["est"], _p["efectiva"], _p["cfg"], slot, f, c) is None:
                _p["historial"].append((slot, f, c))
    try:
        _p["pistas"] = max(0, min(PISTAS_MAX, int(pistas)))
    except (ValueError, TypeError):
        _p["pistas"] = 0
    return _estado_json()


def pista():
    """Dice una colocación que acerca al objetivo: la primera jugada de la
    mejor secuencia que encuentra el jugador automático mirando el lote
    actual y el siguiente. Gasta una de las 3 pistas."""
    p = _p
    est = p["est"]
    cfg = p["cfg"]
    if _terminada(est, p["efectiva"], cfg) is not None:
        return _estado_json("La partida ya ha terminado.")
    if p["pistas"] >= PISTAS_MAX:
        return _estado_json("Ya has usado las %d pistas." % PISTAS_MAX)
    lotes = [_lote(p["efectiva"], j) for j in range(est["lote"], min(est["lote"] + 2, cfg["lotes"]))]
    _lin, secuencia = _plan_bot(est["b"], est["t"], est["usadas"], est["lineas"], lotes, ANCHO_PISTA)
    if not secuencia:
        return _estado_json("No hay ninguna jugada posible.")
    slot, f, c = secuencia[0]
    p["pistas"] += 1
    return _estado_json(pista={"slot": slot, "fila": f, "col": c})


def compartir_texto():
    """Resultado para compartir sin spoilers: no enseña las piezas que te
    tocaron, solo cuántas líneas despejaste en cada lote y cómo quedó el suelo.
    Devuelve "" si no se ha completado."""
    p = _p
    if p is None:
        return ""
    est = p["est"]
    fin = _terminada(est, p["efectiva"], p["cfg"])
    if fin is None or est["lineas"] < p["objetivo"]:
        return ""
    n_est = estrellas(est["lineas"], p["referencia"], p["objetivo"], p["pistas"])
    lineas = [
        "TARIMA · " + (p["etiqueta"] or "práctica"),
        "★" * n_est + "☆" * (3 - n_est) + " · %d líneas (objetivo %d, referencia %d)" % (
            est["lineas"], p["objetivo"], p["referencia"]),
        "Líneas por lote: " + " · ".join(str(x) for x in est["por_lote"][:p["cfg"]["lotes"]]),
    ]
    for f in range(N):
        fila = ""
        for c in range(N):
            i = f * N + c
            if not (est["b"] >> i) & 1:
                fila += CUADRO_VACIO
            elif (est["nudos"] >> i) & 1:
                fila += CUADRO_NUDO
            else:
                fila += CUADRO_TABLA
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


def actualizar_estadisticas(estadisticas_json, fecha_iso, lineas, estrellas_ganadas):
    """Suma un reto diario completado. La racha son los días seguidos con el
    reto completado: si ayer lo hiciste, hoy suma uno; si falta algún día,
    vuelve a empezar. Completar dos veces el mismo día no suma."""
    del lineas
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

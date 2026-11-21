"""EMPEDRADO: lógica del juego (Python 3, sin dependencias externas).

Hay que empedrar una calle: una cuadrícula en la que cada casilla lleva una
piedra o queda vacía. Al borde de cada fila y de cada columna se indica, en
orden, cuántas piedras seguidas hay en cada tramo ("3 1" = un tramo de tres
piedras, al menos un hueco y una piedra suelta). Con esas cifras hay que
deducir dónde va cada piedra.

Reglas:

  - Cada casilla tiene tres estados: vacía (0), piedra (1) y hueco (2, una
    marca tuya que significa "aquí seguro que no hay piedra").
  - Una fila o columna está cumplida cuando sus tramos de piedras coinciden
    con las cifras. Los huecos son solo notas y no cuentan.
  - Se gana cuando todas las filas y columnas están cumplidas.
  - Revisar marca las casillas que están mal (piedra donde no va o hueco donde
    sí va). Pista coloca una casilla que se deduce con lógica. Cada una se usa
    3 veces como máximo y quita estrellas. Deshacer es ilimitado.

Cada calle se genera al azar y se comprueba con un solucionador de lógica de
líneas: solo se acepta si se resuelve entera razonando fila a fila y columna a
columna, sin probar a ciegas. Eso garantiza que tiene una única solución y que
nunca hace falta adivinar. El reto diario usa la fecha como semilla: todo el
mundo recibe la misma calle. Para que el resultado sea idéntico en cualquier
versión de Python, el generador de números aleatorios está escrito aquí (no usa
`random`).

Toda la lógica vive en este archivo. La página (script.js) solo dibuja y llama
a las funciones públicas, que devuelven texto JSON (salvo `semilla_del_dia`,
`racha_vigente` y `compartir_texto`).
"""
import json
from datetime import date, timedelta

VACIA, PIEDRA, HUECO = 0, 1, 2
MAX_AYUDAS = 3            # pistas y también revisiones
INTENTOS = 600

# lado de la cuadrícula y proporción de casillas con piedra (mínimo y máximo)
NIVELES = {
    "facil": {"nombre": "Callejón", "lado": 5, "densidad": (0.50, 0.70)},
    "normal": {"nombre": "Plaza", "lado": 8, "densidad": (0.50, 0.65)},
    "dificil": {"nombre": "Avenida", "lado": 10, "densidad": (0.50, 0.62)},
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
    """Convierte una fecha ISO ("2026-11-11") en una semilla de 32 bits (hash FNV-1a)."""
    h = 0x811C9DC5
    for b in ("empedrado:" + str(fecha_iso)).encode("utf-8"):
        h = ((h ^ b) * 0x01000193) & _M32
    return h


# ------------------------------------------------------------------ reglas

def tramos(linea):
    """Cifras de una línea: longitudes de los tramos seguidos de piedras.
    Una línea sin piedras se anota [0]. Los huecos cuentan como vacío."""
    res, n = [], 0
    for x in linea:
        if x == PIEDRA:
            n += 1
        elif n:
            res.append(n)
            n = 0
    if n:
        res.append(n)
    return res or [0]


def _disposiciones(conocida, pista):
    """Todas las líneas posibles (listas de 0/1) con esas cifras que no
    contradicen lo ya conocido (-1 = desconocido, 0 = vacío, 1 = piedra)."""
    n = len(conocida)
    bloques = [] if pista == [0] else pista
    resto = [0] * (len(bloques) + 1)          # resto[i]: espacio mínimo para los bloques i.. 
    for i in range(len(bloques) - 1, -1, -1):
        resto[i] = bloques[i] + (1 + resto[i + 1] if i + 1 < len(bloques) else 0)
    salida = []
    actual = [0] * n

    def colocar(i, pos):
        if i == len(bloques):
            # lo que queda a la derecha debe poder ser vacío
            for k in range(pos, n):
                if conocida[k] == 1:
                    return
            for k in range(pos, n):
                actual[k] = 0
            salida.append(list(actual))
            return
        ultimo = n - resto[i]
        for ini in range(pos, ultimo + 1):
            ok = True
            for k in range(pos, ini):          # huecos antes del bloque
                if conocida[k] == 1:
                    ok = False
                    break
            if not ok:
                break                           # una piedra obligada quedaría sin cubrir
            fin = ini + bloques[i]
            if any(conocida[k] == 0 for k in range(ini, fin)):
                continue
            if fin < n and conocida[fin] == 1:
                continue
            for k in range(pos, ini):
                actual[k] = 0
            for k in range(ini, fin):
                actual[k] = 1
            if fin < n:
                actual[fin] = 0
            colocar(i + 1, fin + 1)

    colocar(0, 0)
    return salida


def resolver(pistas_f, pistas_c):
    """Solucionador de lógica de líneas. Devuelve (resuelta, cuadrícula, orden)
    donde la cuadrícula tiene 1 (piedra), 0 (vacío) o -1 (no deducido) y orden
    es la lista de (casilla, valor) en el orden en que se deducen."""
    nf, nc = len(pistas_f), len(pistas_c)
    cuad = [-1] * (nf * nc)
    orden = []
    cambio = True
    while cambio:
        cambio = False
        for es_fila, lista in ((True, pistas_f), (False, pistas_c)):
            for k, pista in enumerate(lista):
                if es_fila:
                    idx = [k * nc + j for j in range(nc)]
                else:
                    idx = [i * nc + k for i in range(nf)]
                conocida = [cuad[i] for i in idx]
                if -1 not in conocida:
                    continue
                posibles = _disposiciones(conocida, pista)
                if not posibles:
                    return False, cuad, orden          # cifras contradictorias
                for pos, i in enumerate(idx):
                    if cuad[i] != -1:
                        continue
                    v = posibles[0][pos]
                    if all(p[pos] == v for p in posibles):
                        cuad[i] = v
                        orden.append((i, v))
                        cambio = True
    return -1 not in cuad, cuad, orden


def _pistas_de(sol, nf, nc):
    f = [tramos(sol[i * nc:(i + 1) * nc]) for i in range(nf)]
    c = [tramos([sol[i * nc + j] for i in range(nf)]) for j in range(nc)]
    return f, c


# ------------------------------------------------------------- generación

def _calle(semilla, cfg):
    g = Generador(semilla)
    n = cfg["lado"]
    p = cfg["densidad"][0] + (cfg["densidad"][1] - cfg["densidad"][0]) * g.siguiente()
    return [1 if g.siguiente() < p else 0 for _ in range(n * n)]


def _generar(semilla, nivel):
    """Devuelve (semilla efectiva, solución, pistas de fila, pistas de columna,
    orden de deducción). Solo acepta calles que el solucionador resuelve entera."""
    cfg = NIVELES[nivel]
    n = cfg["lado"]
    for intento in range(INTENTOS):
        efectiva = (semilla + intento * 0x9E3779B9) & _M32
        sol = _calle(efectiva, cfg)
        piedras = sum(sol)
        if not cfg["densidad"][0] <= piedras / (n * n) <= cfg["densidad"][1]:
            continue
        pf, pc = _pistas_de(sol, n, n)
        ok, cuad, orden = resolver(pf, pc)
        if ok:
            return efectiva, sol, pf, pc, orden
    raise RuntimeError("no se ha encontrado una calle resoluble")


def estrellas(ayudas):
    """3 estrellas sin ayudas, 2 con hasta 2 (pistas más revisiones), 1 con más."""
    return 3 if ayudas == 0 else 2 if ayudas <= 2 else 1


# ------------------------------------------------------------ partida

_p = None


def _nueva(semilla, modo, etiqueta, nivel):
    global _p
    if modo == "diario":
        nivel = NIVEL_DIARIO
    elif nivel not in NIVELES:
        nivel = NIVEL_PRACTICA
    semilla = int(semilla) & _M32
    efectiva, sol, pf, pc, orden = _generar(semilla, nivel)
    n = NIVELES[nivel]["lado"]
    _p = {
        "semilla": semilla,
        "efectiva": efectiva,
        "modo": "diario" if modo == "diario" else "practica",
        "etiqueta": etiqueta,
        "nivel": nivel,
        "lado": n,
        "sol": sol,
        "pf": pf,
        "pc": pc,
        "orden": orden,
        "celdas": [VACIA] * (n * n),
        "pila": [],
        "pistas": 0,
        "revisiones": 0,
        "estado": "jugando",
        "malas": [],
    }


def _lineas_ok(p):
    n = p["lado"]
    c = p["celdas"]
    f = [tramos(c[i * n:(i + 1) * n]) == p["pf"][i] for i in range(n)]
    k = [tramos([c[i * n + j] for i in range(n)]) == p["pc"][j] for j in range(n)]
    return f, k


def _comprobar(p):
    f, k = _lineas_ok(p)
    p["estado"] = "completada" if all(f) and all(k) else "jugando"


def _estado_json(error=None, pista=None, aviso=None):
    p = _p
    cfg = NIVELES[p["nivel"]]
    f, k = _lineas_ok(p)
    ayudas = p["pistas"] + p["revisiones"]
    d = {
        "semilla": p["semilla"],
        "modo": p["modo"],
        "etiqueta": p["etiqueta"],
        "nivel": p["nivel"],
        "nivel_nombre": cfg["nombre"],
        "lado": p["lado"],
        "pistas_fila": p["pf"],
        "pistas_col": p["pc"],
        "celdas": list(p["celdas"]),
        "filas_ok": f,
        "cols_ok": k,
        "piedras": sum(1 for x in p["celdas"] if x == PIEDRA),
        "piedras_total": sum(p["sol"]),
        "estado": p["estado"],
        "estrellas": estrellas(ayudas) if p["estado"] == "completada" else 0,
        "puede_deshacer": bool(p["pila"]),
        "pistas": p["pistas"],
        "revisiones": p["revisiones"],
        "ayudas_max": MAX_AYUDAS,
        "malas": p["malas"],
        "pista": pista,
        "aviso": aviso,
    }
    if error:
        d["error"] = error
    return json.dumps(d)


def nueva_partida(semilla, modo, etiqueta="", nivel=""):
    """Empieza una partida. `modo` es "diario" o "practica"."""
    _nueva(semilla, modo, etiqueta, nivel)
    return _estado_json()


def poner(fila, col, estado, paso=True):
    """Pone 0 (vacía), 1 (piedra) o 2 (hueco) en la casilla. `paso` indica si
    esta jugada empieza un paso de deshacer (al arrastrar, solo la primera)."""
    p = _p
    n = p["lado"]
    try:
        fila, col, estado = int(fila), int(col), int(estado)
    except (ValueError, TypeError):
        return _estado_json("Casilla no válida.")
    if not (0 <= fila < n and 0 <= col < n) or estado not in (VACIA, PIEDRA, HUECO):
        return _estado_json("Casilla no válida.")
    if p["estado"] != "jugando":
        return _estado_json("La calle ya está empedrada. Puedes deshacer o empezar otra.")
    i = fila * n + col
    if p["celdas"][i] != estado:
        if paso or not p["pila"]:
            p["pila"].append(list(p["celdas"]))
        p["celdas"][i] = estado
        p["malas"] = []
        _comprobar(p)
    return _estado_json()


def deshacer():
    """Deshace el último paso."""
    p = _p
    if not p["pila"]:
        return _estado_json("No hay nada que deshacer.")
    p["celdas"] = p["pila"].pop()
    p["malas"] = []
    _comprobar(p)
    return _estado_json()


def reiniciar():
    """Vacía la calle (misma calle, sin ayudas gastadas)."""
    p = _p
    p["celdas"] = [VACIA] * (p["lado"] ** 2)
    p["pila"] = []
    p["pistas"] = 0
    p["revisiones"] = 0
    p["malas"] = []
    p["estado"] = "jugando"
    return _estado_json()


def revisar():
    """Marca las casillas que están mal: piedra donde no va o hueco donde sí va.
    Gasta una de las 3 ayudas de revisión."""
    p = _p
    if p["estado"] != "jugando":
        return _estado_json("La calle ya está empedrada.")
    if p["revisiones"] >= MAX_AYUDAS:
        return _estado_json("Ya has usado las %d revisiones." % MAX_AYUDAS)
    p["revisiones"] += 1
    p["malas"] = [i for i, x in enumerate(p["celdas"])
                  if (x == PIEDRA and p["sol"][i] == 0) or (x == HUECO and p["sol"][i] == 1)]
    aviso = "Todo lo que has puesto está bien." if not p["malas"] else None
    return _estado_json(aviso=aviso)


def pista():
    """Coloca una casilla que se deduce con lógica y que aún no tienes bien.
    Gasta una de las 3 pistas."""
    p = _p
    if p["estado"] != "jugando":
        return _estado_json("La calle ya está empedrada.")
    if p["pistas"] >= MAX_AYUDAS:
        return _estado_json("Ya has usado las %d pistas." % MAX_AYUDAS)
    n = p["lado"]
    for i, v in p["orden"]:
        actual = p["celdas"][i]
        # piedra deducida que aún no está puesta, o vacío deducido donde hay piedra o nada anotado
        if (v == 1 and actual != PIEDRA) or (v == 0 and actual in (PIEDRA, VACIA)):
            p["pila"].append(list(p["celdas"]))
            p["celdas"][i] = PIEDRA if v == 1 else HUECO
            p["pistas"] += 1
            p["malas"] = []
            _comprobar(p)
            return _estado_json(pista={"fila": i // n, "col": i % n, "estado": p["celdas"][i]})
    return _estado_json("No queda nada que deducir: ya está todo bien puesto.")


def restaurar(semilla, modo, etiqueta, nivel, celdas_json, pistas=0, revisiones=0):
    """Reconstruye una partida a partir de las casillas guardadas."""
    _nueva(semilla, modo, etiqueta, nivel)
    p = _p
    try:
        celdas = json.loads(celdas_json)
    except (ValueError, TypeError):
        celdas = None
    if isinstance(celdas, list) and len(celdas) == len(p["celdas"]) and all(x in (0, 1, 2) for x in celdas):
        p["celdas"] = [int(x) for x in celdas]
        _comprobar(p)
    p["pistas"] = min(MAX_AYUDAS, _entero(pistas))
    p["revisiones"] = min(MAX_AYUDAS, _entero(revisiones))
    return _estado_json()


def compartir_texto():
    """Resultado para compartir sin spoilers: no enseña la calle, solo el
    tamaño, las estrellas y las ayudas. Devuelve "" si no está completada."""
    p = _p
    if p is None or p["estado"] != "completada":
        return ""
    cfg = NIVELES[p["nivel"]]
    est = estrellas(p["pistas"] + p["revisiones"])
    lineas = [
        "EMPEDRADO · " + (p["etiqueta"] or "práctica"),
        "★" * est + "☆" * (3 - est) + " · %s %d×%d" % (cfg["nombre"], p["lado"], p["lado"]),
        "🟫" * min(p["lado"], 10),
    ]
    ayudas = []
    if p["pistas"]:
        ayudas.append("💡 %d %s" % (p["pistas"], "pista" if p["pistas"] == 1 else "pistas"))
    if p["revisiones"]:
        ayudas.append("🔍 %d %s" % (p["revisiones"], "revisión" if p["revisiones"] == 1 else "revisiones"))
    if ayudas:
        lineas.append(" · ".join(ayudas))
    else:
        lineas.append("Sin ayudas")
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


def actualizar_estadisticas(estadisticas_json, fecha_iso, estrellas_ganadas):
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

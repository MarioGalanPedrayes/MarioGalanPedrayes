"""REGUEROS: lógica del juego (Python 3, sin dependencias externas).

Un prado de 6 x 6 casillas. En cada casilla hay un trozo de reguero (canal):
un final, un recto, un codo, una T o un cruce. Del manantial sale el agua y
tienes que hacerla llegar a TODAS las casillas girándolas, sin que quede
ninguna fuga:

  - Una casilla se riega si el agua llega hasta ella desde el manantial por
    canales que se abren el uno hacia el otro.
  - Hay fuga cuando una casilla regada tiene un brazo abierto que da al borde
    del prado o a una casilla que no se abre hacia ella.
  - Se gana cuando las 36 casillas están regadas y no hay ninguna fuga.
  - Algunas casillas están fijas (con un clavo): no giran y sirven de ancla.

Cada giro de 90 grados cuenta. El prado se genera a partir de un árbol que
une todas las casillas, así que siempre tiene solución. La referencia son los
giros mínimos para reconstruir ese trazado; puntúas con estrellas según lo
cerca que estés.

El reto diario usa la fecha como semilla: todo el mundo recibe el mismo prado
el mismo día. Para que el resultado sea idéntico en cualquier versión de
Python, el generador de números aleatorios está escrito aquí (no usa `random`).

Toda la lógica vive en este archivo. La página (script.js) solo dibuja y llama
a las funciones públicas, que devuelven texto JSON (salvo `semilla_del_dia`,
`racha_vigente` y `compartir_texto`).
"""
import json
from datetime import date, timedelta

TAMANO = 6
NUM_FIJAS = 5
REFERENCIA_MINIMA = 18   # un prado casi resuelto de partida no tiene gracia

# Brazos de una casilla, un bit cada uno.
N, E, S, W = 1, 2, 4, 8
# bit -> (fila, columna, bit opuesto del vecino)
DIRECCIONES = {N: (-1, 0, S), E: (0, 1, W), S: (1, 0, N), W: (0, -1, E)}

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
    """Convierte una fecha ISO ("2026-11-04") en una semilla de 32 bits (hash FNV-1a)."""
    h = 0x811C9DC5
    for b in ("regueros:" + str(fecha_iso)).encode("utf-8"):
        h = ((h ^ b) * 0x01000193) & _M32
    return h


def _mezclar(lista, gen):
    """Baraja la lista en el sitio (Fisher-Yates)."""
    for i in range(len(lista) - 1, 0, -1):
        j = int(gen.siguiente() * (i + 1))
        lista[i], lista[j] = lista[j], lista[i]


# ---------------------------------------------------------------- piezas

def rotar(mascara, sentido):
    """Gira una casilla 90 grados. sentido >= 0: horario (N->E->S->O); si no, antihorario."""
    if sentido >= 0:
        return ((mascara << 1) | (mascara >> 3)) & 15
    return ((mascara >> 1) | ((mascara & 1) << 3)) & 15


def forma(mascara):
    """Nombre de la pieza según sus brazos: final, recto, codo, T o cruce."""
    n = bin(mascara).count("1")
    if n == 2:
        return "recto" if mascara in (N | S, E | W) else "codo"
    return {0: "vacía", 1: "final", 3: "T", 4: "cruce"}[n]


def _coste(actual, objetivo):
    """Giros mínimos (en cualquier sentido) para pasar de `actual` a `objetivo`.
    Devuelve None si no son la misma pieza."""
    mejor = None
    m = actual
    for k in range(4):
        if m == objetivo:
            c = min(k, 4 - k)
            mejor = c if mejor is None else min(mejor, c)
        m = rotar(m, 1)
    return mejor


# ------------------------------------------------------------ generación

def _arbol(n, gen):
    """Árbol aleatorio que une las n*n casillas (Kruskal con aristas barajadas).
    Devuelve la máscara de brazos de cada casilla."""
    aristas = []
    for r in range(n):
        for c in range(n):
            i = r * n + c
            if c + 1 < n:
                aristas.append((i, i + 1, E, W))
            if r + 1 < n:
                aristas.append((i, i + n, S, N))
    _mezclar(aristas, gen)
    padre = list(range(n * n))

    def raiz(x):
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    mascaras = [0] * (n * n)
    for a, b, da, db in aristas:
        ra, rb = raiz(a), raiz(b)
        if ra != rb:
            padre[ra] = rb
            mascaras[a] |= da
            mascaras[b] |= db
    return mascaras


def evaluar(mascaras, fuente, n=TAMANO):
    """Calcula qué casillas riega el agua y dónde hay fugas.

    Devuelve (regados, fugas): `regados[i]` es True si la casilla i está regada
    y `fugas[i]` es la máscara de brazos de i por los que se escapa el agua
    (solo se miran casillas regadas)."""
    total = n * n
    regados = [False] * total
    regados[fuente] = True
    pila = [fuente]
    while pila:
        i = pila.pop()
        r, c = divmod(i, n)
        for bit, (dr, dc, opuesto) in DIRECCIONES.items():
            if not mascaras[i] & bit:
                continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < n and 0 <= cc < n:
                j = rr * n + cc
                if mascaras[j] & opuesto and not regados[j]:
                    regados[j] = True
                    pila.append(j)
    fugas = [0] * total
    for i in range(total):
        if not regados[i]:
            continue
        r, c = divmod(i, n)
        for bit, (dr, dc, opuesto) in DIRECCIONES.items():
            if not mascaras[i] & bit:
                continue
            rr, cc = r + dr, c + dc
            if not (0 <= rr < n and 0 <= cc < n) or not mascaras[rr * n + cc] & opuesto:
                fugas[i] |= bit
    return regados, fugas


def _esta_completo(mascaras, fuente, n=TAMANO):
    regados, fugas = evaluar(mascaras, fuente, n)
    return all(regados) and not any(fugas)


def crear_prado(semilla, n=TAMANO):
    """Genera el prado de una semilla. Es determinista.

    Devuelve un diccionario con la solución prevista, las casillas fijas, el
    manantial, el prado ya desordenado y la referencia de giros."""
    gen = Generador(semilla)
    total = n * n
    for _ in range(60):
        solucion = _arbol(n, gen)
        fuente = int(gen.siguiente() * total)
        # Las fijas deben ser piezas que no son iguales girándolas (no el cruce).
        candidatas = [i for i in range(total) if i != fuente and solucion[i] != 15]
        _mezclar(candidatas, gen)
        fijas = sorted(candidatas[:NUM_FIJAS])
        mascaras = list(solucion)
        for i in range(total):
            if i in fijas:
                continue
            for _ in range(int(gen.siguiente() * 4)):
                mascaras[i] = rotar(mascaras[i], 1)
        referencia = sum(_coste(mascaras[i], solucion[i]) for i in range(total))
        if referencia >= REFERENCIA_MINIMA and not _esta_completo(mascaras, fuente, n):
            break
    return {
        "n": n,
        "solucion": solucion,
        "fijas": fijas,
        "fuente": fuente,
        "inicial": mascaras,
        "referencia": referencia,
    }


def estrellas(giros, referencia):
    """3 estrellas hasta un 20 % por encima de la referencia, 2 hasta un 60 %, 1 si no."""
    if giros * 5 <= referencia * 6:
        return 3
    if giros * 5 <= referencia * 8:
        return 2
    return 1


# ------------------------------------------------------------- partida

_p = None   # partida en curso


def _nueva(semilla, modo, etiqueta):
    global _p
    prado = crear_prado(int(semilla))
    _p = {
        "semilla": int(semilla),
        "modo": "diario" if modo == "diario" else "practica",
        "etiqueta": str(etiqueta or ""),
        "n": prado["n"],
        "solucion": prado["solucion"],
        "fijas": prado["fijas"],
        "fuente": prado["fuente"],
        "inicial": list(prado["inicial"]),
        "mascaras": list(prado["inicial"]),
        "referencia": prado["referencia"],
        "historial": [],      # lista de [casilla, sentido]
        "estado": "jugando",
    }


def _conteo():
    total = _p["n"] * _p["n"]
    cuenta = [0] * total
    for i, _ in _p["historial"]:
        cuenta[i] += 1
    return cuenta


def _estado_json(error=None):
    p = _p
    total = p["n"] * p["n"]
    regados, fugas = evaluar(p["mascaras"], p["fuente"], p["n"])
    n_regados = sum(regados)
    n_fugas = sum(bin(f).count("1") for f in fugas)
    giros = len(p["historial"])
    if p["estado"] == "jugando" and n_regados == total and n_fugas == 0:
        p["estado"] = "completada"
    d = {
        "semilla": p["semilla"],
        "modo": p["modo"],
        "etiqueta": p["etiqueta"],
        "n": p["n"],
        "total": total,
        "mascaras": p["mascaras"],
        "fijas": p["fijas"],
        "fuente": p["fuente"],
        "regados": [1 if r else 0 for r in regados],
        "fugas": fugas,
        "n_regados": n_regados,
        "n_fugas": n_fugas,
        "giros": giros,
        "referencia": p["referencia"],
        "estado": p["estado"],
        "estrellas": estrellas(giros, p["referencia"]) if p["estado"] == "completada" else 0,
        "puede_deshacer": giros > 0 and p["estado"] == "jugando",
        "historial": p["historial"],
        "conteo": _conteo(),
    }
    if error:
        d["error"] = error
    return json.dumps(d)


def nueva_partida(semilla, modo, etiqueta=""):
    """Empieza un prado nuevo. modo: "diario" o "practica"."""
    _nueva(semilla, modo, etiqueta)
    return _estado_json()


def restaurar(semilla, modo, etiqueta, historial_json):
    """Reconstruye una partida guardada repitiendo sus giros. Si el guardado
    no es válido, devuelve el prado desde cero."""
    _nueva(semilla, modo, etiqueta)
    try:
        historial = json.loads(historial_json)
        if not isinstance(historial, list):
            raise ValueError("historial no es una lista")
        for i, s in historial:
            if _p["estado"] != "jugando":
                raise ValueError("giros después de terminar")
            _girar(int(i), int(s))
    except (ValueError, TypeError):
        _nueva(semilla, modo, etiqueta)
    return _estado_json()


def _girar(indice, sentido):
    """Aplica un giro. Lanza ValueError si no es válido."""
    p = _p
    if p["estado"] != "jugando":
        raise ValueError("El reguero ya está completo.")
    if not 0 <= indice < p["n"] * p["n"]:
        raise ValueError("Esa casilla no existe.")
    if indice in p["fijas"]:
        raise ValueError("Esa casilla está fija (tiene un clavo): no gira.")
    sentido = 1 if sentido >= 0 else -1
    p["mascaras"][indice] = rotar(p["mascaras"][indice], sentido)
    p["historial"].append([indice, sentido])
    # Si sale del estado "jugando", _estado_json lo marcará como completada.
    regados, fugas = evaluar(p["mascaras"], p["fuente"], p["n"])
    if all(regados) and not any(fugas):
        p["estado"] = "completada"


def girar(indice, sentido):
    """Gira la casilla `indice` (0 a 35, por filas) 90 grados. sentido: 1 horario, -1 antihorario."""
    if _p is None:
        return json.dumps({"error": "No hay partida en curso."})
    try:
        _girar(int(indice), int(sentido))
    except (ValueError, TypeError) as e:
        return _estado_json(str(e))
    return _estado_json()


def deshacer():
    """Deshace el último giro (no cuenta como giro)."""
    if _p is None:
        return json.dumps({"error": "No hay partida en curso."})
    if _p["estado"] != "jugando":
        return _estado_json("El reguero ya está completo.")
    if not _p["historial"]:
        return _estado_json("No hay nada que deshacer.")
    i, s = _p["historial"].pop()
    _p["mascaras"][i] = rotar(_p["mascaras"][i], -s)
    return _estado_json()


def reiniciar():
    """Vuelve al prado inicial y borra el historial."""
    if _p is None:
        return json.dumps({"error": "No hay partida en curso."})
    _p["mascaras"] = list(_p["inicial"])
    _p["historial"] = []
    _p["estado"] = "jugando"
    return _estado_json()


# ------------------------------------------------- compartir y estadísticas

def compartir_texto():
    """Resultado para compartir sin spoilers: no enseña el trazado, solo cuánto
    has girado cada casilla. Devuelve "" si la partida no está completada."""
    p = _p
    if p is None or p["estado"] != "completada":
        return ""
    giros = len(p["historial"])
    est = estrellas(giros, p["referencia"])
    cuenta = _conteo()
    simbolos = ["⬜", "🟦", "🟩", "🟨"]
    filas = []
    for r in range(p["n"]):
        fila = ""
        for c in range(p["n"]):
            i = r * p["n"] + c
            fila += "⬛" if i in p["fijas"] else simbolos[min(cuenta[i], 3)]
        filas.append(fila)
    cabecera = "REGUEROS · " + (p["etiqueta"] or "práctica")
    linea = "★" * est + "☆" * (3 - est) + f" · {giros} giros (referencia {p['referencia']})"
    return "\n".join([cabecera, linea] + filas)


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


def actualizar_estadisticas(estadisticas_json, fecha_iso, giros, estrellas_ganadas):
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

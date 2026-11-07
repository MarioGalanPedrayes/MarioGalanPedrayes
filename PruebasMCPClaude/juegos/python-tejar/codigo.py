"""TEJAR: lógica del juego (Python 3, sin dependencias externas).

Un tejar es el taller donde se hacen las tejas. Aquí tienes un montón de
fichas apiladas en capas, como tejas en un almacén, y tienes que retirarlas
de dos en dos.

Reglas:

  - Una ficha está LIBRE cuando no tiene ninguna encima y, además, al menos
    uno de sus dos lados (izquierda o derecha) está despejado. Solo se pueden
    tocar fichas libres.
  - Eliges dos fichas libres que sean PAREJA y se retiran. Son pareja las
    fichas con el mismo dibujo (forma y color). Las cuatro ESTACIONES son una
    familia comodín: dos estaciones cualesquiera hacen pareja aunque sean
    distintas.
  - Se gana al retirar todas las fichas.
  - Si no quedan parejas libres puedes BARAJAR: las fichas que quedan se
    recolocan de forma que SIEMPRE hay una manera de terminar. También puedes
    deshacer la última pareja.
  - Estrellas: cada fallo (dos fichas libres que no son pareja) suma 1, cada
    pista 2 y cada baraja 3. Con 2 o menos son tres estrellas; con 7 o menos,
    dos; si no, una.

Cómo se garantiza que siempre hay solución: el reparto se construye AL REVÉS.
Se parte del tablero lleno, se eligen dos fichas libres, se les da el mismo
dibujo y se retiran; se repite hasta vaciarlo. Jugar es deshacer ese camino.
Cuando el jugador elige parejas distintas puede quedarse sin salida (para eso
están deshacer y barajar), y un solucionador con búsqueda en profundidad
indica la pista.

El reto diario usa la fecha como semilla: todo el mundo recibe el mismo
tablero el mismo día. Para que el resultado sea idéntico en cualquier versión
de Python, el generador pseudoaleatorio está escrito aquí (no usa `random`).

Toda la lógica vive en este archivo. La página (script.js) solo dibuja y llama
a las funciones públicas, que devuelven texto JSON (salvo `semilla_del_dia`,
`racha_vigente` y `compartir_texto`).
"""
import json
from datetime import date, timedelta

PISTAS_MAX = 3
LIMITE_NODOS = 60000     # tope de estados que explora el solucionador
_M32 = 0xFFFFFFFF

# ---------------------------------------------------------------- fichas
# 18 dibujos normales (6 formas x 3 colores) y 4 estaciones. La forma se
# dibuja con CSS y cada color lleva además una letra, así que ningún dibujo
# depende solo del color.
FORMAS = [("circulo", "círculo"), ("cuadrado", "cuadrado"), ("rombo", "rombo"),
          ("triangulo", "triángulo"), ("estrella", "estrella"), ("cruz", "cruz")]
COLORES = [("rojo", "#b3402f", "R"), ("verde", "#2f7d4f", "V"), ("azul", "#3a5da8", "A")]
ESTACIONES = [("primavera", "Pri"), ("verano", "Ver"), ("otoño", "Oto"), ("invierno", "Inv")]

SIMBOLOS = []
for _nombre_color, _hex, _letra in COLORES:
    for _forma, _nombre_forma in FORMAS:
        SIMBOLOS.append({"nombre": "%s %s" % (_nombre_forma, _nombre_color), "forma": _forma,
                         "color": _hex, "letra": _letra, "familia": False})
N_NORMALES = len(SIMBOLOS)            # 18
GRUPO_ESTACION = N_NORMALES           # todas las estaciones comparten grupo
for _nombre, _letra in ESTACIONES:
    SIMBOLOS.append({"nombre": "estación: " + _nombre, "forma": "estacion",
                     "color": "#d9b45a", "letra": _letra, "familia": True})


def _grupo(simbolo):
    """Grupo de pareja: el propio dibujo, o el comodín de las estaciones."""
    return simbolo if simbolo < N_NORMALES else GRUPO_ESTACION


# ------------------------------------------------------------ diseños
# Cada ficha mide 2x2 unidades y se coloca en (x, y, capa). Las capas
# superiores pueden quedar desplazadas una unidad, de modo que una ficha tape
# a dos de la capa de abajo.

def _rejilla(x0, y0, columnas, filas, z):
    return [(x0 + 2 * c, y0 + 2 * f, z) for f in range(filas) for c in range(columnas)]


DISENOS = {
    "corral": {"nombre": "Corral",
               "fichas": _rejilla(0, 0, 4, 4, 0) + _rejilla(2, 2, 2, 2, 1)},
    "horreo": {"nombre": "Hórreo",
               "fichas": _rejilla(0, 0, 6, 4, 0) + _rejilla(2, 2, 4, 2, 1) + _rejilla(4, 2, 2, 2, 2)},
    "pajar": {"nombre": "Pajar",
              "fichas": (_rejilla(0, 0, 8, 4, 0) + _rejilla(3, 2, 5, 2, 1)
                         + _rejilla(5, 2, 3, 2, 2) + _rejilla(6, 2, 2, 2, 3))},
}

DIFICULTADES = {
    "facil": {"nombre": "Fácil", "diseno": "corral", "barajas": 3},
    "normal": {"nombre": "Normal", "diseno": "horreo", "barajas": 2},
    "dificil": {"nombre": "Difícil", "diseno": "pajar", "barajas": 2},
}
DIFICULTAD_DIARIA = "dificil"
DIFICULTAD_PRACTICA = "normal"
EMOJIS_CAPA = ["🟫", "🟧", "🟨", "⬜"]

_GEOMETRIAS = {}


def _geometria(nombre):
    """Para cada ficha, máscaras de bits con las fichas que la tapan, las que
    tiene tocando a la izquierda y las que tiene tocando a la derecha."""
    if nombre not in _GEOMETRIAS:
        pos = DISENOS[nombre]["fichas"]
        n = len(pos)
        enc, izq, der = [0] * n, [0] * n, [0] * n
        for i, (xi, yi, zi) in enumerate(pos):
            for j, (xj, yj, zj) in enumerate(pos):
                if i == j:
                    continue
                if zj > zi and abs(xj - xi) < 2 and abs(yj - yi) < 2:
                    enc[i] |= 1 << j
                elif zj == zi and abs(yj - yi) < 2:
                    if xj == xi - 2:
                        izq[i] |= 1 << j
                    elif xj == xi + 2:
                        der[i] |= 1 << j
        _GEOMETRIAS[nombre] = (pos, enc, izq, der)
    return _GEOMETRIAS[nombre]


def _libre(mascara, i, geo):
    """Ficha viva, sin nada encima y con un lado despejado."""
    _, enc, izq, der = geo
    return bool((mascara >> i) & 1) and not (mascara & enc[i]) and (
        not (mascara & izq[i]) or not (mascara & der[i]))


def _libres(mascara, geo):
    return [i for i in range(len(geo[0])) if _libre(mascara, i, geo)]


def _pares(mascara, simbolos, geo):
    """Todas las parejas posibles ahora mismo, como tuplas (i, j) con i < j."""
    libres = _libres(mascara, geo)
    return [(a, b) for k, a in enumerate(libres) for b in libres[k + 1:]
            if _grupo(simbolos[a]) == _grupo(simbolos[b])]


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
    for b in ("tejar:" + str(fecha_iso)).encode("utf-8"):
        h = ((h ^ b) * 0x01000193) & _M32
    return h


def _mezclar(lista, gen):
    """Baraja la lista en el sitio (Fisher-Yates)."""
    for i in range(len(lista) - 1, 0, -1):
        j = int(gen.siguiente() * (i + 1))
        lista[i], lista[j] = lista[j], lista[i]


# --------------------------------------------------------- generación
def _repartir(mascara, pool, geo, gen, intentos=60):
    """Reparte los símbolos de `pool` entre las fichas vivas de `mascara`
    construyendo el tablero al revés: se retiran dos fichas libres a la vez y
    se les da la misma pareja. Devuelve {ficha: símbolo}; el tablero resultante
    siempre se puede terminar."""
    n = len(geo[0])
    for _ in range(intentos):
        por_grupo = {}
        for s in pool:
            por_grupo.setdefault(_grupo(s), []).append(s)
        for g in sorted(por_grupo):
            _mezclar(por_grupo[g], gen)
        asignacion, m, bien = {}, mascara, True
        while m:
            libres = [i for i in range(n) if _libre(m, i, geo)]
            if len(libres) < 2:
                bien = False
                break
            a = libres.pop(int(gen.siguiente() * len(libres)))
            b = libres.pop(int(gen.siguiente() * len(libres)))
            disponibles = sorted(g for g, lista in por_grupo.items() if len(lista) >= 2)
            g = disponibles[int(gen.siguiente() * len(disponibles))]
            asignacion[a] = por_grupo[g].pop()
            asignacion[b] = por_grupo[g].pop()
            m &= ~(1 << a) & ~(1 << b)
        if bien:
            return asignacion
    raise ValueError("no se pudo repartir el tablero")


def _generar(semilla, dificultad):
    cfg = DIFICULTADES[dificultad]
    geo = _geometria(cfg["diseno"])
    n = len(geo[0])
    gen = Generador(semilla)
    normales = list(range(N_NORMALES))
    _mezclar(normales, gen)
    elegidos = normales[:n // 4 - 1]
    pool = [g for g in elegidos for _ in range(4)] + [N_NORMALES + k for k in range(4)]
    asignacion = _repartir((1 << n) - 1, pool, geo, gen)
    return [asignacion[i] for i in range(n)]


# --------------------------------------------------------- solucionador
class _Limite(Exception):
    pass


def _resolver(mascara, simbolos, geo, limite=LIMITE_NODOS):
    """Busca en profundidad una forma de retirar todas las fichas vivas.
    Devuelve la lista de parejas (i, j) o None si no la encuentra (no hay
    salida o se agotó el límite de estados)."""
    pos, enc, _, _ = geo
    n = len(pos)
    grupo = [_grupo(s) for s in simbolos]
    visitados, camino, cuenta = set(), [], [0]

    def sin_salida(m):
        # Si de un grupo solo quedan dos fichas y una tapa a la otra, ninguna
        # de las dos podrá retirarse nunca.
        por = {}
        for i in range(n):
            if (m >> i) & 1:
                por.setdefault(grupo[i], []).append(i)
        for lista in por.values():
            if len(lista) == 2:
                a, b = lista
                if (enc[a] >> b) & 1 or (enc[b] >> a) & 1:
                    return True
        return False

    def dfs(m):
        if m == 0:
            return True
        if m in visitados:
            return False
        cuenta[0] += 1
        if cuenta[0] > limite:
            raise _Limite()
        if sin_salida(m):
            visitados.add(m)
            return False
        candidatos = []
        for a, b in _pares(m, simbolos, geo):
            despues = m & ~(1 << a) & ~(1 << b)
            movilidad = len(_libres(despues, geo))
            candidatos.append((-movilidad, -(pos[a][2] + pos[b][2]), a, b))
        candidatos.sort()
        for _, _, a, b in candidatos:
            camino.append((a, b))
            if dfs(m & ~(1 << a) & ~(1 << b)):
                return True
            camino.pop()
        visitados.add(m)
        return False

    try:
        return list(camino) if dfs(mascara) else None
    except _Limite:
        return None


# ------------------------------------------------------------- partida
_p = None


def estrellas(fallos, pistas=0, barajas=0):
    """Estrellas según la penalización: fallos + 2 por pista + 3 por baraja."""
    penalizacion = int(fallos) + 2 * int(pistas) + 3 * int(barajas)
    if penalizacion <= 2:
        return 3
    return 2 if penalizacion <= 7 else 1


def _recalcular(p):
    """Reconstruye el tablero repitiendo el historial desde el reparto inicial."""
    geo = p["geo"]
    n = len(geo[0])
    simbolos = list(p["inicial"])
    mascara = (1 << n) - 1
    barajas = p["barajas_extra"]
    for accion in p["historial"]:
        if accion[0] == "p":
            mascara &= ~(1 << accion[1]) & ~(1 << accion[2])
        else:
            gen = Generador((p["semilla"] ^ (0x9E3779B1 * (barajas + 1))) & _M32)
            vivas = [i for i in range(n) if (mascara >> i) & 1]
            asignacion = _repartir(mascara, [simbolos[i] for i in vivas], geo, gen)
            for i, s in asignacion.items():
                simbolos[i] = s
            barajas += 1
    p["simbolos"], p["mascara"] = simbolos, mascara


def _barajas_usadas(p):
    return p["barajas_extra"] + sum(1 for a in p["historial"] if a[0] == "b")


def _nueva(semilla, modo, etiqueta, dificultad):
    if dificultad not in DIFICULTADES:
        dificultad = DIFICULTAD_DIARIA if modo == "diario" else DIFICULTAD_PRACTICA
    cfg = DIFICULTADES[dificultad]
    geo = _geometria(cfg["diseno"])
    p = {"semilla": int(semilla) & _M32, "modo": modo, "etiqueta": etiqueta,
         "dificultad": dificultad, "geo": geo, "inicial": _generar(int(semilla) & _M32, dificultad),
         "historial": [], "pistas": 0, "fallos": 0, "barajas_extra": 0}
    _recalcular(p)
    return p


def _estado_json(error=None, pista=None):
    p = _p
    geo, mascara, simbolos = p["geo"], p["mascara"], p["simbolos"]
    pos = geo[0]
    cfg = DIFICULTADES[p["dificultad"]]
    fichas = [{"id": i, "x": pos[i][0], "y": pos[i][1], "z": pos[i][2], "s": simbolos[i],
               "libre": _libre(mascara, i, geo)}
              for i in range(len(pos)) if (mascara >> i) & 1]
    completada = mascara == 0
    pares = [] if completada else _pares(mascara, simbolos, geo)
    usadas = _barajas_usadas(p)
    quitadas = len(pos) - len(fichas)
    d = {
        "estado": "completada" if completada else "jugando",
        "fichas": fichas,
        "simbolos": SIMBOLOS,
        "ancho": max(x for x, _, _ in pos) + 2,
        "alto": max(y for _, y, _ in pos) + 2,
        "capas": max(z for _, _, z in pos) + 1,
        "parejas_hechas": quitadas // 2,
        "parejas_total": len(pos) // 2,
        "parejas_libres": len(pares),
        "sin_movimientos": (not completada) and not pares,
        "fallos": p["fallos"],
        "pistas": p["pistas"], "pistas_max": PISTAS_MAX,
        "barajas": usadas, "barajas_max": cfg["barajas"], "barajas_extra": p["barajas_extra"],
        "puede_deshacer": bool(p["historial"]) and p["historial"][-1][0] == "p",
        "estrellas": estrellas(p["fallos"], p["pistas"], usadas) if completada else 0,
        "dificultad": p["dificultad"], "dificultad_nombre": cfg["nombre"],
        "diseno_nombre": DISENOS[cfg["diseno"]]["nombre"],
        "semilla": p["semilla"], "etiqueta": p["etiqueta"],
        "historial": p["historial"],
    }
    if error:
        d["error"] = error
    if pista:
        d["pista"] = pista
    return json.dumps(d)


# ------------------------------------------------- funciones públicas
def nueva_partida(semilla, modo, etiqueta="", dificultad=""):
    """Empieza una partida nueva y devuelve el estado como JSON."""
    global _p
    _p = _nueva(semilla, modo, etiqueta, dificultad)
    return _estado_json()


def restaurar(semilla, modo, etiqueta, dificultad, historial_json, pistas=0, fallos=0, barajas_extra=0):
    """Reconstruye una partida guardada repitiendo su historial. Ignora lo que
    no sea válido, así que un guardado dañado no rompe nada."""
    global _p
    _p = _nueva(semilla, modo, etiqueta, dificultad)
    p = _p
    n = len(p["geo"][0])
    try:
        historial = json.loads(historial_json)
    except (ValueError, TypeError):
        historial = []
    p["barajas_extra"] = _entero(barajas_extra)
    limite_barajas = DIFICULTADES[p["dificultad"]]["barajas"]
    for accion in historial if isinstance(historial, list) else []:
        if not isinstance(accion, list) or not accion:
            continue
        if accion[0] == "b" and _barajas_usadas(p) < limite_barajas:
            p["historial"].append(["b"])
            _recalcular(p)
        elif accion[0] == "p" and len(accion) == 3:
            a, b = accion[1], accion[2]
            if (isinstance(a, int) and isinstance(b, int) and a != b and 0 <= a < n and 0 <= b < n
                    and _libre(p["mascara"], a, p["geo"]) and _libre(p["mascara"], b, p["geo"])
                    and _grupo(p["simbolos"][a]) == _grupo(p["simbolos"][b])):
                p["historial"].append(["p", a, b])
                _recalcular(p)
    p["pistas"] = min(PISTAS_MAX, _entero(pistas))
    p["fallos"] = _entero(fallos)
    return _estado_json()


def emparejar(a, b):
    """Intenta retirar la pareja formada por las fichas a y b."""
    p = _p
    if p["mascara"] == 0:
        return _estado_json("La partida ya ha terminado.")
    n = len(p["geo"][0])
    try:
        a, b = int(a), int(b)
    except (ValueError, TypeError):
        return _estado_json("Ficha no válida.")
    if a == b or not (0 <= a < n and 0 <= b < n):
        return _estado_json("Elige dos fichas distintas.")
    mascara, geo = p["mascara"], p["geo"]
    if not (mascara >> a) & 1 or not (mascara >> b) & 1:
        return _estado_json("Esa ficha ya se ha retirado.")
    if not _libre(mascara, a, geo) or not _libre(mascara, b, geo):
        return _estado_json("Una de las fichas está tapada o encajonada: no es libre.")
    if _grupo(p["simbolos"][a]) != _grupo(p["simbolos"][b]):
        p["fallos"] += 1
        return _estado_json("No son pareja.")
    p["historial"].append(["p", min(a, b), max(a, b)])
    p["mascara"] = mascara & ~(1 << a) & ~(1 << b)
    return _estado_json()


def deshacer():
    """Devuelve la última pareja al tablero. Una baraja no se puede deshacer."""
    p = _p
    if not p["historial"]:
        return _estado_json("No hay nada que deshacer.")
    if p["historial"][-1][0] != "p":
        return _estado_json("Una baraja no se puede deshacer.")
    p["historial"].pop()
    _recalcular(p)
    return _estado_json()


def barajar():
    """Recoloca las fichas que quedan; el nuevo tablero siempre tiene salida."""
    p = _p
    if p["mascara"] == 0:
        return _estado_json("La partida ya ha terminado.")
    if _barajas_usadas(p) >= DIFICULTADES[p["dificultad"]]["barajas"]:
        return _estado_json("Ya no te quedan barajas.")
    p["historial"].append(["b"])
    _recalcular(p)
    return _estado_json()


def reiniciar():
    """Vuelve al tablero inicial. Fallos, pistas y barajas ya gastados se conservan."""
    p = _p
    p["barajas_extra"] = _barajas_usadas(p)
    p["historial"] = []
    _recalcular(p)
    return _estado_json()


def pista():
    """Indica una pareja que mantiene el tablero con salida (si el solucionador la encuentra)."""
    p = _p
    if p["mascara"] == 0:
        return _estado_json("La partida ya ha terminado.")
    if p["pistas"] >= PISTAS_MAX:
        return _estado_json("Ya has usado las %d pistas." % PISTAS_MAX)
    solucion = _resolver(p["mascara"], p["simbolos"], p["geo"])
    if not solucion:
        return _estado_json("No encuentro salida desde aquí: deshaz alguna pareja o baraja.")
    p["pistas"] += 1
    return _estado_json(None, {"a": solucion[0][0], "b": solucion[0][1]})


# ------------------------------------------------- compartir y estadísticas
def compartir_texto():
    """Resultado para compartir sin spoilers: no enseña el tablero, solo en qué
    capas fuiste retirando las parejas. Devuelve "" si la partida no está completada."""
    p = _p
    if p is None or p["mascara"] != 0:
        return ""
    pos = p["geo"][0]
    usadas = _barajas_usadas(p)
    est = estrellas(p["fallos"], p["pistas"], usadas)
    capas = "".join(EMOJIS_CAPA[max(pos[a[1]][2], pos[a[2]][2])] for a in p["historial"] if a[0] == "p")
    lineas = [
        "TEJAR · " + (p["etiqueta"] or "práctica"),
        "★" * est + "☆" * (3 - est) + " · %d %s" % (p["fallos"], "fallo" if p["fallos"] == 1 else "fallos"),
        "Capas: " + capas,
    ]
    extras = []
    if p["pistas"]:
        extras.append("💡 %d" % p["pistas"])
    if usadas:
        extras.append("🔀 %d" % usadas)
    if extras:
        lineas.append(" ".join(extras))
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


def actualizar_estadisticas(estadisticas_json, fecha_iso, fallos, estrellas_ganadas):
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

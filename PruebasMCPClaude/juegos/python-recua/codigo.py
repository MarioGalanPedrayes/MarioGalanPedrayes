"""RECUA: roguelite de ruta por un puerto de montana con una recua de mulas.

Toda la logica del juego esta en este archivo. Las funciones publicas devuelven
texto JSON para que script.js (Pyodide) solo tenga que dibujarlo.

Reglas en una linea: llevas una recua desde el Valle hasta la Cumbre por un mapa
de senderos que se ve entero. En cada sitio puedes comprar pan, cargar o vender
sacos, descansar, pasar un paso dificil o fiarte de un desconocido. Cada tramo
cuesta un pan (sin pan, la recua pierde animo). En la Cumbre se venden los sacos
que queden; si el total de monedas llega al objetivo, ganas.

Nada es aleatorio en vivo: el mapa, los precios y hasta el resultado oculto de
cada encuentro salen de la semilla de la partida (generador mulberry32 propio).
Por eso un mismo viaje da siempre lo mismo y la partida se puede repetir a partir
de la lista de acciones. Un solucionador exacto (busqueda con memoria) recorre todo
el mapa: asi se sabe que cada viaje se puede ganar, cual es la mejor puntuacion
posible (la referencia) y que accion recomienda una pista.
"""
import json
from datetime import date

M32 = 0xFFFFFFFF

PAN_MAX = 10
ANIMO_MAX_BASE = 10
CARGA_BASE = 4
MAX_PISTAS = 3

NIVELES = {
    # etapas intermedias, recursos de salida, parte de la ganancia maxima que exige el objetivo,
    # rango de dano del paso dificil (animo), de gasto al rodear (panes) y de precio de la Cumbre
    "facil": {"nombre": "Cañada", "etapas": 5, "pan": 6, "animo": 9, "monedas": 8, "frac": 0.50,
              "dano": (1, 3), "rodeo": (1, 2), "cumbre": (4, 5), "ganancia_min": 8},
    "normal": {"nombre": "Collada", "etapas": 6, "pan": 5, "animo": 8, "monedas": 7, "frac": 0.65,
               "dano": (2, 4), "rodeo": (2, 3), "cumbre": (4, 6), "ganancia_min": 10},
    "dificil": {"nombre": "Puerto", "etapas": 7, "pan": 4, "animo": 7, "monedas": 6, "frac": 0.75,
                "dano": (2, 5), "rodeo": (2, 3), "cumbre": (4, 6), "ganancia_min": 12},
}

ETIQUETA = {"valle": "Valle", "aldea": "Aldea", "almacen": "Almacén", "feria": "Feria",
            "paso": "Paso difícil", "encuentro": "Encuentro", "ermita": "Ermita", "cumbre": "Cumbre"}
LETRA = {"valle": "V", "aldea": "A", "almacen": "M", "feria": "F",
         "paso": "P", "encuentro": "?", "ermita": "E", "cumbre": "C"}
EMOJI = {"valle": "🌄", "aldea": "🏠", "almacen": "📦", "feria": "🪙",
         "paso": "⛰️", "encuentro": "❓", "ermita": "⛪", "cumbre": "🏔️"}
TIPOS_MEDIO = ["aldea", "almacen", "feria", "paso", "encuentro", "ermita"]

SUFIJOS = ["del Roble", "de la Fuente", "del Cantu", "de la Peña", "del Tejo", "de la Escoba",
           "del Corzo", "de la Nieve", "del Mazo", "de la Veiga", "del Hayedo", "del Pedrosu",
           "de la Cuesta", "del Arroyu", "de la Cruz", "del Acebo", "de Abajo", "de Arriba",
           "del Pastor", "de la Niebla", "del Cuervo", "de la Loma", "del Argayu", "de la Brañina"]
PRODUCTOS = ["castañas", "queso", "lana", "sidra", "miel", "cecina", "avellanas", "manzanas"]

MEJORAS = {
    "alforjas": {"nombre": "Alforjas", "desc": "+1 de capacidad de carga por nivel", "costes": [3, 5]},
    "zurron": {"nombre": "Zurrón de pan", "desc": "+2 panes al salir por nivel", "costes": [2, 4]},
    "mulas": {"nombre": "Mulas de refresco", "desc": "+2 de ánimo máximo y de salida por nivel", "costes": [3, 5]},
    "bolsa": {"nombre": "Bolsa de monedas", "desc": "+2 monedas al salir por nivel", "costes": [2, 3, 4]},
    "mapa": {"nombre": "Mapa del arriero", "desc": "Enseña cómo saldrá cada encuentro antes de decidir", "costes": [8]},
}


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

    def rango(self, a, b):
        return a + self.entero(b - a + 1)

    def barajar(self, lista):
        lista = list(lista)
        for i in range(len(lista) - 1, 0, -1):
            j = self.entero(i + 1)
            lista[i], lista[j] = lista[j], lista[i]
        return lista


def fnv1a(texto):
    """Hash FNV-1a de 32 bits: convierte la fecha del dia en una semilla."""
    h = 0x811C9DC5
    for b in texto.encode("utf-8"):
        h = ((h ^ b) * 0x01000193) & M32
    return h


def semilla_de_fecha(iso):
    return fnv1a("recua-" + iso)


# ---------------------------------------------------------------- reglas de recursos
# El estado de la recua es una tupla (pan, animo, monedas, sacos).
def _ef(pan=0, animo=0, monedas=0, carga=0):
    return (pan, animo, monedas, carga)


def _ef_txt(ef):
    partes = []
    for i, (uno, varios) in enumerate((("pan", "panes"), ("ánimo", "ánimo"),
                                       ("moneda", "monedas"), ("saco", "sacos"))):
        v = ef[i]
        if v:
            partes.append(f"{'+' if v > 0 else '−'}{abs(v)} {uno if abs(v) == 1 else varios}")
    return ", ".join(partes) if partes else "sin coste"


def _legal(est, ef, animo_max, cap):
    """Comprueba si se puede pagar el coste visible de una oferta."""
    pan, animo, mon, car = est
    dp, da, dm, dc = ef
    if pan + dp < 0 or mon + dm < 0 or car + dc < 0 or car + dc > cap or animo + da < 1:
        return False
    if dp > 0 and pan >= PAN_MAX:
        return False
    if da > 0 and animo >= animo_max:
        return False
    return True


def _motivo_no(est, ef, animo_max, cap):
    pan, animo, mon, car = est
    dp, da, dm, dc = ef
    if mon + dm < 0:
        return "No te llegan las monedas."
    if pan + dp < 0:
        return "No te quedan panes para eso."
    if car + dc < 0:
        return "No llevas sacos que vender."
    if car + dc > cap:
        return "No caben más sacos en las alforjas."
    if animo + da < 1:
        return "La recua no aguantaría ese esfuerzo."
    if dp > 0 and pan >= PAN_MAX:
        return "Ya llevas todos los panes que caben."
    if da > 0 and animo >= animo_max:
        return "El ánimo ya está al máximo."
    return ""


def _aplicar(est, ef, oculto, animo_max, cap):
    pan, animo, mon, car = est
    dp, da, dm, dc = ef
    pan = min(PAN_MAX, pan + dp)
    animo = min(animo_max, animo + da)
    mon += dm
    car += dc
    if oculto:
        dp, da, dm, dc = oculto
        pan = min(PAN_MAX, max(0, pan + dp))
        animo = min(animo_max, max(1, animo + da))
        mon = max(0, mon + dm)
        car = min(cap, max(0, car + dc))
    return (pan, animo, mon, car)


def _viaje(est):
    """Cada tramo gasta un pan; sin pan la recua pierde 2 de animo. None si no aguanta."""
    pan, animo, mon, car = est
    if pan > 0:
        return (pan - 1, animo, mon, car)
    if animo - 2 < 1:
        return None
    return (pan, animo - 2, mon, car)


# ---------------------------------------------------------------- mapa
def _oferta(k, tipo, txt, ef, grupo=-1, clase="", orden=0, oculto=None, res=None):
    return {"k": k, "tipo": tipo, "txt": txt, "ef": ef, "grupo": grupo, "clase": clase,
            "orden": orden, "oculto": oculto, "res": res}


def _ofertas_de(tipo, rng, cfg, precio_cumbre):
    of = []

    def add(*a, **kw):
        of.append(_oferta(len(of), *a, **kw))

    if tipo == "valle":
        for i in range(3):
            add("pan", "Comprar 1 pan", _ef(pan=1, monedas=-1), clase="pan", orden=i)
        for i in range(6):
            add("carga", "Cargar un saco de " + PRODUCTOS[rng.entero(len(PRODUCTOS))],
                _ef(monedas=-2, carga=1), clase="carga", orden=i)
    elif tipo == "aldea":
        p = rng.rango(1, 3)
        for i in range(2):
            add("pan", "Comprar 2 panes", _ef(pan=2, monedas=-p), clase="pan", orden=i)
        add("descanso", "Descansar y dar de comer a las mulas", _ef(animo=2, monedas=-rng.rango(2, 3)))
    elif tipo == "almacen":
        p = rng.rango(2, 3)
        prod = PRODUCTOS[rng.entero(len(PRODUCTOS))]
        for i in range(3):
            add("carga", "Cargar un saco de " + prod, _ef(monedas=-p, carga=1), clase="carga", orden=i)
    elif tipo == "feria":
        q = precio_cumbre + rng.rango(1, 3)
        for i in range(3):
            add("venta", "Vender un saco", _ef(monedas=q, carga=-1), clase="venta", orden=i)
    elif tipo == "paso":
        d = rng.rango(*cfg["dano"])
        r = rng.rango(*cfg["rodeo"])
        add("cruzar", "Cruzar por el paso", _ef(animo=-d), grupo=0)
        add("rodear", "Rodear por la ladera", _ef(pan=-r), grupo=0)
    elif tipo == "encuentro":
        bueno = rng.siguiente() < 0.6
        clase = rng.entero(3)
        if clase == 0:
            if bueno:
                b = rng.rango(4, 6)
                add("azar", "Aceptar el trato de un forastero", _ef(), oculto=_ef(monedas=b),
                    res=f"El trato era bueno: +{b} monedas.")
            else:
                c = rng.rango(2, 4)
                add("azar", "Aceptar el trato de un forastero", _ef(), oculto=_ef(monedas=-c),
                    res=f"Era un timo: −{c} monedas.")
        elif clase == 1:
            if bueno:
                add("azar", "Pagar una moneda a la curandera", _ef(monedas=-1), oculto=_ef(animo=3),
                    res="Las hierbas funcionan: +3 de ánimo.")
            else:
                add("azar", "Pagar una moneda a la curandera", _ef(monedas=-1), oculto=_ef(animo=-1),
                    res="El remedio sienta mal: −1 de ánimo.")
        else:
            if bueno:
                add("azar", "Cambiar con el mercader errante", _ef(), oculto=_ef(carga=1),
                    res="Te deja un saco de más: +1 saco.")
            else:
                add("azar", "Cambiar con el mercader errante", _ef(), oculto=_ef(monedas=-2),
                    res="Te cobra de más: −2 monedas.")
    elif tipo == "ermita":
        add("curar", "Rezar y descansar", _ef(animo=3), grupo=0)
        add("pan", "Aceptar el pan del ermitaño", _ef(pan=3), grupo=0)
    return of


def _preparar_nodo(nodo):
    """Calcula las mascaras de bits que usan las reglas de cada oferta (una sola vez)."""
    of = nodo["ofertas"]
    for o in of:
        req = 0
        gm = 0
        for p in of:
            if p["k"] == o["k"]:
                continue
            if o["clase"] and p["clase"] == o["clase"] and p["orden"] < o["orden"]:
                req |= 1 << p["k"]
            if o["grupo"] >= 0 and p["grupo"] == o["grupo"]:
                gm |= 1 << p["k"]
        o["req"] = req
        o["gm"] = gm
    nodo["obl"] = nodo["tipo"] == "paso"
    nodo["obl_mask"] = sum(1 << o["k"] for o in of if o["grupo"] >= 0) if nodo["obl"] else 0


def _crear_mapa(semilla, cfg, intento):
    rng = Mulberry((semilla * 2654435761 + intento * 0x9E3779B1 + 1013904223) & M32)
    etapas = cfg["etapas"]
    precio = rng.rango(*cfg["cumbre"])
    sufijos = rng.barajar(SUFIJOS)
    nodos = []

    def nuevo(etapa, col, tipo):
        if tipo == "valle":
            nombre = "Valle de salida"
        elif tipo == "cumbre":
            nombre = "Mercado de la Cumbre"
        else:
            nombre = f"{ETIQUETA[tipo]} {sufijos.pop()}"
        nodo = {"id": len(nodos), "etapa": etapa, "col": col, "tipo": tipo, "nombre": nombre,
                "salidas": [], "ofertas": _ofertas_de(tipo, rng, cfg, precio)}
        _preparar_nodo(nodo)
        nodos.append(nodo)
        return nodo["id"]

    ids = [[nuevo(0, 1, "valle")]]
    for e in range(1, etapas + 1):
        tipos = rng.barajar(TIPOS_MEDIO)[:3]
        ids.append([nuevo(e, c, tipos[c]) for c in range(3)])
    ids.append([nuevo(etapas + 1, 1, "cumbre")])

    for a in ids[0]:
        nodos[a]["salidas"] = list(ids[1])
    for e in range(1, etapas):
        rectas = [(0, 0), (1, 1), (2, 2)]
        diagonales = rng.barajar([(0, 1), (1, 0), (1, 2), (2, 1)])
        senderos = rectas + diagonales[rng.entero(3):]   # se quitan 0, 1 o 2 diagonales
        for c, c2 in sorted(senderos):
            nodos[ids[e][c]]["salidas"].append(ids[e + 1][c2])
    for a in ids[etapas]:
        nodos[a]["salidas"] = list(ids[etapas + 1])
    return {"nodos": nodos, "precio": precio, "cumbre": ids[etapas + 1][0]}


# ---------------------------------------------------------------- solucionador exacto
def _disponible(nodo, mask, k):
    o = nodo["ofertas"][k]
    return not (mask >> k & 1) and not (mask & o["gm"]) and (mask & o["req"]) == o["req"]


def _puede_salir(nodo, mask):
    return not nodo["obl"] or bool(mask & nodo["obl_mask"])


class Solucionador:
    """Busca con memoria la mejor puntuacion final posible desde cualquier punto del mapa."""

    def __init__(self, mapa, animo_max, cap):
        self.nodos = mapa["nodos"]
        self.precio = mapa["precio"]
        self.cumbre = mapa["cumbre"]
        self.animo_max = animo_max
        self.cap = cap
        self.memo = {}

    def valor(self, nid, est, mask):
        """Mejor valor final (monedas + sacos a precio de Cumbre); -1 si no se puede llegar."""
        clave = (nid, est, mask)
        r = self.memo.get(clave)
        if r is not None:
            return r
        nodo = self.nodos[nid]
        if nid == self.cumbre:
            r = est[2] + est[3] * self.precio
        else:
            r = -1
            if _puede_salir(nodo, mask):
                e2 = _viaje(est)
                if e2 is not None:
                    for s in nodo["salidas"]:
                        v = self.valor(s, e2, 0)
                        if v > r:
                            r = v
            for o in nodo["ofertas"]:
                if _disponible(nodo, mask, o["k"]) and _legal(est, o["ef"], self.animo_max, self.cap):
                    v = self.valor(nid, _aplicar(est, o["ef"], o["oculto"], self.animo_max, self.cap),
                                   mask | (1 << o["k"]))
                    if v > r:
                        r = v
        self.memo[clave] = r
        return r

    def mejor_accion(self, nid, est, mask):
        """Accion ('m<id>' o 'o<k>') que lleva al mejor valor final. Prefiere seguir a gastar en ofertas."""
        nodo = self.nodos[nid]
        mejor, accion = -2, None
        if _puede_salir(nodo, mask):
            e2 = _viaje(est)
            if e2 is not None:
                for s in nodo["salidas"]:
                    v = self.valor(s, e2, 0)
                    if v > mejor:
                        mejor, accion = v, f"m{s}"
        for o in nodo["ofertas"]:
            if _disponible(nodo, mask, o["k"]) and _legal(est, o["ef"], self.animo_max, self.cap):
                v = self.valor(nid, _aplicar(est, o["ef"], o["oculto"], self.animo_max, self.cap),
                               mask | (1 << o["k"]))
                if v > mejor:
                    mejor, accion = v, f"o{o['k']}"
        return accion if mejor >= 0 else None


# ---------------------------------------------------------------- partidas
def _contexto(cfg, mejoras):
    n = lambda c: int(mejoras.get(c, 0))
    animo_max = ANIMO_MAX_BASE + 2 * n("mulas")
    return {"animo_max": animo_max, "cap": CARGA_BASE + n("alforjas"),
            "ini": (min(PAN_MAX, cfg["pan"] + 2 * n("zurron")),
                    min(animo_max, cfg["animo"] + 2 * n("mulas")),
                    cfg["monedas"] + 2 * n("bolsa"), 0),
            "ve_resultados": n("mapa") > 0}


def _mejoras_validas(datos):
    out = {}
    if isinstance(datos, dict):
        for clave, m in MEJORAS.items():
            try:
                v = int(datos.get(clave, 0))
            except (TypeError, ValueError):
                v = 0
            if v > 0:
                out[clave] = min(v, len(m["costes"]))
    return out


_CACHE_PARTIDAS = {}


def crear_partida(semilla, nivel):
    """Genera (y guarda) el mapa de una semilla. Prueba mapas parecidos hasta que el
    mejor viaje posible (sin mejoras) gane lo bastante como para que haya objetivo."""
    clave = (semilla, nivel)
    if clave in _CACHE_PARTIDAS:
        return _CACHE_PARTIDAS[clave]
    cfg = NIVELES[nivel]
    base = _contexto(cfg, {})
    ini = base["ini"]
    for intento in range(80):
        mapa = _crear_mapa(semilla, cfg, intento)
        sol = Solucionador(mapa, base["animo_max"], base["cap"])
        opt = sol.valor(0, ini, 0)
        if opt - ini[2] >= cfg["ganancia_min"]:
            break
    ganancia = max(0, opt - ini[2])
    objetivo = ini[2] + -(-int(cfg["frac"] * 1000) * ganancia // 1000)
    p = {"cfg": cfg, "nivel": nivel, "semilla": semilla, "mapa": mapa, "objetivo": objetivo,
         "opt_base": opt, "intentos": intento + 1, "solucionadores": {(base["animo_max"], base["cap"]): sol}}
    _CACHE_PARTIDAS[clave] = p
    return p


def _solucionador(p, ctx):
    clave = (ctx["animo_max"], ctx["cap"])
    if clave not in p["solucionadores"]:
        p["solucionadores"][clave] = Solucionador(p["mapa"], ctx["animo_max"], ctx["cap"])
    return p["solucionadores"][clave]


def _estrellas(valor, ref, monedas_ini, pistas):
    g_ref = max(1, ref - monedas_ini)
    g = valor - monedas_ini
    if g * 100 >= 90 * g_ref:
        e = 3
    elif g * 100 >= 70 * g_ref:
        e = 2
    else:
        e = 1
    return min(e, 2) if pistas > 0 else e


# ---------------------------------------------------------------- simulacion de acciones
def _sim_nueva(ctx):
    return {"est": ctx["ini"], "nid": 0, "mask": 0, "ruta": [0], "resultado": "jugando",
            "motivo": "", "valor": None, "msg": ""}


def _hay_jugada(sim, p, ctx):
    nodo = p["mapa"]["nodos"][sim["nid"]]
    if _puede_salir(nodo, sim["mask"]) and _viaje(sim["est"]) is not None:
        return True
    return any(_disponible(nodo, sim["mask"], o["k"]) and _legal(sim["est"], o["ef"], ctx["animo_max"], ctx["cap"])
               for o in nodo["ofertas"])


def _paso_sim(sim, p, ctx, accion):
    """Aplica una accion. Devuelve el texto del error (y no cambia nada) o '' si fue bien."""
    if sim["resultado"] != "jugando":
        return "El viaje ya ha terminado."
    nodos = p["mapa"]["nodos"]
    nodo = nodos[sim["nid"]]
    try:
        tipo, n = accion[0], int(accion[1:])
    except (TypeError, ValueError, IndexError):
        return "Acción no válida."
    if tipo == "o":
        if not 0 <= n < len(nodo["ofertas"]):
            return "Esa oferta no existe."
        o = nodo["ofertas"][n]
        if not _disponible(nodo, sim["mask"], n):
            return "Esa oferta ya no está disponible aquí."
        if not _legal(sim["est"], o["ef"], ctx["animo_max"], ctx["cap"]):
            return _motivo_no(sim["est"], o["ef"], ctx["animo_max"], ctx["cap"])
        sim["est"] = _aplicar(sim["est"], o["ef"], o["oculto"], ctx["animo_max"], ctx["cap"])
        sim["mask"] |= 1 << n
        sim["msg"] = o["res"] if o["res"] else f"{o['txt']}: {_ef_txt(o['ef'])}."
    elif tipo == "m":
        if n not in nodo["salidas"]:
            return "Desde aquí no hay sendero a ese sitio."
        if not _puede_salir(nodo, sim["mask"]):
            return "Antes de seguir tienes que decidir cómo pasar."
        e2 = _viaje(sim["est"])
        if e2 is None:
            return "Sin pan, la recua no tiene fuerzas para otro tramo."
        hambre = sim["est"][0] == 0
        sim["est"] = e2
        sim["nid"] = n
        sim["mask"] = 0
        sim["ruta"].append(n)
        destino = nodos[n]
        sim["msg"] = (f"Llegáis a {destino['nombre']}. " +
                      ("No quedaba pan: la recua pasa hambre (−2 de ánimo)." if hambre else "El tramo gasta 1 pan."))
        if n == p["mapa"]["cumbre"]:
            valor = e2[2] + e2[3] * p["mapa"]["precio"]
            sim["valor"] = valor
            if valor >= p["objetivo"]:
                sim["resultado"] = "ganada"
                sim["motivo"] = f"Vendes lo que queda en la Cumbre y reúnes {valor} monedas."
            else:
                sim["resultado"] = "perdida"
                sim["motivo"] = f"Llegáis con {valor} monedas de valor, pero el objetivo era {p['objetivo']}."
            return ""
    else:
        return "Acción no válida."
    if sim["resultado"] == "jugando" and not _hay_jugada(sim, p, ctx):
        sim["resultado"] = "perdida"
        sim["motivo"] = "La recua se ha quedado sin fuerzas ni recursos para seguir."
    return ""


# ---------------------------------------------------------------- estado que ve la interfaz
JUEGO = {}


def _iniciar(modo, nivel, semilla, fecha, mejoras):
    p = crear_partida(semilla, nivel)
    ctx = _contexto(p["cfg"], mejoras)
    sol = _solucionador(p, ctx)
    ref = sol.valor(0, ctx["ini"], 0)
    JUEGO.clear()
    JUEGO.update({"modo": modo, "nivel": nivel, "semilla": semilla, "fecha": fecha, "mejoras": mejoras,
                  "partida": p, "ctx": ctx, "sol": sol, "ref": ref, "acciones": [], "pistas": 0,
                  "pista": None, "sim": _sim_nueva(ctx), "error": ""})


def _publico_oferta(o, ctx):
    d = {"k": o["k"], "txt": o["txt"], "efecto": _ef_txt(o["ef"]), "azar": o["oculto"] is not None,
         "grupo": o["grupo"]}
    if d["azar"] and ctx["ve_resultados"]:
        bueno = o["oculto"][1] > 0 or o["oculto"][2] > 0 or o["oculto"][3] > 0
        d["adivina"] = ("Saldrá bien: " if bueno else "Saldrá mal: ") + _ef_txt(o["oculto"])
    return d


def _estado(error=""):
    j = JUEGO
    p, sim, ctx = j["partida"], j["sim"], j["ctx"]
    nodos = p["mapa"]["nodos"]
    nodo = nodos[sim["nid"]]
    est = sim["est"]
    fin = sim["resultado"] != "jugando"
    publicos = []
    for n in nodos:
        publicos.append({"id": n["id"], "etapa": n["etapa"], "col": n["col"], "tipo": n["tipo"],
                         "letra": LETRA[n["tipo"]], "etiqueta": ETIQUETA[n["tipo"]], "nombre": n["nombre"],
                         "salidas": n["salidas"], "obligatorio": n["obl"],
                         "ofertas": [_publico_oferta(o, ctx) for o in n["ofertas"]]})
    ofertas = []
    for o in nodo["ofertas"]:
        disp = _disponible(nodo, sim["mask"], o["k"])
        legal = disp and _legal(est, o["ef"], ctx["animo_max"], ctx["cap"])
        usada = bool(sim["mask"] >> o["k"] & 1)
        if usada:
            motivo = "Ya lo has hecho."
        elif not disp:
            motivo = "Antes hay que hacer lo anterior." if o["req"] else "Ya has elegido otra opción."
        else:
            motivo = "" if legal else _motivo_no(est, o["ef"], ctx["animo_max"], ctx["cap"])
        ofertas.append({"k": o["k"], "usada": usada, "legal": bool(legal and not fin), "motivo": motivo})
    sale = _puede_salir(nodo, sim["mask"])
    fuerzas = _viaje(est) is not None
    destinos = []
    if sim["nid"] != p["mapa"]["cumbre"]:
        for s in nodo["salidas"]:
            motivo = ""
            if not sale:
                motivo = "Antes de seguir tienes que decidir cómo pasar."
            elif not fuerzas:
                motivo = "Sin pan, la recua no tiene fuerzas para otro tramo."
            destinos.append({"id": s, "legal": not fin and sale and fuerzas, "motivo": motivo})
    precio = p["mapa"]["precio"]
    valor_ahora = est[2] + est[3] * precio
    viable = j["sol"].valor(sim["nid"], est, sim["mask"]) >= p["objetivo"] if not fin else None
    ini_mon = ctx["ini"][2]
    estrellas = 0
    sellos = 0
    if sim["resultado"] == "ganada":
        estrellas = _estrellas(sim["valor"], j["ref"], ini_mon, j["pistas"])
        sellos = (2 if j["modo"] == "diario" else 1) + estrellas
    elif sim["resultado"] == "perdida" and j["modo"] != "diario" and nodo["etapa"] >= 3:
        sellos = 1
    return {
        "modo": j["modo"], "nivel": j["nivel"], "nombre_nivel": p["cfg"]["nombre"],
        "semilla": str(j["semilla"]), "fecha": j["fecha"],
        "id_partida": f"{j['modo']}:{j['nivel']}:{j['semilla']}",
        "nodos": publicos, "actual": sim["nid"], "ruta": sim["ruta"], "ultima_etapa": p["cfg"]["etapas"] + 1,
        "recursos": {"pan": est[0], "animo": est[1], "monedas": est[2], "carga": est[3],
                     "pan_max": PAN_MAX, "animo_max": ctx["animo_max"], "capacidad": ctx["cap"]},
        "precio_cumbre": precio, "valor_ahora": valor_ahora, "objetivo": p["objetivo"], "ref": j["ref"],
        "monedas_ini": ini_mon, "viable": viable,
        "ofertas_estado": ofertas, "destinos": destinos,
        "resultado": sim["resultado"], "motivo": sim["motivo"], "valor_final": sim["valor"],
        "estrellas": estrellas, "sellos": sellos, "mensaje": sim["msg"],
        "acciones": list(j["acciones"]), "pistas": j["pistas"], "max_pistas": MAX_PISTAS,
        "pista": j["pista"], "mejoras": j["mejoras"], "error": error,
    }


# ---------------------------------------------------------------- funciones publicas
def nueva(modo, nivel, semilla_o_fecha, mejoras_json="{}"):
    """Empieza un viaje. diario: la semilla sale de la fecha y no se usan mejoras."""
    if nivel not in NIVELES:
        nivel = "normal"
    if modo == "diario":
        fecha = str(semilla_o_fecha)
        semilla, mejoras = semilla_de_fecha(fecha), {}
    else:
        modo, fecha = "practica", ""
        semilla = int(semilla_o_fecha) & M32
        mejoras = _mejoras_validas(json.loads(mejoras_json or "{}"))
    _iniciar(modo, nivel, semilla, fecha, mejoras)
    return json.dumps(_estado())


def reconstruir(modo, nivel, semilla_o_fecha, acciones_json, pistas, mejoras_json="{}"):
    """Vuelve a jugar desde el principio la lista de acciones guardada (el viaje es determinista)."""
    nueva(modo, nivel, semilla_o_fecha, mejoras_json)
    j = JUEGO
    for a in json.loads(acciones_json):
        if _paso_sim(j["sim"], j["partida"], j["ctx"], a) == "":
            j["acciones"].append(a)
        else:
            break
    j["pistas"] = max(0, min(MAX_PISTAS, int(pistas)))
    return json.dumps(_estado())


def accion(codigo):
    """'o<k>': usar la oferta k del sitio actual. 'm<id>': ir al sitio con ese id."""
    j = JUEGO
    err = _paso_sim(j["sim"], j["partida"], j["ctx"], codigo)
    j["pista"] = None
    if err == "":
        j["acciones"].append(codigo)
    return json.dumps(_estado(err))


def reiniciar():
    j = JUEGO
    _iniciar(j["modo"], j["nivel"], j["semilla"], j["fecha"], j["mejoras"])
    return json.dumps(_estado())


def pista():
    """Recomienda la mejor accion segun el solucionador (3 como maximo)."""
    j = JUEGO
    sim = j["sim"]
    if sim["resultado"] != "jugando":
        return json.dumps(_estado())
    if j["pistas"] >= MAX_PISTAS:
        return json.dumps(_estado("Ya has usado las tres pistas."))
    a = j["sol"].mejor_accion(sim["nid"], sim["est"], sim["mask"])
    if a is None:
        return json.dumps(_estado("No hay ninguna jugada que mejore la situación."))
    j["pistas"] += 1
    j["pista"] = a
    return json.dumps(_estado())


def jugar_bot(semilla, nivel="normal", mejoras=None):
    """Juega el viaje perfecto con el solucionador. Sirve para probar y para la referencia."""
    nueva("practica", nivel, str(semilla), json.dumps(mejoras or {}))
    j = JUEGO
    while j["sim"]["resultado"] == "jugando":
        a = j["sol"].mejor_accion(j["sim"]["nid"], j["sim"]["est"], j["sim"]["mask"])
        if a is None or _paso_sim(j["sim"], j["partida"], j["ctx"], a) != "":
            break
        j["acciones"].append(a)
    e = _estado()
    return {"gana": e["resultado"] == "ganada", "valor": e["valor_final"], "objetivo": e["objetivo"],
            "ref": e["ref"], "acciones": len(j["acciones"]), "estrellas": e["estrellas"]}


def compartir():
    """Texto para pegar en cualquier sitio: nota y ruta de tipos de sitio, sin desvelar los resultados."""
    j = JUEGO
    p, sim = j["partida"], j["sim"]
    nodos = p["mapa"]["nodos"]
    titulo = f"RECUA {j['fecha']} · {p['cfg']['nombre']}" if j["modo"] == "diario" else f"RECUA · {p['cfg']['nombre']}"
    if sim["resultado"] == "ganada":
        e = _estrellas(sim["valor"], j["ref"], j["ctx"]["ini"][2], j["pistas"])
        nota = "★" * e + "☆" * (3 - e) + f" {sim['valor']} monedas de valor (objetivo {p['objetivo']}, referencia {j['ref']})"
    elif sim["resultado"] == "perdida":
        nota = f"no llegué al objetivo: etapa {nodos[sim['nid']]['etapa']} de {p['cfg']['etapas'] + 1}"
    else:
        nota = "viaje en marcha"
    ruta = "".join(EMOJI[nodos[i]["tipo"]] for i in sim["ruta"])
    return "\n".join([titulo, nota, ruta])


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


def catalogo_mejoras(mejoras_json="{}"):
    """Mejoras permanentes con su nivel actual y el coste del siguiente."""
    nivel = _mejoras_validas(json.loads(mejoras_json or "{}"))
    out = []
    for clave, m in MEJORAS.items():
        n = nivel.get(clave, 0)
        out.append({"clave": clave, "nombre": m["nombre"], "desc": m["desc"], "nivel": n,
                    "max": len(m["costes"]), "coste": m["costes"][n] if n < len(m["costes"]) else None})
    return json.dumps(out)


def comprar_mejora(mejoras_json, clave, sellos):
    """Intenta comprar el siguiente nivel de una mejora. Devuelve {ok, mejoras, sellos, error}."""
    nivel = _mejoras_validas(json.loads(mejoras_json or "{}"))
    sellos = max(0, int(sellos))
    if clave not in MEJORAS:
        return json.dumps({"ok": False, "mejoras": nivel, "sellos": sellos, "error": "Esa mejora no existe."})
    n = nivel.get(clave, 0)
    costes = MEJORAS[clave]["costes"]
    if n >= len(costes):
        return json.dumps({"ok": False, "mejoras": nivel, "sellos": sellos, "error": "Ya está al máximo."})
    if sellos < costes[n]:
        return json.dumps({"ok": False, "mejoras": nivel, "sellos": sellos,
                           "error": f"Te faltan {costes[n] - sellos} sellos."})
    nivel[clave] = n + 1
    return json.dumps({"ok": True, "mejoras": nivel, "sellos": sellos - costes[n], "error": ""})

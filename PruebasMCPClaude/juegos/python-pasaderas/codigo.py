"""PASADERAS: lógica del juego (Python 3, sin dependencias externas).

Hay que cruzar un río pisando piedras. Cada piedra es una palabra de cuatro
letras y de una piedra a la siguiente solo se puede pasar cambiando UNA letra
(CASA -> CASO -> CESO...). Se empieza en una orilla (la palabra de salida) y hay
que llegar a la otra (la palabra meta) en el menor número de pasos posible.

Reglas:

  - Solo valen palabras de la lista del juego (nombres, adjetivos y algunas
    formas verbales frecuentes, sin tildes ni eñes: "mama" vale, "mamá" se
    escribe igual sin tilde).
  - Cada paso cambia exactamente una letra de la piedra en la que estás.
  - No se pisa dos veces la misma piedra.
  - La crecida: en los niveles Corriente y Torrente el río trae agua de más y
    deja algunas piedras bajo el agua. Esas palabras están bloqueadas, y se ven
    en la pantalla antes de empezar. Siempre se llega a la meta sin ellas.
  - "Par" es el menor número de pasos que hay hasta la meta esquivando la
    crecida, calculado por una búsqueda en anchura (es exacto, no una estimación).
  - Pista: te dice la siguiente piedra de un camino mínimo desde donde estás.
    Hay 3 por partida. Deshacer es ilimitado. Si te quedas en una piedra sin
    salida, la pantalla te avisa.

La misma partida para todos: el reto diario convierte la fecha en una semilla.
Para que salga igual en cualquier versión de Python, el generador de números
aleatorios está escrito aquí (no usa `random`).

Toda la lógica vive en este archivo. La página (script.js) solo dibuja y llama a
las funciones públicas, que devuelven texto JSON (salvo `semilla_del_dia`,
`racha_vigente` y `compartir_texto`).
"""
import json
from datetime import date, timedelta

LARGO = 4
MAX_AYUDAS = 3            # pistas por partida
INTENTOS = 500

# Lista propia de palabras (escrita para este juego). Sin tildes ni eñes.
_TEXTO_PALABRAS = """
aire alba alma alto ante arco arpa asno aura auto azul agua alga algo alza aula
aves ayer arar asar atar azar azor aspa asta arca anca amar alas aros arte ases
asas ajos
baba bajo baja bala bata beso bien bola bolo boca boda bota brea buey bulo buzo
base bate bazo beca beba bebe bote boga
cada caer caja cala cama cana cano capa cara caro casa caso cava cebo cena cera
cero cima cine cita clan coco coda cola coma cono copa copo coro cosa coto cruz
cubo cuna cura cabo cabe cese chal chef chip cien cojo come como cual cuco cuba
cuya cuyo cose coge caza cazo
dama dado dato debe dedo deja dejo dice dijo dime dolo dote duda dudo duna dura
duro daba dame
edad ente eras eres erre esas esos esta este esto euro
faja fama faro fase fila fino fina fiel fiar flan flor foca foco fosa foto fuga
fusa fado fajo feto fijo fija feas feos fuel
gafa gala gana gano gama gato gata gema gene gira giro goma gozo gota gris gula
gafe gasa
haba hace hada halo hado hago haga hato haya hijo hija hilo hoja hoyo hoya hora
hola hule humo heno hiel hito huso huir
idea isla iris
jara jefe jeta judo jugo juez jura juro jota joya jaca
kilo
lado lago lama lana lata lava lazo leer lema lila lima limo lino lira liso lobo
loba loca loco logo lomo lona loro losa lote luna lupa lujo luto lees lodo
mala malo mama mano mapa masa mata mate mazo mesa meta mide miel mimo mina mira
miro misa mito moda modo mono mora mota moto mozo moza mudo muda mula muro musa
mote
nabo nada nana nata nave neto nido nuca nudo nuez nulo nota nena nene
obra ocas ocre odio olas olla olor onda ojos oral orca oros orla osar osos otra
otro oval oler ocio ocho orar
paca pala palo pana papa para pase pasa pata pato pavo paso pega pelo pela pena
pera peso pesa pica pico pide piel pila pino pipa pisa piso pita plan poca poco
poda polo pomo pone pozo poza puma pura puro puso pude pudo puse pues pupa pote
rabo raja rana rama rata rato raya rayo raza real reja rema remo reno reto rica
rico rima rizo robo roca roce rojo roja ropa rosa roto rota ruta ruda rudo risa
rito roer reza rezo roza rozo
saca saco sala sale sana sano sapo sede seda seis seno seta seto sexo silo sima
sino sola solo sopa sota suba subo sube suda suma sumo supo seca seco
taco tala tapa tara taza teja tejo tela tema temo toca toda todo toga toma tomo
tono topo tope toro tren tina tino tipo tira tiro tubo tuna tuyo tuya tiza tuba
unas unos uvas urna usar
vaca vago vale vano vara vaso vela velo vena vida vino viga vive vivo viva voto
vaya veta vial
yema yate yoga yeso yugo yoyo
zona zoco zeta
"""

PALABRAS = tuple(sorted(set(_TEXTO_PALABRAS.split())))
_CONJUNTO = frozenset(PALABRAS)

# Nivel -> nombre, rango del par (pasos mínimos con la crecida ya contada) y
# cuántas piedras deja bajo el agua la crecida.
NIVELES = {
    "vado": {"nombre": "Vado", "par": (3, 4), "crecidas": 0},
    "corriente": {"nombre": "Corriente", "par": (4, 6), "crecidas": 1},
    "torrente": {"nombre": "Torrente", "par": (5, 8), "crecidas": 2},
}
NIVEL_DIARIO = "corriente"
NIVEL_PRACTICA = "corriente"

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

    def elegir(self, lista):
        """Elige un elemento de una lista no vacía."""
        return lista[int(self.siguiente() * len(lista))]


def semilla_del_dia(fecha_iso):
    """Convierte una fecha ISO ("2026-11-24") en una semilla de 32 bits (hash FNV-1a)."""
    h = 0x811C9DC5
    for b in ("pasaderas:" + str(fecha_iso)).encode("utf-8"):
        h = ((h ^ b) * 0x01000193) & _M32
    return h


# ------------------------------------------------------------ grafo de piedras

def _construir_vecinos():
    """Dos palabras son vecinas si se diferencian en exactamente una letra."""
    cubos = {}
    for p in PALABRAS:
        for i in range(LARGO):
            cubos.setdefault(p[:i] + "_" + p[i + 1:], []).append(p)
    vecinos = {p: set() for p in PALABRAS}
    for grupo in cubos.values():
        for a in grupo:
            for b in grupo:
                if a != b:
                    vecinos[a].add(b)
    return {p: sorted(v) for p, v in vecinos.items()}


VECINOS = _construir_vecinos()


def distancias(origen, prohibidas=frozenset()):
    """Búsqueda en anchura desde `origen` sin pisar `prohibidas`.
    Devuelve {palabra: pasos mínimos}."""
    dist = {origen: 0}
    cola = [origen]
    i = 0
    while i < len(cola):
        p = cola[i]
        i += 1
        for v in VECINOS[p]:
            if v not in dist and v not in prohibidas:
                dist[v] = dist[p] + 1
                cola.append(v)
    return dist


def camino_mas_corto(origen, destino, prohibidas=frozenset()):
    """Un camino mínimo [origen, ..., destino] o None si no hay. Es determinista:
    entre varios caminos mínimos devuelve siempre el mismo."""
    if origen == destino:
        return [origen]
    padre = {origen: None}
    cola = [origen]
    i = 0
    while i < len(cola):
        p = cola[i]
        i += 1
        for v in VECINOS[p]:
            if v in padre or v in prohibidas:
                continue
            padre[v] = p
            if v == destino:
                ruta = [v]
                while padre[ruta[-1]] is not None:
                    ruta.append(padre[ruta[-1]])
                return ruta[::-1]
            cola.append(v)
    return None


def _componente_principal():
    """Palabras de la mayor zona conectada: las únicas que se usan para generar."""
    visto, mejor = set(), []
    for p in PALABRAS:
        if p in visto:
            continue
        zona = sorted(distancias(p))
        visto.update(zona)
        if len(zona) > len(mejor):
            mejor = zona
    return mejor


COMPONENTE = _componente_principal()


def diferencias(a, b):
    """Cuántas letras distintas hay entre dos palabras de la misma longitud."""
    return sum(1 for x, y in zip(a, b) if x != y)


# ------------------------------------------------------------------ generación

def _en_caminos_minimos(ini, fin, prohibidas):
    """Palabras (sin contar los extremos) que están en algún camino mínimo."""
    di = distancias(ini, prohibidas)
    df = distancias(fin, prohibidas)
    if fin not in di:
        return []
    total = di[fin]
    return sorted(p for p, d in di.items() if p not in (ini, fin) and p in df and d + df[p] == total)


def _generar(semilla, nivel):
    """Crea la partida de una semilla: salida, meta, piedras bajo el agua y par.
    Se garantiza que hay solución y que el par es exacto."""
    cfg = NIVELES[nivel]
    lo, hi = cfg["par"]
    k = cfg["crecidas"]
    g = Generador(semilla)
    for _ in range(INTENTOS):
        ini = g.elegir(COMPONENTE)
        if len(VECINOS[ini]) < 2:
            continue
        di = distancias(ini)
        candidatas = sorted(p for p, d in di.items() if max(2, lo - k) <= d <= hi and len(VECINOS[p]) >= 2)
        if not candidatas:
            continue
        fin = g.elegir(candidatas)
        bloqueadas = []
        valida = True
        for _ in range(k):
            en_ruta = _en_caminos_minimos(ini, fin, set(bloqueadas))
            if not en_ruta:
                valida = False
                break
            bloqueadas.append(g.elegir(en_ruta))
            if camino_mas_corto(ini, fin, set(bloqueadas)) is None:
                valida = False
                break
        if not valida:
            continue
        par = len(camino_mas_corto(ini, fin, set(bloqueadas))) - 1
        if lo <= par <= hi:
            return {"inicio": ini, "fin": fin, "bloqueadas": sorted(bloqueadas), "par": par,
                    "nivel": nivel, "semilla": int(semilla) & _M32}
    raise RuntimeError("no se ha podido generar la partida")


# --------------------------------------------------------------------- estrellas

def estrellas(pasos, par, pistas):
    """3 estrellas con el par exacto, 2 hasta par+2 y 1 con más pasos. Las pistas
    quitan estrellas: una o dos, una; las tres, dos. Nunca menos de 1."""
    base = 3 if pasos <= par else 2 if pasos <= par + 2 else 1
    quitar = 0 if pistas == 0 else 1 if pistas <= 2 else 2
    return max(1, base - quitar)


# ---------------------------------------------------------------------- partida

_p = {}


def _normalizar(texto):
    t = str(texto).strip().lower()
    return t.translate(str.maketrans("áéíóúü", "aeiouu"))


def _prohibidas():
    return set(_p["bloqueadas"]) | set(_p["camino"][:-1])


def _estado(extra=None):
    p = _p
    camino = p["camino"]
    actual = camino[-1]
    piedras = []
    for i, w in enumerate(camino):
        cambio = -1
        if i:
            cambio = next(j for j in range(LARGO) if w[j] != camino[i - 1][j])
        piedras.append({"palabra": w, "cambio": cambio})
    jugando = p["estado"] == "jugando"
    sin_salida = False
    if jugando and actual != p["fin"]:
        sin_salida = camino_mas_corto(actual, p["fin"], _prohibidas()) is None
    est = {
        "inicio": p["inicio"], "fin": p["fin"], "bloqueadas": p["bloqueadas"],
        "par": p["par"], "nivel": p["nivel"], "nivel_nombre": NIVELES[p["nivel"]]["nombre"],
        "etiqueta": p["etiqueta"], "camino": camino, "piedras": piedras,
        "actual": actual, "pasos": len(camino) - 1,
        "en_su_sitio": [actual[j] == p["fin"][j] for j in range(LARGO)],
        "pistas": p["pistas"], "ayudas_max": MAX_AYUDAS,
        "estado": p["estado"], "sin_salida": sin_salida,
        "puede_deshacer": jugando and len(camino) > 1,
        "estrellas": estrellas(len(camino) - 1, p["par"], p["pistas"]) if p["estado"] == "completada" else 0,
        "solucion": p.get("solucion", []),
    }
    if extra:
        est.update(extra)
    return json.dumps(est, ensure_ascii=False)


def _error(texto):
    return json.dumps({"error": texto}, ensure_ascii=False)


def _poner_partida(datos, etiqueta):
    global _p
    _p = {
        "inicio": datos["inicio"], "fin": datos["fin"], "bloqueadas": list(datos["bloqueadas"]),
        "par": datos["par"], "nivel": datos["nivel"], "semilla": datos["semilla"],
        "etiqueta": str(etiqueta), "camino": [datos["inicio"]], "pistas": 0, "estado": "jugando",
    }


def nueva_partida(semilla, nivel, etiqueta=""):
    """Empieza una partida nueva. `etiqueta` es la fecha (reto diario) o 'práctica'."""
    if nivel not in NIVELES:
        nivel = NIVEL_PRACTICA
    _poner_partida(_generar(semilla, nivel), etiqueta)
    return _estado()


def _validar_paso(palabra):
    """Devuelve (palabra normalizada, None) si el paso vale, o (None, texto de error)."""
    p = _p
    w = _normalizar(palabra)
    if len(w) != LARGO or not all("a" <= c <= "z" for c in w):
        return None, "Escribe una palabra de %d letras, sin eñes." % LARGO
    actual = p["camino"][-1]
    if w == actual:
        return None, "Ya estás en esa piedra."
    if w not in _CONJUNTO:
        return None, "«%s» no está en la lista de piedras del juego." % w
    d = diferencias(w, actual)
    if d != 1:
        return None, "Hay que cambiar exactamente una letra, y «%s» cambia %d." % (w, d)
    if w in p["bloqueadas"]:
        return None, "«%s» está bajo el agua por la crecida." % w
    if w in p["camino"]:
        return None, "Esa piedra ya la has pisado."
    return w, None


def pisar(palabra):
    """Da un paso a la palabra indicada. Si no vale devuelve {"error": ...} y
    la partida no cambia."""
    if not _p or _p["estado"] != "jugando":
        return _error("La partida ya ha terminado.")
    w, error = _validar_paso(palabra)
    if error:
        return _error(error)
    _p["camino"].append(w)
    if w == _p["fin"]:
        _p["estado"] = "completada"
    return _estado()


def deshacer():
    """Vuelve a la piedra anterior (ilimitado)."""
    if not _p or _p["estado"] != "jugando" or len(_p["camino"]) < 2:
        return _error("No hay nada que deshacer.")
    _p["camino"].pop()
    return _estado()


def reiniciar():
    """Vuelve a la orilla de salida. Las pistas gastadas no se recuperan."""
    if not _p or _p["estado"] != "jugando":
        return _error("La partida ya ha terminado.")
    _p["camino"] = [_p["inicio"]]
    return _estado()


def pista():
    """Revela la siguiente piedra de un camino mínimo desde donde estás."""
    if not _p or _p["estado"] != "jugando":
        return _error("La partida ya ha terminado.")
    if _p["pistas"] >= MAX_AYUDAS:
        return _error("Ya has usado las %d pistas." % MAX_AYUDAS)
    ruta = camino_mas_corto(_p["camino"][-1], _p["fin"], _prohibidas())
    if ruta is None:
        return _error("Desde aquí no hay salida: deshaz algún paso.")
    _p["pistas"] += 1
    return _estado({"pista": ruta[1], "pasos_restantes": len(ruta) - 1})


def rendirse():
    """Enseña un camino mínimo desde la salida. La partida no cuenta como superada."""
    if not _p or _p["estado"] != "jugando":
        return _error("La partida ya ha terminado.")
    _p["solucion"] = camino_mas_corto(_p["inicio"], _p["fin"], set(_p["bloqueadas"]))
    _p["estado"] = "rendida"
    return _estado()


def restaurar(semilla, nivel, camino_json, pistas, rendida=False, etiqueta=""):
    """Reconstruye una partida guardada: vuelve a jugar cada paso comprobando que
    sea válido (se queda con los que valen) y recupera las pistas gastadas."""
    if nivel not in NIVELES:
        nivel = NIVEL_PRACTICA
    _poner_partida(_generar(semilla, nivel), etiqueta)
    try:
        pasos = json.loads(camino_json)
    except (TypeError, ValueError):
        pasos = []
    if isinstance(pasos, list) and pasos and pasos[0] == _p["inicio"]:
        for w in pasos[1:]:
            if not isinstance(w, str):
                break
            valida, error = _validar_paso(w)
            if error:
                break
            _p["camino"].append(valida)
            if valida == _p["fin"]:
                _p["estado"] = "completada"
                break
    try:
        _p["pistas"] = max(0, min(MAX_AYUDAS, int(pistas)))
    except (TypeError, ValueError):
        _p["pistas"] = 0
    if rendida and _p["estado"] == "jugando":
        return rendirse()
    return _estado()


def estado():
    """Estado actual de la partida (o error si no hay ninguna)."""
    if not _p:
        return _error("No hay partida.")
    return _estado()


def compartir_texto():
    """Texto para compartir: no enseña ninguna palabra, solo el resultado."""
    p = _p
    if not p or p["estado"] != "completada":
        return ""
    pasos = len(p["camino"]) - 1
    n = estrellas(pasos, p["par"], p["pistas"])
    est = "★" * n + "☆" * (3 - n)
    pistas = "sin pistas" if p["pistas"] == 0 else "%d %s" % (p["pistas"], "pista" if p["pistas"] == 1 else "pistas")
    nombre = NIVELES[p["nivel"]]["nombre"]
    return "Pasaderas · %s · %s\n%s %d pasos (par %d) · %s\n%s" % (
        p["etiqueta"], nombre, est, pasos, p["par"], pistas, "▪" * pasos)


# ------------------------------------------------------------------ estadísticas

def _leer_fecha(iso):
    try:
        return date.fromisoformat(str(iso))
    except ValueError:
        return None


def actualizar_estadisticas(estadisticas_json, fecha_iso, estrellas_obtenidas):
    """Suma un reto diario superado. La racha sube si el reto anterior fue ayer."""
    try:
        e = json.loads(estadisticas_json)
    except (TypeError, ValueError):
        e = {}
    if not isinstance(e, dict):
        e = {}
    hoy = _leer_fecha(fecha_iso)
    previo = _leer_fecha(e.get("ultimo"))
    if hoy is not None and previo == hoy:
        return json.dumps(e, ensure_ascii=False)
    racha = int(e.get("racha", 0))
    if hoy is not None and previo is not None and previo == hoy - timedelta(days=1):
        racha += 1
    else:
        racha = 1
    e["racha"] = racha
    e["mejor_racha"] = max(int(e.get("mejor_racha", 0)), racha)
    e["completados"] = int(e.get("completados", 0)) + 1
    if int(estrellas_obtenidas) == 3:
        e["tres_estrellas"] = int(e.get("tres_estrellas", 0)) + 1
    e["ultimo"] = str(fecha_iso)
    return json.dumps(e, ensure_ascii=False)


def racha_vigente(estadisticas_json, hoy_iso):
    """Racha que se muestra: cuenta si el último reto fue hoy o ayer; si no, 0."""
    try:
        e = json.loads(estadisticas_json)
    except (TypeError, ValueError):
        return 0
    if not isinstance(e, dict):
        return 0
    hoy, ultimo = _leer_fecha(hoy_iso), _leer_fecha(e.get("ultimo"))
    if hoy is None or ultimo is None:
        return 0
    if ultimo == hoy or ultimo == hoy - timedelta(days=1):
        return int(e.get("racha", 0))
    return 0

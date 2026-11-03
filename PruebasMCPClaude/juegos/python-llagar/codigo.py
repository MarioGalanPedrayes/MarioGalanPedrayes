"""LLAGAR: lógica de un juego incremental (idle) en Python 3, sin dependencias.

Un llagar es el lugar donde, en Asturias, se machaca la manzana para hacer
sidra. Aquí empiezas recogiendo manzanas a mano y vas montando un pomar, un
llagar y una sidrería que producen solos.

Mecánicas:
  - Recoger: cada pulsación suma manzanas.
  - Edificios: producen manzanas por segundo. Cada unidad nueva cuesta un 15 %
    más que la anterior (coste = base * 1,15 ** cantidad).
  - Mejoras: compras únicas que multiplican edificios o la recogida a mano.
  - Progreso sin conexión: al volver, se suma lo producido mientras no estabas
    (con un tope de 8 horas).
  - Nueva cosecha (prestigio): reinicia el pomar a cambio de Sellos, que dan un
    bono permanente de producción. Sellos ganados = raíz cuadrada de
    (manzanas de esta cosecha / 1.000.000).

La página (script.js) solo dibuja y llama a estas funciones públicas, que
devuelven texto JSON. El tiempo lo mide la página y se lo pasa a avanzar().
"""
import json
import math

CAP_FUERA = 8 * 3600          # máximo de segundos de progreso sin conexión
CRECIMIENTO = 1.15            # cada unidad cuesta un 15 % más
BONO_SELLO = 0.20             # +20 % de producción por Sello
BASE_PRESTIGIO = 1_000_000    # manzanas de la cosecha por cada Sello al cuadrado

# id, nombre, descripción, coste base, manzanas por segundo de cada unidad
EDIFICIOS = [
    ("manzano", "Manzano", "Da fruta sin que nadie lo toque.", 15, 0.2),
    ("cuadrilla", "Cuadrilla de recogida", "Varias manos y un cesto grande.", 100, 1),
    ("carro", "Carro con mulas", "Lleva la fruta del pomar al llagar.", 1100, 8),
    ("llagar", "Llagar de mazo", "Machaca la manzana al modo tradicional.", 12000, 47),
    ("bodega", "Bodega de toneles", "La sidra reposa y se vende sola.", 130000, 260),
    ("sidreria", "Sidrería", "Escanciar para media ciudad.", 1400000, 1400),
]
_BASE = {e[0]: e for e in EDIFICIOS}


def _generar_mejoras():
    # cada mejora: id, nombre, desc, coste, requisito, efecto
    m = [
        ("cestos", "Cestos de mimbre", "Recoger a mano rinde el doble.", 60,
         ("total", 50), ("click_x", 2)),
        ("guantes", "Guantes de faena", "Recoger a mano rinde el doble.", 800,
         ("total", 1000), ("click_x", 2)),
        ("escalera", "Escalera de tres patas",
         "Cada recogida suma además un 2 % de lo que produces por segundo.", 20000,
         ("total", 15000), ("click_prod", 0.02)),
        ("denominacion", "Denominación de origen", "Toda la producción +25 %.", 500000,
         ("total", 300000), ("global_x", 1.25)),
    ]
    for ident, nombre, _desc, base, _p in EDIFICIOS:
        m.append((ident + "_a", nombre + ": técnica mejorada",
                  "Los %s producen el doble." % nombre.lower(), base * 10,
                  ("edif", ident, 10), ("edif_x", ident, 2)))
        m.append((ident + "_b", nombre + ": maestría",
                  "Los %s producen el doble." % nombre.lower(), base * 200,
                  ("edif", ident, 25), ("edif_x", ident, 2)))
    return [dict(id=a, nombre=b, desc=c, coste=d, req=e, efecto=f)
            for a, b, c, d, e, f in m]


MEJORAS = _generar_mejoras()
_MEJORA = {m["id"]: m for m in MEJORAS}


# --------------------------------------------------------------------------
# Formato de números (castellano: coma decimal, "mil", "M", "mil M", "B")
# --------------------------------------------------------------------------
_ESCALAS = [(1e12, " B"), (1e9, " mil M"), (1e6, " M"), (1e3, " mil")]


def fmt(n):
    n = max(0.0, float(n))
    if n >= 1e15:
        return ("%.2e" % n).replace(".", ",")
    for limite, sufijo in _ESCALAS:
        if n >= limite:
            v = math.floor(n / limite * 100) / 100
            return ("%.2f" % v).rstrip("0").rstrip(".").replace(".", ",") + sufijo
    return str(int(n))


def fmt_tasa(x):
    x = max(0.0, float(x))
    if x < 10:
        return ("%.1f" % x).replace(".", ",")
    return fmt(x)


# --------------------------------------------------------------------------
# Estado y cálculos
# --------------------------------------------------------------------------
S = {}


def _vacio():
    return {
        "manzanas": 0.0,        # saldo actual
        "total_run": 0.0,       # recogidas en esta cosecha (para el prestigio)
        "total_hist": 0.0,      # recogidas en toda la partida
        "edif": {e[0]: 0 for e in EDIFICIOS},
        "mejoras": [],
        "sellos": 0,
        "cosechas": 0,
        "recogidas": 0,
        "segundos": 0.0,
    }


def _efectos(tipo):
    return [m["efecto"] for m in MEJORAS if m["id"] in S["mejoras"] and m["efecto"][0] == tipo]


def _mult_edif(ident):
    mult = 1.0
    for ef in _efectos("edif_x"):
        if ef[1] == ident:
            mult *= ef[2]
    return mult


def _mult_global():
    mult = 1.0 + BONO_SELLO * S["sellos"]
    for ef in _efectos("global_x"):
        mult *= ef[1]
    return mult


def _prod_edificio(ident):
    return S["edif"][ident] * _BASE[ident][4] * _mult_edif(ident) * _mult_global()


def _prod_s():
    return sum(_prod_edificio(e[0]) for e in EDIFICIOS)


def _click():
    base = 1.0
    for ef in _efectos("click_x"):
        base *= ef[1]
    base *= 1.0 + BONO_SELLO * S["sellos"]
    extra = sum(ef[1] for ef in _efectos("click_prod")) * _prod_s()
    return base + extra


def _coste(ident, cantidad=None):
    n = S["edif"][ident] if cantidad is None else cantidad
    return math.ceil(_BASE[ident][3] * CRECIMIENTO ** n)


def _sellos_ganables():
    return int(math.sqrt(S["total_run"] / BASE_PRESTIGIO))


def _requisito_cumplido(req):
    if req[0] == "total":
        return S["total_run"] >= req[1]
    return S["edif"][req[1]] >= req[2]


def _estado_json(error=None, fuera=None):
    mult = _mult_global()
    edificios = []
    for ident, nombre, desc, base, prod in EDIFICIOS:
        n = S["edif"][ident]
        c = _coste(ident)
        edificios.append({
            "id": ident, "nombre": nombre, "desc": desc, "cantidad": n,
            "visible": n > 0 or S["total_run"] >= base * 0.5,
            "coste": c, "coste_txt": fmt(c), "comprable": S["manzanas"] >= c,
            "unidad_txt": fmt_tasa(prod * _mult_edif(ident) * mult),
            "total_txt": fmt_tasa(_prod_edificio(ident)),
        })
    mejoras = []
    for m in MEJORAS:
        if m["id"] in S["mejoras"] or not _requisito_cumplido(m["req"]):
            continue
        mejoras.append({
            "id": m["id"], "nombre": m["nombre"], "desc": m["desc"],
            "coste": m["coste"], "coste_txt": fmt(m["coste"]),
            "comprable": S["manzanas"] >= m["coste"],
        })
    ganables = _sellos_ganables()
    datos = {
        "manzanas": int(S["manzanas"]), "manzanas_txt": fmt(S["manzanas"]),
        "prod_txt": fmt_tasa(_prod_s()), "click_txt": fmt_tasa(_click()),
        "total_run_txt": fmt(S["total_run"]), "total_hist_txt": fmt(S["total_hist"]),
        "edificios": edificios, "mejoras": mejoras,
        "sellos": S["sellos"], "cosechas": S["cosechas"], "recogidas": S["recogidas"],
        "tiempo_txt": _fmt_tiempo(S["segundos"]),
        "bono_txt": "+%d %%" % round(BONO_SELLO * S["sellos"] * 100),
        "sellos_ganables": ganables,
        "bono_tras_txt": "+%d %%" % round(BONO_SELLO * (S["sellos"] + ganables) * 100),
        "siguiente_sello_txt": fmt(BASE_PRESTIGIO * (ganables + 1) ** 2),
        "puede_prestigio": ganables >= 1,
        "fuera": fuera, "error": error,
    }
    return json.dumps(datos, ensure_ascii=False)


def _fmt_tiempo(seg):
    seg = int(seg)
    h, resto = divmod(seg, 3600)
    m, s = divmod(resto, 60)
    if h:
        return "%d h %02d min" % (h, m)
    if m:
        return "%d min %02d s" % (m, s)
    return "%d s" % s


# --------------------------------------------------------------------------
# API pública (la usa script.js)
# --------------------------------------------------------------------------
def nuevo_juego():
    S.clear()
    S.update(_vacio())
    return _estado_json()


def estado():
    return _estado_json()


def recoger():
    g = _click()
    S["manzanas"] += g
    S["total_run"] += g
    S["total_hist"] += g
    S["recogidas"] += 1
    return _estado_json()


def _sumar(segundos):
    segundos = min(max(float(segundos), 0.0), CAP_FUERA)
    g = _prod_s() * segundos
    S["manzanas"] += g
    S["total_run"] += g
    S["total_hist"] += g
    S["segundos"] += segundos
    return g


def avanzar(segundos):
    """Hace pasar el tiempo (lo llama la página unas 10 veces por segundo)."""
    _sumar(segundos)
    return _estado_json()


def avanzar_fuera(segundos):
    """Progreso mientras la página estaba cerrada (tope de 8 horas)."""
    pedido = max(float(segundos), 0.0)
    ganado = _sumar(pedido)
    fuera = {"segundos": min(pedido, CAP_FUERA), "tiempo_txt": _fmt_tiempo(min(pedido, CAP_FUERA)),
             "ganado_txt": fmt(ganado), "ganado": int(ganado), "tope": pedido > CAP_FUERA}
    return _estado_json(fuera=fuera)


def comprar(ident, cantidad=1):
    """Compra edificios. cantidad = 0 significa «todos los que pueda pagar»."""
    if ident not in _BASE:
        return _estado_json("Ese edificio no existe.")
    cantidad = int(cantidad)
    comprados = 0
    while (cantidad == 0 or comprados < cantidad) and comprados < 1000:
        c = _coste(ident)
        if S["manzanas"] < c:
            break
        S["manzanas"] -= c
        S["edif"][ident] += 1
        comprados += 1
    if comprados == 0:
        return _estado_json("No tienes manzanas suficientes.")
    return _estado_json()


def comprar_mejora(ident):
    m = _MEJORA.get(ident)
    if m is None:
        return _estado_json("Esa mejora no existe.")
    if ident in S["mejoras"]:
        return _estado_json("Ya tienes esa mejora.")
    if not _requisito_cumplido(m["req"]):
        return _estado_json("Todavía no puedes comprar esa mejora.")
    if S["manzanas"] < m["coste"]:
        return _estado_json("No tienes manzanas suficientes.")
    S["manzanas"] -= m["coste"]
    S["mejoras"].append(ident)
    return _estado_json()


def prestigio():
    """Nueva cosecha: reinicia el pomar y suma Sellos (bono permanente)."""
    ganables = _sellos_ganables()
    if ganables < 1:
        return _estado_json("Aún no has recogido las manzanas suficientes para un Sello.")
    nuevos = {**_vacio(), "sellos": S["sellos"] + ganables, "cosechas": S["cosechas"] + 1,
              "total_hist": S["total_hist"], "recogidas": S["recogidas"],
              "segundos": S["segundos"]}
    S.clear()
    S.update(nuevos)
    return _estado_json()


def exportar():
    return json.dumps(S)


def cargar(texto):
    """Restaura una partida guardada, descartando lo que no sea válido."""
    try:
        d = json.loads(texto)
        if not isinstance(d, dict):
            raise ValueError
    except (ValueError, TypeError):
        return nuevo_juego()

    def num(v, tope=1e300):
        try:
            f = float(v)
        except (ValueError, TypeError):
            return 0.0
        return f if math.isfinite(f) and 0 <= f <= tope else 0.0

    nuevo = _vacio()
    for clave in ("manzanas", "total_run", "total_hist", "segundos"):
        nuevo[clave] = num(d.get(clave))
    for clave in ("sellos", "cosechas", "recogidas"):
        nuevo[clave] = int(num(d.get(clave), 1e9))
    edif = d.get("edif") if isinstance(d.get("edif"), dict) else {}
    for ident in nuevo["edif"]:
        nuevo["edif"][ident] = int(num(edif.get(ident), 100000))
    mejoras = d.get("mejoras") if isinstance(d.get("mejoras"), list) else []
    nuevo["mejoras"] = [m for m in dict.fromkeys(mejoras) if m in _MEJORA]
    S.clear()
    S.update(nuevo)
    return _estado_json()

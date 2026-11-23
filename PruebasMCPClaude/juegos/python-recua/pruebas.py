"""Pruebas de la logica de Recua. Uso: python pruebas.py"""
import json
import time
import codigo as c


def _estado_json():
    return json.dumps(c._estado(), sort_keys=True)


def _colocar(nid, est, mask=0):
    """Pone la recua en un sitio y con unos recursos concretos (solo para pruebas)."""
    s = c.JUEGO["sim"]
    s["nid"], s["est"], s["mask"] = nid, est, mask
    if nid not in s["ruta"]:
        s["ruta"].append(nid)


def _nodo_de_tipo(tipo, nivel="normal"):
    for semilla in range(1, 200):
        c.nueva("practica", nivel, str(semilla))
        for n in c.JUEGO["partida"]["mapa"]["nodos"]:
            if n["tipo"] == tipo:
                return n
    raise AssertionError("no hay ningun sitio de tipo " + tipo)


def prueba_azar_y_semillas():
    a, b = c.Mulberry(123), c.Mulberry(123)
    xs = [a.siguiente() for _ in range(50)]
    assert xs == [b.siguiente() for _ in range(50)]
    assert all(0 <= x < 1 for x in xs)
    assert c.semilla_de_fecha("2026-11-23") == c.semilla_de_fecha("2026-11-23")
    assert c.semilla_de_fecha("2026-11-23") != c.semilla_de_fecha("2026-11-24")
    assert c.fnv1a("") == 0x811C9DC5                       # valor de referencia de FNV-1a
    assert sorted(c.Mulberry(5).barajar(range(10))) == list(range(10))


def prueba_determinismo():
    a = c.crear_partida(20261123, "normal")
    ja = json.dumps(a["mapa"], sort_keys=True), a["objetivo"]
    c._CACHE_PARTIDAS.clear()
    b = c.crear_partida(20261123, "normal")
    assert ja == (json.dumps(b["mapa"], sort_keys=True), b["objetivo"])
    otra = c.crear_partida(20261124, "normal")
    assert json.dumps(otra["mapa"], sort_keys=True) != ja[0]


def prueba_estructura_del_mapa():
    for nivel, cfg in c.NIVELES.items():
        for semilla in range(1, 25):
            p = c.crear_partida(semilla, nivel)
            nodos = p["mapa"]["nodos"]
            assert len(nodos) == 3 * cfg["etapas"] + 2
            assert nodos[0]["tipo"] == "valle" and nodos[p["mapa"]["cumbre"]]["tipo"] == "cumbre"
            for n in nodos:
                if n["tipo"] != "cumbre":
                    assert n["salidas"], "todo sitio debe tener salida"
                for s in n["salidas"]:
                    assert nodos[s]["etapa"] == n["etapa"] + 1
                    assert abs(nodos[s]["col"] - n["col"]) <= 1
            for e in range(1, cfg["etapas"] + 1):
                tipos = [n["tipo"] for n in nodos if n["etapa"] == e]
                assert len(tipos) == 3 and len(set(tipos)) == 3
            llega = {0}
            for n in nodos:                                   # los ids van por etapas
                if n["id"] in llega:
                    llega.update(n["salidas"])
            assert llega == {n["id"] for n in nodos}, "todo sitio debe ser alcanzable"
            nombres = [n["nombre"] for n in nodos]
            assert len(set(nombres)) == len(nombres)


def prueba_el_bot_gana_siempre():
    for nivel in c.NIVELES:
        for semilla in range(20261101, 20261131):
            r = c.jugar_bot(semilla, nivel)
            p = c.crear_partida(semilla, nivel)
            assert r["gana"], (nivel, semilla)
            assert r["valor"] == r["ref"] >= r["objetivo"]
            assert r["estrellas"] == 3
            assert p["intentos"] <= 5, (nivel, semilla, p["intentos"])
            assert p["objetivo"] > p["cfg"]["monedas"] + 2, "el objetivo exige comerciar"


def prueba_objetivo_no_trivial():
    """Quedarse con lo que se lleva (ir solo al sitio de al lado) no puede ganar."""
    for nivel in c.NIVELES:
        for semilla in range(1, 30):
            p = c.crear_partida(semilla, nivel)
            cfg = p["cfg"]
            assert p["objetivo"] > cfg["monedas"]
            assert p["objetivo"] <= p["opt_base"]


def prueba_acciones_invalidas_no_cambian_nada():
    c.nueva("practica", "normal", "42")
    antes = _estado_json()
    for malo in ["", "x", "o", "m", "o99", "o-1", "m999", "m-3", "o1.5", None, 7, "zz1", "m0"]:
        e = json.loads(c.accion(malo))
        assert e["error"], malo
        assert e["acciones"] == [] and e["recursos"]["pan"] == c.JUEGO["ctx"]["ini"][0]
    c.JUEGO["pista"] = None
    assert _estado_json().replace('"error": ""', "") == antes.replace('"error": ""', "")


def prueba_ofertas_y_limites():
    c.nueva("practica", "normal", "42")
    ini = c.JUEGO["ctx"]["ini"]
    nodo = c.JUEGO["partida"]["mapa"]["nodos"][0]
    # las ofertas ordenadas (sacos, panes) se compran en orden y no se repiten
    primera_carga = next(o["k"] for o in nodo["ofertas"] if o["tipo"] == "carga")
    e = json.loads(c.accion(f"o{primera_carga + 1}"))
    assert e["error"], "no se puede saltar el orden"
    e = json.loads(c.accion(f"o{primera_carga}"))
    assert not e["error"] and e["recursos"]["carga"] == 1 and e["recursos"]["monedas"] == ini[2] - 2
    e = json.loads(c.accion(f"o{primera_carga}"))
    assert e["error"], "no se repite la misma oferta"
    # el limite de las alforjas
    for _ in range(10):
        e = json.loads(c.accion(f"o{primera_carga + e['recursos']['carga']}"))
    assert e["recursos"]["carga"] <= e["recursos"]["capacidad"]
    assert e["recursos"]["monedas"] >= 0


def prueba_paso_dificil_es_obligatorio():
    n = _nodo_de_tipo("paso")
    j = c.JUEGO
    _colocar(n["id"], (5, 8, 5, 0))
    e = json.loads(c.accion(f"m{n['salidas'][0]}"))
    assert "decidir" in e["error"] and e["actual"] == n["id"]
    assert all(not d["legal"] for d in e["destinos"])
    cruzar = next(o for o in n["ofertas"] if o["tipo"] == "cruzar")
    rodear = next(o for o in n["ofertas"] if o["tipo"] == "rodear")
    e = json.loads(c.accion(f"o{cruzar['k']}"))
    assert e["recursos"]["animo"] == 8 + cruzar["ef"][1]
    e = json.loads(c.accion(f"o{rodear['k']}"))
    assert e["error"], "cruzar y rodear son excluyentes"
    e = json.loads(c.accion(f"m{n['salidas'][0]}"))
    assert not e["error"] and e["actual"] == n["salidas"][0]
    # sin animo para cruzar y sin panes para rodear, no se puede decidir: viaje perdido
    _colocar(n["id"], (0, 1, 5, 0), 0)
    j["sim"]["resultado"], j["sim"]["motivo"] = "jugando", ""
    assert not c._hay_jugada(j["sim"], j["partida"], j["ctx"])


def prueba_hambre():
    c.nueva("practica", "normal", "42")
    j = c.JUEGO
    sig = j["partida"]["mapa"]["nodos"][0]["salidas"][0]
    _colocar(0, (0, 6, 3, 0))
    e = json.loads(c.accion(f"m{sig}"))
    assert e["recursos"]["animo"] == 4 and e["recursos"]["pan"] == 0 and "hambre" in e["mensaje"]
    c.nueva("practica", "normal", "42")
    _colocar(0, (0, 2, 3, 0))
    e = json.loads(c.accion(f"m{sig}"))
    assert e["error"] and e["actual"] == 0, "con 2 de animo no aguanta otro tramo sin pan"


def prueba_encuentros_ocultos_y_deterministas():
    n = _nodo_de_tipo("encuentro")
    j = c.JUEGO
    k = n["ofertas"][0]["k"]
    res = []
    for _ in range(3):
        c.nueva("practica", "normal", j["semilla"])
        _colocar(n["id"], (5, 6, 9, 2))
        e = json.loads(c.accion(f"o{k}"))
        res.append((e["recursos"], e["mensaje"]))
    assert res[0] == res[1] == res[2]
    c.nueva("practica", "normal", j["semilla"])
    texto = c.nueva("practica", "normal", j["semilla"])
    assert '"oculto"' not in texto and '"res"' not in texto and "adivina" not in texto
    c.nueva("practica", "normal", j["semilla"], json.dumps({"mapa": 1}))
    assert "adivina" in json.dumps(c._estado())


def prueba_reconstruir_es_igual_que_jugar():
    for nivel in c.NIVELES:
        c.nueva("practica", nivel, "777")
        j = c.JUEGO
        for _ in range(6):
            a = j["sol"].mejor_accion(j["sim"]["nid"], j["sim"]["est"], j["sim"]["mask"])
            c.accion(a)
        c.pista()
        vivo = json.loads(c.pista())
        rec = json.loads(c.reconstruir("practica", nivel, "777", json.dumps(vivo["acciones"]), vivo["pistas"]))
        vivo["pista"] = rec["pista"] = None
        assert vivo == rec
        # una lista de acciones con basura se corta en la primera mala
        rec2 = json.loads(c.reconstruir("practica", nivel, "777", json.dumps(vivo["acciones"][:2] + ["m999", "o0"]), 0))
        assert rec2["acciones"] == vivo["acciones"][:2]


def prueba_pistas():
    c.nueva("practica", "normal", "99")
    j = c.JUEGO
    esperada = j["sol"].mejor_accion(0, j["sim"]["est"], 0)
    e = json.loads(c.pista())
    assert e["pista"] == esperada and e["pistas"] == 1
    c.pista(), c.pista()
    e = json.loads(c.pista())
    assert e["pistas"] == 3 and "tres pistas" in e["error"]
    e = json.loads(c.accion(esperada))
    assert e["pista"] is None
    # seguir siempre al solucionador (sin gastar pistas) da el mejor valor y 3 estrellas
    r = c.jugar_bot(99, "normal")
    assert r["gana"] and r["estrellas"] == 3


def prueba_estrellas():
    assert c._estrellas(40, 40, 7, 0) == 3
    assert c._estrellas(40, 40, 7, 1) == 2
    assert c._estrellas(31, 40, 7, 0) == 2      # 24 de 33 de ganancia: 73 %
    assert c._estrellas(30, 40, 7, 0) == 1      # 23 de 33: 69,7 %, no llega al 70 %
    assert c._estrellas(20, 40, 7, 0) == 1


def prueba_mejoras():
    for nivel in c.NIVELES:
        base = c.jugar_bot(11, nivel)
        todas = {k: len(m["costes"]) for k, m in c.MEJORAS.items()}
        con = c.jugar_bot(11, nivel, todas)
        assert con["gana"] and con["ref"] >= base["ref"]
    c.nueva("practica", "normal", "11", json.dumps({"alforjas": 2, "mulas": 1, "zurron": 99, "bolsa": -3, "x": 1}))
    ctx = c.JUEGO["ctx"]
    assert ctx["cap"] == 6 and ctx["animo_max"] == 12
    assert c.JUEGO["mejoras"] == {"alforjas": 2, "mulas": 1, "zurron": 2}
    assert ctx["ini"] == (9, 10, 7, 0)
    # el reto diario nunca usa mejoras
    e = json.loads(c.nueva("diario", "normal", "2026-11-23", json.dumps({"alforjas": 2})))
    assert e["mejoras"] == {} and e["recursos"]["capacidad"] == 4


def prueba_comprar_mejoras():
    r = json.loads(c.comprar_mejora("{}", "alforjas", 2))
    assert not r["ok"] and "Te faltan 1" in r["error"] and r["sellos"] == 2
    r = json.loads(c.comprar_mejora("{}", "alforjas", 5))
    assert r["ok"] and r["mejoras"] == {"alforjas": 1} and r["sellos"] == 2
    r = json.loads(c.comprar_mejora(json.dumps(r["mejoras"]), "alforjas", 10))
    assert r["ok"] and r["sellos"] == 5 and r["mejoras"] == {"alforjas": 2}
    r = json.loads(c.comprar_mejora(json.dumps(r["mejoras"]), "alforjas", 99))
    assert not r["ok"] and "máximo" in r["error"]
    assert not json.loads(c.comprar_mejora("{}", "inventada", 99))["ok"]
    cat = json.loads(c.catalogo_mejoras('{"bolsa": 2}'))
    bolsa = next(m for m in cat if m["clave"] == "bolsa")
    assert bolsa["nivel"] == 2 and bolsa["coste"] == 4
    assert json.loads(c.comprar_mejora("not json".replace("not json", "{}"), "mapa", 8))["ok"]


def prueba_sellos_y_resultado():
    c.jugar_bot(5, "normal")
    e = c._estado()
    assert e["resultado"] == "ganada" and e["sellos"] == 1 + e["estrellas"]
    c.nueva("diario", "normal", "2026-11-23")
    j = c.JUEGO
    while j["sim"]["resultado"] == "jugando":
        c.accion(j["sol"].mejor_accion(j["sim"]["nid"], j["sim"]["est"], j["sim"]["mask"]))
    assert c._estado()["sellos"] == 2 + 3
    # llegar a la Cumbre sin el objetivo es perder
    c.nueva("practica", "normal", "5")
    j = c.JUEGO
    nodos = j["partida"]["mapa"]["nodos"]
    cumbre = j["partida"]["mapa"]["cumbre"]
    ultimo = next(n for n in nodos if cumbre in n["salidas"])
    _colocar(ultimo["id"], (3, 8, 1, 0))
    e = json.loads(c.accion(f"m{cumbre}"))
    assert e["resultado"] == "perdida" and "objetivo" in e["motivo"]
    e = json.loads(c.accion("o0"))
    assert e["error"], "no se juega con el viaje terminado"


def prueba_compartir_no_desvela():
    c.jugar_bot(5, "normal")
    t = c.compartir()
    assert t.startswith("RECUA · Collada") and "★★★" in t and "🏔️" in t and "🌄" in t
    n = _nodo_de_tipo("encuentro")
    _colocar(n["id"], (5, 6, 9, 2))
    c.accion(f"o{n['ofertas'][0]['k']}")
    t = c.compartir()
    for palabra in ("timo", "bueno", "hierbas", "remedio", "forastero", "curandera", "mercader"):
        assert palabra not in t.lower()


def prueba_racha():
    f = json.dumps(["2026-11-20", "2026-11-21", "2026-11-22", "2026-11-18"])
    assert json.loads(c.racha(f, "2026-11-23")) == {"actual": 3, "mejor": 3, "total": 4}
    assert json.loads(c.racha(f, "2026-11-25"))["actual"] == 0
    assert json.loads(c.racha("[]", "2026-11-23")) == {"actual": 0, "mejor": 0, "total": 0}


def prueba_tiempos():
    t = time.time()
    c._CACHE_PARTIDAS.clear()
    for s in range(30):
        c.crear_partida(s, "dificil")
    assert time.time() - t < 30, "generar mapas no debe ser lento"


if __name__ == "__main__":
    n = 0
    for nombre, f in sorted(globals().items()):
        if nombre.startswith("prueba_") and callable(f):
            f()
            n += 1
            print("ok", nombre)
    print(f"{n} pruebas correctas")

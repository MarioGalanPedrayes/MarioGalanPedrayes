"""Pruebas de la logica de Corrada. Uso: python pruebas.py"""
import json
import codigo as c


def prueba_determinismo():
    a = c.crear_partida(20261115, "normal")
    c._CACHE_PARTIDAS.clear()
    b = c.crear_partida(20261115, "normal")
    assert a["piedras0"] == b["piedras0"] and a["solucion"] == b["solucion"]
    assert c.semilla_de_fecha("2026-11-15") == c.semilla_de_fecha("2026-11-15")
    assert c.semilla_de_fecha("2026-11-15") != c.semilla_de_fecha("2026-11-16")


def prueba_geometria():
    vec, borde = c.geometria(11, 11)
    for i, vs in enumerate(vec):
        assert len(vs) <= 6 and i not in vs
        for j in vs:
            assert i in vec[j], "los vecinos deben ser simetricos"
    assert len(vec[5 * 11 + 5]) == 6
    assert len(borde) == 4 * 11 - 4


def prueba_bot_gana_siempre():
    for nivel in c.NIVELES:
        for s in range(20261101, 20261113):
            p = c.crear_partida(s, nivel)
            e = c.simular(p["cfg"], p["piedras0"], p["ternero0"], p["semilla"], p["solucion"])
            assert e["resultado"] == "ganada", (nivel, s)
            assert len(p["solucion"]) <= p["cfg"]["presupuesto"]
            libre = e["libre"]
            vec, borde = c.geometria(p["cfg"]["filas"], p["cfg"]["cols"])
            assert c.distancias(libre, vec, borde)[e["ternero"]] == -1


def prueba_casos_limite():
    p = c.crear_partida(7, "facil")
    cfg, p0, t0, s = p["cfg"], p["piedras0"], p["ternero0"], p["semilla"]
    e = c.simular(cfg, p0, t0, s, [t0, p0[0], -3, 10 ** 6, "x"])   # todo invalido
    assert e["turno"] == 0 and e["rechazadas"] == 5
    # sin hacer nada util el ternero acaba escapando o se agota el presupuesto
    libres = [i for i in range(81) if i not in p0 and i != t0]
    e = c.simular(cfg, p0, t0, s, libres[-cfg["presupuesto"]:])
    assert e["resultado"] in ("perdida", "ganada")
    # despues del final se ignoran las acciones
    e2 = c.simular(cfg, p0, t0, s, p["solucion"] + p["solucion"])
    assert e2["resultado"] == "ganada" and e2["turno"] == len(p["solucion"])


def prueba_interfaz():
    est = json.loads(c.nueva("practica", "normal", "12345"))
    assert est["resultado"] == "jugando" and est["usadas"] == 0 and est["ref"] > 0
    assert json.loads(c.colocar(est["ternero"]))["error"]          # sobre el ternero
    est = json.loads(c.pista())
    assert est["pista"] is not None and est["pistas"] == 1
    est = json.loads(c.colocar(est["pista"]))
    assert est["usadas"] == 1
    est = json.loads(c.deshacer())
    assert est["usadas"] == 0
    for _ in range(5):
        est = json.loads(c.pista())
    assert est["error"] and est["pistas"] == 3
    est = json.loads(c.reconstruir("practica", "normal", "12345", json.dumps([]), 0))
    for casilla in c.crear_partida(12345, "normal")["solucion"]:
        est = json.loads(c.colocar(casilla))
    assert est["resultado"] == "ganada" and 1 <= est["estrellas"] <= 3
    assert "CORRADA" in c.compartir()
    est2 = json.loads(c.reconstruir("practica", "normal", "12345", json.dumps(est["acciones"]), 0))
    assert est2["resultado"] == "ganada"


def prueba_racha():
    r = json.loads(c.racha(json.dumps(["2026-11-12", "2026-11-13", "2026-11-14", "2026-11-01"]), "2026-11-15"))
    assert r["actual"] == 3 and r["mejor"] == 3 and r["total"] == 4
    r = json.loads(c.racha(json.dumps(["2026-11-10"]), "2026-11-15"))
    assert r["actual"] == 0 and r["mejor"] == 1
    r = json.loads(c.racha(json.dumps([]), "2026-11-15"))
    assert r["actual"] == 0 and r["mejor"] == 0


if __name__ == "__main__":
    for nombre, f in list(globals().items()):
        if nombre.startswith("prueba_"):
            f()
            print("ok", nombre)

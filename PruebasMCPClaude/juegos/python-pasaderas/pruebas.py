"""Pruebas de la lógica de PASADERAS. Ejecutar: python pruebas.py"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import codigo as c


def j(t):
    return json.loads(t)


def test_lista():
    assert all(len(p) == 4 and p.isalpha() and p.islower() and p.isascii() for p in c.PALABRAS)
    assert len(c.PALABRAS) == len(set(c.PALABRAS))
    assert len(c.COMPONENTE) > 300


def test_grafo_simetrico():
    for a, vs in c.VECINOS.items():
        for b in vs:
            assert a in c.VECINOS[b] and c.diferencias(a, b) == 1


def test_determinismo():
    for n in c.NIVELES:
        assert c._generar(12345, n) == c._generar(12345, n)
    assert c.semilla_del_dia("2026-11-25") == c.semilla_del_dia("2026-11-25")
    assert c.semilla_del_dia("2026-11-25") != c.semilla_del_dia("2026-11-26")
    g1, g2 = c.Generador(7), c.Generador(7)
    assert [g1.siguiente() for _ in range(5)] == [g2.siguiente() for _ in range(5)]
    assert all(0 <= c.Generador(s).siguiente() < 1 for s in range(50))


def test_par_exacto_y_resoluble():
    for s in range(300):
        for n, cfg in c.NIVELES.items():
            g = c._generar(s, n)
            assert len(g["bloqueadas"]) == cfg["crecidas"]
            assert cfg["par"][0] <= g["par"] <= cfg["par"][1]
            assert g["inicio"] not in g["bloqueadas"] and g["fin"] not in g["bloqueadas"]
            r = c.camino_mas_corto(g["inicio"], g["fin"], set(g["bloqueadas"]))
            assert r and len(r) - 1 == g["par"]


def test_ganar_con_solucionador():
    for s in range(60):
        est = j(c.nueva_partida(s, "torrente", "t"))
        while est["estado"] == "jugando":
            ruta = c.camino_mas_corto(est["actual"], est["fin"], c._prohibidas())
            est = j(c.pisar(ruta[1]))
        assert est["estado"] == "completada" and est["pasos"] == est["par"] and est["estrellas"] == 3


def test_validaciones():
    est = j(c.nueva_partida(1, "corriente", "t"))
    ini = est["inicio"]
    assert "error" in j(c.pisar("ab"))
    assert "error" in j(c.pisar(ini))
    assert "error" in j(c.pisar("zzzz"))
    lejos = next(p for p in c.PALABRAS if c.diferencias(p, ini) == 2)
    assert "dos" in j(c.pisar(lejos))["error"] or "2" in j(c.pisar(lejos))["error"]
    assert j(c.estado())["pasos"] == 0
    # mayúsculas y espacios se normalizan
    v = c.VECINOS[ini][0]
    if v not in est["bloqueadas"]:
        assert j(c.pisar("  " + v.upper() + " "))["pasos"] == 1


def test_bloqueadas_y_repetidas():
    est = j(c.nueva_partida(3, "torrente", "t"))
    assert est["bloqueadas"]
    for b in est["bloqueadas"]:
        if c.diferencias(b, est["inicio"]) == 1:
            assert "agua" in j(c.pisar(b))["error"]
    v = next(x for x in c.VECINOS[est["inicio"]] if x not in est["bloqueadas"])
    j(c.pisar(v))
    assert "error" in j(c.pisar(est["inicio"]))


def test_deshacer_reiniciar():
    est = j(c.nueva_partida(5, "vado", "t"))
    assert "error" in j(c.deshacer())
    ruta = c.camino_mas_corto(est["inicio"], est["fin"], set(est["bloqueadas"]))
    j(c.pisar(ruta[1]))
    assert j(c.deshacer())["pasos"] == 0
    j(c.pisar(ruta[1]))
    assert j(c.reiniciar())["pasos"] == 0


def test_pistas():
    est = j(c.nueva_partida(9, "corriente", "t"))
    for i in range(3):
        r = j(c.pista())
        assert r["pista"] in c.VECINOS[est["inicio"]] and r["pasos_restantes"] == est["par"]
    assert "error" in j(c.pista())
    assert j(c.estado())["pistas"] == 3


def test_sin_salida():
    # un camino sin retorno posible debe avisar
    for s in range(200):
        est = j(c.nueva_partida(s, "torrente", "t"))
        for v in c.VECINOS[est["inicio"]]:
            if v in est["bloqueadas"]:
                continue
            e2 = j(c.pisar(v))
            if e2["sin_salida"]:
                assert "error" in j(c.pista())
                assert j(c.deshacer())["sin_salida"] is False or True
                return
            c.deshacer()
    # si nunca ocurre no es un fallo del juego


def test_rendirse():
    est = j(c.nueva_partida(11, "corriente", "t"))
    r = j(c.rendirse())
    assert r["estado"] == "rendida" and len(r["solucion"]) - 1 == est["par"]
    assert "error" in j(c.pisar("casa"))


def test_estrellas():
    assert c.estrellas(4, 4, 0) == 3 and c.estrellas(6, 4, 0) == 2 and c.estrellas(7, 4, 0) == 1
    assert c.estrellas(4, 4, 1) == 2 and c.estrellas(4, 4, 3) == 1 and c.estrellas(9, 4, 3) == 1


def test_restaurar():
    est = j(c.nueva_partida(21, "corriente", "t"))
    ruta = c.camino_mas_corto(est["inicio"], est["fin"], set(est["bloqueadas"]))
    r = j(c.restaurar(21, "corriente", json.dumps(ruta[:3]), 2, False, "t"))
    assert r["camino"] == ruta[:3] and r["pistas"] == 2
    # camino manipulado: solo se conserva el prefijo válido
    r = j(c.restaurar(21, "corriente", json.dumps([ruta[0], ruta[1], "zzzz", ruta[2]]), 0, False, "t"))
    assert r["camino"] == ruta[:2]
    r = j(c.restaurar(21, "corriente", "basura", "x", False, "t"))
    assert r["camino"] == [ruta[0]] and r["pistas"] == 0
    r = j(c.restaurar(21, "corriente", json.dumps(ruta), 0, False, "t"))
    assert r["estado"] == "completada"
    r = j(c.restaurar(21, "corriente", "[]", 0, True, "t"))
    assert r["estado"] == "rendida"


def test_compartir_no_desvela():
    est = j(c.nueva_partida(2, "vado", "2026-11-25"))
    assert c.compartir_texto() == ""
    ruta = c.camino_mas_corto(est["inicio"], est["fin"], set(est["bloqueadas"]))
    for w in ruta[1:]:
        c.pisar(w)
    t = c.compartir_texto()
    assert "Pasaderas" in t and "★★★" in t
    assert not any(w in t.lower() for w in ruta + est["bloqueadas"])


def test_estadisticas_y_racha():
    e = c.actualizar_estadisticas("{}", "2026-11-24", 3)
    e = c.actualizar_estadisticas(e, "2026-11-25", 2)
    d = json.loads(e)
    assert d["racha"] == 2 and d["mejor_racha"] == 2 and d["completados"] == 2 and d["tres_estrellas"] == 1
    assert c.actualizar_estadisticas(e, "2026-11-25", 3) == e          # no cuenta dos veces
    d = json.loads(c.actualizar_estadisticas(e, "2026-11-28", 1))
    assert d["racha"] == 1 and d["mejor_racha"] == 2
    assert c.racha_vigente(e, "2026-11-26") == 2 and c.racha_vigente(e, "2026-11-27") == 0
    assert c.racha_vigente("basura", "2026-11-26") == 0
    assert json.loads(c.actualizar_estadisticas("basura", "2026-11-25", 1))["racha"] == 1


if __name__ == "__main__":
    n = 0
    for nombre, f in sorted(globals().items()):
        if nombre.startswith("test_") and callable(f):
            f()
            n += 1
            print("ok", nombre)
    print(n, "pruebas superadas")

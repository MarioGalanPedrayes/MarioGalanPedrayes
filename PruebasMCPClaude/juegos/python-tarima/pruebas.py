"""Pruebas de la lógica de TARIMA. Se ejecutan con:  python pruebas.py"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import codigo as c  # noqa: E402

fallos = []


def comprobar(condicion, texto):
    if not condicion:
        fallos.append(texto)
        print("FALLO:", texto)


def estado(texto_json):
    return json.loads(texto_json)


# ---- catálogo de piezas
formas = [tuple(map(tuple, p["celdas"])) for p in c.PIEZAS.values()]
comprobar(len(formas) == len(set(formas)), "hay piezas repetidas en el catálogo")
for ident, p in c.PIEZAS.items():
    comprobar(min(f for f, _ in p["celdas"]) == 0 and min(cc for _, cc in p["celdas"]) == 0,
              "pieza %d no está normalizada" % ident)
    comprobar(len(c._POS[ident]) == (c.N - p["alto"] + 1) * (c.N - p["ancho"] + 1),
              "posiciones de la pieza %d" % ident)
comprobar(len(c.PIEZAS) == 37, "el catálogo debe tener 37 piezas (hay %d)" % len(c.PIEZAS))

# ---- semilla y generador deterministas
comprobar(c.semilla_del_dia("2026-11-20") == c.semilla_del_dia("2026-11-20"), "semilla del día no determinista")
comprobar(c.semilla_del_dia("2026-11-20") != c.semilla_del_dia("2026-11-21"), "dos días con la misma semilla")
g1, g2 = c.Generador(123), c.Generador(123)
comprobar([g1.siguiente() for _ in range(5)] == [g2.siguiente() for _ in range(5)], "generador no determinista")
comprobar(all(0 <= c.Generador(s).siguiente() < 1 for s in range(200)), "generador fuera de [0, 1)")
comprobar("import random" not in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "codigo.py"),
                                      encoding="utf-8").read(), "no debe usar el módulo random")
comprobar([c._lote(77, j) for j in range(6)] == [c._lote(77, j) for j in range(6)], "lotes no deterministas")
comprobar(c._id_pieza(77, 4) == c._lote(77, 1)[1], "la pieza k no coincide con su lote")

# ---- despeje de líneas (con el motor de bits)
b = t = 0
for col in range(7):  # fila 3 casi llena
    b |= 1 << (3 * 8 + col)
    t |= 1 << (col * 8 + 3)
m, tm = c._POSD[1][(3, 7)]  # pieza 1 = punto
nb, nt, filas, cols, _ = c._poner_y_despejar(b, t, m, tm)
comprobar(filas == [3] and cols == [] and nb == 0 and nt == 0, "una fila completa debe despejarse")
b = t = 0
for f in range(7):  # columna 5 casi llena
    b |= 1 << (f * 8 + 5)
    t |= 1 << (5 * 8 + f)
m, tm = c._POSD[1][(7, 5)]
nb, nt, filas, cols, _ = c._poner_y_despejar(b, t, m, tm)
comprobar(cols == [5] and filas == [] and nb == 0 and nt == 0, "una columna completa debe despejarse")
b = t = 0  # cruz: fila 2 y columna 2 llenas salvo el cruce
for k in range(8):
    if k != 2:
        b |= (1 << (2 * 8 + k)) | (1 << (k * 8 + 2))
        t |= (1 << (k * 8 + 2)) | (1 << (2 * 8 + k))
m, tm = c._POSD[1][(2, 2)]
nb, nt, filas, cols, despejadas = c._poner_y_despejar(b, t, m, tm)
comprobar(filas == [2] and cols == [2] and nb == 0 and nt == 0, "fila y columna a la vez")
comprobar(bin(despejadas).count("1") == 15, "la cruz despeja 15 casillas")
# el suelo y el traspuesto deben decir siempre lo mismo
for s in range(20):
    est = c._nuevo_estado(900 + s, c.NIVELES["normal"])
    ok = all(((est["b"] >> (f * 8 + col)) & 1) == ((est["t"] >> (col * 8 + f)) & 1)
             for f in range(8) for col in range(8))
    comprobar(ok, "suelo y traspuesto no coinciden (semilla %d)" % (900 + s))

# ---- nudos de partida
for nivel, cfg in c.NIVELES.items():
    for s in range(40):
        est = c._nuevo_estado(5000 + s, cfg)
        comprobar(bin(est["b"]).count("1") == cfg["nudos"], "número de nudos en %s" % nivel)
        _, _, fl, cl, _ = c._poner_y_despejar(est["b"], est["t"], 0, 0)
        comprobar(not fl and not cl, "la partida no puede empezar con una línea completa")

# ---- partida: colocación, errores y deshacer
e0 = estado(c.nueva_partida(20261120, "practica", "prueba", "normal"))
comprobar(e0["estado"] == "jugando" and e0["lote"] == 1 and e0["lineas"] == 0, "estado inicial")
comprobar(len(e0["bandeja"]) == 3 and all(not p["usada"] for p in e0["bandeja"]), "el lote tiene 3 piezas")
comprobar(len(e0["siguiente"]) == 3, "se ve el lote siguiente")
comprobar(estado(c.colocar(0, -1, 0))["error"], "posición fuera del suelo")
comprobar(estado(c.colocar(0, 0, 8))["error"], "columna fuera del suelo")
comprobar(estado(c.colocar(5, 0, 0))["error"], "pieza inexistente")
ocupada = next(i for i, v in enumerate(e0["tab"]) if v == c.NUDO)
p0 = e0["bandeja"][0]
fo, co = divmod(ocupada, 8)
solape = estado(c.colocar(0, fo - p0["celdas"][0][0], co - p0["celdas"][0][1]))
comprobar(solape["error"] or solape["tab"] != e0["tab"], "no se puede pisar un nudo")
if not solape["error"]:  # la pieza no llegó a pisarlo (se salía): no debe haber cambiado nada
    comprobar(solape["historial"] == [], "no se debe registrar una jugada pisando")
e0 = estado(c.nueva_partida(20261120, "practica", "prueba", "normal"))
pos = next((f, col) for f, col, m, _ in c._POS[c._lote(e0 and c._p["efectiva"], 0)[0]] if not (c._p["est"]["b"] & m))
e1 = estado(c.colocar(0, *pos))
comprobar(not e1["error"] and e1["bandeja"][0]["usada"], "colocar una pieza libre")
comprobar(estado(c.colocar(0, *pos))["error"], "no se puede colocar dos veces la misma pieza")
e2 = estado(c.deshacer())
comprobar(e2["tab"] == e0["tab"] and e2["historial"] == [] and not e2["bandeja"][0]["usada"], "deshacer restaura")
comprobar(estado(c.deshacer())["error"], "deshacer sin jugadas")
vp = json.loads(c.vista_previa(0, *pos))
comprobar(vp["valida"] and len(vp["celdas"]) == len(e0["bandeja"][0]["celdas"]), "vista previa válida")
comprobar(not json.loads(c.vista_previa(0, 7, 7))["valida"] or e0["bandeja"][0]["celdas"] == [[0, 0]],
          "vista previa fuera del suelo")

# ---- el jugador automático gana siempre, con las reglas reales
# Se repite su secuencia a través de la API pública y se comprueba el resultado.
resumen = {}
for nivel, cfg in c.NIVELES.items():
    ganadas = 0
    tres = 0
    total = 24
    for k in range(total):
        semilla = 20261100 + 31 * k
        efectiva, ref, obj = c._generar(semilla, nivel)
        comprobar(ref >= obj >= 3, "objetivo por encima de la referencia (%s, %d)" % (nivel, semilla))
        est0 = c._nuevo_estado(efectiva, cfg)
        lotes = [c._lote(efectiva, j) for j in range(cfg["lotes"])]
        _lin, secuencia = c._plan_bot(est0["b"], est0["t"], 0, 0, lotes, c.ANCHO_BUSQUEDA)
        e = estado(c.nueva_partida(semilla, "practica", "bot", nivel))
        comprobar(e["referencia"] == ref and e["objetivo"] == obj, "referencia y objetivo coinciden")
        for slot, f, col in secuencia:
            e = estado(c.colocar(slot, f, col))
            comprobar(not e["error"], "la secuencia del bot es válida (%s, %d): %s" % (nivel, semilla, e["error"]))
            if e["error"]:
                break
        if e["estado"] == "completada":
            ganadas += 1
        if e["estrellas"] == 3:
            tres += 1
        comprobar(e["lineas"] == ref, "las líneas de la partida son las de la referencia (%s, %d)" % (nivel, semilla))
    comprobar(ganadas == total, "el bot debe ganar siempre en %s (%d/%d)" % (nivel, ganadas, total))
    comprobar(tres == total, "el bot debe sacar tres estrellas en %s" % nivel)
    resumen[nivel] = (ganadas, total)

# ---- restaurar repitiendo las jugadas
c.nueva_partida(777, "practica", "x", "normal")
for _ in range(6):
    e = estado(c.pista())
    h = e["pista"]
    if not h:
        break
    c.colocar(h["slot"], h["fila"], h["col"])
guardado = estado(c._estado_json())
r = estado(c.restaurar(777, "practica", "x", "normal", json.dumps(guardado["historial"]), guardado["pistas"]))
comprobar(r["tab"] == guardado["tab"] and r["lineas"] == guardado["lineas"] and r["pistas"] == guardado["pistas"],
          "restaurar debe dejar la misma partida")
comprobar(estado(c.restaurar(777, "practica", "x", "normal", "esto no es json", 0))["estado"] == "jugando",
          "restaurar con basura no debe romper")
comprobar(estado(c.restaurar(777, "practica", "x", "normal", json.dumps([[9, 9, 9], [0, 0]]), 99))["pistas"] == c.PISTAS_MAX,
          "pistas restauradas limitadas")

# ---- pistas
c.nueva_partida(4242, "practica", "x", "normal")
for _ in range(c.PISTAS_MAX):
    comprobar(estado(c.pista())["pista"] is not None, "pista disponible")
comprobar(estado(c.pista())["error"], "sin pistas al gastar las tres")

# ---- estrellas
comprobar(c.estrellas(4, 10, 7) == 0, "por debajo del objetivo: 0 estrellas")
comprobar(c.estrellas(7, 10, 7) == 1, "objetivo cumplido: 1 estrella")
comprobar(c.estrellas(9, 10, 7) == 2, "85 % de la referencia: 2 estrellas")
comprobar(c.estrellas(10, 10, 7) == 3 and c.estrellas(12, 10, 7) == 3, "referencia: 3 estrellas")
comprobar(c.estrellas(10, 10, 7, pistas=1) == 2, "con pistas el máximo es 2 estrellas")

# ---- final de partida: sin sitio y fin de lotes
c.nueva_partida(31337, "practica", "x", "dificil")
est = c._p["est"]
est["b"] = c._TODO & ~1  # solo queda libre la casilla (0, 0)
est["t"] = c._TODO & ~1
ids = c._lote(c._p["efectiva"], 0)
algo_cabe = any(c._cabe(est["b"], x) for x in ids)
fin = c._terminada(est, c._p["efectiva"], c._p["cfg"])
comprobar(fin == (None if algo_cabe else "sin_sitio"), "detección de «sin sitio»")
est2 = c._nuevo_estado(1, c.NIVELES["facil"])
est2["lote"] = c.NIVELES["facil"]["lotes"]
comprobar(c._terminada(est2, 1, c.NIVELES["facil"]) == "lotes", "fin por lotes")

# ---- compartir sin spoilers
c.nueva_partida(20261120, "diario", "2026-11-20 · reto diario", "normal")
comprobar(c.compartir_texto() == "", "no se comparte una partida sin terminar")
c._p["est"]["lote"] = c._p["cfg"]["lotes"]
c._p["est"]["lineas"] = c._p["referencia"]
texto = c.compartir_texto()
comprobar(texto.startswith("TARIMA") and "★★★" in texto, "texto para compartir")
comprobar(len(texto.splitlines()) >= 11, "el texto para compartir incluye el suelo")
comprobar("pieza" not in texto.lower(), "el texto no revela las piezas")

# ---- estadísticas y racha
e = {}
e = json.loads(c.actualizar_estadisticas(json.dumps(e), "2026-11-18", 8, 3))
e = json.loads(c.actualizar_estadisticas(json.dumps(e), "2026-11-19", 7, 2))
comprobar(e["racha"] == 2 and e["completados"] == 2 and e["tres_estrellas"] == 1, "racha de dos días")
e2 = json.loads(c.actualizar_estadisticas(json.dumps(e), "2026-11-19", 7, 3))
comprobar(e2 == e, "completar dos veces el mismo día no suma")
e = json.loads(c.actualizar_estadisticas(json.dumps(e), "2026-11-22", 7, 1))
comprobar(e["racha"] == 1 and e["mejor_racha"] == 2, "la racha se rompe si falta un día")
comprobar(c.racha_vigente(json.dumps(e), "2026-11-22") == 1, "racha vigente el mismo día")
comprobar(c.racha_vigente(json.dumps(e), "2026-11-24") == 0, "racha caducada")
comprobar(c.racha_vigente("basura", "2026-11-24") == 0, "estadísticas corruptas")
comprobar(json.loads(c.actualizar_estadisticas("{", "no-es-fecha", 1, 1))["racha"] == 0, "fecha no válida")

if fallos:
    print("\n%d fallos" % len(fallos))
    sys.exit(1)
print("Todas las pruebas correctas. Jugador automático:",
      ", ".join("%s %d/%d" % (n, g, t) for n, (g, t) in resumen.items()))

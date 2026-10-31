import json

COLORS = {"r": "coral", "b": "cobalto", "l": "lima"}
SHAPES = {"c": "círculo", "t": "triángulo", "q": "cuadrado"}
PULSES = {"1": "uno", "2": "dos", "3": "tres"}
EMOJI = {"r": "🟥", "b": "🟦", "l": "🟩"}

def rule(name, label, *conditions):
    return {"name": name, "label": label, "conditions": conditions}

STAGES = [
    {"name":"Código cromático","brief":"Cada paquete debe ir al muelle del mismo color.",
     "rules":[rule("Muelle coral","COLOR · CORAL",("color","coral")),rule("Muelle cobalto","COLOR · COBALTO",("color","cobalto")),rule("Muelle lima","COLOR · LIMA",("color","lima"))],
     "rows":"rc1 bt2 lq3 rq2 bc3 lt1 rt3 bq1 lc2"},
    {"name":"Geometría de carga","brief":"El color distrae: fíjate únicamente en la silueta.",
     "rules":[rule("Muelle circular","FORMA · CÍRCULO",("shape","círculo")),rule("Muelle triangular","FORMA · TRIÁNGULO",("shape","triángulo")),rule("Muelle cuadrado","FORMA · CUADRADO",("shape","cuadrado"))],
     "rows":"rc2 lt1 bq3 bc1 rt3 lq2 lc3 bt2 rq1"},
    {"name":"Ritmo de señal","brief":"Los pulsos marcan el destino. Cuenta los destellos.",
     "rules":[rule("Frecuencia uno","PULSO · 1",("pulse","uno")),rule("Frecuencia dos","PULSO · 2",("pulse","dos")),rule("Frecuencia tres","PULSO · 3",("pulse","tres"))],
     "rows":"rc1 bq3 lt2 lc1 rq3 bt2 bc1 lq3 rt2"},
    {"name":"Doble condición","brief":"Ahora necesitas dos datos a la vez: color Y pulso.",
     "rules":[rule("Canal coral","CORAL + PULSO 1",("color","coral"),("pulse","uno")),rule("Canal cobalto","COBALTO + PULSO 2",("color","cobalto"),("pulse","dos")),rule("Canal lima","LIMA + PULSO 3",("color","lima"),("pulse","tres"))],
     "rows":"rc1 bt2 lq3 rt1 bc2 lc3 rq1 bq2 lt3"},
    {"name":"Forma y color","brief":"El destino depende de la combinación exacta de dos atributos.",
     "rules":[rule("Archivo redondo","CORAL + CÍRCULO",("color","coral"),("shape","círculo")),rule("Archivo angular","COBALTO + TRIÁNGULO",("color","cobalto"),("shape","triángulo")),rule("Archivo recto","LIMA + CUADRADO",("color","lima"),("shape","cuadrado"))],
     "rows":"rc1 bt2 lq3 rc3 bt1 lq2 rc2 bt3 lq1"},
    {"name":"Protocolo NODO","brief":"Último examen: forma Y ritmo. El color ya no importa.",
     "rules":[rule("Ruta breve","CÍRCULO + PULSO 1",("shape","círculo"),("pulse","uno")),rule("Ruta media","TRIÁNGULO + PULSO 2",("shape","triángulo"),("pulse","dos")),rule("Ruta larga","CUADRADO + PULSO 3",("shape","cuadrado"),("pulse","tres"))],
     "rows":"rc1 lt2 bq3 bc1 rt2 lq3 lc1 bt2 rq3"},
]

state = {}

def _cargo_rows(stage):
    prefix = "ABCDEFGHJK"[STAGES.index(stage)]
    items = []
    for i, token in enumerate(stage["rows"].split(), 1):
        color, shape, pulse = token
        items.append({"code": prefix + "-" + str(i).zfill(2), "color": COLORS[color],
                      "shape": SHAPES[shape], "pulse": PULSES[pulse], "emoji": EMOJI[color]})
    return items

def _matches(rule_data, cargo):
    return all(cargo[field] == value for field, value in rule_data["conditions"])

def _destination(cargo):
    rules = STAGES[state["stage"]]["rules"]
    matches = [i for i, item in enumerate(rules) if _matches(item, cargo)]
    if len(matches) != 1:
        raise ValueError("Nivel inválido: el paquete no tiene un único destino.")
    return matches[0]

def _start(stage_index=0, total_score=0):
    global state
    state = {"stage":stage_index,"index":0,"errors":0,"streak":0,"score":total_score,
             "stage_start_score":total_score,"bins":[0,0,0],"completed":False,
             "failed":False,"game_finished":False,"feedback":"Clasifica el primer paquete.","hints":0}
    return _state_json()

def _state():
    stage = STAGES[state["stage"]]
    cargo_list = _cargo_rows(stage)
    current = cargo_list[state["index"]] if state["index"] < len(cargo_list) else None
    return {**state,"stage_name":stage["name"],"brief":stage["brief"],
            "rules":[{"name":r["name"],"label":r["label"]} for r in stage["rules"]],
            "cargo":current,"total_stages":len(STAGES),"total_cargo":len(cargo_list),
            "progress":state["index"],"stage_number":state["stage"]+1}

def _state_json():
    return json.dumps(_state(), ensure_ascii=False)

def new_game_json():
    return _start()

def submit_json(lane):
    if state.get("failed") or state.get("completed") or state.get("game_finished"):
        return _state_json()
    try:
        lane = int(lane)
    except (TypeError, ValueError):
        state["feedback"] = "Selecciona un muelle válido."
        return _state_json()
    if lane not in (0,1,2):
        state["feedback"] = "Selecciona un muelle válido."
        return _state_json()
    stage = STAGES[state["stage"]]
    cargo = _cargo_rows(stage)[state["index"]]
    correct = _destination(cargo)
    if lane == correct:
        state["bins"][lane] += 1
        state["index"] += 1
        state["streak"] += 1
        state["score"] += 100 + min(state["streak"]-1,5)*20
        state["feedback"] = "¡Ruta correcta! " + stage["rules"][lane]["name"] + "."
        if state["index"] >= 9:
            state["completed"] = True
            state["score"] += 300
            state["feedback"] = "Turno completado. Los nueve paquetes han llegado a su destino."
    else:
        state["errors"] += 1
        state["streak"] = 0
        state["feedback"] = "Ruta incorrecta. Revisa los atributos y vuelve a intentarlo."
        if state["errors"] >= 3:
            state["failed"] = True
            state["feedback"] = "Demasiados desvíos. Reinicia el turno y prueba otra vez."
    return _state_json()

def hint_json():
    if state.get("failed") or state.get("completed") or state.get("game_finished"):
        return _state_json()
    stage = STAGES[state["stage"]]
    cargo = _cargo_rows(stage)[state["index"]]
    lane = _destination(cargo)
    state["hints"] += 1
    state["score"] = max(0, state["score"]-75)
    state["feedback"] = "Pista: este paquete pertenece a «" + stage["rules"][lane]["name"] + "». Se descuentan 75 puntos."
    return _state_json()

def restart_stage_json():
    return _start(state.get("stage",0),state.get("stage_start_score",0))

def next_stage_json():
    if state.get("completed"):
        if state["stage"]+1 >= len(STAGES):
            state["game_finished"] = True
            state["feedback"] = "¡Protocolo completado! Has clasificado toda la carga."
            return _state_json()
        return _start(state["stage"]+1,state["score"])
    return _state_json()

new_game_json()

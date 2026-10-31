import json

SIZE = 7
DIRECTIONS = {"up": (0, -1), "right": (1, 0), "down": (0, 1), "left": (-1, 0)}
ARROWS = {"up": "↑", "right": "→", "down": "↓", "left": "←"}
ROTATION = ["up", "right", "down", "left"]

LEVELS = [
    {"name":"La ensenada quieta","brief":"Aprende a leer las corrientes. Recupera las dos boyas y alcanza el faro.","start":[0,6],"exit":[6,0],"buoys":[[3,5],[5,2]],"reefs":[[1,4],[2,4],[2,3],[2,2],[4,1],[4,2]],"currents":[{"at":[1,5],"dir":"right"},{"at":[4,3],"dir":"up"},{"at":[5,1],"dir":"right"}],"fuel":30},
    {"name":"El canal quebrado","brief":"Los arrecifes estrechan el paso. Usa el ancla para esperar una marea favorable.","start":[0,6],"exit":[6,0],"buoys":[[4,5],[3,1]],"reefs":[[1,5],[1,4],[1,3],[3,2],[3,3],[3,4],[5,1],[5,2]],"currents":[{"at":[2,5],"dir":"up"},{"at":[4,4],"dir":"right"},{"at":[4,2],"dir":"down"},{"at":[4,1],"dir":"left"}],"fuel":34},
    {"name":"La garganta azul","brief":"Las corrientes se cruzan entre paredes de roca. Planifica cada giro.","start":[0,6],"exit":[6,0],"buoys":[[3,4],[5,1]],"reefs":[[2,5],[2,4],[2,3],[2,2],[4,2],[4,3],[4,4],[3,1]],"currents":[{"at":[1,5],"dir":"right"},{"at":[3,4],"dir":"up"},{"at":[5,2],"dir":"right"},{"at":[4,1],"dir":"down"}],"fuel":36},
    {"name":"El delta errante","brief":"Un delta lleno de corrientes cruzadas. No confundas avanzar con dejarte llevar.","start":[0,6],"exit":[6,0],"buoys":[[5,5],[2,1]],"reefs":[[1,5],[1,4],[1,3],[1,2],[4,1],[4,2],[4,3],[4,4]],"currents":[{"at":[3,5],"dir":"up"},{"at":[2,3],"dir":"right"},{"at":[5,2],"dir":"left"},{"at":[3,1],"dir":"down"}],"fuel":38},
    {"name":"El ojo de la tormenta","brief":"Último trayecto. Conserva el casco y el combustible hasta el faro.","start":[0,6],"exit":[6,0],"buoys":[[4,5],[2,1]],"reefs":[[1,5],[1,4],[1,3],[1,2],[1,1],[3,4],[3,3],[3,2],[3,1],[5,5]],"currents":[{"at":[2,5],"dir":"up"},{"at":[2,3],"dir":"right"},{"at":[4,2],"dir":"down"},{"at":[5,1],"dir":"left"},{"at":[4,0],"dir":"up"}],"fuel":40}
]

state = {}

def _inside(x, y):
    return 0 <= x < SIZE and 0 <= y < SIZE

def _rotate(direction, phase):
    return ROTATION[(ROTATION.index(direction) + phase) % 4]

def _start(level=0, score=0):
    global state
    data = LEVELS[level]
    state = {"level":level,"x":data["start"][0],"y":data["start"][1],
             "phase":0,"fuel":data["fuel"],"hull":3,"buoys":[],
             "moves":0,"score":score,"level_start_score":score,
             "won":False,"lost":False,"finished":False,
             "message":"Expedición iniciada. Recupera las dos boyas y encuentra el faro.",
             "log":"Sonda desplegada · motor estable."}
    return _json()

def _state():
    data = LEVELS[state["level"]]
    currents = {tuple(item["at"]):item["dir"] for item in data["currents"]}
    reefs = {tuple(p) for p in data["reefs"]}
    buoys = {tuple(p) for p in data["buoys"]}
    collected = {tuple(p) for p in state["buoys"]}
    board = []
    for y in range(SIZE):
        row = []
        for x in range(SIZE):
            p = (x,y)
            if p in reefs: cell = {"kind":"reef","arrow":""}
            elif p == tuple(data["exit"]): cell = {"kind":"lighthouse","arrow":""}
            elif p in buoys and p not in collected: cell = {"kind":"buoy","arrow":""}
            elif p in currents: cell = {"kind":"current","arrow":ARROWS[_rotate(currents[p],state["phase"])]}
            elif p == tuple(data["start"]): cell = {"kind":"dock","arrow":""}
            else: cell = {"kind":"sea","arrow":""}
            row.append(cell)
        board.append(row)
    return {**state,"level_name":data["name"],"brief":data["brief"],
            "total_levels":len(LEVELS),"board":board,"size":SIZE,
            "exit":data["exit"],"buoy_total":len(data["buoys"]),
            "buoys_collected":len(state["buoys"]),
            "phase_name":["PLEAMAR","CORRIENTE ESTE","BAJAMAR","CORRIENTE OESTE"][state["phase"]],
            "current_arrows":["↑","→","↓","←"],
            "complete":state["won"] or state["finished"]}

def _json():
    return json.dumps(_state(),ensure_ascii=False)

def new_game_json():
    return _start()

def act_json(action):
    if state.get("won") or state.get("lost") or state.get("finished"):
        return _json()
    if action not in ("up","right","down","left","anchor"):
        state["message"]="Orden desconocida. Usa un rumbo o echa el ancla."
        return _json()

    state["fuel"] -= 1
    state["moves"] += 1
    state["phase"] = (state["phase"] + 1) % 4
    data = LEVELS[state["level"]]
    reefs = {tuple(p) for p in data["reefs"]}
    currents = {tuple(item["at"]):item["dir"] for item in data["currents"]}
    old = (state["x"],state["y"])
    message = ""

    if action == "anchor":
        message = "Ancla echada. La marea ha cambiado."
        state["log"] = "ANCLA · " + _state_phase_label()
    else:
        dx,dy = DIRECTIONS[action]
        nx,ny = state["x"]+dx,state["y"]+dy
        if not _inside(nx,ny) or (nx,ny) in reefs:
            state["hull"] -= 1
            message = "¡Golpe contra un arrecife o límite! El casco pierde integridad."
            state["log"] = "IMPACTO · casco -" + str(1)
        else:
            state["x"],state["y"] = nx,ny
            message = "Rumbo actualizado."
            if (nx,ny) in currents:
                drift = _rotate(currents[(nx,ny)],state["phase"])
                ddx,ddy = DIRECTIONS[drift]
                tx,ty = nx+ddx,ny+ddy
                if _inside(tx,ty) and (tx,ty) not in reefs:
                    state["x"],state["y"] = tx,ty
                    message = "La corriente te arrastra " + drift + "."
                    state["log"] = "DERIVA · " + ARROWS[drift]
                else:
                    state["hull"] -= 1
                    message = "La corriente te empuja contra un obstáculo. ¡Casco dañado!"
                    state["log"] = "CORRIENTE · impacto"
            else:
                state["log"] = "RUMBO · " + action.upper()

    pos = (state["x"],state["y"])
    for buoy in data["buoys"]:
        point = tuple(buoy)
        if pos == point and list(point) not in state["buoys"]:
            state["buoys"].append(list(point))
            state["score"] += 150
            message += " Boya científica recuperada: +150 puntos."
            state["log"] = "BOYA RECUPERADA · +150"

    if pos == tuple(data["exit"]) and len(state["buoys"]) == len(data["buoys"]):
        state["won"] = True
        state["score"] += max(0,state["fuel"])*10 + state["hull"]*100 + 250
        message = "¡Faro alcanzado! Expedición completada. Bonificación por combustible y casco conservados."
        state["log"] = "FARO ALCANZADO · EXPEDICIÓN COMPLETA"
    elif pos == tuple(data["exit"]):
        message = "Has llegado al faro, pero faltan boyas científicas. Vuelve a recogerlas."
    elif state["hull"] <= 0:
        state["lost"] = True
        message = "Casco perdido. La expedición ha terminado; reinicia el mapa."
    elif state["fuel"] <= 0:
        state["lost"] = True
        message = "Sin combustible. La expedición ha terminado; reinicia el mapa."
    state["message"] = message
    return _json()

def _state_phase_label():
    return ["PLEAMAR","CORRIENTE ESTE","BAJAMAR","CORRIENTE OESTE"][state["phase"]]

def restart_level_json():
    return _start(state.get("level",0),state.get("level_start_score",0))

def next_level_json():
    if not state.get("won"):
        return _json()
    if state["level"] + 1 >= len(LEVELS):
        state["finished"] = True
        state["message"] = "¡Has cartografiado todo el archipiélago! La expedición ha terminado."
        return _json()
    return _start(state["level"]+1,state["score"])

new_game_json()

"""SEMILLA CERO — lógica de puzles gravitatorios. Python ejecutado en Pyodide."""
import json

LEVELS = [
    {"name":"Primer brote","start":[1,1],"goal":[5,5],"drops":[[3,1],[5,2],[2,4]],"walls":[[2,2],[3,2],[4,2],[4,4]],"gravity":0},
    {"name":"Canal de piedra","start":[1,5],"goal":[5,1],"drops":[[1,3],[3,3],[5,4]],"walls":[[2,1],[2,2],[2,3],[4,3],[4,4]],"gravity":1},
    {"name":"Viento cruzado","start":[1,1],"goal":[5,5],"drops":[[3,1],[1,4],[5,3]],"walls":[[2,2],[3,2],[4,2],[2,4],[3,4]],"gravity":2},
    {"name":"La cámara húmeda","start":[5,1],"goal":[1,5],"drops":[[3,1],[5,3],[2,5]],"walls":[[3,2],[3,3],[3,4],[1,3],[5,4]],"gravity":3},
    {"name":"Corazón del jardín","start":[1,5],"goal":[5,1],"drops":[[1,2],[3,3],[5,4],[3,1]],"walls":[[2,1],[2,2],[4,2],[4,3],[2,4],[3,4]],"gravity":0},
]
DIRS = [(0,1),(1,0),(0,-1),(-1,0)]
DIR_NAMES = ["SUR","ESTE","NORTE","OESTE"]
ARROWS = ["↓","→","↑","←"]
state = {}

def _inside(pos):
    return 0 <= pos[0] < 7 and 0 <= pos[1] < 7

def _blocked(pos):
    return not _inside(pos) or pos in state["walls"]

def _collect():
    pos = tuple(state["player"])
    if pos in state["drops"]:
        state["drops"].remove(pos)
        state["water"] += 1

def _finish_check():
    if tuple(state["player"]) == state["goal"] and not state["drops"]:
        state["status"] = "won"
        state["message"] = "¡Raíces establecidas! Has restaurado este jardín."
        state["score"] += max(0, 100 - state["turns"] * 3)
        return True
    if state["turns"] >= 45:
        state["status"] = "lost"
        state["message"] = "La semilla ha agotado su ciclo. Reinicia el jardín e intenta otra ruta."
        return True
    return False

def _public():
    if not state:
        return {"started":False}
    level = LEVELS[state["level"]]
    return {
        "started":True,"level":state["level"],"total":len(LEVELS),
        "name":level["name"],"player":list(state["player"]),
        "start":level["start"],"goal":list(state["goal"]),
        "walls":[list(p) for p in state["walls"]],
        "drops":[list(p) for p in state["drops"]],
        "water":state["water"],"water_total":state["water_total"],
        "gravity":state["gravity"],"gravity_name":DIR_NAMES[state["gravity"]],
        "gravity_arrow":ARROWS[state["gravity"]],
        "turns":state["turns"],"score":state["score"],
        "status":state["status"],"message":state["message"],
        "complete":state["status"]=="won" and state["level"]==len(LEVELS)-1
    }

def _load_level():
    level=LEVELS[state["level"]]
    state["player"]=tuple(level["start"])
    state["goal"]=tuple(level["goal"])
    state["walls"]={tuple(p) for p in level["walls"]}
    state["drops"]={tuple(p) for p in level["drops"]}
    state["water"]=0
    state["water_total"]=len(state["drops"])
    state["gravity"]=level["gravity"]
    state["turns"]=0
    state["status"]="playing"
    state["message"]="Recoge todas las gotas y alcanza la tierra fértil."

def start_game():
    global state
    state={"level":0,"score":0}
    _load_level()
    return json.dumps(_public(),ensure_ascii=False)

def get_state():
    return json.dumps(_public(),ensure_ascii=False)

def move(dx,dy):
    if not state or state["status"]!="playing":
        return json.dumps(_public(),ensure_ascii=False)
    try:
        dx,dy=int(dx),int(dy)
    except (TypeError,ValueError):
        return json.dumps(_public(),ensure_ascii=False)
    if abs(dx)+abs(dy)!=1:
        return json.dumps(_public(),ensure_ascii=False)
    target=(state["player"][0]+dx,state["player"][1]+dy)
    if _blocked(target):
        state["message"]="La roca bloquea el paso. Prueba otra dirección."
        return json.dumps(_public(),ensure_ascii=False)
    state["player"]=target
    state["turns"]+=1
    _collect()
    if not _finish_check():
        gx,gy=DIRS[state["gravity"]]
        pulled=(state["player"][0]+gx,state["player"][1]+gy)
        if not _blocked(pulled):
            state["player"]=pulled
            _collect()
        state["gravity"]=(state["gravity"]+1)%4
        _finish_check()
    if state["status"]=="playing":
        state["message"]="La gravedad ha girado. Gotas: "+str(state["water"])+"/"+str(state["water_total"])+"."
    return json.dumps(_public(),ensure_ascii=False)

def wait_turn():
    if not state or state["status"]!="playing":
        return json.dumps(_public(),ensure_ascii=False)
    state["turns"]+=1
    gx,gy=DIRS[state["gravity"]]
    pulled=(state["player"][0]+gx,state["player"][1]+gy)
    if not _blocked(pulled):
        state["player"]=pulled
        _collect()
    state["gravity"]=(state["gravity"]+1)%4
    _finish_check()
    if state["status"]=="playing":
        state["message"]="Has dejado actuar a la gravedad. Planifica el siguiente paso."
    return json.dumps(_public(),ensure_ascii=False)

def restart_level():
    if state:
        score=state["score"]
        level=state["level"]
        state.clear()
        state.update({"level":level,"score":score})
        _load_level()
    else:
        return start_game()
    return json.dumps(_public(),ensure_ascii=False)

def next_level():
    if not state:
        return start_game()
    if state["status"]=="won" and state["level"]<len(LEVELS)-1:
        state["level"]+=1
        _load_level()
    elif state["status"] in ("won","lost"):
        return start_game()
    return json.dumps(_public(),ensure_ascii=False)

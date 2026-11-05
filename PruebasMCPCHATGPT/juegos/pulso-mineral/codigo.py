"""PULSO MINERAL: lógica de conexión de circuitos. Ejecutado en Pyodide."""
import json

N, E, S, W = 1, 2, 4, 8
DIRS = [(-1,0,N,S),(0,1,E,W),(1,0,S,N),(0,-1,W,E)]
LEVELS = [
    {"name":"Galería de cuarzo","path":[(0,2),(1,2),(1,1),(2,1),(3,1),(3,2),(4,2)],"relays":[2,4],"scramble":[0,3,1,3,1,3,0]},
    {"name":"Veta azul","path":[(0,2),(1,2),(1,3),(2,3),(3,3),(3,2),(4,2)],"relays":[2,4],"scramble":[0,1,2,1,2,1,0]},
    {"name":"Cámara de amatista","path":[(0,2),(1,2),(1,1),(2,1),(2,2),(2,3),(3,3),(4,3),(4,2)],"relays":[2,5,7],"scramble":[0,1,3,1,3,1,3,1,0]},
    {"name":"Falla magnética","path":[(0,2),(1,2),(2,2),(2,1),(3,1),(3,2),(3,3),(4,3),(4,2)],"relays":[3,6],"scramble":[0,2,1,2,1,2,1,2,0]},
    {"name":"Corazón de la montaña","path":[(0,2),(1,2),(1,1),(2,1),(2,2),(3,2),(3,3),(4,3),(4,2)],"relays":[2,4,6],"scramble":[0,3,1,3,1,3,1,3,0]},
]
state = {}

def _rotate(mask):
    result = 0
    for old, new in ((N,E),(E,S),(S,W),(W,N)):
        if mask & old:
            result |= new
    return result

def _base_masks(path):
    masks = []
    for i, (x,y) in enumerate(path):
        mask = 0
        for j in (i-1, i+1):
            if 0 <= j < len(path):
                nx, ny = path[j]
                dx, dy = nx-x, ny-y
                for ax, ay, bit, _ in DIRS:
                    if (dx,dy) == (ax,ay):
                        mask |= bit
        masks.append(mask)
    return masks

def _powered_cells():
    powered = set()
    stack = [state["source"]]
    while stack:
        pos = stack.pop()
        if pos in powered:
            continue
        powered.add(pos)
        x,y = pos
        mask = state["tiles"].get(pos, 0)
        for dx,dy,bit,opposite in DIRS:
            nxt = (x+dx,y+dy)
            if mask & bit and nxt in state["tiles"] and state["tiles"][nxt] & opposite and nxt not in powered:
                stack.append(nxt)
    return powered

def _check():
    powered = _powered_cells()
    if state["target"] in powered and all(p in powered for p in state["relays"]):
        state["status"] = "won"
        state["message"] = "¡Circuito restaurado! La energía vuelve a recorrer la galería."
        state["score"] += max(20, 160 - state["rotations"] * 4)
        return True
    return False

def _public():
    if not state:
        return {"started":False}
    powered = _powered_cells()
    tiles = []
    for (x,y),mask in sorted(state["tiles"].items(), key=lambda item:(item[0][1],item[0][0])):
        tiles.append({"x":x,"y":y,"mask":mask,"kind":"source" if (x,y)==state["source"] else "target" if (x,y)==state["target"] else "relay" if (x,y) in state["relays"] else "pipe","powered":(x,y) in powered,"rotatable":(x,y) not in (state["source"],state["target"])})
    return {
        "started":True,"level":state["level"],"total":len(LEVELS),
        "name":LEVELS[state["level"]]["name"],"tiles":tiles,
        "relays_total":len(state["relays"]),
        "relays_powered":sum(1 for p in state["relays"] if p in powered),
        "rotations":state["rotations"],"score":state["score"],
        "status":state["status"],"message":state["message"],
        "complete":state["status"]=="won" and state["level"]==len(LEVELS)-1
    }

def _load_level():
    level = LEVELS[state["level"]]
    path = level["path"]
    masks = _base_masks(path)
    state["source"] = path[0]
    state["target"] = path[-1]
    state["relays"] = {path[i] for i in level["relays"]}
    state["tiles"] = {}
    for pos, mask, turns in zip(path, masks, level["scramble"]):
        for _ in range(turns):
            mask = _rotate(mask)
        state["tiles"][pos] = mask
    state["rotations"] = 0
    state["status"] = "playing"
    state["message"] = "Gira los conductos para llevar energía hasta el núcleo y activar todos los relés."

def start_game():
    global state
    state = {"level":0,"score":0}
    _load_level()
    return json.dumps(_public(),ensure_ascii=False)

def get_state():
    return json.dumps(_public(),ensure_ascii=False)

def rotate_tile(x,y):
    if not state or state["status"] != "playing":
        return json.dumps(_public(),ensure_ascii=False)
    try:
        pos = (int(x),int(y))
    except (TypeError,ValueError):
        return json.dumps(_public(),ensure_ascii=False)
    if pos not in state["tiles"] or pos in (state["source"],state["target"]):
        state["message"] = "Ese elemento no se puede girar."
        return json.dumps(_public(),ensure_ascii=False)
    state["tiles"][pos] = _rotate(state["tiles"][pos])
    state["rotations"] += 1
    if not _check():
        powered = _powered_cells()
        state["message"] = "Energía conectada: "+str(len(powered))+"/"+str(len(state["tiles"]))+" conductos · Relés: "+str(sum(1 for p in state["relays"] if p in powered))+"/"+str(len(state["relays"]))+"."
    return json.dumps(_public(),ensure_ascii=False)

def restart_level():
    if not state:
        return start_game()
    score, level = state["score"], state["level"]
    state.clear()
    state.update({"score":score,"level":level})
    _load_level()
    return json.dumps(_public(),ensure_ascii=False)

def next_level():
    if not state:
        return start_game()
    if state["status"] == "won" and state["level"] < len(LEVELS)-1:
        state["level"] += 1
        _load_level()
    elif state["status"] in ("won","lost"):
        return start_game()
    return json.dumps(_public(),ensure_ascii=False)

import json

LEVELS = [
    {"name":"Anillo de servicio","start":[0,0],"exit":[6,4],"cores":[[2,0],[4,2]],"walls":[[1,1],[1,2],[3,1],[5,1],[5,2],[2,3]],"hazards":[[4,4]],"battery":22},
    {"name":"Conductos cruzados","start":[0,4],"exit":[6,0],"cores":[[1,3],[3,2],[5,1]],"walls":[[1,0],[1,1],[3,4],[3,3],[5,3],[5,4],[2,1]],"hazards":[[4,0],[2,4]],"battery":27},
    {"name":"Zona de baja gravedad","start":[0,0],"exit":[6,4],"cores":[[2,1],[4,3],[6,2]],"walls":[[1,0],[1,1],[3,1],[3,2],[5,2],[5,3],[2,4]],"hazards":[[2,2],[4,1]],"battery":30},
    {"name":"El núcleo silencioso","start":[0,4],"exit":[6,0],"cores":[[1,3],[3,1],[5,2]],"walls":[[1,0],[2,0],[3,3],[4,3],[5,4],[2,2],[4,1]],"hazards":[[0,2],[6,3]],"battery":32},
    {"name":"Última transmisión","start":[0,0],"exit":[6,4],"cores":[[1,2],[3,0],[5,3],[3,4]],"walls":[[1,1],[2,1],[4,1],[5,1],[2,3],[4,3]],"hazards":[[3,2],[6,1],[0,4]],"battery":38}
]
W, H = 7, 5
DELTAS = {"up":(0,-1),"down":(0,1),"left":(-1,0),"right":(1,0)}

def fresh(level=0):
    spec = LEVELS[level]
    return {"level":level,"pos":spec["start"][:],"cores":[],"energy":spec["battery"],"moves":0,"status":"playing","message":"Recupera todos los núcleos y encuentra la compuerta."}

def payload(state):
    spec = LEVELS[state["level"]]
    x,y = state["pos"]
    grid = []
    for row in range(H):
        line=[]
        for col in range(W):
            p=[col,row]
            if p == [x,y]: tile="R"
            elif p == spec["exit"]: tile="E"
            elif p in spec["walls"]: tile="#"
            elif p in spec["hazards"]: tile="!"
            elif p in spec["cores"] and p not in state["cores"]: tile="C"
            else: tile="."
            line.append(tile)
        grid.append(line)
    return {"state":state,"grid":grid,"level_name":spec["name"],"total_cores":len(spec["cores"]),"total_levels":len(LEVELS)}

def new_game():
    return json.dumps(payload(fresh()), ensure_ascii=False)

def act(state_json, direction):
    state=json.loads(state_json)
    if state["status"] != "playing" or direction not in DELTAS:
        return json.dumps(payload(state), ensure_ascii=False)
    dx,dy=DELTAS[direction]
    x,y=state["pos"]
    nx,ny=x+dx,y+dy
    spec=LEVELS[state["level"]]
    if not (0<=nx<W and 0<=ny<H) or [nx,ny] in spec["walls"]:
        state["message"]="Ruta bloqueada. Busca otro pasillo."
        return json.dumps(payload(state), ensure_ascii=False)
    cost=2 if [nx,ny] in spec["hazards"] else 1
    if state["energy"] < cost:
        state["status"]="failed"
        state["message"]="Batería agotada. La operación ha terminado."
        return json.dumps(payload(state), ensure_ascii=False)
    state["pos"]=[nx,ny]
    state["energy"]-=cost
    state["moves"]+=1
    if [nx,ny] in spec["hazards"]:
        state["message"]="¡Zona inestable! Has consumido 2 unidades de energía."
    if [nx,ny] in spec["cores"] and [nx,ny] not in state["cores"]:
        state["cores"].append([nx,ny])
        state["message"]="Núcleo recuperado. Buen trabajo."
    if [nx,ny] == spec["exit"]:
        if len(state["cores"]) == len(spec["cores"]):
            if state["level"] == len(LEVELS)-1:
                state["status"]="won"
                state["message"]="¡Estación restaurada! Has completado las cinco operaciones."
            else:
                state["status"]="level_complete"
                state["message"]="Sector asegurado. La compuerta se ha desbloqueado."
        else:
            state["message"]="Compuerta cerrada: todavía faltan núcleos."
    elif state["energy"] == 0:
        state["status"]="failed"
        state["message"]="Sin energía suficiente para continuar."
    return json.dumps(payload(state), ensure_ascii=False)

def next_level(state_json):
    state=json.loads(state_json)
    if state["status"] == "level_complete" and state["level"] < len(LEVELS)-1:
        return json.dumps(payload(fresh(state["level"]+1)), ensure_ascii=False)
    return json.dumps(payload(state), ensure_ascii=False)

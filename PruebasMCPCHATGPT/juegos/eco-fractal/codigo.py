import json

MAPS = [
    ["########", "#S..#..#", "#.#...X#", "#.#.##.#", "#...C..#", "###.#..#", "#C..C..#", "########"],
    ["########", "#S#....#", "#.#.##.#", "#...C..#", "###.##.#", "#C.....#", "#..C..X#", "########"],
    ["########", "#S...#.#", "##.#...#", "#C.#.#X#", "#..C...#", "#.####.#", "#...C..#", "########"],
    ["########", "#S..#..#", "#.#...C#", "#.#.##.#", "#...#..#", "#C..#..#", "#..C..X#", "########"],
    ["########", "#S.....#", "#.###..#", "#C..#C.#", "##..#..#", "#...C..#", "#.....X#", "########"]
]

def _new(level=0):
    grid = MAPS[level]
    walls, crystals = [], []
    start, exit_pos = None, None
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell == "#":
                walls.append([x, y])
            elif cell == "S":
                start = [x, y]
            elif cell == "C":
                crystals.append([x, y])
            elif cell == "X":
                exit_pos = [x, y]
    return {"level": level, "player": start, "walls": walls, "crystals": crystals,
            "exit": exit_pos, "moves": 0, "won": False, "message": "Recoge los tres fragmentos y encuentra la salida."}

def start_game():
    return json.dumps(_new())

def move_player(state_text, direction):
    s = json.loads(state_text)
    if s.get("won"):
        return json.dumps(s)
    delta = {"up": [0, -1], "down": [0, 1], "left": [-1, 0], "right": [1, 0]}
    if direction not in delta:
        return json.dumps(s)
    dx, dy = delta[direction]
    nx, ny = s["player"][0] + dx, s["player"][1] + dy
    if [nx, ny] in s["walls"]:
        s["message"] = "Pared de basalto. Busca otro camino."
        return json.dumps(s)
    s["player"] = [nx, ny]
    s["moves"] += 1
    if [nx, ny] in s["crystals"]:
        s["crystals"].remove([nx, ny])
        s["message"] = "¡Fragmento recuperado! La señal se fortalece."
    elif [nx, ny] == s["exit"]:
        if not s["crystals"]:
            s["won"] = True
            s["message"] = "¡Sector estabilizado! Has recuperado el eco."
        else:
            s["message"] = "La salida está sellada: aún quedan fragmentos."
    else:
        s["message"] = "Explora con cuidado. Cada paso cuenta."
    return json.dumps(s)

def next_level(state_text):
    s = json.loads(state_text)
    if not s.get("won"):
        return json.dumps(s)
    level = s["level"] + 1
    if level >= len(MAPS):
        return json.dumps({"complete": True, "level": level, "message": "¡Has restaurado los cinco sectores del Eco Fractal!"})
    return json.dumps(_new(level))

def restart_level(state_text):
    s = json.loads(state_text)
    return json.dumps(_new(s.get("level", 0)))

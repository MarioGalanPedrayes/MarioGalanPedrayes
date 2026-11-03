"""Lógica original de FRECUENCIA: Código fantasma. Ejecutado en Pyodide."""
import json
import random

SYMBOLS = ["▲", "●", "◆", "✦", "⬟", "☾"]
LABELS = ["triángulo", "círculo", "rombo", "estrella", "hexágono", "luna"]
LEVELS = [
    {"name": "Señal de prueba", "length": 3, "tries": 7},
    {"name": "Eco distante", "length": 4, "tries": 8},
    {"name": "Ruido cruzado", "length": 4, "tries": 7},
    {"name": "Cámara profunda", "length": 5, "tries": 9},
    {"name": "Núcleo fantasma", "length": 5, "tries": 8},
]

state = {}

def _public():
    if not state:
        return {"started": False}
    level = LEVELS[state["level"]]
    return {
        "started": True,
        "level": state["level"],
        "level_name": level["name"],
        "total_levels": len(LEVELS),
        "length": level["length"],
        "tries_left": level["tries"] - len(state["history"]),
        "max_tries": level["tries"],
        "history": state["history"],
        "symbols": SYMBOLS,
        "labels": LABELS,
        "status": state["status"],
        "score": state["score"],
        "hint_used": state["hint_used"],
        "message": state["message"],
        "complete": state["status"] == "won" and state["level"] == len(LEVELS) - 1,
        "secret": state["secret"] if state["status"] in ("won", "lost") else None,
    }

def start_game():
    global state
    state = {
        "level": 0,
        "secret": [],
        "history": [],
        "status": "playing",
        "score": 0,
        "hint_used": False,
        "message": "Descifra la secuencia antes de quedarte sin intentos."
    }
    _new_level()
    return json.dumps(_public(), ensure_ascii=False)

def _new_level():
    level = LEVELS[state["level"]]
    state["secret"] = random.sample(range(6), level["length"])
    state["history"] = []
    state["status"] = "playing"
    state["hint_used"] = False
    state["message"] = "Nueva transmisión detectada. ¡A descifrar!"

def get_state():
    return json.dumps(_public(), ensure_ascii=False)

def submit_guess(values):
    if not state or state["status"] != "playing":
        return json.dumps(_public(), ensure_ascii=False)
    try:
        guess = [int(v) for v in values]
    except (TypeError, ValueError):
        state["message"] = "Selección no válida."
        return json.dumps(_public(), ensure_ascii=False)
    length = LEVELS[state["level"]]["length"]
    if len(guess) != length or any(v < 0 or v >= 6 for v in guess) or len(set(guess)) != length:
        state["message"] = "Usa símbolos distintos y completa todas las posiciones."
        return json.dumps(_public(), ensure_ascii=False)

    exact = sum(1 for i, value in enumerate(guess) if value == state["secret"][i])
    misplaced = len(set(guess) & set(state["secret"])) - exact
    state["history"].append({
        "guess": guess,
        "exact": exact,
        "misplaced": misplaced
    })

    if exact == length:
        bonus = 120 + max(0, (LEVELS[state["level"]]["tries"] - len(state["history"])) * 20)
        if state["hint_used"]:
            bonus = max(40, bonus - 60)
        state["score"] += bonus
        state["status"] = "won"
        state["message"] = "¡Código descifrado! La transmisión vuelve a estar estable."
    elif len(state["history"]) >= LEVELS[state["level"]]["tries"]:
        state["status"] = "lost"
        state["message"] = "Se agotaron los intentos. La secuencia correcta queda revelada."
    else:
        state["message"] = "Lectura recibida: revisa las coincidencias y prueba otra combinación."
    return json.dumps(_public(), ensure_ascii=False)

def request_hint():
    if not state or state["status"] != "playing":
        return json.dumps(_public(), ensure_ascii=False)
    if state["hint_used"]:
        state["message"] = "Ya has utilizado la pista de esta transmisión."
    else:
        state["hint_used"] = True
        hidden = [i for i, value in enumerate(state["secret"]) if all(row["guess"][i] != value for row in state["history"])]
        if hidden:
            pos = hidden[0]
            state["message"] = "Pista: la posición " + str(pos + 1) + " contiene " + LABELS[state["secret"][pos]] + " " + SYMBOLS[state["secret"][pos]] + "."
        else:
            state["message"] = "Pista: ya has probado el símbolo correcto en cada posición; cambia el orden."
    return json.dumps(_public(), ensure_ascii=False)

def next_level():
    if not state:
        return start_game()
    if state["status"] == "won" and state["level"] < len(LEVELS) - 1:
        state["level"] += 1
        _new_level()
    elif state["status"] in ("won", "lost"):
        return start_game()
    return json.dumps(_public(), ensure_ascii=False)

def retry_level():
    if not state:
        return start_game()
    _new_level()
    return json.dumps(_public(), ensure_ascii=False)

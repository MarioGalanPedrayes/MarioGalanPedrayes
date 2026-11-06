import json
import random

CARDS = {
    "tajo": {"name": "Tajo", "cost": 1, "kind": "attack", "text": "Inflige 6 de daño.", "symbol": "✦"},
    "guardia": {"name": "Guardia", "cost": 1, "kind": "defense", "text": "Gana 6 de bloqueo.", "symbol": "◈"},
    "impulso": {"name": "Impulso", "cost": 0, "kind": "skill", "text": "+1 energía y +2 al próximo ataque.", "symbol": "↗"},
    "riposta": {"name": "Riposta", "cost": 1, "kind": "hybrid", "text": "Inflige 4 y gana 3 de bloqueo.", "symbol": "⤴"},
    "martillo": {"name": "Martillo", "cost": 2, "kind": "heavy", "text": "Inflige 11 de daño.", "symbol": "✹"},
}

def _draw(state, amount):
    for _ in range(amount):
        if not state["deck"]:
            if not state["discard"]:
                break
            state["deck"] = state["discard"][:]
            state["discard"] = []
            random.shuffle(state["deck"])
        state["hand"].append(state["deck"].pop())

def _public(state, event=""):
    result = dict(state)
    result["cards"] = CARDS
    result["event"] = event
    result["hand_cards"] = [dict(id=cid, **CARDS[cid]) for cid in state["hand"]]
    return json.dumps(result, ensure_ascii=False)

def start_game():
    deck = ["tajo"] * 5 + ["guardia"] * 3 + ["impulso"] * 2 + ["riposta"] * 2 + ["martillo"]
    random.shuffle(deck)
    state = {
        "hero_hp": 40, "hero_max": 40, "enemy_hp": 68, "enemy_max": 68,
        "energy": 3, "max_energy": 3, "block": 0, "focus": 0,
        "turn": 1, "intent": 7, "deck": deck, "discard": [], "hand": [],
        "status": "playing",
        "history": ["El Magistrado de Hojalata exige una última función."]
    }
    _draw(state, 5)
    return _public(state, "El duelo comienza. Tu turno.")

def play_card(state_json, hand_index):
    state = json.loads(state_json)
    if state["status"] != "playing":
        return _public(state, "El duelo ha terminado.")
    try:
        index = int(hand_index)
        cid = state["hand"][index]
    except (ValueError, TypeError, IndexError):
        return _public(state, "Esa carta ya no está disponible.")
    card = CARDS[cid]
    if state["energy"] < card["cost"]:
        return _public(state, "No tienes energía suficiente.")

    state["energy"] -= card["cost"]
    state["hand"].pop(index)
    state["discard"].append(cid)
    event = ""
    if cid == "tajo":
        damage = 6 + state["focus"]
        state["focus"] = 0
        state["enemy_hp"] = max(0, state["enemy_hp"] - damage)
        event = f"Tajo certero: {damage} de daño."
    elif cid == "guardia":
        state["block"] += 6
        event = "Adoptas guardia: +6 de bloqueo."
    elif cid == "impulso":
        state["energy"] = min(state["max_energy"] + 1, state["energy"] + 1)
        state["focus"] += 2
        event = "El mecanismo acelera: +1 energía y el próximo ataque gana +2."
    elif cid == "riposta":
        damage = 4 + state["focus"]
        state["focus"] = 0
        state["enemy_hp"] = max(0, state["enemy_hp"] - damage)
        state["block"] += 3
        event = f"Riposta: {damage} de daño y +3 de bloqueo."
    elif cid == "martillo":
        damage = 11 + state["focus"]
        state["focus"] = 0
        state["enemy_hp"] = max(0, state["enemy_hp"] - damage)
        event = f"Golpe demoledor: {damage} de daño."

    if state["enemy_hp"] <= 0:
        state["status"] = "won"
        event += " El Magistrado cae. ¡Victoria!"
    state["history"].append(event)
    return _public(state, event)

def end_turn(state_json):
    state = json.loads(state_json)
    if state["status"] != "playing":
        return _public(state, "El duelo ha terminado.")
    incoming = state["intent"]
    absorbed = min(state["block"], incoming)
    damage = incoming - absorbed
    state["hero_hp"] = max(0, state["hero_hp"] - damage)
    state["block"] = 0
    state["discard"].extend(state["hand"])
    state["hand"] = []
    state["turn"] += 1
    state["intent"] = 7 + min(8, state["turn"] // 2)
    state["energy"] = state["max_energy"]
    if state["hero_hp"] <= 0:
        state["status"] = "lost"
        event = f"El impacto atraviesa tu defensa por {damage}. El taller queda en silencio."
    else:
        _draw(state, 5)
        event = f"El Magistrado ataca por {incoming}: bloqueas {absorbed} y recibes {damage}. Comienza el turno {state['turn']}."
    state["history"].append(event)
    return _public(state, event)

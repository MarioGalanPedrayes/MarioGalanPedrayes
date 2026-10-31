"""Reglas y estado de BROTE: Ecosistema Perdido."""
from __future__ import annotations

from copy import deepcopy
import random

PLOT_COUNT = 9
WEATHER = ["Brisa", "Llovizna", "Sol suave", "Niebla luminosa"]
PLANTS = {
    "luna": {"name": "Flor de luna", "emoji": "🌙", "cost": {"seeds": 1}, "days": 2, "reward": {"dew": 2}},
    "amber": {"name": "Caléndula ámbar", "emoji": "🌼", "cost": {"seeds": 1, "dew": 1}, "days": 3, "reward": {"seeds": 2}},
    "fern": {"name": "Helecho susurrante", "emoji": "🌿", "cost": {"seeds": 2, "dew": 1}, "days": 3, "reward": {"wood": 1, "dew": 1}},
}
CREATURES = [
    {"id": "moth", "name": "Polilla farol", "emoji": "🦋", "hint": "Le atraen las flores nocturnas."},
    {"id": "fox", "name": "Zorrito musgo", "emoji": "🦊", "hint": "Busca rincones tranquilos y refugios."},
    {"id": "frog", "name": "Ranita lluvia", "emoji": "🐸", "hint": "Aparece cuando el suelo está húmedo."},
    {"id": "bird", "name": "Pájaro brisa", "emoji": "🐦", "hint": "Visita jardines llenos de brotes."},
]


def new_game():
    return {
        "day": 1, "energy": 8, "max_energy": 8,
        "resources": {"dew": 5, "seeds": 5, "wood": 2, "petals": 0},
        "plots": [None] * PLOT_COUNT,
        "shelter": 0, "creatures": [], "weather": "Brisa",
        "log": ["El claro está en silencio. Es hora de devolverle la vida."],
        "mission": {"text": "Planta 2 brotes para despertar el jardín.", "target": 2, "progress": 0, "done": False, "reward": {"dew": 3, "seeds": 2}},
        "score": 0,
    }


def snapshot(state):
    return deepcopy(state)


def _log(state, message):
    state["log"].insert(0, message)
    state["log"] = state["log"][:7]


def _spend(state, costs):
    for key, amount in costs.items():
        if state["resources"].get(key, 0) < amount:
            raise ValueError("No tienes suficientes recursos.")
    for key, amount in costs.items():
        state["resources"][key] -= amount


def _energy(state, amount=1):
    if state["energy"] < amount:
        raise ValueError("Te falta energía. Pasa el día para recuperarla.")
    state["energy"] -= amount


def perform_action(state, action, data=None):
    data = data or {}
    if action == "gather":
        _energy(state)
        found = random.choices(["dew", "seeds", "wood", "petals"], weights=[40, 30, 20, 10])[0]
        amount = 2 if found in ("dew", "seeds") else 1
        state["resources"][found] += amount
        names = {"dew": "rocío", "seeds": "semillas", "wood": "madera", "petals": "pétalos"}
        _log(state, f"Has reunido {amount} de {names[found]} en el claro.")
    elif action == "plant":
        _energy(state)
        index = int(data.get("plot", -1))
        kind = str(data.get("kind", "luna"))
        if not 0 <= index < PLOT_COUNT or state["plots"][index] is not None:
            raise ValueError("Esa parcela no está disponible.")
        if kind not in PLANTS:
            raise ValueError("Semilla desconocida.")
        plant = PLANTS[kind]
        _spend(state, plant["cost"])
        state["plots"][index] = {"kind": kind, "days_left": plant["days"], "watered": False, "grown": False}
        state["mission"]["progress"] += 1
        _log(state, f"Has plantado {plant['name'].lower()}.")
        _check_mission(state)
    elif action == "water":
        _energy(state)
        index = int(data.get("plot", -1))
        if not 0 <= index < PLOT_COUNT or not state["plots"][index] or state["plots"][index]["grown"]:
            raise ValueError("No hay una planta que necesite agua en esa parcela.")
        if state["plots"][index]["watered"]:
            raise ValueError("Esa planta ya está regada hoy.")
        _spend(state, {"dew": 1})
        state["plots"][index]["watered"] = True
        state["plots"][index]["days_left"] = max(0, state["plots"][index]["days_left"] - 1)
        _log(state, "Una gota de rocío acelera el crecimiento.")
        if state["plots"][index]["days_left"] == 0:
            _grow(state, index)
    elif action == "harvest":
        index = int(data.get("plot", -1))
        if not 0 <= index < PLOT_COUNT or not state["plots"][index] or not state["plots"][index]["grown"]:
            raise ValueError("Todavía no hay nada que recolectar.")
        plant = PLANTS[state["plots"][index]["kind"]]
        for key, amount in plant["reward"].items():
            state["resources"][key] += amount
        state["resources"]["petals"] += 1
        state["score"] += 10
        _log(state, f"¡Cosecha conseguida! {plant['name']} te ha dado recursos.")
        state["plots"][index] = None
    elif action == "explore":
        _energy(state, 2)
        roll = random.random()
        if roll < 0.42:
            state["resources"]["seeds"] += 2
            _log(state, "Entre las raíces has encontrado 2 semillas.")
        elif roll < 0.72:
            state["resources"]["wood"] += 2
            _log(state, "Has encontrado madera seca: +2.")
        elif roll < 0.9:
            state["resources"]["dew"] += 3
            _log(state, "Un pequeño manantial te regala 3 de rocío.")
        else:
            _meet_creature(state)
    elif action == "build":
        _energy(state, 2)
        if state["shelter"] >= 3:
            raise ValueError("Ya has construido todos los refugios disponibles.")
        _spend(state, {"wood": 3, "petals": 2})
        state["shelter"] += 1
        _log(state, "Has construido un refugio acogedor. Quizá alguien venga a visitarlo.")
    elif action == "end_day":
        _end_day(state)
    else:
        raise ValueError("Acción no reconocida.")
    return snapshot(state)


def _grow(state, index):
    plot = state["plots"][index]
    plot["grown"] = True
    plot["watered"] = False
    _log(state, f"{PLANTS[plot['kind']]['name']} ha florecido. ¡Puedes cosecharla!")


def _meet_creature(state):
    available = [c for c in CREATURES if c["id"] not in [x["id"] for x in state["creatures"]]]
    if available:
        creature = random.choice(available)
        state["creatures"].append(creature)
        state["score"] += 25
        _log(state, f"¡Ha llegado {creature['name']} {creature['emoji']}! {creature['hint']}")
    else:
        state["resources"]["petals"] += 2
        _log(state, "El claro está lleno de vida. Has recogido 2 pétalos.")


def _check_mission(state):
    mission = state["mission"]
    if not mission["done"] and mission["progress"] >= mission["target"]:
        mission["done"] = True
        for key, amount in mission["reward"].items():
            state["resources"][key] += amount
        _log(state, "Encargo completado: el jardín despierta. Recompensa recibida.")


def _end_day(state):
    for i, plot in enumerate(state["plots"]):
        if plot and not plot["grown"]:
            plot["days_left"] -= 1
            plot["watered"] = False
            if plot["days_left"] <= 0:
                _grow(state, i)
    state["day"] += 1
    state["energy"] = state["max_energy"]
    state["weather"] = random.choice(WEATHER)
    if state["weather"] == "Llovizna":
        for plot in state["plots"]:
            if plot and not plot["grown"]:
                plot["days_left"] = max(0, plot["days_left"] - 1)
    if state["shelter"] and random.random() < min(0.35 + state["shelter"] * 0.18, 0.85):
        _meet_creature(state)
    _log(state, f"Amanece el día {state['day']}. El tiempo: {state['weather'].lower()}.")

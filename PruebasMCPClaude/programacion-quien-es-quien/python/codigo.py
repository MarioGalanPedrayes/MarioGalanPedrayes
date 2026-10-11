"""¿Quién es quién? de lenguajes de programación (lógica del juego).

El ordenador elige un lenguaje secreto; tú haces preguntas de sí/no sobre
sus características y vas descartando candidatos hasta adivinarlo.
"""
import json
import random

PERSONAJES = {
    "Python":     {"ejecucion": "interpretado", "tipado": "dinámico", "epoca": "1990-1999",      "uso": "datos"},
    "JavaScript": {"ejecucion": "interpretado", "tipado": "dinámico", "epoca": "1990-1999",      "uso": "web"},
    "Java":       {"ejecucion": "compilado",    "tipado": "estático", "epoca": "1990-1999",      "uso": "empresa"},
    "C":          {"ejecucion": "compilado",    "tipado": "estático", "epoca": "antes de 1990",  "uso": "sistemas"},
    "C++":        {"ejecucion": "compilado",    "tipado": "estático", "epoca": "antes de 1990",  "uso": "sistemas"},
    "Rust":       {"ejecucion": "compilado",    "tipado": "estático", "epoca": "2000 o después", "uso": "sistemas"},
    "PHP":        {"ejecucion": "interpretado", "tipado": "dinámico", "epoca": "1990-1999",      "uso": "web"},
    "Ruby":       {"ejecucion": "interpretado", "tipado": "dinámico", "epoca": "1990-1999",      "uso": "web"},
    "Swift":      {"ejecucion": "compilado",    "tipado": "estático", "epoca": "2000 o después", "uso": "móvil"},
    "Kotlin":     {"ejecucion": "compilado",    "tipado": "estático", "epoca": "2000 o después", "uso": "móvil"},
    "R":          {"ejecucion": "interpretado", "tipado": "dinámico", "epoca": "1990-1999",      "uso": "datos"},
    "C#":         {"ejecucion": "compilado",    "tipado": "estático", "epoca": "2000 o después", "uso": "empresa"},
}

ETIQUETAS = {
    "ejecucion": "¿Se ejecuta de forma",
    "tipado": "¿Tiene tipado",
    "epoca": "¿Apareció en la época",
    "uso": "¿Se usa sobre todo para",
}

_secreto = None
_preguntas = 0


def nuevo_juego():
    """Elige un lenguaje secreto al azar y reinicia el contador."""
    global _secreto, _preguntas
    _secreto = random.choice(list(PERSONAJES))
    _preguntas = 0


def tablero():
    """Devuelve los personajes y las preguntas posibles como JSON."""
    opciones = {}
    for datos in PERSONAJES.values():
        for clave, valor in datos.items():
            opciones.setdefault(clave, [])
            if valor not in opciones[clave]:
                opciones[clave].append(valor)
    return json.dumps({"personajes": PERSONAJES, "opciones": opciones, "etiquetas": ETIQUETAS},
                      ensure_ascii=False)


def preguntar(clave, valor):
    """Responde True/False: ¿el lenguaje secreto tiene esa característica?"""
    global _preguntas
    _preguntas += 1
    return PERSONAJES[_secreto][clave] == valor


def adivinar(nombre):
    """Comprueba la respuesta final. Devuelve (acierto, secreto, preguntas)."""
    return json.dumps({"acierto": nombre == _secreto, "secreto": _secreto, "preguntas": _preguntas},
                      ensure_ascii=False)

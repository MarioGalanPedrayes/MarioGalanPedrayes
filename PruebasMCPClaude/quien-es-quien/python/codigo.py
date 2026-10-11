# Quién es quién en Python
# El ordenador piensa en un "tipo de dato" de Python y tú le haces preguntas
# de sí/no para adivinarlo. Después de cada pregunta se descartan candidatos.

import random

PERSONAJES = {
    "int":   {"mutable": False, "ordenado": False, "coleccion": False, "clave_valor": False, "unico": False, "ejemplo": "42"},
    "float": {"mutable": False, "ordenado": False, "coleccion": False, "clave_valor": False, "unico": False, "ejemplo": "3.14"},
    "str":   {"mutable": False, "ordenado": True,  "coleccion": True,  "clave_valor": False, "unico": False, "ejemplo": "'hola'"},
    "bool":  {"mutable": False, "ordenado": False, "coleccion": False, "clave_valor": False, "unico": False, "ejemplo": "True"},
    "list":  {"mutable": True,  "ordenado": True,  "coleccion": True,  "clave_valor": False, "unico": False, "ejemplo": "[1, 2, 3]"},
    "tuple": {"mutable": False, "ordenado": True,  "coleccion": True,  "clave_valor": False, "unico": False, "ejemplo": "(1, 2, 3)"},
    "dict":  {"mutable": True,  "ordenado": True,  "coleccion": True,  "clave_valor": True,  "unico": True,  "ejemplo": "{'a': 1}"},
    "set":   {"mutable": True,  "ordenado": False, "coleccion": True,  "clave_valor": False, "unico": True,  "ejemplo": "{1, 2, 3}"},
}

PREGUNTAS = {
    "mutable": "¿Se puede modificar después de crearlo (es mutable)?",
    "ordenado": "¿Mantiene el orden de sus elementos (se puede indexar)?",
    "coleccion": "¿Es una colección que contiene varios elementos?",
    "clave_valor": "¿Guarda pares clave-valor?",
    "unico": "¿No admite elementos repetidos?",
}


def jugar():
    secreto = random.choice(list(PERSONAJES))
    candidatos = list(PERSONAJES)
    print("Estoy pensando en un tipo de dato de Python.")
    print("Candidatos: " + ", ".join(candidatos))
    print()

    # Demostración automática: se hacen todas las preguntas y se filtra
    for clave, pregunta in PREGUNTAS.items():
        respuesta = PERSONAJES[secreto][clave]
        print(pregunta + " -> " + ("Sí" if respuesta else "No"))
        candidatos = [c for c in candidatos if PERSONAJES[c][clave] == respuesta]
        print("   Quedan: " + ", ".join(candidatos))
        if len(candidatos) == 1:
            break

    print()
    if len(candidatos) == 1:
        c = candidatos[0]
        print("¡Es " + c + "! Ejemplo: " + PERSONAJES[c]["ejemplo"])
    else:
        print("Quedan varios candidatos: " + ", ".join(candidatos))
        print("El secreto era: " + secreto)


def probar_candidato(nombre, respuestas):
    """Dado un nombre y un dict de respuestas, devuelve los candidatos que encajan."""
    return [
        c for c, atributos in PERSONAJES.items()
        if all(atributos[k] == v for k, v in respuestas.items())
    ]


if __name__ == "__main__":
    jugar()

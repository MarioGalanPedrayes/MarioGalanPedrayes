"""
Quiz sobre mitos y seres de la mitología asturiana.
Versión de consola: autocontenida, sin dependencias externas,
sin acceso a red ni a ficheros del sistema.
"""

import random

PREGUNTAS = [
    {
        "enunciado": (
            "¿Cómo se llama el ser protector de los bosques y las minas en la mitología "
            "asturiana, descrito como un anciano pequeño y peludo?"
        ),
        "opciones": ["El Nuberu", "El Busgosu", "El Cuélebre", "El Trasgu"],
        "correcta": 1,
    },
    {
        "enunciado": (
            "El Cuélebre es una gran serpiente alada que, según la leyenda, vigila un "
            "tesoro y vive muchos años. ¿Qué guardián suele acompañarlo o enfrentarse a él?"
        ),
        "opciones": ["La Xana", "El Sumiciu", "El Ñuberu", "El Diañu Burlón"],
        "correcta": 0,
    },
    {
        "enunciado": "¿Qué es una Xana en el folclore asturiano?",
        "opciones": [
            "Un gigante de piedra",
            "Un hada que habita en fuentes y ríos",
            "Un espíritu del fuego",
            "Un dragón marino",
        ],
        "correcta": 1,
    },
    {
        "enunciado": (
            "El Trasgu es un duende travieso muy conocido en Asturias. ¿Qué se dice que "
            "hay que hacer para librarse de sus travesuras en casa?"
        ),
        "opciones": [
            "Regalarle un gorro rojo",
            "Dejarle miel en la puerta",
            "Barrer al revés o esparcir semillas de mijo para que las cuente",
            "Cantarle una nana",
        ],
        "correcta": 2,
    },
    {
        "enunciado": (
            "¿A qué ser mitológico asturiano se le atribuye el control de las "
            "tormentas y el granizo?"
        ),
        "opciones": ["El Nuberu", "El Busgosu", "La Guaxa", "El Trasgu"],
        "correcta": 0,
    },
]


def leer_opcion(num_opciones):
    valor = -1
    while valor < 1 or valor > num_opciones:
        entrada = input(f"Tu respuesta (1-{num_opciones}): ").strip()
        if entrada.isdigit():
            valor = int(entrada)
        if valor < 1 or valor > num_opciones:
            print("Opción no válida, inténtalo de nuevo.")
    return valor


def mensaje_final(aciertos, total):
    ratio = aciertos / total
    if ratio == 1:
        return "¡Excelente! Conoces bien la mitología asturiana."
    if ratio >= 0.6:
        return "Buen resultado, pero aún hay mitos por descubrir."
    return "Te vendría bien repasar las leyendas asturianas."


def main():
    preguntas = PREGUNTAS.copy()
    random.shuffle(preguntas)
    aciertos = 0

    print("=== Quiz de mitos asturianos ===")
    print("Responde con el número de la opción correcta.\n")

    for i, pregunta in enumerate(preguntas, start=1):
        print(f"Pregunta {i}/{len(preguntas)}: {pregunta['enunciado']}")
        for j, opcion in enumerate(pregunta["opciones"], start=1):
            print(f"  {j}) {opcion}")

        respuesta = leer_opcion(len(pregunta["opciones"]))

        if respuesta - 1 == pregunta["correcta"]:
            print("¡Correcto!\n")
            aciertos += 1
        else:
            correcta = pregunta["opciones"][pregunta["correcta"]]
            print(f"Incorrecto. La respuesta correcta era: {correcta}\n")

    print("=== Resultado final ===")
    print(f"Aciertos: {aciertos} de {len(preguntas)}")
    print(mensaje_final(aciertos, len(preguntas)))


if __name__ == "__main__":
    main()

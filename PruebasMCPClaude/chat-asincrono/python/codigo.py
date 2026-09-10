"""
Chat asíncrono (simulación): varios usuarios "escriben a la vez" y sus
mensajes llegan intercalados según un retraso aleatorio, usando asyncio.
Versión de consola: autocontenida, sin dependencias externas,
sin acceso a red ni a ficheros del sistema.
"""

import asyncio
import random
from datetime import datetime

MENSAJES = {
    "Ana": [
        "¿Alguien ha visto el correo del cliente?",
        "Lo reviso ahora mismo",
        "Perfecto, gracias",
    ],
    "Bruno": [
        "Estoy terminando el despliegue",
        "Ya está en producción",
        "Todo verde en el pipeline",
    ],
    "Clara": [
        "¿Quedamos a las 17:00 para la reunión?",
        "Por mí vale",
        "Nos vemos entonces",
    ],
}


async def enviar_mensajes(usuario, mensajes, log):
    """Simula que un usuario escribe varios mensajes seguidos, cada uno
    con un pequeño retraso aleatorio, sin bloquear a los demás usuarios."""
    for texto in mensajes:
        retraso = random.uniform(0.3, 1.5)
        await asyncio.sleep(retraso)
        hora = datetime.now().strftime("%H:%M:%S")
        linea = f"[{hora}] {usuario}: {texto}"
        log.append(linea)
        print(linea)


async def chat():
    log = []
    tareas = [
        enviar_mensajes(usuario, mensajes, log)
        for usuario, mensajes in MENSAJES.items()
    ]
    # asyncio.gather ejecuta las tres conversaciones a la vez: mientras
    # una espera su retraso, las otras pueden seguir avanzando.
    await asyncio.gather(*tareas)
    return log


def main():
    print("=== Chat asíncrono (simulación) ===")
    print(
        "Varios usuarios escriben \"a la vez\"; los mensajes llegan "
        "intercalados según el retraso simulado de cada uno.\n"
    )
    asyncio.run(chat())
    print("\n=== Fin de la conversación ===")


if __name__ == "__main__":
    main()

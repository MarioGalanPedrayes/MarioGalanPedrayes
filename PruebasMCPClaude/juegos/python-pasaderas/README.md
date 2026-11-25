# PASADERAS

Juego de palabras con reto diario. Para cruzar un río hay que pisar piedras, y cada piedra es una palabra de cuatro letras: de una a la siguiente solo se pasa cambiando una letra. El objetivo es llegar a la otra orilla en el menor número de pasos.

## Objetivo
Mostrar que un juego con solucionador exacto puede tener toda su lógica en Python y publicarse como web estática. Python se ejecuta en el navegador con Pyodide 0.26.0 (hace falta conexión para cargarlo desde su CDN).

## Reglas
- Se empieza en la palabra de salida y se escribe, en cada paso, una palabra de la lista del juego que se diferencie de la actual en exactamente una letra (sustituida en su misma posición).
- No se pisa dos veces la misma piedra ni las palabras que la **crecida** deja bajo el agua (se ven antes de empezar).
- Se gana al pisar la palabra meta. El **par** es el menor número de pasos posible con la crecida ya contada (búsqueda en anchura, exacto).
- **Estrellas:** 3 con el par o menos, 2 hasta dos pasos de más, 1 con más. Una o dos pistas quitan una estrella; tres, dos; nunca menos de una.
- **Pista (3):** la siguiente piedra de un camino mínimo desde donde estás. **Deshacer** es ilimitado. Si no hay salida, el juego avisa.
- **Niveles:** Vado (par 3-4, sin crecida), Corriente (4-6, una piedra tapada) y Torrente (5-8, dos tapadas).
- **Reto diario:** la semilla sale de la fecha (siempre Corriente); cuenta para la racha. **Práctica:** partida aleatoria con nivel a elegir, sin efecto en las estadísticas. Rendirse enseña un camino mínimo y no cuenta.

## Controles
Escribe la palabra (sin tildes ni eñes) y pulsa `Intro`. `Ctrl`+`Z` deshace. Con el foco fuera del cuadro de texto, `U` deshace y `P` pide una pista.

## Archivos
- `index.html`: estructura y textos explicativos.
- `style.css`: estilos; las piedras se dibujan con CSS y texto.
- `script.js`: interfaz, guardado en `localStorage` (con try/catch) y puente con Pyodide.
- `codigo.py`: toda la lógica (lista de palabras, grafo, búsqueda en anchura, generador con mulberry32, validación, pistas, estrellas, texto para compartir, racha).
- `pruebas.py`: pruebas de la lógica (`python pruebas.py`).

## Originalidad y licencias
Pasar de una palabra a otra cambiando una letra por paso es un pasatiempo clásico y de uso libre. El nombre, el tema del río, la lista de palabras (escrita para este juego, sin copiar ninguna lista de terceros), la crecida, el par exacto, las pistas, las estrellas, los textos y el diseño son propios; no se usan imágenes, sonidos, marcas ni personajes de terceros. El único componente externo es Pyodide, cargado desde su CDN.

Hecho con ayuda de IA (Claude) como herramienta

Mario Galán Pedrayes

Técnico en Desarrollo Web y Multiplataforma

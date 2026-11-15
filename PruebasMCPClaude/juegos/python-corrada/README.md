# CORRADA

Puzle de acorralar a un ternero en un prado de casillas hexagonales, con reto diario. En cada turno pones una piedra y después el ternero da un paso hacia el borde por el camino más corto. Si le cortas todos los caminos, ganas; si pisa el borde, se escapa.

## Objetivo
Mostrar que un puzle de persecución sobre una rejilla hexagonal, con su jugador automático incluido, puede tener toda su lógica en Python y publicarse como web estática. Python se ejecuta en el navegador con Pyodide 0.26.0 (se necesita conexión para cargarlo desde su CDN).

## Reglas
- El prado es una cuadrícula hexagonal (cada casilla tiene hasta seis vecinas). El ternero empieza en el centro y hay piedras de partida repartidas al azar (a partir de una semilla).
- **Tu turno:** pones una piedra en una casilla libre (no sobre el ternero). Solo se quitan con Deshacer.
- **Turno del ternero:** da un paso por un camino de longitud mínima hasta el borde. Si hay varios igual de cortos, elige uno con un generador (mulberry32) que depende de la semilla y del número de turno: no hay azar oculto.
- **Ganas** si, tras tu piedra, el ternero no tiene ningún camino libre hasta el borde.
- **Pierdes** si el ternero pisa una casilla de borde o si te quedas sin piedras. El presupuesto de piedras es una vez y media la referencia más unas pocas de margen según el nivel.
- **Ruta más corta:** puedes marcar las casillas por las que podría pasar el ternero en un camino mínimo.
- **Niveles:** Prau (9×9, 13 piedras de partida), Corral (11×11, 15) y Pumarada (11×11, 10).
- **Estrellas:** la referencia son las piedras que gasta el jugador automático en esa partida. 3 estrellas hasta un 15 % por encima, 2 hasta un 50 %, 1 si se gana. Con pistas, máximo 2.
- **Pistas:** 3 como máximo; el jugador automático señala una casilla.
- **Reto diario:** la semilla sale de la fecha (nivel Corral), así que el prado es el mismo para todos ese día. Cuenta para la racha de días seguidos.
- **Práctica:** prado aleatorio y nivel a elegir, sin efecto en las estadísticas.

## Controles
Clic o toque en una casilla. Con teclado: flechas para moverte, `Espacio` o `Intro` para poner la piedra, `U` deshace y `P` pide una pista.

## Archivos
- `index.html`: estructura y textos explicativos.
- `style.css`: estilos; las casillas hexagonales, el ternero y las piedras se dibujan con CSS y texto.
- `script.js`: interfaz, guardado en `localStorage` y puente con Pyodide.
- `codigo.py`: toda la lógica (geometría hexagonal, búsqueda en anchura, movimiento del ternero, repetición de la partida, jugador automático, pistas, estrellas, texto para compartir, racha de días).
- `pruebas.py`: pruebas de la lógica (`python pruebas.py`).

Para probar la lógica en el ordenador: `python -c "import codigo; print(codigo.jugar_bot(20261115, 'normal'))"`.

## Originalidad y licencias
Poner obstáculos para encerrar a una pieza que huye es una mecánica genérica. El nombre, el tema asturiano, la ruta más corta visible, el presupuesto de piedras con referencia y estrellas, las pistas, el reto diario con racha, los textos y el diseño son propios; no se usan imágenes, sonidos, marcas ni personajes de terceros. El único componente externo es Pyodide, cargado desde su CDN.

Hecho con ayuda de IA (Claude) como herramienta

Mario Galán Pedrayes

Técnico en Desarrollo Web y Multiplataforma

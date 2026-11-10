# PLANTÍOS

Puzzle de fusionar piezas en un huerto, con reto diario. Te llegan semillas, brotes y plantones de uno en uno; los colocas y, cuando tres o más iguales quedan juntos, se funden en una pieza de nivel superior. Hay que criar la pieza objetivo del nivel antes de que el huerto se llene.

## Objetivo
Mostrar que un juego de fusión completo, con un jugador automático incluido, puede tener toda su lógica en Python y publicarse como web estática. Python se ejecuta en el navegador con Pyodide 0.26.0 (se necesita conexión para cargarlo desde su CDN).

## Reglas
- Seis niveles de pieza: semilla (1), brote (2), plantón (3), manzano (4), pumar (5) y pumarada (6). Se ve la pieza actual y las dos siguientes.
- **Colocar:** se elige una casilla vacía. Si la pieza forma con sus vecinas (arriba, abajo, izquierda, derecha; las diagonales no cuentan) un grupo de 3 o más iguales, todo el grupo se funde en una pieza del nivel siguiente en la casilla elegida.
- **Injerto doble:** un grupo de 5 o más sube dos niveles.
- **Cadena:** la pieza nueva puede fundirse con otras iguales de alrededor.
- **Savia:** comodín; cuenta como cualquier nivel para completar un grupo y se gasta. Si no completa ninguno, se queda esperando.
- **Piedras:** ocupan casilla y se deshacen cuando una fusión ocurre pegada a ellas.
- **Cesto:** una vez por turno se puede cambiar la pieza actual por la del cesto (si está vacío, la actual se guarda y llega la siguiente). No cuenta como turno.
- **Niveles:** Cuadro (5×5, objetivo manzano, con savia), Huerto (5×5 con 3 piedras, objetivo pumar) y Pumarada (5×5 con 4 piedras, objetivo pumar, sin savia).
- Se gana al criar la pieza objetivo; se pierde si el huerto se llena. Deshacer quita la última acción.
- **Estrellas:** la referencia son los turnos que gasta el jugador automático en esa partida. 3 estrellas hasta un 15 % por encima, 2 hasta un 50 %, 1 si se gana. Con pistas, máximo 2.
- **Pistas:** 3 como máximo; el jugador automático (mirando también la pieza siguiente) indica la casilla o si conviene pasar antes por el cesto.
- **Reto diario:** la semilla sale de la fecha (nivel Huerto), así que las piezas y las piedras son las mismas para todos ese día. Cuenta para la racha de días seguidos.
- **Práctica:** piezas aleatorias y nivel a elegir, sin efecto en las estadísticas.

## Controles
Clic o toque en una casilla. Con teclado: flechas para moverte por el huerto, `Espacio` o `Intro` para colocar, `C` usa el cesto, `U` deshace y `P` pide una pista.

## Archivos
- `index.html`: estructura y textos explicativos.
- `style.css`: estilos; las piezas (círculo, hoja, triángulo, rombo, estrella y cruz) se dibujan con CSS.
- `script.js`: interfaz, guardado en `localStorage` y puente con Pyodide.
- `codigo.py`: toda la lógica (generador de números aleatorios determinista, sucesión de piezas, fusiones en cadena, savia, piedras, cesto, jugador automático, pistas, estrellas, texto para compartir, racha de días).

Para probar la lógica en el ordenador: `python -c "import codigo; print(codigo.jugar_bot(20261109, 'normal'))"`.

## Originalidad y licencias
Colocar piezas y fundir grupos de tres iguales es una mecánica genérica. El nombre, el tema del huerto, la cola visible junto al cesto, el injerto doble por grupos de cinco, la savia, las piedras que se deshacen, las pistas, las estrellas, los textos y el diseño son propios; no se usan imágenes, sonidos, marcas ni personajes de terceros. El único componente externo es Pyodide, cargado desde su CDN.

Hecho con ayuda de IA (Claude) como herramienta

Mario Galán Pedrayes

Técnico en Desarrollo Web y Multiplataforma

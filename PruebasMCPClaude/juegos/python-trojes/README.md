# TROJES

Puzzle de ordenar la cosecha con reto diario. Hay varios trojes (compartimentos de madera) con productos mezclados y hay que dejar cada producto junto y sellado en su propio troje.

## Objetivo
Mostrar que un juego completo, con solucionador incluido, puede tener toda su lógica en Python y publicarse como web estática. Python se ejecuta en el navegador con Pyodide 0.26.0 (se necesita conexión para cargarlo desde su CDN).

## Reglas
- Cada troje cabe 4 fichas, apiladas de abajo arriba. Solo se coge lo de arriba.
- Al mover pasan al destino las fichas iguales pegadas arriba del origen que quepan. El destino debe estar vacío o tener arriba una ficha igual.
- Un troje lleno de fichas iguales se **sella** solo y ya no se toca.
- **Candado** (solo en difícil): un troje no se puede coger ni llenar hasta que se selle el primer troje.
- Se gana con todos los trojes vacíos o sellados.
- **Estrellas:** la referencia son los movimientos de una solución que encuentra el programa. 3 estrellas hasta un 25 % por encima, 2 hasta un 75 %, 1 si se completa. Con pistas, máximo 2.
- **Pistas:** 3 como máximo; el solucionador indica un primer movimiento válido desde la posición actual.
- **Reto diario:** la semilla sale de la fecha (siempre difícil), así que el reparto es el mismo para todos ese día. Cuenta para la racha de días seguidos.
- **Práctica:** reparto aleatorio y dificultad a elegir (fácil, normal, difícil), sin efecto en las estadísticas.

## Controles
Clic o toque en el troje de origen y luego en el de destino. Con teclado: `←` `→` para moverte, `Espacio` o `Intro` para elegir, teclas `1`–`8` para elegir un troje directamente, `U` deshace, `P` pide pista y `Esc` cancela la selección.

## Archivos
- `index.html`: estructura y textos explicativos.
- `style.css`: estilos; los trojes y las fichas (círculo, triángulo, cuadrado, rombo, estrella y cruz) se dibujan con CSS.
- `script.js`: interfaz, guardado en `localStorage` y puente con Pyodide.
- `codigo.py`: toda la lógica (generador de números aleatorios determinista, generación, validación de movimientos, solucionador A* ponderado, sellado, candado, pistas, estrellas, texto para compartir, racha de días).

## Originalidad y licencias
Repartir fichas entre recipientes por tipos es una mecánica genérica. El nombre, el tema de la cosecha, el sellado automático, el candado, las pistas, las estrellas, los textos y el diseño son propios; no se usan imágenes, sonidos, marcas ni personajes de terceros. El único componente externo es Pyodide, cargado desde su CDN.

Hecho con ayuda de IA (Claude) como herramienta

Mario Galán Pedrayes

Técnico en Desarrollo Web y Multiplataforma

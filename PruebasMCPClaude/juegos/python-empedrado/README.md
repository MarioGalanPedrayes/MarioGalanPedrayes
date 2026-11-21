# EMPEDRADO

Puzle de lógica en cuadrícula con reto diario. Las cifras al borde de cada fila y columna dan la longitud de los tramos de piedras seguidas; hay que deducir dónde va cada piedra, sin adivinar.

## Objetivo
Mostrar que un juego de lógica con solucionador incluido puede tener toda su lógica en Python y publicarse como web estática. Python se ejecuta en el navegador con Pyodide 0.26.0 (se necesita conexión para cargarlo desde su CDN).

## Reglas
- Cada casilla lleva una piedra o se queda vacía. Las cifras de cada fila y columna, en orden, son las longitudes de sus tramos de piedras seguidas (`3 1` = tres piedras, al menos un hueco, una piedra). `0` es una línea sin piedras.
- La herramienta **Hueco** es una nota («aquí no hay piedra») y no cuenta en la solución.
- Una fila o columna cumplida tacha sus cifras y muestra ✓. Se gana con todas cumplidas.
- **Sin adivinar y con solución única:** cada calle se genera al azar y solo se acepta si un solucionador de lógica de líneas la completa entera.
- **Pista (3):** coloca una casilla que se deduce con lógica. **Revisar (3):** marca con `!` las casillas mal puestas. **Estrellas:** 3 sin ayudas, 2 con una o dos, 1 con más. Deshacer es ilimitado.
- **Tamaños:** Callejón 5×5, Plaza 8×8 y Avenida 10×10.
- **Reto diario:** la semilla sale de la fecha (siempre la Plaza), así que la calle es la misma para todos ese día. Cuenta para la racha de días seguidos.
- **Práctica:** calle aleatoria y tamaño a elegir, sin efecto en las estadísticas.

## Controles
Clic o toque en una casilla con la herramienta activa; arrastrar pinta varias. Botón derecho o `Mayús` usan la otra herramienta. Con teclado: flechas para moverte, `Espacio` o `Intro` usan la herramienta, `X` pone o quita un hueco, `Retroceso` vacía la casilla, `T` cambia de herramienta, `U` deshace, `P` pide una pista y `V` revisa.

## Archivos
- `index.html`: estructura y textos explicativos.
- `style.css`: estilos; las piedras, los huecos y las marcas se dibujan con CSS y texto.
- `script.js`: interfaz, arrastre, guardado en `localStorage` y puente con Pyodide.
- `codigo.py`: toda la lógica (generador de números aleatorios determinista, cifras, solucionador de líneas, comprobación, pistas, revisión, estrellas, texto para compartir, racha de días).

Para probar la lógica en el ordenador: `python -c "import codigo; print(codigo.resolver(*codigo._generar(20261121, 'normal')[2:4])[0])"`.

## Originalidad y licencias
Deducir una cuadrícula a partir de las longitudes de los tramos de cada línea es una mecánica de lógica clásica y de uso libre. El nombre, el tema, las calles generadas al azar (no hay dibujos de terceros), la garantía de solución única sin adivinar, las pistas y la revisión limitadas, las estrellas, los textos y el diseño son propios; no se usan imágenes, sonidos, marcas ni personajes de terceros. El único componente externo es Pyodide, cargado desde su CDN.

Hecho con ayuda de IA (Claude) como herramienta

Mario Galán Pedrayes

Técnico en Desarrollo Web y Multiplataforma

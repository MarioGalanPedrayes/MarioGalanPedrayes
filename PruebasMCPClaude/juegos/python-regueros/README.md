# REGUEROS

Puzzle de lógica espacial con reto diario. Un prado de 6 × 6 casillas con trozos de canal (finales, rectos, codos, T y cruces) mal colocados y una fonte de la que sale el agua. Hay que girar las casillas hasta que el agua llegue a todas, sin fugas.

## Objetivo
Mostrar que un juego completo puede tener toda su lógica en Python y publicarse como web estática. Python se ejecuta en el navegador con Pyodide 0.26.0 (se necesita conexión para cargarlo desde su CDN).

## Reglas
- Una casilla está **regada** si el agua llega hasta ella desde la fonte por canales que se abren el uno hacia el otro.
- Hay **fuga** cuando una casilla regada tiene un brazo abierto que da al borde del prado o a una casilla que no se abre hacia ella.
- Se gana con las 36 casillas regadas y ninguna fuga.
- Hay 5 casillas **fijas** (con un clavo): ya están bien colocadas y no giran.
- Cada giro de 90° cuenta. **Deshacer** no cuenta; **Reiniciar** vuelve al principio.
- **Estrellas:** la referencia son los giros mínimos para reconstruir el trazado previsto. 3 estrellas hasta un 20 % por encima de la referencia, 2 hasta un 60 %, 1 si se completa.
- **Reto diario:** la semilla sale de la fecha, así que el prado es el mismo para todos ese día. Cuenta para la racha de días seguidos con el reto completado.
- **Práctica:** prado aleatorio, sin límite de partidas y sin efecto en las estadísticas.

## Controles
Clic o toque sobre una casilla para girarla. El botón *Sentido* alterna horario y antihorario; `Mayús` o clic derecho giran al revés del sentido elegido. Con teclado: flechas para moverte, `Espacio` o `Intro` giran, `E` gira en horario, `Q` en antihorario, `U` deshace.

## Archivos
- `index.html`: estructura y textos explicativos.
- `style.css`: estilos; el canal, la fonte, las fugas y los clavos se dibujan con CSS.
- `script.js`: interfaz, guardado en `localStorage` y puente con Pyodide.
- `codigo.py`: toda la lógica (generador de números aleatorios determinista, generación del prado a partir de un árbol, evaluación de riego y fugas, giros, deshacer, estrellas, texto para compartir, racha de días).

## Originalidad y licencias
Girar piezas de canal para conectarlas es una mecánica genérica. El nombre, el tema, la regla de las fugas, las casillas fijas, las estrellas, los textos y el diseño son propios; no se usan imágenes, sonidos, marcas ni personajes de terceros. El único componente externo es Pyodide, cargado desde su CDN.

Hecho con ayuda de IA (Claude) como herramienta

Mario Galán Pedrayes

Técnico en Desarrollo Web y Multiplataforma

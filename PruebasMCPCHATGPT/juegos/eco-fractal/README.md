# ECO FRACTAL — Cartógrafos del silencio

Juego original de exploración y rutas por turnos. Recorre cinco sectores, recoge tres fragmentos de señal en cada uno y alcanza la salida.

## Ejecución

Abre [ECO FRACTAL](https://MarioGalanPedrayes.github.io/MarioGalanPedrayes/PruebasMCPCHATGPT/juegos/eco-fractal/) en un navegador moderno. La primera carga necesita conexión para descargar Pyodide desde su CDN.

## Controles

- Flechas del teclado o WASD.
- En pantallas táctiles, usa el panel direccional.
- «Reiniciar sector» vuelve al inicio del mapa actual.

## Estructura

- `index.html`: portada, instrucciones y tablero.
- `style.css`: presentación adaptable.
- `script.js`: carga Pyodide, conecta controles y dibuja el estado.
- `codigo.py`: mapas, movimientos, colisiones, recogida de fragmentos y progresión.

## Tecnología

Método B: Python ejecutado en el navegador mediante Pyodide 0.26.0. JavaScript se limita a la interfaz y a invocar las funciones Python; no se usa servidor ni almacenamiento externo.

## Aprendizaje

Orientación espacial, planificación de rutas, pensamiento secuencial y resolución de problemas.

Todo el código, los mapas y los elementos visuales son originales.

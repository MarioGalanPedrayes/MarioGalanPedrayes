# SEMILLA CERO — Jardín gravitatorio

Puzle estratégico por turnos. Guía una semilla por cinco jardines, recoge todas las gotas de agua y alcanza la tierra fértil. La gravedad gira 90 grados después de cada movimiento, y las rocas detienen tanto a la semilla como al empuje gravitatorio.

## Jugar online

https://MarioGalanPedrayes.github.io/MarioGalanPedrayes/PruebasMCPCHATGPT/juegos/semilla-cero/

La primera carga necesita conexión a Internet para descargar Pyodide 0.26.0 desde su CDN. La lógica Python se ejecuta dentro del navegador.

## Controles y reglas

- Flechas del teclado o WASD para moverse.
- También puedes usar los botones direccionales en pantallas táctiles.
- Cada paso manual hace girar la gravedad.
- El botón «Dejar girar la gravedad» permite avanzar un ciclo sin movimiento manual.
- Recoge todas las gotas antes de alcanzar la tierra fértil.
- Las rocas y los límites del tablero bloquean el desplazamiento.
- Reinicia el jardín si agotas el ciclo.

## Tecnología — Método B: Pyodide

- `codigo.py`: mapas, colisiones, movimiento, gravedad, recogida de agua, turnos y puntuación.
- `index.html`: portada, tablero e instrucciones.
- `style.css`: interfaz adaptable y representación visual.
- `script.js`: carga Pyodide, conecta controles y dibuja el estado.

No requiere servidor propio, base de datos ni servicios externos salvo el CDN de Pyodide. No utiliza `eval()` ni `exec()` ni recoge datos personales.

## Qué se practica

Orientación espacial, anticipación de estados, planificación de rutas, razonamiento secuencial y resolución de problemas.

## Originalidad

Nombre, reglas, mapas, textos, código e interfaz creados para este proyecto. No se utilizan personajes, marcas, música ni recursos gráficos de terceros.

---

Hecho con ayuda de IA (ChatGPT) como herramienta.

Mario Galan Pedrayes  
Técnico en Desarrollo Web y Multiplataforma

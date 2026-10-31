# NODO 7 — Clasificador de señales

Juego original de lógica y clasificación. Trabajas en una terminal logística: cada paquete presenta tres atributos (color, forma y ritmo) y debes enviarlo al único muelle cuyas reglas cumple. Supera seis expedientes de dificultad creciente sin acumular tres desvíos.

## Jugar online

https://MarioGalanPedrayes.github.io/MarioGalanPedrayes/PruebasMCPCHATGPT/juegos/nodo-7/

La primera carga descarga Pyodide desde su CDN. Es necesaria una conexión a Internet para iniciar el motor Python.

## Objetivo y progresión

- Clasifica nueve paquetes en cada expediente.
- Los tres muelles muestran filtros distintos.
- Los primeros expedientes comprueban un atributo; los siguientes combinan dos.
- Tres errores interrumpen el turno actual.
- Cada acierto suma puntos y aumenta la racha.
- Una pista revela el destino correcto, con una penalización de 75 puntos.
- Completa los seis expedientes y supera tu récord local.

## Controles

- Ratón o pantalla táctil: pulsa uno de los tres muelles.
- Teclas 1, 2 y 3: seleccionar muelle.
- Revelar pista: consultar el destino del paquete actual.
- Reiniciar turno: repetir el expediente en curso.

## Cómo está hecho

**Método B — Pyodide.** Las reglas, la validación de destinos, los errores, la puntuación y la progresión están implementados en `codigo.py` y se ejecutan en Python dentro del navegador.

- `index.html`: estructura de la página, instrucciones e interfaz.
- `style.css`: diseño adaptable.
- `script.js`: interacción, renderizado y comunicación con Python.
- `codigo.py`: reglas y lógica íntegra del juego.

No necesita servidor propio, base de datos ni cuentas. El récord se guarda en `localStorage` con manejo de errores.

## Qué se practica

- Clasificación por atributos.
- Lectura de condiciones simples y compuestas.
- Atención selectiva y detección de patrones.
- Toma de decisiones y control de errores.

## Originalidad

Reglas, expedientes, código, interfaz y elementos gráficos creados para este proyecto. No se utilizan personajes, marcas, música ni recursos protegidos de terceros.

---
Hecho con ayuda de IA (ChatGPT) como herramienta · Mario Galan Pedrayes · Técnico en Desarrollo Web y Multiplataforma
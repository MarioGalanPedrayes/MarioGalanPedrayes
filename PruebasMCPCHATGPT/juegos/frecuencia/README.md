# FRECUENCIA — Código fantasma

Juego original de deducción por turnos. Descifra cinco transmisiones con secuencias de símbolos sin repetir. Cada intento informa de cuántos símbolos están en su posición exacta y cuántos aparecen en otra posición.

## Jugar online

https://MarioGalanPedrayes.github.io/MarioGalanPedrayes/PruebasMCPCHATGPT/juegos/frecuencia/

La primera carga necesita conexión a Internet para descargar Pyodide 0.26.0 desde su CDN. Después, la lógica Python se ejecuta en el navegador.

## Controles y reglas

- Pulsa o toca los símbolos para construir la secuencia.
- Pulsa un símbolo seleccionado para retirarlo.
- «Transmitir intento» comprueba la combinación.
- El indicador verde informa de símbolos correctos en posición exacta; el ámbar indica símbolos correctos en otra posición.
- Cada transmisión tiene un número limitado de intentos.
- Una pista revela un símbolo en su posición y reduce la bonificación.
- Supera cinco transmisiones para completar la campaña.

## Tecnología — Método B: Pyodide

- `codigo.py`: genera códigos y calcula coincidencias, intentos, pistas, puntuación y progresión.
- `index.html`: portada, instrucciones y tablero.
- `style.css`: interfaz adaptable.
- `script.js`: carga Pyodide, conecta las acciones y representa el estado.

No necesita servidor propio, base de datos ni servicios externos salvo el CDN de Pyodide. No usa `eval()` ni `exec()`, ni recoge datos personales.

## Qué se practica

Deducción, lógica combinatoria, memoria de trabajo, análisis de retroalimentación y planificación de estrategias.

## Originalidad

Nombre, símbolos de interfaz, reglas, textos y código creados para este proyecto. No utiliza personajes, marcas, música ni recursos gráficos de terceros.

---

Hecho con ayuda de IA (ChatGPT) como herramienta.

Mario Galan Pedrayes  
Técnico en Desarrollo Web y Multiplataforma

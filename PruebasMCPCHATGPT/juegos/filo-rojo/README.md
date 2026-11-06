# FILO ROJO — Duelo de autómatas

Juego original de combate táctico con cartas. Vera Voltio debe derrotar al Magistrado de Hojalata administrando energía, ataques y bloqueo.

## Cómo jugar
- Cada turno recibes 3 puntos de energía y una mano de cinco cartas.
- Selecciona cartas para atacar, defenderte o preparar un golpe más potente.
- El enemigo anuncia el daño de su siguiente ataque. Usa el bloqueo para reducirlo.
- Pulsa **Terminar turno** para recibir el golpe y robar una nueva mano.
- Derrota al Magistrado antes de quedarte sin vida.

## Controles
- Ratón o toque: seleccionar una carta.
- Teclas 1–5: jugar la carta correspondiente.
- Intro: terminar turno.

## Tecnología
- Python contiene las reglas del combate, la baraja, los efectos de las cartas y la resolución de turnos.
- Pyodide 0.26.0 ejecuta `codigo.py` en el navegador.
- JavaScript solo conecta las acciones con Python y actualiza la interfaz.
- HTML y CSS construyen una mesa de combate editorial; las ilustraciones de los combatientes son formas CSS originales.

## Aprendizaje
Gestión de recursos, planificación de turnos, evaluación de riesgos y lectura de intenciones del adversario.

## Archivos
- `index.html`: portada, mesa de juego y reglas.
- `style.css`: identidad visual y diseño adaptable.
- `script.js`: puente entre interfaz y motor Python.
- `codigo.py`: lógica del juego.

El código Python se muestra en la página y puede descargarse desde el panel «Ver código Python».

# TEJAR

Puzzle de retirar parejas de fichas libres apiladas en capas, con reto diario. Un *tejar* es el taller donde se hacen las tejas; aquí el «almacén» es un montón de fichas que hay que vaciar de dos en dos.

## Objetivo
Mostrar que un juego con geometría (capas, solapes y una regla de «ficha libre»), con generador que garantiza solución y solucionador incluidos, puede tener toda su lógica en Python y publicarse como web estática. Python se ejecuta en el navegador con Pyodide 0.26.0 (se necesita conexión para cargarlo desde su CDN).

## Reglas
- Una ficha está **libre** si no tiene ninguna encima y tiene despejado al menos un lado (izquierda o derecha). Solo se tocan fichas libres.
- Se eligen dos fichas libres que hagan **pareja** y se retiran. Hacen pareja las del mismo dibujo (forma y color).
- Las cuatro **estaciones** (primavera, verano, otoño e invierno) son una familia comodín: dos estaciones cualesquiera hacen pareja.
- Se gana al retirar todas las fichas.
- **Deshacer** devuelve la última pareja. **Barajar** recoloca las fichas que quedan y la nueva distribución siempre tiene salida (3 barajas en fácil, 2 en normal y difícil; una baraja no se deshace).
- **Pistas:** 3 como máximo; el solucionador indica una pareja que mantiene una salida posible.
- **Estrellas:** penalización = fallos + 2 por pista + 3 por baraja. Hasta 2: tres estrellas; hasta 7: dos; más: una. Elegir una ficha tapada no cuenta como fallo.
- **Reto diario:** la semilla sale de la fecha (siempre difícil, almacén «Pajar»), así que el tablero es el mismo para todos ese día. Cuenta para la racha de días seguidos.
- **Práctica:** tablero aleatorio y dificultad a elegir (Corral 20 fichas, Hórreo 36, Pajar 52), sin efecto en las estadísticas.

## Controles
Clic o toque en dos fichas libres. Con teclado: flechas para moverte por las fichas, `Espacio` o `Intro` para elegir, `N` salta a la siguiente ficha libre, `U` deshace, `P` pide pista, `B` baraja y `Esc` cancela la elección.

## Archivos
- `index.html`: estructura y textos explicativos.
- `style.css`: estilos; las fichas y sus formas (círculo, cuadrado, rombo, triángulo, estrella, cruz y estación) se dibujan con CSS.
- `script.js`: interfaz, guardado en `localStorage` y puente con Pyodide.
- `codigo.py`: toda la lógica (generador pseudoaleatorio determinista, diseños, fichas libres con máscaras de bits, generación hacia atrás con solución garantizada, solucionador en profundidad, barajas, pistas, estrellas, texto para compartir, racha de días).

## Originalidad y licencias
Retirar parejas de fichas libres apiladas es una mecánica genérica. El nombre, el tema del tejar, los dibujos, la familia comodín de las estaciones, las barajas con salida garantizada, las pistas, las estrellas, los diseños de almacén, los textos y el aspecto son propios; no se usan imágenes, sonidos, marcas ni personajes de terceros. El único componente externo es Pyodide, cargado desde su CDN.

Hecho con ayuda de IA (Claude) como herramienta

Mario Galán Pedrayes

Técnico en Desarrollo Web y Multiplataforma

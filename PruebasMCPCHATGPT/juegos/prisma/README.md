# PRISMA: Archivo de Luz

Puzle de lógica óptica por niveles. Orienta espejos para desviar un haz y conectar el emisor con el receptor.

## Jugar online

Aplicación web estática compatible con GitHub Pages. No necesita Python, servidor propio ni instalación.

https://mariogalanpedrayes.github.io/MarioGalanPedrayes/PruebasMCPCHATGPT/juegos/prisma/

## Cómo jugar

- Pulsa o toca un espejo para alternar su orientación.
- El haz se recalcula automáticamente.
- Conecta el emisor (círculo ámbar) con el receptor.
- Completa cinco expedientes intentando usar pocos giros.
- Usa «Revelar una pista» si necesitas ayuda.
- Al completar un expediente, pulsa el botón «Siguiente nivel» que aparece en el panel de misión.
- En el último expediente, ese botón te permite volver al primero.
- Pulsa «Reiniciar tablero» o la tecla R para recuperar la disposición inicial.
- Pulsa Enter al completar un nivel para avanzar.

Los mejores resultados y el progreso desbloqueado se guardan en localStorage del navegador.

## Arquitectura

- `index.html`: estructura y elementos de interfaz.
- `style.css`: diseño adaptable, tablero y efectos visuales.
- `game.js`: niveles, reflexión óptica, detección de objetivos, progresión y guardado.

No utiliza bibliotecas de juego, imágenes, audio ni recursos gráficos de terceros. El tablero y los efectos se dibujan con HTML, CSS y SVG originales.

## Originalidad

Nombre, niveles, código, reglas, interfaz y gráficos creados para este proyecto. No se incorporan personajes, marcas, música ni ilustraciones protegidas de terceros.

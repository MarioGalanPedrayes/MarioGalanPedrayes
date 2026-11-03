# FAROS DE NIEBLA

Puzzle de deducción con reto diario. Hay un código oculto de 4 faros, cada uno con uno de 6 símbolos (sin repetir). Hay que descubrirlo en 7 intentos usando las pistas de cada intento y hasta 3 sondas.

## Objetivo
Mostrar que un juego completo puede tener toda su lógica en Python y publicarse como web estática. Python se ejecuta en el navegador con Pyodide 0.26.0 (se necesita conexión para cargarlo desde su CDN).

## Reglas
- Cada intento son 4 símbolos distintos.
- Pistas por intento: cuántos símbolos correctos están **en su sitio** y cuántos están **en otro sitio**. No se indica cuáles.
- **Sondas (3):** preguntan si un símbolo está en el código, sin decir dónde. Cada una resta 120 puntos.
- Puntuación: 1000, menos 100 por cada intento extra y 120 por cada sonda (mínimo 50 si se gana, 0 si se pierde).
- **Reto diario:** la semilla es la fecha, así que el código es el mismo para todos ese día. Se juega una vez al día y cuenta para la racha.
- **Práctica:** código aleatorio, sin límite de partidas y sin efecto en las estadísticas.

## Controles
Ratón o toque sobre los símbolos; teclas `1`–`6` para añadir, `Retroceso` para borrar el último, `Enter` para probar.

## Archivos
- `index.html`: estructura y textos explicativos.
- `style.css`: estilos.
- `script.js`: interfaz, guardado en `localStorage` y puente con Pyodide.
- `codigo.py`: toda la lógica (generador de números aleatorios determinista, evaluación de intentos, sondas, puntuación, texto para compartir, racha de días).

## Originalidad y licencias
La mecánica de deducción de códigos es genérica. El nombre, los símbolos, los textos y el diseño son propios; no se usan imágenes, sonidos, marcas ni personajes de terceros. El único componente externo es Pyodide, cargado desde su CDN.

Hecho con ayuda de IA (Claude) como herramienta

Mario Galán Pedrayes

Técnico en Desarrollo Web y Multiplataforma

# BESTIARIO: Ecos de lo Salvaje

Juego original de exploración y captura no violenta de 70 criaturas, mediante memoria, escucha y resonancia por turnos. Las especies se distribuyen en seis biomas.

## Objetivo
Explorar los biomas, encontrar criaturas y registrar las 70 especies. Para conseguirlo hay que escuchar un patrón de cuatro tonos y reproducirlo por turnos, evitando que la agitación alcance el 100%.

## Controles
- **Explorar:** encuentra una criatura.
- **Escuchar eco:** muestra el patrón de cuatro tonos.
- **Bruma, Raíz y Chispa:** selecciona un tono por turno.
- **Siguiente rastro:** comienza otro encuentro al terminar.
- **Reiniciar expedición:** borra el progreso local, previa confirmación.

Los aciertos reducen la agitación en 8 puntos y los errores la aumentan en 34. La captura se consigue al completar los cuatro turnos con una agitación igual o inferior al 55%. El progreso se guarda en el almacenamiento local del navegador.

## Tecnologías y archivos
- `index.html`: estructura, controles, portada y explicación.
- `style.css`: diseño adaptable.
- `script.js`: interfaz, eventos, persistencia y puente con Pyodide.
- `codigo.py`: catálogo de 70 criaturas y toda la lógica de exploración, turnos, resonancia y captura.
- `README.md`: documentación.

Python se ejecuta en el navegador mediante Pyodide 0.26.0. Se necesita conexión a Internet para cargar Pyodide desde su CDN.

## Aprendizaje y objetivo educativo
Practicar memoria de trabajo, reconocimiento de patrones, toma de decisiones secuenciales y diseño de lógica de estados. La lógica del juego se separa de la representación visual y los controles.

Hecho con ayuda de IA (Claude) como herramienta

Mario Galán Pedrayes

Técnico en Desarrollo Web y Multiplataforma

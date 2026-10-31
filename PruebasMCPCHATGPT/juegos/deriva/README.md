# DERIVA — Cartógrafo de Mareas

Juego táctico de navegación por turnos. Pilota un barco científico por cinco mapas, recupera las boyas de investigación y alcanza el faro de cada sector.

## Jugar

https://MarioGalanPedrayes.github.io/MarioGalanPedrayes/PruebasMCPCHATGPT/juegos/deriva/

La primera carga necesita conexión a Internet para descargar Pyodide desde su CDN. Después, el motor Python se ejecuta en el navegador.

## Reglas

- Cada mapa contiene un punto de salida, un faro, dos boyas, arrecifes y corrientes.
- Recupera las dos boyas antes de entrar en el faro.
- Las corrientes giran 90 grados tras cada maniobra.
- Si entras en una casilla de corriente, el agua te arrastra una casilla en su dirección actual.
- Puedes echar el ancla para cambiar la marea sin desplazarte.
- Cada maniobra consume una unidad de combustible.
- Tres impactos destruyen el casco; quedarse sin combustible también termina la expedición.
- El combustible y la integridad conservados aumentan la puntuación final del mapa.

## Controles

- Flechas del teclado o WASD: navegar.
- Botones de dirección: navegar en pantallas táctiles.
- Botón del ancla o barra espaciadora: esperar un ciclo de marea.
- Reiniciar mapa: volver al inicio del sector actual.

## Tecnología: método B — Pyodide

La lógica del juego se implementa en Python y se ejecuta en el navegador mediante Pyodide.

- \`codigo.py\`: mapas, corrientes, colisiones, combustible, integridad, objetivos y puntuación.
- \`index.html\`: estructura, instrucciones y tablero.
- \`style.css\`: interfaz adaptable y mapa.
- \`script.js\`: carga de Pyodide, controles y representación de estado.

No requiere servidor, base de datos ni compilación. El progreso no contiene datos personales y no se guarda en un servicio externo.

## Qué se practica

Orientación espacial, anticipación de movimientos, lectura de patrones, planificación de rutas y gestión de recursos limitados.

## Originalidad

Los mapas, reglas, textos, código e interfaz son originales para este proyecto. No se utilizan personajes, marcas, música ni recursos gráficos de terceros.

---
Hecho con ayuda de IA (ChatGPT) como herramienta · Mario Galan Pedrayes · Técnico en Desarrollo Web y Multiplataforma
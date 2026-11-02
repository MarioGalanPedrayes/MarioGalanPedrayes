# TRAZA: Rescate orbital

Aventura original de lógica y navegación por turnos. Controla un robot de mantenimiento, recupera todos los núcleos de energía y alcanza la compuerta antes de agotar la batería en cinco sectores.

## Ejecutar

Abre `index.html` desde GitHub Pages o un servidor estático. Se necesita conexión inicial al CDN de Pyodide (v0.26.0). No requiere instalación ni backend.

## Controles

- Flechas del teclado o WASD.
- También puedes usar los botones direccionales.
- Cada movimiento consume una unidad de batería; las zonas inestables consumen dos.
- Los muros bloquean el paso. Recoge todos los núcleos antes de entrar en la salida.

## Tecnologías y archivos

- `codigo.py`: reglas, mapas, colisiones, energía y progresión del juego.
- `script.js`: carga Pyodide, llama a las funciones Python y dibuja el tablero.
- `index.html`: portada, tablero, controles y explicación.
- `style.css`: interfaz adaptable.

**Método B — Pyodide.** Python se ejecuta en el navegador mediante Pyodide 0.26.0. No se usa servidor Python, base de datos ni recursos gráficos de terceros.

## Qué se practica

Planificación de rutas, gestión de recursos, lectura de mapas, toma de decisiones y programación de lógica por turnos.

## Créditos

Hecho con ayuda de IA (ChatGPT) como herramienta.

Mario Galan Pedrayes  
Técnico en Desarrollo Web y Multiplataforma

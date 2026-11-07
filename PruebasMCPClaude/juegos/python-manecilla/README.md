# MANECILLA

Juego hipercasual de un solo toque. Una aguja gira por una esfera de reloj y hay que pararla cuando pasa por el sector marcado. Cada acierto acelera la aguja y estrecha el sector. Partidas de uno o dos minutos, con récord guardado en el navegador.

## Objetivo
Mostrar que un juego de reflejos, con partidas cortas y reinicio inmediato, puede tener toda su lógica en Python y publicarse como web estática. Python se ejecuta en el navegador con Pyodide 0.26.0 (se necesita conexión para cargarlo desde su CDN).

## Reglas
- **3 vidas.** Se pierde una al pulsar fuera del sector o al agotarse el anillo de tiempo. Cada 8 aciertos se recupera una (máximo 3).
- **Puntos:** acierto = 10; acierto perfecto (40 % central del sector) = 20.
- **Combo** (aciertos seguidos): ×2 desde 5, ×3 desde 10, ×4 desde 15, ×5 desde 20. Un fallo lo pone a cero.
- **Sentido:** cada 5 aciertos la aguja cambia de sentido.
- **Dificultad:** durante los primeros 20 aciertos la velocidad pasa de 150 a 270 °/s, el sector de 70° a 28° y el tiempo por sector de 4,5 s a 2,5 s. Después se queda fija.
- Margen de 2° en los bordes del sector.

## Controles
Botón *Parar*, barra espaciadora o toque sobre la esfera. Tras perder, la barra espaciadora tarda 0,7 s en reiniciar para evitar reinicios por accidente.

## Equilibrio
Simulación con jugadores de error angular gaussiano al pulsar (25 partidas cada uno, tope de 300 aciertos):

| Error (σ) | Aciertos (mediana) |
|---|---|
| 4° | 300 (tope) |
| 8° | 300 (tope; mínimo 27) |
| 14° | 29 |
| 22° | 14 |

A 200 °/s, 14° equivalen a unos 70 ms de error.

## Archivos
- `index.html`: estructura, esfera SVG y textos explicativos.
- `style.css`: estilos.
- `script.js`: bucle de tiempo, dibujo, guardado en `localStorage` y puente con Pyodide.
- `codigo.py`: toda la lógica (giro, sectores, puntuación, combo, vidas, dificultad, texto para compartir y estadísticas).

## Originalidad y licencias
La mecánica de pulsar en el momento justo es genérica. El nombre, el tema, las reglas, los textos y el diseño son propios; no se usan imágenes, sonidos, marcas ni personajes de terceros. El único componente externo es Pyodide, cargado desde su CDN.

Hecho con ayuda de IA (Claude) como herramienta

Mario Galán Pedrayes

Técnico en Desarrollo Web y Multiplataforma

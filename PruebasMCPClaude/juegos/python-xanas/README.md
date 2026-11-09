# MONTAÑA DE XANAS

Aventura 2D vista desde arriba: recorre una montaña con aldea, prado, bosque y gruta, tranquiliza criaturas del folclore en duelos por turnos y hazte amiga de las 12 especies. Con equipo, niveles, registro, partida guardada y un visitante distinto cada día.

## Objetivo
Mostrar que una aventura 2D completa (mapa por casillas, encuentros aleatorios, combate por turnos, equipo, experiencia y guardado) puede tener toda su lógica en Python y publicarse como web estática. Python se ejecuta en el navegador con Pyodide 0.26.0 (se necesita conexión para cargarlo desde su CDN).

## Reglas
- **Mundo:** se camina por casillas. Camino y césped son tranquilos; en la **hierba alta** pueden salir criaturas (prado, bosque y gruta tienen especies y niveles distintos).
- **Duelo sin heridos:** el «ánimo» es la vida. Si el de la criatura salvaje llega a 0 se tranquiliza y se hace amiga. Si el de la tuya llega a 0, se cansa y entra otra; si se cansan todas, vuelves a la fuente de la aldea con el equipo curado y sin perder nada.
- **Elementos en círculo:** Bosque gana a Roca, Roca gana a Niebla y Niebla gana a Bosque (×1,5 con ventaja, ×0,67 con desventaja).
- **Gestos:** cada criatura tiene uno básico, uno fuerte (5 usos) y un resguardo (4 usos) que reduce a la mitad el siguiente golpe.
- **Ofrendas:** cuestan 1 y se aceptan con probabilidad `25 % + 65 % × (1 − ánimo restante)`, con tope del 90 %. Empiezas con 6; cada encuentro resuelto en paz da 1; la fuente deja al menos 3.
- **Cambiar** de criatura gasta el turno; **huir** funciona el 75 % de las veces.
- **Equipo:** hasta 3 criaturas; el resto va a la reserva. Nivel máximo 12.
- **Objetivo:** completar el registro de 12 especies.
- **Visitante del día:** en el claro de la cumbre espera cada día una criatura (nivel 7) elegida a partir de la fecha, igual para todos. Recibirla cuenta para la racha de días.

## Controles
Caminar: flechas o `W` `A` `S` `D`, o los botones de la pantalla (también con pulsación mantenida). En un encuentro: `1` `2` `3` gestos, `O` ofrenda, `4` `5` `6` cambiar de criatura, `F` huir. Todo se puede hacer también con los botones y el tabulador.

## Archivos
- `index.html`: estructura y textos explicativos.
- `style.css`: estilos.
- `script.js`: interfaz (canvas, sprites, paneles), guardado en `localStorage` y puente con Pyodide.
- `codigo.py`: toda la lógica (mapa, 12 especies, generador pseudoaleatorio mulberry32 con estado guardado, encuentros, duelo, ofrendas, experiencia, equipo, guardado validado, texto para compartir, racha de días).

## Originalidad y licencias
Recorrer un mapa visto desde arriba, encontrar criaturas en la hierba y hacerse amigas por turnos son mecánicas genéricas. El nombre, el mundo, las doce criaturas (de nombres inspirados en el folclore tradicional asturiano), el triángulo Bosque-Roca-Niebla, las ofrendas, el duelo sin heridos, los gestos, los dibujos y los textos son propios; no se usan imágenes, sonidos, marcas ni personajes de terceros. Todo se dibuja con canvas. El único componente externo es Pyodide, cargado desde su CDN.

Hecho con ayuda de IA (Claude) como herramienta

Mario Galán Pedrayes

Técnico en Desarrollo Web y Multiplataforma

# VOIDRUN: SECTOR 9

Roguelite arcade de supervivencia, original y desarrollado en Python con Pygame-CE. Pygbag empaqueta el juego para ejecutarlo en navegadores compatibles mediante WebAssembly.

## Características
- Arena de supervivencia con oleadas y dificultad creciente.
- Cinco enemigos: dron, acechador, tanque, francotirador y jefe Núcleo Titán.
- Jefe cada cinco oleadas, con proyectiles en abanico y barra de vida.
- Experiencia, niveles y elección de 3 mejoras aleatorias entre 10.
- Armas pasivas: dron de combate y nova automática.
- Disparo automático al enemigo más cercano y apuntado manual con ratón.
- Dash con invulnerabilidad, pulso de área, disparos perforantes, combos y orbes de experiencia/curación.
- HUD de vida, nivel, experiencia, oleada, tiempo, puntuación y enfriamientos.
- Récord local guardado en localStorage cuando corre bajo Pygbag.
- Menú, pausa, pantalla de mejoras, derrota y reinicio.
- Gráficos procedurales originales; no requiere recursos de terceros.

## Controles
| Control | Acción |
|---|---|
| WASD / flechas | Movimiento |
| Automático | Dispara al enemigo más cercano |
| Ratón pulsado | Apuntar y disparar manualmente |
| Espacio | Dash |
| Q | Pulso de energía |
| Esc | Pausar / continuar |
| 1, 2, 3 | Elegir mejora |
| Clic / toque | Iniciar, elegir mejora o reintentar |

## Ejecutar en navegador
Requiere Python 3.10+ y conexión a Internet durante la instalación/compilación para descargar el runtime WebAssembly de Pygbag.

    python -m pip install -r requirements.txt
    python -m pygbag --build --ume_block 0 --title "VOIDRUN: SECTOR 9" .

Pygbag genera el sitio listo para servir dentro de build/web/. Para probarlo localmente, ejecuta python -m pygbag . desde esta carpeta y abre http://localhost:8000. No abras el HTML con file://: WebAssembly necesita HTTP.

## Publicar en GitHub Pages
1. Ejecuta el comando de compilación anterior.
2. Añade al repositorio todo el contenido generado de build/web/, incluidos los ficheros WASM, DATA, JS y HTML.
3. Publica la rama main desde la raíz del repositorio con GitHub Pages.
4. La portada de este directorio enlaza a build/web/index.html.

**Importante:** GitHub Pages no ejecuta Python directamente. main.py es el código fuente; el paquete WebAssembly que genera Pygbag es lo que hace posible jugar en el navegador.

## Escritorio
    python -m pip install pygame-ce
    python main.py

## Originalidad
Nombre, código, reglas, interfaz y gráficos creados para este proyecto. No se utilizan personajes, música, ilustraciones ni marcas de terceros.

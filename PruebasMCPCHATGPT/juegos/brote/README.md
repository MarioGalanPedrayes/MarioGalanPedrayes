# BROTE: Ecosistema Perdido

Un pequeño juego cozy de gestión y exploración: recupera un claro olvidado, cultiva brotes, reúne recursos, atrae criaturas y completa encargos.

## Jugar online

La versión estática es compatible con GitHub Pages. No necesita Python, Flask ni instalación: abre la página index.html publicada en GitHub Pages.

Si GitHub Pages está configurado para publicar la rama main desde la raíz del repositorio, la dirección será:

https://mariogalanpedrayes.github.io/MarioGalanPedrayes/PruebasMCPCHATGPT/juegos/brote/

La partida se guarda automáticamente en el almacenamiento local del navegador (localStorage).

## Ejecutar en local con Python

También se conserva la versión Python/Flask original:

    python -m venv .venv
    pip install -r requirements.txt
    python app.py

Abre http://127.0.0.1:5000.

## Cómo jugar

- Recolectar: consigue rocío, semillas y madera.
- Plantar: coloca semillas en parcelas vacías; las plantas crecen al pasar de día.
- Regar: acelera el crecimiento.
- Cosechar: recoge recursos cuando la planta florezca.
- Explorar: descubre recursos y criaturas.
- Construir: instala refugios para atraer visitantes.
- Pasar el día: recupera energía, avanza el crecimiento y activa el clima siguiente.

## Archivos

- index.html, style.css, game.js: versión estática para GitHub Pages.
- app.py, game.py, templates/, static/: versión Flask original.
- requirements.txt: dependencias de la versión Flask.

Los elementos visuales son CSS y emoji del sistema; no se incorporan imágenes ni música de terceros.

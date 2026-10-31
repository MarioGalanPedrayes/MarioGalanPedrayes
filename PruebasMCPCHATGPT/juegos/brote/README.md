# BROTE: Ecosistema Perdido

Un pequeño juego cozy de gestión y exploración: recupera un claro olvidado, cultiva brotes, reúne recursos, atrae criaturas y completa encargos antes de que termine la jornada.

## Requisitos

- Python 3.10 o posterior
- Navegador moderno

## Instalación y ejecución

Desde esta carpeta:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abre http://127.0.0.1:5000 en el navegador.

## Cómo jugar

- **Recolectar**: consigue rocío, semillas y madera en el claro.
- **Plantar**: coloca semillas en parcelas vacías; las plantas crecen al pasar de día.
- **Regar**: acelera el crecimiento y ayuda a mantener el jardín sano.
- **Explorar**: descubre recursos y posibilidades de encontrar criaturas.
- **Construir**: instala refugios para atraer visitantes.
- **Pasar el día**: recupera energía, avanza el crecimiento y activa el clima del día siguiente.

El estado de cada partida se guarda en la sesión del servidor. No utiliza recursos, imágenes ni música de terceros: los elementos visuales son CSS y arte original mediante formas y emoji del sistema.

## Estructura

- `app.py`: servidor Flask y API.
- `game.py`: reglas, estado y acciones del juego.
- `templates/index.html`: interfaz.
- `static/style.css`: estilos adaptables.
- `static/game.js`: interacción del navegador.
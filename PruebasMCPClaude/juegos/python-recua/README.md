# Recua

Roguelite de ruta por un puerto de montaña. Lógica 100 % en Python (Pyodide en el navegador).

## Objetivo
Llevar una recua de mulas del valle a la cumbre por un mapa de senderos visible y reunir, entre monedas y sacos vendidos, el valor que pide el objetivo.

## Reglas
- Cada tramo gasta 1 pan; sin pan, −2 de ánimo. Sin ánimo suficiente no se puede seguir.
- En cada sitio se hacen las ofertas que se quiera (aldea, almacén, feria, ermita, encuentro, paso difícil) y luego se sigue; no se vuelve atrás.
- Paso difícil: hay que decidir entre cruzar (ánimo) o rodear (panes).
- Encuentro: apuesta con resultado oculto, fijado por la semilla.
- Cumbre: se venden los sacos; se gana si monedas + sacos × precio ≥ objetivo.
- Referencia exacta calculada por un solucionador con memoria; 3 estrellas ≥ 90 % de la ganancia, 2 ≥ 70 %. Las pistas (máx. 3) limitan a 2 estrellas.
- Reto diario (semilla = hash de la fecha, sin mejoras, con racha) y práctica (mapa aleatorio, sellos y mejoras permanentes).

## Controles
Ratón/toque, o teclado: flechas para elegir sitio, `I` para ir, `1`-`9` para ofertas, `P` para pista.

## Archivos
`index.html`, `style.css`, `script.js` (interfaz), `codigo.py` (lógica), `pruebas.py` (19 pruebas: `python pruebas.py`).

## Licencias y originalidad
Código propio. Mecánicas genéricas (ruta con ramas, gestión de recursos). Sin imágenes ni audio externos; solo Pyodide desde su CDN. Hecho con ayuda de IA (Claude) como herramienta.

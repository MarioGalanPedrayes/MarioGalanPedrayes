# TARIMA

Puzle de colocar piezas de tablas en un suelo de 8 × 8 casillas y despejar filas y columnas, con reto diario. Cada lote trae tres piezas que se colocan sin girar; hay un número fijo de lotes para despejar las líneas del objetivo.

## Objetivo
Mostrar que un puzle de colocar piezas, con generador de partidas, jugador automático y vista previa incluidos, puede tener toda su lógica en Python y publicarse como web estática. Python se ejecuta en el navegador con Pyodide 0.26.0 (se necesita conexión para cargarlo desde su CDN).

## Reglas
- El suelo tiene 8 × 8 casillas. Al empezar hay algunos **nudos** (casillas ocupadas, con un dibujo rayado) que se despejan como cualquier otra casilla.
- Cada **lote** son 3 piezas, que se colocan en cualquier orden. Las piezas **no se giran** y deben caber enteras en casillas libres. Se ve el lote siguiente.
- Una fila o columna completa se **despeja**. Una pieza puede despejar varias a la vez (una fila y una columna son dos líneas).
- La partida dura 5 o 6 lotes según el nivel. Hay que despejar al menos las líneas del **objetivo**. Si ninguna de las piezas que quedan en el lote cabe, la partida termina.
- Puntos (solo para comparar): 1 por casilla cubierta, 10 × líneas² por jugada que despeja y 5 × la racha de jugadas seguidas que despejan.
- La **referencia** son las líneas que despeja el jugador automático en esa partida. Tres estrellas si la igualas o la superas, dos si llegas al 85 %, una si cumples el objetivo. Con pistas (3 como máximo) la nota máxima es de dos estrellas. Deshacer es gratis.
- **Reto diario:** la fecha es la semilla, así que todo el mundo tiene el mismo suelo y las mismas piezas. Cuenta para la racha de días. **Práctica:** partidas aleatorias en tres niveles (Tablón, Entarimado y Parqué).

## Controles
- Ratón o toque: elige una pieza del lote y pulsa una casilla del suelo; esa casilla es el centro de la pieza. Al pasar el ratón se ve dónde cabe (verde) y qué líneas se despejarían (rayas).
- Teclado: `1`, `2`, `3` eligen pieza; flechas, `Inicio` y `Fin` mueven el foco por el suelo; `Espacio` o `Intro` colocan; `U` deshace; `P` pide una pista.

## Archivos
- `codigo.py`: toda la lógica (reglas, catálogo de 37 piezas, generador con semilla, jugador automático por búsqueda en haz, pistas, estrellas, texto para compartir, estadísticas y racha).
- `script.js`: interfaz y puente con Pyodide; guarda el reto del día y las estadísticas en `localStorage`.
- `index.html` y `style.css`: página y diseño; muestran el código Python y permiten descargarlo.
- `pruebas.py`: pruebas de la lógica (`python pruebas.py`).

## Licencias y originalidad
Colocar piezas en una cuadrícula y despejar líneas completas es una mecánica genérica y de uso libre. El nombre, el tema, el objetivo de líneas en un número fijo de lotes, los nudos de partida, el catálogo de piezas, los textos y el diseño son propios. No se usan imágenes, audio ni código de terceros; todo se dibuja con CSS. La única dependencia externa es Pyodide (MPL 2.0), cargado desde su CDN. El generador pseudoaleatorio es mulberry32 (dominio público), escrito en el propio archivo.

Hecho con ayuda de IA (Claude) como herramienta · Mario Galán Pedrayes.

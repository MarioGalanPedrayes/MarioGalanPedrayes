# PULSO MINERAL — Circuitos bajo tierra

Puzle lógico de conexión de circuitos. Gira los conductos para llevar energía desde la fuente hasta el núcleo de salida y activar todos los relés de cada galería. Supera cinco sectores con redes cada vez más complejas.

## Jugar online

https://MarioGalanPedrayes.github.io/MarioGalanPedrayes/PruebasMCPCHATGPT/juegos/pulso-mineral/

La primera carga necesita conexión a Internet para descargar Pyodide 0.26.0 desde su CDN. La lógica Python se ejecuta dentro del navegador.

## Controles y reglas

- Pulsa o toca un conducto para girarlo 90 grados en sentido horario.
- La fuente y el núcleo de salida son piezas fijas.
- Las piezas iluminadas reciben energía desde la fuente.
- Conecta el núcleo y todos los relés para completar el sector.
- Reinicia el sector para recuperar su disposición inicial.
- La puntuación recompensa resolver el circuito con menos giros.

## Tecnología — Método B: Pyodide

- `codigo.py`: define los mapas, las conexiones entre puertos, el giro de piezas, el recorrido de energía, los relés y la puntuación.
- `index.html`: portada, tablero e instrucciones.
- `style.css`: interfaz adaptable y representación visual de los circuitos.
- `script.js`: carga Pyodide, dibuja las piezas y conecta las acciones.

No necesita servidor propio, base de datos ni servicios externos salvo el CDN de Pyodide. No utiliza `eval()` ni `exec()` ni recoge datos personales.

## Qué se practica

Orientación espacial, reconocimiento de patrones, pensamiento sistémico y resolución de problemas.

## Originalidad

Nombre, reglas, mapas, textos, código e interfaz creados para este proyecto. No utiliza personajes, marcas, música ni recursos gráficos de terceros.

---

Hecho con ayuda de IA (ChatGPT) como herramienta.

Mario Galan Pedrayes  
Técnico en Desarrollo Web y Multiplataforma

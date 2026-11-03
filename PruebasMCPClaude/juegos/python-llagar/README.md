# LLAGAR

Juego incremental (idle) con temática de sidra asturiana. Se empieza recogiendo manzanas a mano y se construye un pomar, un llagar y una sidrería que producen solos. El juego sigue avanzando con la página cerrada.

## Objetivo
Mostrar que un juego incremental completo (economía, mejoras, progreso sin conexión y prestigio) puede tener toda su lógica en Python y publicarse como web estática. Python se ejecuta en el navegador con Pyodide 0.26.0 (se necesita conexión para cargarlo desde su CDN).

## Reglas
- **Recoger:** cada pulsación suma manzanas (también con la barra espaciadora).
- **Edificios:** manzano, cuadrilla, carro, llagar, bodega y sidrería. Coste = base × 1,15^cantidad.
- **Mejoras:** compras únicas que duplican un edificio, mejoran la recogida a mano o dan un bono global. Aparecen al cumplir un requisito.
- **Sin conexión:** al volver se suma lo producido mientras no estabas, con un tope de 8 horas.
- **Nueva cosecha (prestigio):** reinicia manzanas, edificios y mejoras. Da Sellos = raíz cuadrada de (manzanas de la cosecha / 1.000.000). Cada Sello da +20 % de producción permanente.

## Equilibrio
Simulación de una persona activa (3 recogidas por segundo, compra por mejor rentabilidad): primer manzano en ~5 s, 1 M de manzanas en ~34 min sin Sellos, ~24 min con 2 y ~17 min con 5.

## Archivos
- `index.html`: estructura y textos explicativos.
- `style.css`: estilos.
- `script.js`: temporizador, interfaz, guardado en `localStorage` y puente con Pyodide.
- `codigo.py`: toda la lógica.

## Originalidad y licencias
Las mecánicas incrementales son genéricas. El tema, los nombres, los textos y el diseño son propios; no se usan imágenes, sonidos, marcas ni personajes de terceros. El único componente externo es Pyodide, cargado desde su CDN.

Hecho con ayuda de IA (Claude) como herramienta

Mario Galán Pedrayes

Técnico en Desarrollo Web y Multiplataforma

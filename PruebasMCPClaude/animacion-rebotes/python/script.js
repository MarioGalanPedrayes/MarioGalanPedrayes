let pyodideReady = null;
let funcionIniciar = null;
let funcionAvanzar = null;
let animando = false;
let idAnimacion = null;

const ANCHO = 600;
const ALTO = 400;

async function cargarPyodide() {
  if (!pyodideReady) {
    document.getElementById("estado").textContent = "Cargando Python en el navegador (Pyodide)…";
    pyodideReady = await loadPyodide();
    const codigo = document.getElementById("codigoPython").textContent;
    await pyodideReady.runPythonAsync(codigo);
    funcionIniciar = pyodideReady.globals.get("iniciar");
    funcionAvanzar = pyodideReady.globals.get("avanzar");
    document.getElementById("estado").textContent = "";
  }
  return pyodideReady;
}

function dibujar(bolasProxy) {
  const canvas = document.getElementById("lienzo");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, ANCHO, ALTO);

  const bolas = bolasProxy.toJs({ dict_converter: Object.fromEntries });

  bolas.forEach((bola) => {
    ctx.beginPath();
    ctx.arc(bola.x, bola.y, bola.radio, 0, Math.PI * 2);
    ctx.fillStyle = bola.color;
    ctx.fill();
  });
}

function bucleAnimacion() {
  if (!animando) return;
  const bolasProxy = funcionAvanzar(ANCHO, ALTO);
  dibujar(bolasProxy);
  idAnimacion = requestAnimationFrame(bucleAnimacion);
}

async function iniciarAnimacion() {
  const boton = document.getElementById("btnIniciar");
  boton.disabled = true;
  document.getElementById("estado").textContent = "Cargando Python en el navegador (Pyodide)…";

  await cargarPyodide();
  document.getElementById("estado").textContent = "";

  const cantidad = parseInt(document.getElementById("cantidadBolas").value, 10) || 8;
  funcionIniciar(cantidad, ANCHO, ALTO);

  animando = true;
  boton.disabled = false;
  boton.textContent = "Reiniciar";
  bucleAnimacion();
}

function detenerAnimacion() {
  animando = false;
  if (idAnimacion) cancelAnimationFrame(idAnimacion);
}

window.addEventListener("beforeunload", detenerAnimacion);

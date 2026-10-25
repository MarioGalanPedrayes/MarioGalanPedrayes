let pyodide, iniciarPy, avanzarPy;
let corriendo = false, pausado = false, idAnim = null, ultimo = 0;
const $ = (id) => document.getElementById(id);
const W = 480, H = 380, PIVOTE_X = W / 2, PIVOTE_Y = 40;

async function cargar() {
  try {
    pyodide = await loadPyodide();
    const codigo = await (await fetch("codigo.py")).text();
    $("codigoPython").textContent = codigo;
    await pyodide.runPythonAsync(codigo);
    iniciarPy = pyodide.globals.get("iniciar");
    avanzarPy = pyodide.globals.get("avanzar");
    $("estado").textContent = "Python cargado ✔";
    $("btnSoltar").disabled = false;
    $("btnPausa").disabled = false;
    reiniciar();
  } catch (e) {
    $("estado").textContent = "No se pudo cargar Python (¿sin conexión?): " + e;
  }
}

function valores() {
  return [
    parseFloat($("masa").value),
    parseFloat($("longitud").value),
    parseFloat($("angulo").value),
    parseFloat($("roce").value),
  ];
}

function etiquetas() {
  $("vMasa").textContent = $("masa").value + " kg";
  $("vLongitud").textContent = $("longitud").value + " m";
  $("vAngulo").textContent = $("angulo").value + "°";
  $("vRoce").textContent = $("roce").value === "0" ? "sin rozamiento" : $("roce").value;
}

function reiniciar() {
  etiquetas();
  const datos = JSON.parse(iniciarPy(...valores()));
  pintar(datos);
}

function pintar(d) {
  const L = parseFloat($("longitud").value);
  const escala = (H - PIVOTE_Y - 50) / 3; // 3 m es la longitud máxima
  const px = PIVOTE_X + Math.sin(d.theta) * L * escala;
  const py = PIVOTE_Y + Math.cos(d.theta) * L * escala;
  const suelo = PIVOTE_Y + L * escala; // altura del punto más bajo

  const ctx = $("lienzo").getContext("2d");
  ctx.clearRect(0, 0, W, H);

  // Línea de referencia (h = 0) y línea de altura actual
  ctx.strokeStyle = "#2a2d3a"; ctx.setLineDash([6, 6]);
  ctx.beginPath(); ctx.moveTo(30, suelo); ctx.lineTo(W - 30, suelo); ctx.stroke();
  ctx.setLineDash([]);
  ctx.strokeStyle = "#60a5fa"; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(40, py); ctx.lineTo(40, suelo); ctx.stroke();
  ctx.fillStyle = "#60a5fa"; ctx.font = "13px sans-serif";
  ctx.fillText("h = " + d.h.toFixed(2) + " m", 48, (py + suelo) / 2 + 4);

  // Cuerda y soporte
  ctx.strokeStyle = "#9ca3af"; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(PIVOTE_X, PIVOTE_Y); ctx.lineTo(px, py); ctx.stroke();
  ctx.fillStyle = "#9ca3af";
  ctx.fillRect(PIVOTE_X - 40, PIVOTE_Y - 8, 80, 6);

  // Masa: el radio crece un poco con la masa
  const r = 10 + parseFloat($("masa").value) * 3;
  ctx.fillStyle = "#6ee7b7";
  ctx.beginPath(); ctx.arc(px, py, r, 0, Math.PI * 2); ctx.fill();

  // Barras de energía (escala = energía inicial)
  const tope = Math.max(d.e0, 0.0001);
  barra("Ep", d.ep, tope); barra("Ec", d.ec, tope); barra("Et", d.total, tope);
  $("datos").textContent =
    "Velocidad: " + d.v.toFixed(2) + " m/s · Energía inicial: " + d.e0.toFixed(2) + " J";
}

function barra(id, valor, tope) {
  $("b" + id).style.width = Math.min(100, (valor / tope) * 100) + "%";
  $("t" + id).textContent = valor.toFixed(2) + " J";
}

function bucle(ahora) {
  if (!corriendo) return;
  if (!pausado) {
    const dt = Math.min(0.05, (ahora - ultimo) / 1000 || 1 / 60);
    pintar(JSON.parse(avanzarPy(dt, 20)));
  }
  ultimo = ahora;
  idAnim = requestAnimationFrame(bucle);
}

function soltar() {
  cancelAnimationFrame(idAnim);
  reiniciar();
  corriendo = true; pausado = false;
  $("btnPausa").textContent = "Pausa";
  ultimo = performance.now();
  idAnim = requestAnimationFrame(bucle);
}

["masa", "longitud", "angulo", "roce"].forEach((id) =>
  $(id).addEventListener("input", () => {
    etiquetas();
    if (iniciarPy) { corriendo = false; cancelAnimationFrame(idAnim); reiniciar(); }
  })
);
$("btnSoltar").addEventListener("click", soltar);
$("btnPausa").addEventListener("click", () => {
  if (!corriendo) return;
  pausado = !pausado;
  $("btnPausa").textContent = pausado ? "Seguir" : "Pausa";
});
window.addEventListener("beforeunload", () => cancelAnimationFrame(idAnim));

etiquetas();
cargar();

let pyodide, iniciarPy, avanzarPy;
let corriendo = false, pausado = false, idAnim = null, ultimo = 0, terminado = false;
const $ = (id) => document.getElementById(id);
const W = 600, H = 200, ESCALA = 50, SUELO = 150; // 50 px por metro; x=0 m a 50 px
const X0 = 50;

async function cargar() {
  try {
    pyodide = await loadPyodide();
    const codigo = await (await fetch("codigo.py")).text();
    $("codigoPython").textContent = codigo;
    await pyodide.runPythonAsync(codigo);
    iniciarPy = pyodide.globals.get("iniciar");
    avanzarPy = pyodide.globals.get("avanzar");
    $("estado").textContent = "Python cargado ✔";
    $("btnLanzar").disabled = false;
    $("btnPausa").disabled = false;
    preparar();
  } catch (e) {
    $("estado").textContent = "No se pudo cargar Python (¿sin conexión?): " + e;
  }
}

function valores() {
  return ["m1", "v1", "m2", "v2", "e"].map((id) => parseFloat($(id).value));
}

function etiquetas() {
  $("vm1").textContent = $("m1").value + " kg";
  $("vv1").textContent = $("v1").value + " m/s";
  $("vm2").textContent = $("m2").value + " kg";
  $("vv2").textContent = $("v2").value + " m/s";
  const e = parseFloat($("e").value);
  $("ve").textContent = e + (e === 1 ? " (elástico)" : e === 0 ? " (inelástico)" : "");
}

function preparar() {
  etiquetas();
  terminado = false;
  limpiarTabla();
  const d = JSON.parse(iniciarPy(...valores()));
  $("aviso").textContent = d.habra_choque
    ? "Pulsa «Lanzar» para ver el choque."
    : "Con estas velocidades no habrá choque: el carrito de la izquierda no alcanza al de la derecha.";
  pintar(d);
}

function limpiarTabla() {
  ["pa", "pd", "ea", "ed", "v1a", "v1d", "v2a", "v2d"].forEach((id) => ($(id).textContent = "—"));
  $("pc").textContent = "—"; $("ec").textContent = "—";
}

function pintar(d) {
  const ctx = $("lienzo").getContext("2d");
  ctx.clearRect(0, 0, W, H);
  ctx.strokeStyle = "#2a2d3a"; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(0, SUELO); ctx.lineTo(W, SUELO); ctx.stroke();
  dibujarCarro(ctx, d.x1, d.w1, "#6ee7b7", "1", d.v1);
  dibujarCarro(ctx, d.x2, d.w2, "#f59e0b", "2", d.v2);
  $("pc").textContent = d.p.toFixed(2) + " kg·m/s";
  $("ec").textContent = d.ec.toFixed(2) + " J";
}

function dibujarCarro(ctx, x, w, color, nombre, v) {
  const px = X0 + (x - w / 2) * ESCALA, ancho = w * ESCALA, alto = ancho * 0.8 + 10;
  ctx.fillStyle = color;
  ctx.fillRect(px, SUELO - alto, ancho, alto);
  ctx.fillStyle = "#06141f"; ctx.font = "bold 14px sans-serif"; ctx.textAlign = "center";
  ctx.fillText(nombre, px + ancho / 2, SUELO - alto / 2 + 5);
  // flecha de velocidad
  if (Math.abs(v) > 0.01) {
    const cx = px + ancho / 2, largo = v * 14, y = SUELO - alto - 14;
    ctx.strokeStyle = color; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(cx, y); ctx.lineTo(cx + largo, y); ctx.stroke();
    const dir = Math.sign(v);
    ctx.beginPath(); ctx.moveTo(cx + largo, y);
    ctx.lineTo(cx + largo - 7 * dir, y - 5); ctx.lineTo(cx + largo - 7 * dir, y + 5);
    ctx.closePath(); ctx.fillStyle = color; ctx.fill();
  }
}

function tablaChoque(c) {
  $("pa").textContent = c.antes.p.toFixed(2); $("pd").textContent = c.despues.p.toFixed(2);
  $("ea").textContent = c.antes.ec.toFixed(2); $("ed").textContent = c.despues.ec.toFixed(2);
  $("v1a").textContent = c.antes.v1.toFixed(2); $("v1d").textContent = c.despues.v1.toFixed(2);
  $("v2a").textContent = c.antes.v2.toFixed(2); $("v2d").textContent = c.despues.v2.toFixed(2);
  const perdida = c.antes.ec - c.despues.ec;
  $("aviso").textContent = perdida > 0.005
    ? "El momento se conserva, pero se pierden " + perdida.toFixed(2) + " J de energía cinética (deformación y calor)."
    : "El momento y la energía cinética se conservan: choque elástico.";
}

function bucle(ahora) {
  if (!corriendo) return;
  if (!pausado && !terminado) {
    const dt = Math.min(0.05, (ahora - ultimo) / 1000 || 1 / 60);
    const d = JSON.parse(avanzarPy(dt));
    pintar(d);
    if (d.choque) tablaChoque(d.choque);
    if (d.fuera) {
      terminado = true;
      if (!d.choque) $("aviso").textContent = "No ha habido choque.";
    }
  }
  ultimo = ahora;
  idAnim = requestAnimationFrame(bucle);
}

function lanzar() {
  cancelAnimationFrame(idAnim);
  preparar();
  corriendo = true; pausado = false;
  $("btnPausa").textContent = "Pausa";
  ultimo = performance.now();
  idAnim = requestAnimationFrame(bucle);
}

["m1", "v1", "m2", "v2", "e"].forEach((id) =>
  $(id).addEventListener("input", () => {
    etiquetas();
    if (iniciarPy) { corriendo = false; cancelAnimationFrame(idAnim); preparar(); }
  })
);
$("btnLanzar").addEventListener("click", lanzar);
$("btnPausa").addEventListener("click", () => {
  if (!corriendo) return;
  pausado = !pausado;
  $("btnPausa").textContent = pausado ? "Seguir" : "Pausa";
});
window.addEventListener("beforeunload", () => cancelAnimationFrame(idAnim));

etiquetas();
cargar();

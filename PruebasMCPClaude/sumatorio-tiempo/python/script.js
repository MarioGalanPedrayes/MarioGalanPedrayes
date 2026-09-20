let pyodideReady = null;
let contadorFilas = 0;

async function cargarPyodide() {
  if (!pyodideReady) {
    document.getElementById("estado").textContent = "Cargando Python en el navegador (Pyodide)…";
    pyodideReady = await loadPyodide();
    const codigo = document.getElementById("codigoPython").textContent;
    await pyodideReady.runPythonAsync(codigo);
    document.getElementById("estado").textContent = "";
  }
  return pyodideReady;
}

function crearFila() {
  contadorFilas++;
  const id = contadorFilas;
  const contenedor = document.getElementById("filas");

  const fila = document.createElement("div");
  fila.className = "fila-duracion";
  fila.id = `fila-${id}`;

  fila.innerHTML = `
    <input type="number" min="0" value="0" class="campo-h" aria-label="Horas"> h
    <input type="number" min="0" max="59" value="0" class="campo-m" aria-label="Minutos"> m
    <input type="number" min="0" max="59" value="0" class="campo-s" aria-label="Segundos"> s
    <input type="number" min="0" max="999" value="0" class="campo-ms" aria-label="Milisegundos"> ms
    <button type="button" onclick="eliminarFila(${id})" class="btn-eliminar">✕</button>
  `;

  contenedor.appendChild(fila);
}

function eliminarFila(id) {
  const fila = document.getElementById(`fila-${id}`);
  if (fila) fila.remove();
}

function leerFilas() {
  const filas = document.querySelectorAll(".fila-duracion");
  const duraciones = [];
  filas.forEach((fila) => {
    const h = parseInt(fila.querySelector(".campo-h").value, 10) || 0;
    const m = parseInt(fila.querySelector(".campo-m").value, 10) || 0;
    const s = parseInt(fila.querySelector(".campo-s").value, 10) || 0;
    const ms = parseInt(fila.querySelector(".campo-ms").value, 10) || 0;
    duraciones.push([h, m, s, ms]);
  });
  return duraciones;
}

async function calcularTotal() {
  const boton = document.getElementById("btnCalcular");
  const estado = document.getElementById("estado");
  const resultadoEl = document.getElementById("resultado");

  const duraciones = leerFilas();
  if (duraciones.length === 0) {
    resultadoEl.textContent = "Añade al menos una duración.";
    resultadoEl.className = "resultado mal";
    return;
  }

  boton.disabled = true;
  estado.textContent = "Calculando…";
  resultadoEl.textContent = "";

  try {
    const pyodide = await cargarPyodide();
    pyodide.globals.set("duraciones_js", pyodide.toPy(duraciones));
    const resultadoProxy = await pyodide.runPythonAsync("sumar_duraciones(duraciones_js)");
    const r = resultadoProxy.toJs({ dict_converter: Object.fromEntries });

    estado.textContent = "";
    resultadoEl.className = "resultado ok";
    const formateado = `${String(r.horas).padStart(2, "0")}:${String(r.minutos).padStart(2, "0")}:${String(r.segundos).padStart(2, "0")}.${String(r.milisegundos).padStart(3, "0")}`;
    resultadoEl.textContent =
      `Total: ${formateado}  (${r.total_ms} ms · ${r.total_segundos} s)`;
  } catch (err) {
    estado.textContent = "";
    resultadoEl.className = "resultado mal";
    resultadoEl.textContent = "Ha ocurrido un error al calcular.";
    console.error(err);
  } finally {
    boton.disabled = false;
  }
}

window.addEventListener("DOMContentLoaded", () => {
  crearFila();
  crearFila();
  cargarPyodide();
});

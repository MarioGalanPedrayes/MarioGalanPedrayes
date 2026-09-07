let pyodideReady = null;

async function cargarPyodide() {
  if (!pyodideReady) {
    document.getElementById("estado").textContent = "Cargando Python en el navegador (Pyodide)…";
    pyodideReady = await loadPyodide();
    const codigo = document.getElementById("codigoPython").textContent;
    await pyodideReady.runPythonAsync(codigo);
  }
  return pyodideReady;
}

function dibujarTrayectoria(puntos) {
  const canvas = document.getElementById("canvasTrayectoria");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (puntos.length === 0) return;

  const maxX = Math.max(...puntos.map(p => p[0]), 1);
  const maxY = Math.max(...puntos.map(p => p[1]), 1);
  const margen = 30;
  const escalaX = (canvas.width - margen * 2) / maxX;
  const escalaY = (canvas.height - margen * 2) / maxY;

  ctx.strokeStyle = "#60a5fa";
  ctx.lineWidth = 2;
  ctx.beginPath();
  puntos.forEach(([x, y], i) => {
    const px = margen + x * escalaX;
    const py = canvas.height - margen - y * escalaY;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.stroke();

  // Suelo
  ctx.strokeStyle = "#3a3d4a";
  ctx.beginPath();
  ctx.moveTo(0, canvas.height - margen);
  ctx.lineTo(canvas.width, canvas.height - margen);
  ctx.stroke();
}

async function ejecutar() {
  const boton = document.getElementById("btnCalcular");
  const estado = document.getElementById("estado");
  const resultados = document.getElementById("resultados");

  const velocidad = parseFloat(document.getElementById("velInput").value);
  const angulo = parseFloat(document.getElementById("anguloInput").value);

  if (isNaN(velocidad) || velocidad <= 0 || velocidad > 500) {
    estado.textContent = "Escribe una velocidad entre 0 y 500 m/s.";
    return;
  }
  if (isNaN(angulo) || angulo < 0 || angulo > 90) {
    estado.textContent = "Escribe un ángulo entre 0 y 90 grados.";
    return;
  }

  boton.disabled = true;
  estado.textContent = "Calculando…";
  resultados.innerHTML = "";

  try {
    const pyodide = await cargarPyodide();
    pyodide.globals.set("v0_js", velocidad);
    pyodide.globals.set("angulo_js", angulo);

    const resultado = await pyodide.runPythonAsync(`tiro_parabolico(v0_js, angulo_js)`);
    const r = resultado.toJs({ dict_converter: Object.fromEntries });

    const puntosPy = await pyodide.runPythonAsync(`trayectoria(v0_js, angulo_js)`);
    const puntos = puntosPy.toJs();

    estado.textContent = "";
    resultados.innerHTML = `
      <div class="resultado-item"><strong>${r.tiempo_vuelo.toFixed(2)} s</strong><span>Tiempo de vuelo</span></div>
      <div class="resultado-item"><strong>${r.altura_maxima.toFixed(2)} m</strong><span>Altura máxima</span></div>
      <div class="resultado-item"><strong>${r.alcance.toFixed(2)} m</strong><span>Alcance</span></div>
    `;

    dibujarTrayectoria(puntos);
  } catch (err) {
    estado.textContent = "Ha ocurrido un error al ejecutar el código.";
    console.error(err);
  } finally {
    boton.disabled = false;
  }
}

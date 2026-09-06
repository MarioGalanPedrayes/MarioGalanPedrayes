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

async function ejecutar() {
  const boton = document.getElementById("btnCalcular");
  const estado = document.getElementById("estado");
  const salida = document.getElementById("salida");
  const limiteInput = document.getElementById("limiteInput");

  const limite = parseInt(limiteInput.value, 10);

  if (isNaN(limite) || limite < 2) {
    estado.textContent = "Escribe un número entero de 2 o más.";
    salida.textContent = "";
    return;
  }

  if (limite > 100000) {
    estado.textContent = "Por seguridad, límite máximo: 100000.";
    salida.textContent = "";
    return;
  }

  boton.disabled = true;
  estado.textContent = "Calculando…";
  salida.textContent = "";

  try {
    const pyodide = await cargarPyodide();
    pyodide.globals.set("limite_js", limite);
    const primos = await pyodide.runPythonAsync(`criba_eratostenes(limite_js)`);
    const lista = primos.toJs();

    estado.textContent = `Hay ${lista.length} números primos hasta ${limite}:`;
    salida.textContent = lista.join(", ");
  } catch (err) {
    estado.textContent = "Ha ocurrido un error al ejecutar el código.";
    console.error(err);
  } finally {
    boton.disabled = false;
  }
}

let pyodideReady = null;

const NOMBRES_CATEGORIA = {
  longitud: "Longitud",
  peso: "Peso",
  temperatura: "Temperatura",
};

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

async function cambiarCategoria() {
  const pyodide = await cargarPyodide();
  const categoria = document.getElementById("categoriaSelect").value;

  const unidadesProxy = await pyodide.runPythonAsync(`unidades_disponibles("${categoria}")`);
  const unidades = unidadesProxy.toJs();

  const desdeSelect = document.getElementById("desdeSelect");
  const hastaSelect = document.getElementById("hastaSelect");
  desdeSelect.innerHTML = "";
  hastaSelect.innerHTML = "";

  unidades.forEach((u, i) => {
    const opt1 = document.createElement("option");
    opt1.value = u;
    opt1.textContent = u;
    desdeSelect.appendChild(opt1);

    const opt2 = document.createElement("option");
    opt2.value = u;
    opt2.textContent = u;
    hastaSelect.appendChild(opt2);
  });

  if (unidades.length > 1) {
    hastaSelect.selectedIndex = 1;
  }

  document.getElementById("resultado").textContent = "";
}

async function convertir() {
  const boton = document.getElementById("btnConvertir");
  const estado = document.getElementById("estado");
  const resultadoEl = document.getElementById("resultado");

  const categoria = document.getElementById("categoriaSelect").value;
  const desde = document.getElementById("desdeSelect").value;
  const hasta = document.getElementById("hastaSelect").value;
  const valorTexto = document.getElementById("valorInput").value.replace(",", ".");
  const valor = parseFloat(valorTexto);

  if (isNaN(valor)) {
    resultadoEl.textContent = "Escribe un número válido.";
    resultadoEl.className = "resultado mal";
    return;
  }

  boton.disabled = true;
  estado.textContent = "Calculando…";
  resultadoEl.textContent = "";

  try {
    const pyodide = await cargarPyodide();
    const resultado = await pyodide.runPythonAsync(
      `convertir("${categoria}", ${valor}, "${desde}", "${hasta}")`
    );
    estado.textContent = "";
    resultadoEl.className = "resultado ok";
    resultadoEl.textContent = `${valor} ${desde} = ${resultado} ${hasta} (${NOMBRES_CATEGORIA[categoria]})`;
  } catch (err) {
    estado.textContent = "";
    resultadoEl.className = "resultado mal";
    resultadoEl.textContent = "Ha ocurrido un error al convertir.";
    console.error(err);
  } finally {
    boton.disabled = false;
  }
}

window.addEventListener("DOMContentLoaded", () => {
  cargarPyodide().then(cambiarCategoria);
});

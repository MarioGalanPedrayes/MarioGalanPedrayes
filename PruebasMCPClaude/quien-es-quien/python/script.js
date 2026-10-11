const boton = document.getElementById("jugar");
const salida = document.getElementById("salida");
const bloqueCodigo = document.getElementById("codigo");

let pyodide = null;
let codigo = "";

async function iniciar() {
  try {
    const resp = await fetch("codigo.py");
    codigo = await resp.text();
    bloqueCodigo.textContent = codigo;
    pyodide = await loadPyodide();
    boton.disabled = false;
    boton.textContent = "Jugar";
  } catch (e) {
    boton.textContent = "No se pudo cargar Python";
    salida.textContent = "Error al cargar: " + e;
  }
}

async function jugar() {
  boton.disabled = true;
  let texto = "";
  pyodide.setStdout({ batched: (s) => { texto += s + "\n"; } });
  try {
    await pyodide.runPythonAsync(codigo);
    salida.textContent = texto;
  } catch (e) {
    salida.textContent = "Error: " + e;
  }
  boton.disabled = false;
  boton.textContent = "Jugar otra vez";
}

boton.addEventListener("click", jugar);
iniciar();

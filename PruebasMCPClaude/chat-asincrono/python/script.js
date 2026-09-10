let pyodideReady = null;

const COLORES = {
  Ana: "#6ee7b7",
  Bruno: "#60a5fa",
  Clara: "#f0abfc",
};

// Esta función la llama Python (vía Pyodide) cada vez que "llega" un
// mensaje, en tiempo real, mientras las corrutinas siguen en marcha.
function agregarMensajeJS(usuario, texto, hora) {
  const log = document.getElementById("chatLog");
  const linea = document.createElement("div");
  linea.className = "mensaje";
  linea.style.borderLeftColor = COLORES[usuario] || "#9ca3af";

  const cabecera = document.createElement("span");
  cabecera.className = "mensaje-cabecera";
  cabecera.style.color = COLORES[usuario] || "#9ca3af";
  cabecera.textContent = `${hora} · ${usuario}`;

  const cuerpo = document.createElement("div");
  cuerpo.textContent = texto;

  linea.appendChild(cabecera);
  linea.appendChild(cuerpo);
  log.appendChild(linea);
  log.scrollTop = log.scrollHeight;
}
window.agregarMensajeJS = agregarMensajeJS;

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

async function iniciarChat() {
  const boton = document.getElementById("btnIniciar");
  const estado = document.getElementById("estado");
  const log = document.getElementById("chatLog");

  boton.disabled = true;
  log.innerHTML = "";
  estado.textContent = "Cargando Python en el navegador (Pyodide)…";

  try {
    const pyodide = await cargarPyodide();
    estado.textContent = "Chateando…";
    await pyodide.runPythonAsync("await iniciar_chat()");
    estado.textContent = "Conversación terminada.";
  } catch (err) {
    estado.textContent = "Ha ocurrido un error al iniciar el chat.";
    console.error(err);
  } finally {
    boton.disabled = false;
  }
}

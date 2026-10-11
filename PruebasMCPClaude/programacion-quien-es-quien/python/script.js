let pyodide, py, datos, descartados = new Set(), terminado = false;
const $ = (id) => document.getElementById(id);

async function iniciar() {
  try {
    pyodide = await loadPyodide();
    const codigo = await (await fetch("codigo.py")).text();
    await pyodide.runPythonAsync(codigo);
    py = {
      nuevo: pyodide.globals.get("nuevo_juego"),
      tablero: pyodide.globals.get("tablero"),
      preguntar: pyodide.globals.get("preguntar"),
      adivinar: pyodide.globals.get("adivinar"),
    };
    $("estado").textContent = "Python cargado ✔";
    empezar();
  } catch (e) {
    $("estado").textContent = "No se pudo cargar Python (¿sin conexión?): " + e;
  }
}

function empezar() {
  py.nuevo();
  datos = JSON.parse(py.tablero());
  descartados = new Set(); terminado = false;
  $("log").innerHTML = ""; $("msg").textContent = "He elegido un lenguaje en secreto. ¡Pregunta!";
  $("btnPreguntar").disabled = false;
  const sel = $("pregunta");
  sel.innerHTML = "";
  for (const [clave, vals] of Object.entries(datos.opciones))
    for (const v of vals) {
      const o = document.createElement("option");
      o.value = clave + "|" + v;
      o.textContent = datos.etiquetas[clave] + " " + v + "?";
      sel.appendChild(o);
    }
  pintar();
}

function pintar() {
  const g = $("tablero"); g.innerHTML = "";
  for (const [nombre, d] of Object.entries(datos.personajes)) {
    const b = document.createElement("button");
    b.className = "card" + (descartados.has(nombre) ? " out" : "");
    b.innerHTML = `<span class="n"></span><span class="s">${d.epoca}</span>`;
    b.querySelector(".n").textContent = nombre;
    b.onclick = () => adivinar(nombre);
    g.appendChild(b);
  }
}

function preguntar() {
  if (terminado) return;
  const [clave, valor] = $("pregunta").value.split("|");
  const r = py.preguntar(clave, valor);
  const li = document.createElement("li");
  li.innerHTML = `${datos.etiquetas[clave]} <b></b>? → <span class="${r ? "si" : "no"}">${r ? "SÍ" : "NO"}</span>`;
  li.querySelector("b").textContent = valor;
  $("log").appendChild(li);
  for (const [n, d] of Object.entries(datos.personajes))
    if ((d[clave] === valor) !== r) descartados.add(n);
  pintar();
}

function adivinar(nombre) {
  if (terminado) return;
  const r = JSON.parse(py.adivinar(nombre));
  terminado = true; $("btnPreguntar").disabled = true;
  $("msg").textContent = r.acierto
    ? `🎉 ¡Correcto! Era ${r.secreto}. Lo has resuelto con ${r.preguntas} pregunta(s).`
    : `❌ No era ${nombre}: el lenguaje secreto era ${r.secreto}.`;
}

$("btnPreguntar").onclick = preguntar;
$("btnNuevo").onclick = () => py && empezar();
fetch("codigo.py").then(r => r.text()).then(t => { $("codigoPython").textContent = t; });
iniciar();

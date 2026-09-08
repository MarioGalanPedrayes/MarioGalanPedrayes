let pyodideReady = null;
let indiceActual = 0;
let aciertos = 0;
let totalPreguntas = 0;

async function cargarPyodide() {
  if (!pyodideReady) {
    document.getElementById("estado").textContent = "Cargando Python en el navegador (Pyodide)…";
    pyodideReady = await loadPyodide();
    const codigo = document.getElementById("codigoPython").textContent;
    await pyodideReady.runPythonAsync(codigo);
  }
  return pyodideReady;
}

function pyToJs(proxy) {
  return proxy.toJs({ dict_converter: Object.fromEntries });
}

async function iniciarQuiz() {
  const boton = document.getElementById("btnEmpezar");
  const estado = document.getElementById("estado");
  boton.disabled = true;
  estado.textContent = "Cargando Python en el navegador (Pyodide)…";

  try {
    const pyodide = await cargarPyodide();
    totalPreguntas = await pyodide.runPythonAsync("iniciar_quiz()");
    indiceActual = 0;
    aciertos = 0;

    document.getElementById("intro").style.display = "none";
    document.getElementById("quiz-box").style.display = "block";
    document.getElementById("final-box").style.display = "none";
    estado.textContent = "";

    await mostrarPregunta();
  } catch (err) {
    estado.textContent = "Ha ocurrido un error al cargar Python.";
    console.error(err);
  } finally {
    boton.disabled = false;
  }
}

async function mostrarPregunta() {
  const pyodide = await cargarPyodide();
  const preguntaProxy = await pyodide.runPythonAsync(`pregunta_actual(${indiceActual})`);
  const pregunta = pyToJs(preguntaProxy);

  document.getElementById("progreso").textContent =
    `Pregunta ${indiceActual + 1}/${totalPreguntas}`;
  document.getElementById("enunciado").textContent = pregunta.enunciado;
  document.getElementById("feedback").textContent = "";
  document.getElementById("feedback").className = "resultado";

  const opcionesDiv = document.getElementById("opciones");
  opcionesDiv.innerHTML = "";
  pregunta.opciones.forEach((texto, i) => {
    const btn = document.createElement("button");
    btn.textContent = texto;
    btn.className = "opcion-btn";
    btn.onclick = () => responder(i);
    opcionesDiv.appendChild(btn);
  });

  document.getElementById("btnSiguiente").style.display = "none";
}

async function responder(indiceOpcion) {
  const pyodide = await cargarPyodide();

  document.querySelectorAll(".opcion-btn").forEach(btn => btn.disabled = true);

  const resultadoProxy = await pyodide.runPythonAsync(
    `comprobar_respuesta(${indiceActual}, ${indiceOpcion})`
  );
  const resultado = pyToJs(resultadoProxy);

  const feedback = document.getElementById("feedback");
  if (resultado.correcta) {
    feedback.textContent = "¡Correcto!";
    feedback.className = "resultado ok";
    aciertos++;
  } else {
    feedback.textContent = `Incorrecto. La respuesta correcta era: ${resultado.respuesta_correcta}`;
    feedback.className = "resultado mal";
  }

  document.getElementById("btnSiguiente").style.display = "inline-block";
}

async function siguientePregunta() {
  indiceActual++;
  if (indiceActual >= totalPreguntas) {
    await mostrarFinal();
  } else {
    await mostrarPregunta();
  }
}

async function mostrarFinal() {
  const pyodide = await cargarPyodide();
  const mensaje = await pyodide.runPythonAsync(`mensaje_final(${aciertos}, ${totalPreguntas})`);

  document.getElementById("quiz-box").style.display = "none";
  document.getElementById("final-box").style.display = "block";
  document.getElementById("resultado-final").textContent =
    `Aciertos: ${aciertos} de ${totalPreguntas}`;
  document.getElementById("mensaje-final").textContent = mensaje;
}

function reiniciar() {
  document.getElementById("final-box").style.display = "none";
  document.getElementById("intro").style.display = "block";
}

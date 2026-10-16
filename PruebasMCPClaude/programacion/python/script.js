let pyodide, jugarPy, reiniciarPy;
const $ = (id) => document.getElementById(id);
const ICONOS = { piedra: "✊", papel: "✋", tijeras: "✌️" };

async function iniciar() {
  try {
    pyodide = await loadPyodide();
    const codigo = await (await fetch("codigo.py")).text();
    $("codigoPython").textContent = codigo;
    await pyodide.runPythonAsync(codigo);
    jugarPy = pyodide.globals.get("jugar");
    reiniciarPy = pyodide.globals.get("reiniciar");
    $("estado").textContent = "Python cargado ✔";
    document.querySelectorAll(".opcion").forEach((b) => (b.disabled = false));
    $("btnReiniciar").disabled = false;
  } catch (e) {
    $("estado").textContent = "No se pudo cargar Python (¿sin conexión?): " + e;
  }
}

function jugar(eleccion) {
  const r = JSON.parse(jugarPy(eleccion));
  if (r.error) { $("msg").textContent = r.error; return; }
  const texto = {
    jugador: "¡Ganas esta ronda!",
    ordenador: "Gana el ordenador.",
    empate: "Empate.",
  }[r.ganador];
  $("jugadas").textContent = ICONOS[r.jugador] + "  vs  " + ICONOS[r.ordenador];
  $("msg").textContent = "Tú: " + r.jugador + " · Ordenador: " + r.ordenador + ". " + texto;
  pintarMarcador(r.marcador);
}

function pintarMarcador(m) {
  $("mJugador").textContent = m.jugador;
  $("mOrdenador").textContent = m.ordenador;
  $("mEmpates").textContent = m.empates;
}

document.querySelectorAll(".opcion").forEach((b) =>
  b.addEventListener("click", () => jugar(b.dataset.op))
);
$("btnReiniciar").addEventListener("click", () => {
  pintarMarcador(JSON.parse(reiniciarPy()));
  $("jugadas").textContent = "";
  $("msg").textContent = "Marcador a cero. ¡Elige una jugada!";
});

iniciar();

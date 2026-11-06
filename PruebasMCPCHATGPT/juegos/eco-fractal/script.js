const board = document.querySelector("#board");
const statusText = document.querySelector("#status");
const levelText = document.querySelector("#level");
const movesText = document.querySelector("#moves");
const nextBtn = document.querySelector("#next");
const restartBtn = document.querySelector("#restart");
const pyStatus = document.querySelector("#py-status");
let pyodide, state;

async function boot() {
  try {
    pyStatus.textContent = "Preparando el núcleo Python…";
    pyodide = await loadPyodide();
    const response = await fetch("codigo.py");
    if (!response.ok) throw new Error("No se pudo cargar codigo.py");
    await pyodide.runPythonAsync(await response.text());
    state = JSON.parse(pyodide.globals.get("start_game")());
    pyStatus.textContent = "Núcleo activo · Python + Pyodide";
    render();
  } catch (error) {
    pyStatus.textContent = "No se pudo iniciar: " + error.message;
    statusText.textContent = "Comprueba la conexión y recarga la página.";
  }
}

function render() {
  if (state.complete) {
    board.innerHTML = '<div class="complete">✦<br><strong>SEÑAL RESTAURADA</strong><p>Los cinco sectores vuelven a emitir.</p></div>';
    statusText.textContent = state.message;
    levelText.textContent = "5 / 5";
    nextBtn.hidden = true;
    return;
  }
  const width = 8, height = 8;
  board.innerHTML = "";
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const cell = document.createElement("div");
      cell.className = "cell";
      const pos = [x, y];
      if (state.walls.some(p => p[0] === x && p[1] === y)) cell.classList.add("wall");
      else if (state.player[0] === x && state.player[1] === y) {
        cell.classList.add("player"); cell.textContent = "◈";
      } else if (state.crystals.some(p => p[0] === x && p[1] === y)) {
        cell.classList.add("crystal"); cell.textContent = "✧";
      } else if (state.exit[0] === x && state.exit[1] === y) {
        cell.classList.add("exit"); cell.textContent = "⌂";
      }
      board.appendChild(cell);
    }
  }
  levelText.textContent = (state.level + 1) + " / 5";
  movesText.textContent = state.moves;
  statusText.textContent = state.message;
  nextBtn.hidden = !state.won;
}

function act(direction) {
  if (!pyodide || !state || state.won) return;
  state = JSON.parse(pyodide.globals.get("move_player")(JSON.stringify(state), direction));
  render();
}
document.querySelectorAll("[data-dir]").forEach(btn => btn.addEventListener("click", () => act(btn.dataset.dir)));
document.addEventListener("keydown", event => {
  const keys = {ArrowUp:"up", w:"up", ArrowDown:"down", s:"down", ArrowLeft:"left", a:"left", ArrowRight:"right", d:"right"};
  const dir = keys[event.key];
  if (dir) { event.preventDefault(); act(dir); }
});
restartBtn.addEventListener("click", () => {
  if (!pyodide || !state) return;
  state = JSON.parse(pyodide.globals.get("restart_level")(JSON.stringify(state)));
  nextBtn.hidden = true; render();
});
nextBtn.addEventListener("click", () => {
  if (!pyodide || !state) return;
  state = JSON.parse(pyodide.globals.get("next_level")(JSON.stringify(state)));
  render();
});
boot();

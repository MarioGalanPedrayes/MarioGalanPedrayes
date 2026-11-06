const handNode = document.getElementById('hand');
const logNode = document.getElementById('battle-log');
const endButton = document.getElementById('end-turn');
let pyodide = null, state = null, busy = false;

function updateView(next) {
  state = next;
  document.getElementById('hero-hp-label').textContent = next.hero_hp + ' / ' + next.hero_max;
  document.getElementById('enemy-hp-label').textContent = next.enemy_hp + ' / ' + next.enemy_max;
  document.getElementById('hero-hp-bar').style.width = (100 * next.hero_hp / next.hero_max) + '%';
  document.getElementById('enemy-hp-bar').style.width = (100 * next.enemy_hp / next.enemy_max) + '%';
  document.getElementById('block-value').textContent = next.block;
  document.getElementById('energy-value').textContent = next.energy;
  document.getElementById('energy-big').textContent = String(next.energy).padStart(2, '0');
  document.getElementById('intent-value').textContent = next.intent;
  document.getElementById('turn-label').textContent = 'RONDA ' + String(next.turn).padStart(2, '0');
  logNode.textContent = next.event || 'Elige una carta.';
  handNode.replaceChildren();
  next.hand_cards.forEach((card, index) => {
    const button = document.createElement('button');
    button.className = 'card ' + card.kind;
    button.type = 'button';
    button.disabled = busy || next.status !== 'playing' || next.energy < card.cost;
    button.innerHTML = '<span class="card-top"><span>' + card.kind.toUpperCase() + '</span><b class="card-cost">' + card.cost + '</b></span><span class="card-symbol">' + card.symbol + '</span><span class="card-name"></span><span class="card-desc"></span><span class="card-key">JUGAR · ' + (index + 1) + '</span>';
    button.querySelector('.card-name').textContent = card.name;
    button.querySelector('.card-desc').textContent = card.text;
    button.addEventListener('click', () => play(index));
    handNode.append(button);
  });
  endButton.disabled = busy || next.status !== 'playing';
  if (next.status === 'won' || next.status === 'lost') {
    endButton.disabled = false;
    endButton.textContent = next.status === 'won' ? 'VOLVER A JUGAR ↻' : 'INTENTAR DE NUEVO ↻';
    endButton.onclick = restart;
  } else {
    endButton.textContent = 'TERMINAR TURNO ↗';
    endButton.onclick = finishTurn;
  }
}

function play(index) {
  if (!state || busy) return;
  busy = true;
  const raw = pyodide.globals.get('play_card')(JSON.stringify(state), index);
  updateView(JSON.parse(raw));
  busy = false;
  updateView(state);
}

function finishTurn() {
  if (!state || busy) return;
  if (state.status !== 'playing') return restart();
  busy = true;
  endButton.disabled = true;
  const raw = pyodide.globals.get('end_turn')(JSON.stringify(state));
  updateView(JSON.parse(raw));
  busy = false;
  updateView(state);
}

function restart() {
  const raw = pyodide.globals.get('start_game')();
  updateView(JSON.parse(raw));
}

async function boot() {
  try {
    const response = await fetch('codigo.py');
    const source = await response.text();
    document.getElementById('python-source').textContent = source;
    pyodide = await loadPyodide();
    await pyodide.runPythonAsync(source);
    restart();
  } catch (error) {
    handNode.textContent = 'No se pudo iniciar Python. Comprueba la conexión y recarga la página.';
    logNode.textContent = 'Error al cargar Pyodide: ' + error.message;
  }
}

document.addEventListener('keydown', (event) => {
  if (!state || busy || event.repeat) return;
  if (/^[1-5]$/.test(event.key)) play(Number(event.key) - 1);
  if (event.key === 'Enter') finishTurn();
});
boot();

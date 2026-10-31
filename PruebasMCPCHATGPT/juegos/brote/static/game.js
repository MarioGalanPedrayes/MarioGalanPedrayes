const $ = (id) => document.getElementById(id);
let game = null;
let selectedPlot = 0;
let selectedSeed = 'luna';
let toastTimer;
const plantInfo = {
  luna: { name: 'Flor de luna', emoji: '🌙' },
  amber: { name: 'Caléndula ámbar', emoji: '🌼' },
  fern: { name: 'Helecho susurrante', emoji: '🌿' }
};

async function api(path, body) {
  const response = await fetch(path, {
    method: body ? 'POST' : 'GET',
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined
  });
  const result = await response.json();
  if (!response.ok || result.ok === false) throw new Error(result.error || 'No se ha podido completar la acción.');
  return result.state || result;
}

function notify(message) {
  const toast = $('toast');
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2500);
}

async function act(action, data = {}) {
  try {
    game = await api('/api/action', { action, data });
    render();
  } catch (error) {
    notify(error.message);
  }
}

function render() {
  if (!game) return;
  $('day-label').textContent = `DÍA ${game.day}`;
  $('weather-label').textContent = game.weather;
  $('dew').textContent = game.resources.dew;
  $('seeds').textContent = game.resources.seeds;
  $('wood').textContent = game.resources.wood;
  $('petals').textContent = game.resources.petals;
  $('energy-label').textContent = `${game.energy} / ${game.max_energy}`;
  $('energy-fill').style.width = `${100 * game.energy / game.max_energy}%`;
  $('weather-note').textContent = ({ 'Brisa': 'Una brisa recorre las hojas', 'Llovizna': 'La lluvia acaricia la tierra', 'Sol suave': 'El sol calienta el claro', 'Niebla luminosa': 'La niebla trae calma' })[game.weather] || 'El claro respira';

  const grid = $('garden-grid');
  grid.innerHTML = '';
  game.plots.forEach((plot, index) => {
    const button = document.createElement('button');
    button.className = `plot ${plot ? '' : 'empty'} ${selectedPlot === index ? 'selected' : ''}`;
    button.type = 'button';
    button.setAttribute('aria-label', plot ? `${plantInfo[plot.kind].name}, parcela ${index + 1}` : `Parcela vacía ${index + 1}`);
    if (plot) {
      const emoji = plot.grown ? '🌸' : plantInfo[plot.kind].emoji;
      button.innerHTML = `<span class="plant-emoji">${emoji}</span><span class="plot-caption">${plot.grown ? 'LISTA' : `${plot.days_left} DÍA(S)`}</span>${plot.grown ? '<span class="ready">✦</span>' : ''}`;
    }
    button.addEventListener('click', () => { selectedPlot = index; render(); });
    grid.appendChild(button);
  });

  const chosen = game.plots[selectedPlot];
  $('plot-hint').textContent = chosen ? (chosen.grown ? '¡Ha florecido! Ya puedes recoger tu cosecha.' : chosen.watered ? 'Esta planta ya ha recibido agua hoy.' : 'Tu brote está creciendo. Puedes regarlo para acelerar el proceso.') : `Parcela ${selectedPlot + 1}: un pequeño espacio listo para una nueva vida.`;
  $('plant-button').disabled = !!chosen || game.energy < 1;
  $('water-button').disabled = !chosen || chosen.grown || chosen.watered || game.energy < 1 || game.resources.dew < 1;
  $('harvest-button').disabled = !chosen || !chosen.grown;
  $('gather-button').disabled = game.energy < 1;
  $('explore-button').disabled = game.energy < 2;
  $('build-button').disabled = game.energy < 2 || game.shelter >= 3;

  const mission = game.mission;
  $('mission-text').textContent = mission.text;
  $('mission-count').textContent = `${Math.min(mission.progress, mission.target)} / ${mission.target}`;
  $('mission-fill').style.width = `${Math.min(100, 100 * mission.progress / mission.target)}%`;
  $('mission-status').textContent = mission.done ? 'COMPLETADO' : 'EN CURSO';
  $('shelter-count').textContent = `${game.shelter} refugios · 3 madera + 2 pétalos`;
  [...$('shelter-dots').children].forEach((dot, i) => dot.classList.toggle('active', i < game.shelter));

  $('visitor-count').textContent = `${game.creatures.length} / 4`;
  const visitors = $('visitor-list');
  visitors.innerHTML = '';
  if (!game.creatures.length) {
    const empty = document.createElement('p'); empty.className = 'empty-visitors';
    empty.textContent = 'Todavía no hay huellas. La naturaleza tiene su propio ritmo.'; visitors.appendChild(empty);
  } else {
    game.creatures.forEach(creature => {
      const item = document.createElement('div'); item.className = 'visitor';
      item.innerHTML = `<span class="visitor-emoji">${creature.emoji}</span><span><b>${creature.name}</b><small>${creature.hint}</small></span>`;
      visitors.appendChild(item);
    });
  }

  $('journal-list').innerHTML = '';
  game.log.slice(0, 4).forEach(entry => {
    const item = document.createElement('div'); item.className = 'journal-entry'; item.textContent = entry;
    $('journal-list').appendChild(item);
  });
  $('score').textContent = game.score;
}

$('plant-button').addEventListener('click', () => act('plant', { plot: selectedPlot, kind: selectedSeed }));
$('water-button').addEventListener('click', () => act('water', { plot: selectedPlot }));
$('harvest-button').addEventListener('click', () => act('harvest', { plot: selectedPlot }));
$('gather-button').addEventListener('click', () => act('gather'));
$('explore-button').addEventListener('click', () => act('explore'));
$('build-button').addEventListener('click', () => act('build'));
$('end-day-button').addEventListener('click', () => act('end_day'));
document.querySelectorAll('.seed-choice').forEach(button => button.addEventListener('click', () => {
  selectedSeed = button.dataset.kind;
  document.querySelectorAll('.seed-choice').forEach(item => item.classList.toggle('selected', item === button));
}));
$('help-button').addEventListener('click', () => $('help-dialog').showModal());
$('close-help').addEventListener('click', () => $('help-dialog').close());
$('got-it').addEventListener('click', () => $('help-dialog').close());
$('reset-button').addEventListener('click', async () => {
  if (!window.confirm('¿Seguro que quieres empezar una partida nueva? Se reiniciará tu progreso actual.')) return;
  try { game = await api('/api/reset', {}); selectedPlot = 0; render(); notify('El claro vuelve a empezar. ¡A cuidarlo!'); }
  catch (error) { notify(error.message); }
});

api('/api/state').then(state => { game = state; render(); }).catch(() => notify('No se ha podido cargar la partida. Recarga la página.'));

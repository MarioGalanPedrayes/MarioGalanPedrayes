(() => {
'use strict';
const $=id=>document.getElementById(id);
let py=null,state=null;
const keyMap={ArrowUp:'up',w:'up',W:'up',ArrowRight:'right',d:'right',D:'right',ArrowDown:'down',s:'down',S:'down',ArrowLeft:'left',a:'left',A:'left'};
function invoke(name,...args){const fn=py.globals.get(name);try{return JSON.parse(fn(...args))}finally{fn.destroy()}}
function score(n){return String(n).padStart(5,'0')}
function render(){
 if(!state)return;
 $('level-tag').textContent=String(state.level+1).padStart(2,'0')+' / 05';
 $('map-number').textContent='· '+String(state.level+1).padStart(2,'0');
 $('score').textContent=score(state.score);$('fuel').textContent=state.fuel;
 $('hull').textContent='♥ '.repeat(Math.max(0,state.hull))+'♡ '.repeat(Math.max(0,3-state.hull));
 $('buoys').textContent=state.buoys_collected+' / '+state.buoy_total;
 $('level-name').textContent=state.level_name;$('brief').textContent=state.brief;
 $('tide').textContent=state.phase_name;$('tide-title').textContent=state.phase_name.toLowerCase().replace(/^./,c=>c.toUpperCase());
 $('tide-symbol').textContent=state.current_arrows[state.phase];
 $('objective-buoys').textContent=state.buoys_collected+' de '+state.buoy_total+' muestras';
 $('objective-check').textContent=state.buoys_collected===state.buoy_total?'✓':'○';
 $('objective-exit').textContent=state.won||state.finished?'✓':'○';
 $('log').textContent=state.log;
 const grid=$('map-grid');grid.replaceChildren();
 for(let y=0;y<state.size;y++)for(let x=0;x<state.size;x++){
   const cell=state.board[y][x],tile=document.createElement('div');
   tile.className='tile '+cell.kind;
   const symbols={reef:'✕',current:cell.arrow,buoy:'●',lighthouse:'⌂',dock:'⚓',sea:''};
   tile.textContent=symbols[cell.kind]||'';
   if(x===state.x&&y===state.y){tile.className='tile boat';tile.textContent='▲';tile.setAttribute('aria-label','Tu barco');}
   else tile.setAttribute('aria-label',cell.kind);
   grid.append(tile);
 }
 const msg=$('message');msg.className='message'+(state.lost?' error':state.won||state.finished?' success':'');msg.querySelector('span').textContent=state.message;
 const stopped=state.lost||state.won||state.finished;
 document.querySelectorAll('[data-action]:not(#result-button)').forEach(b=>b.disabled=stopped);
 $('restart').disabled=state.finished;
 $('result').hidden=true;
 if(state.lost)result('!','Expedición interrumpida','El barco no puede continuar. Reinicia el mapa para intentarlo de nuevo.','Reintentar mapa ↺','restart');
 else if(state.won&&state.level<state.total_levels-1)result('✓','¡Mapa cartografiado!','Boyas recuperadas y faro alcanzado. El siguiente sector espera.','Siguiente mapa →','next');
 else if(state.won)result('★','¡Archipiélago cartografiado!','Has completado los cinco sectores. La expedición científica es un éxito.','Nueva expedición ↻','new');
 else if(state.finished)result('★','Expedición completada','Tu atlas del archipiélago está terminado.','Nueva expedición ↻','new');
}
function result(icon,title,copy,label,action){$('result').hidden=false;$('result-icon').textContent=icon;$('result-title').textContent=title;$('result-text').textContent=copy;$('result-button').textContent=label;$('result-button').dataset.action=action;$('result-button').disabled=false;}
function update(next){state=next;render()}
function act(action){if(!py||!state||state.lost||state.won||state.finished)return;update(invoke('act_json',action));}
document.querySelectorAll('[data-action]').forEach(b=>b.addEventListener('click',()=>{if(b.dataset.action==='anchor')act('anchor');else act(b.dataset.action)}));
$('restart').addEventListener('click',()=>{if(state&&!state.finished)update(invoke('restart_level_json'))});
$('result-button').addEventListener('click',()=>{const a=$('result-button').dataset.action;if(a==='restart')update(invoke('restart_level_json'));if(a==='next')update(invoke('next_level_json'));if(a==='new')update(invoke('new_game_json'))});
$('help').addEventListener('click',()=>$('help-dialog').showModal());$('close-help').addEventListener('click',()=>$('help-dialog').close());
document.addEventListener('keydown',e=>{if($('help-dialog').open){if(e.key==='Escape')$('help-dialog').close();return;}const action=keyMap[e.key];if(action){e.preventDefault();act(action)}else if(e.key===' '){e.preventDefault();act('anchor')}});
async function boot(){
 try{$('loading-message').textContent='Descargando Pyodide…';py=await loadPyodide();$('loading-message').textContent='Cargando las reglas de navegación…';const r=await fetch('./codigo.py',{cache:'no-store'});if(!r.ok)throw new Error('No se pudo descargar codigo.py ('+r.status+').');const source=await r.text();$('python-source').textContent=source;await py.runPythonAsync(source);update(invoke('new_game_json'));$('loading').classList.add('done');setTimeout(()=>$('loading').remove(),350);}
 catch(error){$('loading').querySelector('strong').textContent='No se pudo iniciar la expedición';$('loading-message').textContent=error.message;console.error(error);}
}
boot();
})();
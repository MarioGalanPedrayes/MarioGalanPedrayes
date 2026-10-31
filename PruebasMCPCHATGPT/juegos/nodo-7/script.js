(() => {
'use strict';
const $=id=>document.getElementById(id), BEST_KEY='nodo7-record-v1';
let pyodide=null,state=null,best=0;
function readBest(){try{best=Number(localStorage.getItem(BEST_KEY)||0)||0}catch(_){best=0}}
function saveBest(){if(state&&state.score>best){best=state.score;try{localStorage.setItem(BEST_KEY,String(best))}catch(_){}}}
function callPython(name,...args){const fn=pyodide.globals.get(name);try{return JSON.parse(fn(...args))}finally{fn.destroy()}}
function setText(id,value){$(id).textContent=value}
function formatScore(value){return String(value).padStart(5,'0')}
function toast(message){const el=$('toast');el.textContent=message;el.classList.add('show');window.setTimeout(()=>el.classList.remove('show'),2200)}
function showResult(symbol,title,copy,button,action){$('result-panel').hidden=false;setText('result-symbol',symbol);setText('result-title',title);setText('result-copy',copy);setText('result-button',button);$('result-button').dataset.action=action}
function hideResult(){$('result-panel').hidden=true}
function render(){
 if(!state)return;saveBest();
 setText('stage-label',state.game_finished?'PROTOCOLO COMPLETADO':'EXPEDIENTE '+String(state.stage_number).padStart(2,'0')+' / 06');
 setText('score',formatScore(state.score));setText('best-score',formatScore(best));setText('streak','×'+state.streak);setText('errors',state.errors+' / 3');
 setText('stage-name',state.stage_name);setText('stage-brief',state.brief);setText('progress-count',String(state.progress).padStart(2,'0')+' / 09');setText('mission-progress',state.progress);
 $('progress-fill').style.width=(state.progress/state.total_cargo*100)+'%';$('mission-fill').style.width=(state.progress/state.total_cargo*100)+'%';
 const rules=$('rule-list');rules.replaceChildren();const colors=['var(--coral)','var(--blue)','var(--lime)'];
 state.rules.forEach((rule,i)=>{const row=document.createElement('div');row.className='rule-row';const dot=document.createElement('i');dot.className='rule-dot';dot.style.background=colors[i];const name=document.createElement('strong');name.textContent=rule.label;const number=document.createElement('span');number.textContent='0'+(i+1);row.append(dot,name,number);rules.append(row)});
 document.querySelectorAll('.lane-button').forEach((button,i)=>{const rule=state.rules[i];button.querySelector('.lane-name').textContent=rule.name;button.querySelector('.lane-rule').textContent=rule.label;button.querySelector('.lane-count').textContent=state.bins[i]+' / 3 recibidos';button.disabled=state.failed||state.completed||state.game_finished});
 const card=$('cargo-card'),attrs=$('attributes');attrs.replaceChildren();
 if(state.cargo&&!state.game_finished&&!state.completed&&!state.failed){setText('cargo-emoji',state.cargo.emoji);setText('cargo-code','CARGA · '+state.cargo.code);setText('cargo-name','Paquete de tránsito');setText('cargo-index',String(state.index+1).padStart(2,'0'));
 ['COLOR: '+state.cargo.color.toUpperCase(),'FORMA: '+state.cargo.shape.toUpperCase(),'PULSO: '+state.cargo.pulse.toUpperCase()].forEach(label=>{const chip=document.createElement('span');chip.className='attribute';chip.textContent=label;attrs.append(chip)});card.style.opacity='1'
 }else{setText('cargo-emoji',state.game_finished?'🏁':'✓');setText('cargo-code',state.game_finished?'TODOS LOS EXPEDIENTES':'TURNO CERRADO');setText('cargo-name',state.game_finished?'Protocolo completado':'Carga clasificada');setText('cargo-index','—');card.style.opacity='.65'}
 const feedback=$('feedback');feedback.className='feedback'+(state.failed?' error':state.completed||state.game_finished?' good':'');feedback.querySelector('span:last-child').textContent=state.feedback;hideResult();
 if(state.failed)showResult('!','Turno interrumpido','Has cometido tres desvíos. Puedes repetir este expediente.','Reintentar turno ↺','retry');
 else if(state.game_finished)showResult('★','¡Terminal asegurada!','Has completado los seis expedientes con '+formatScore(state.score)+' puntos.','Jugar otra vez ↻','new');
 else if(state.completed&&state.stage_number<state.total_stages)showResult('✓','Expediente completado','Nueve paquetes clasificados. El siguiente protocolo ya está disponible.','Siguiente expediente →','next');
 else if(state.completed&&state.stage_number===state.total_stages)showResult('★','Último expediente superado','Has resuelto los seis protocolos. Cierra el turno para ver tu resultado final.','Finalizar protocolo →','next')
}
function update(next){state=next;render()}
function chooseLane(lane){if(!state||state.failed||state.completed||state.game_finished)return;update(callPython('submit_json',lane));if(state.errors>0&&!state.failed&&state.feedback.startsWith('Ruta incorrecta'))toast('Desvío detectado: revisa los filtros.')}
async function boot(){
 readBest();setText('best-score',formatScore(best));
 try{setText('loading-message','Descargando el motor Pyodide…');pyodide=await loadPyodide();setText('loading-message','Cargando las reglas escritas en Python…');
 const response=await fetch('./codigo.py',{cache:'no-store'});if(!response.ok)throw new Error('No se pudo cargar codigo.py ('+response.status+').');
 const source=await response.text();setText('python-source',source);await pyodide.runPythonAsync(source);update(callPython('new_game_json'));$('loading-screen').classList.add('done');window.setTimeout(()=>$('loading-screen').remove(),350)
 }catch(error){setText('loading-message','No se pudo iniciar el motor Python.');$('loading-screen').querySelector('strong').textContent='Error de conexión';toast(error.message||'Comprueba la conexión e inténtalo de nuevo.');console.error(error)}
}
document.querySelectorAll('.lane-button').forEach(button=>button.addEventListener('click',()=>chooseLane(Number(button.dataset.lane))));
$('hint-button').addEventListener('click',()=>{if(!state||state.failed||state.completed||state.game_finished)return;update(callPython('hint_json'));toast('Pista revelada: se han descontado 75 puntos.')});
$('restart-button').addEventListener('click',()=>{if(!state)return;update(callPython('restart_stage_json'));toast('Turno reiniciado.')});
$('result-button').addEventListener('click',()=>{const action=$('result-button').dataset.action;if(action==='retry')update(callPython('restart_stage_json'));if(action==='next')update(callPython('next_stage_json'));if(action==='new')update(callPython('new_game_json'))});
$('help-button').addEventListener('click',()=>$('help-dialog').showModal());$('close-help').addEventListener('click',()=>$('help-dialog').close());
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&$('help-dialog').open)$('help-dialog').close();if($('help-dialog').open)return;if(['1','2','3'].includes(event.key))chooseLane(Number(event.key)-1)});
boot()
})();
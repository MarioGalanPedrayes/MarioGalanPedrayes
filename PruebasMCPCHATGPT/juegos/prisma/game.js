(() => {
'use strict';
const SIZE=7, SAVE_KEY='prisma-archivo-luz-v1';
const levels=[
 {name:'Primer rebote',source:[0,3],dir:[1,0],target:[6,1],par:5,mirrors:[[2,3,'/'],[2,1,'/'],[4,1,'\\'],[4,4,'\\'],[6,4,'/']],hint:'El primer espejo debe enviar la luz hacia arriba.'},
 {name:'El ángulo oculto',source:[0,5],dir:[1,0],target:[6,4],par:4,mirrors:[[2,5,'/'],[2,1,'/'],[5,1,'\\'],[5,4,'\\']],hint:'Busca una ruta que suba primero y descienda al final.'},
 {name:'Eje vertical',source:[3,6],dir:[0,-1],target:[1,6],par:4,mirrors:[[3,4,'/'],[6,4,'\\'],[6,5,'/'],[1,5,'/']],hint:'El emisor comienza mirando hacia arriba.'},
 {name:'Retorno',source:[6,6],dir:[0,-1],target:[5,5],par:3,mirrors:[[6,3,'\\'],[2,3,'/'],[2,5,'\\']],hint:'La primera reflexión debe llevar el haz hacia la izquierda.'},
 {name:'Luz de cierre',source:[0,0],dir:[0,1],target:[1,6],par:4,mirrors:[[0,3,'\\'],[3,3,'/'],[3,1,'\\'],[1,1,'/']],hint:'Comienza descendiendo por el borde izquierdo.'}
];
let levelIndex=0,moves=0,orientations=[],beam=[],solved=false,toastTimer=null;
let saved={best:{},unlocked:1};
try{const raw=JSON.parse(localStorage.getItem(SAVE_KEY)||'{}');saved={best:raw.best||{},unlocked:Math.max(1,Math.min(5,raw.unlocked||1))};}catch(_){}
const $=id=>document.getElementById(id);
const board=$('board'),beamLayer=$('beam-layer');
const key=(x,y)=>x+','+y;
function persist(){try{localStorage.setItem(SAVE_KEY,JSON.stringify(saved));}catch(_){}}
function current(){return levels[levelIndex];}
function solutionMap(){const m=new Map();current().mirrors.forEach(([x,y,o])=>m.set(key(x,y),o));return m;}
function initialOrientations(){return current().mirrors.map((m,i)=>((levelIndex+i)%3===0)?m[2]:(m[2]==='/'?'\\':'/'));}
function reflect(dx,dy,mirror){return mirror==='/'?[-dy,-dx]:[dy,dx];}
function trace(){
 const l=current(), mirrors=new Map();
 l.mirrors.forEach((m,i)=>mirrors.set(key(m[0],m[1]),orientations[i]));
 let [x,y]=l.source, [dx,dy]=l.dir; const points=[[x,y]],visited=new Set();let hit=false;
 for(let step=0;step<60;step++){
  x+=dx;y+=dy;if(x<0||y<0||x>=SIZE||y>=SIZE)break;
  points.push([x,y]);if(x===l.target[0]&&y===l.target[1]){hit=true;break;}
  const k=key(x,y);if(visited.has(k+':'+dx+':'+dy))break;visited.add(k+':'+dx+':'+dy);
  const mirror=mirrors.get(k);if(mirror)[dx,dy]=reflect(dx,dy,mirror);
 }
 return {points,hit};
}
function render(){
 const l=current(),solution=solutionMap();board.innerHTML='';
 for(let y=0;y<SIZE;y++)for(let x=0;x<SIZE;x++){
  const i=l.mirrors.findIndex(m=>m[0]===x&&m[1]===y),cell=document.createElement('button');
  cell.type='button';cell.className='tile empty';cell.dataset.x=x;cell.dataset.y=y;
  if(x===l.source[0]&&y===l.source[1]){cell.className='tile source';cell.textContent='◉';cell.setAttribute('aria-label','Emisor');}
  else if(x===l.target[0]&&y===l.target[1]){cell.className='tile target'+(solved?' active':'');cell.textContent='◎';cell.setAttribute('aria-label','Receptor');}
  else if(i>=0){cell.className='tile mirror';cell.innerHTML='<span class="mirror-glyph">'+(orientations[i]==='/'?'／':'＼')+'</span>';cell.setAttribute('aria-label','Espejo '+(i+1)+', orientación '+orientations[i]+'. Girar');cell.addEventListener('click',()=>rotate(i));}
  board.appendChild(cell);
 }
 const result=trace();beam=result.points;drawBeam(result);
 $('level-name').textContent=String(levelIndex+1).padStart(2,'0')+' · '+l.name;
 $('chapter-label').textContent=String(levelIndex+1).padStart(2,'0')+' / 05';
 $('moves').textContent=String(moves).padStart(2,'0');$('par').textContent='≤ '+String(l.par).padStart(2,'0');
 $('progress-label').textContent=String(levelIndex+1).padStart(2,'0')+' / 05';
 $('progress-fill').style.width=((levelIndex+1)/5*100)+'%';
 $('mission-title').textContent=solved?'Conexión estable':'Activa el receptor';
 $('mission-copy').textContent=solved?'El haz ha alcanzado el receptor. Expediente completado.':'Gira los espejos hasta que el haz alcance el receptor.';
 $('next-level-button').hidden=!solved;
 $('next-level-button').textContent=levelIndex===levels.length-1?'Volver al inicio →':'Siguiente nivel →';
 $('board-state').textContent=solved?'RECEPTOR ACTIVO':'HAZ EN TRÁNSITO';
 $('best-score').textContent=saved.best[levelIndex]===undefined?'—':saved.best[levelIndex]+' GIROS';
 $('unlocked-count').textContent=String(saved.unlocked).padStart(2,'0')+' / 05';
 $('hint-text').textContent='Las pistas no consumen giros.';
}
function drawBeam(result){
 const pts=result.points.map(([x,y])=>[((x+.5)/SIZE*700).toFixed(1),((y+.5)/SIZE*700).toFixed(1)].join(',')).join(' ');
 beamLayer.innerHTML='<polyline class="beam-line '+(result.hit?'':'failed')+'" points="'+pts+'"/>';
 const last=result.points[result.points.length-1];beamLayer.innerHTML+='<circle class="beam-dot" cx="'+((last[0]+.5)/SIZE*700)+'" cy="'+((last[1]+.5)/SIZE*700)+'" r="5"/>';
}
function rotate(i){if(solved)return;orientations[i]=orientations[i]==='/'?'\\':'/';moves++;const result=trace();if(result.hit)complete();else{render();$('moves').textContent=String(moves).padStart(2,'0');}}
function complete(){
 solved=true;const prev=saved.best[levelIndex];if(prev===undefined||moves<prev)saved.best[levelIndex]=moves;
 saved.unlocked=Math.max(saved.unlocked,Math.min(5,levelIndex+2));persist();render();
 $('mission-copy').textContent=levelIndex===levels.length-1?'¡Has completado los cinco expedientes! El Archivo de Luz está restaurado.':(moves<=current().par?'Conexión perfecta. Has igualado o superado el registro objetivo.':'Conexión conseguida. Puedes repetir para mejorar tu número de giros.');
 $('hint-text').textContent='Expediente completado · '+moves+' giros.';
 showToast(levelIndex===levels.length-1?'¡Archivo de Luz completado!':(moves<=current().par?'¡Conexión perfecta!':'¡Receptor activado!'));
 $('board-state').textContent='CONEXIÓN ESTABLE';
}
function reset(){orientations=initialOrientations();moves=0;solved=false;render();$('next-level-button').hidden=true;}
function showToast(message){const t=$('toast');t.textContent=message;t.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.classList.remove('show'),2200);}
function nextLevel(){if(!solved)return;if(levelIndex<levels.length-1){levelIndex++;reset();showToast('Expediente '+String(levelIndex+1).padStart(2,'0')+' desbloqueado.');}else{showToast('Has completado el Archivo de Luz.');levelIndex=0;reset();}}
function hint(){if(solved){showToast('Este expediente ya está resuelto.');return;}const solution=current().mirrors;const wrong=solution.findIndex((m,i)=>orientations[i]!==m[2]);if(wrong<0){showToast('La configuración es correcta.');return;}const [x,y]=solution[wrong];const tile=board.querySelector('[data-x="'+x+'"][data-y="'+y+'"]');if(tile){tile.classList.remove('hint-pulse');void tile.offsetWidth;tile.classList.add('hint-pulse');$('hint-text').textContent='Pista: prueba a girar el espejo señalado.';}}
$('reset-button').addEventListener('click',reset);$('hint-button').addEventListener('click',hint);
$('next-level-button').addEventListener('click',nextLevel);
$('help-button').addEventListener('click',()=>$('help-dialog').showModal());
$('close-help').addEventListener('click',()=>$('help-dialog').close());$('close-help-bottom').addEventListener('click',()=>$('help-dialog').close());
document.addEventListener('keydown',e=>{if(e.key==='Enter'&&solved)nextLevel();if(e.key.toLowerCase()==='r')reset();});
reset();
})();
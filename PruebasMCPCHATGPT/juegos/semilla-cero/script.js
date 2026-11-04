let py=null,game=null;
const $=id=>document.getElementById(id);
const parse=value=>JSON.parse(value);
const call=(name,...args)=>py.globals.get(name)(...args);
function update(){
 if(!game)return;
 $("level").textContent="JARDÍN "+String(game.level+1).padStart(2,"0")+" / "+String(game.total).padStart(2,"0");
 $("water").textContent=game.water+" / "+game.water_total;
 $("turns").textContent=game.turns;
 $("score").textContent=game.score;
 $("name").textContent=game.name;
 $("gravity").textContent="GRAVEDAD "+game.gravity_arrow+" "+game.gravity_name;
 $("message").textContent=game.message;
 const board=$("board");board.innerHTML="";
 for(let y=0;y<7;y++)for(let x=0;x<7;x++){
  const cell=document.createElement("div");cell.className="cell";
  const key=[x,y];
  if(game.walls.some(p=>p[0]===x&&p[1]===y)){cell.classList.add("wall");cell.textContent="▧";}
  if(game.drops.some(p=>p[0]===x&&p[1]===y)){cell.classList.add("drop");cell.textContent="✿";}
  if(game.goal[0]===x&&game.goal[1]===y){cell.classList.add("goal");cell.textContent="◎";}
  if(game.player[0]===x&&game.player[1]===y){cell.className="cell player";cell.textContent="●";}
  board.appendChild(cell);
 }
 const active=game.status==="playing";
 document.querySelectorAll("[data-move]").forEach(b=>b.disabled=!active);
 $("wait").disabled=!active;$("restart").disabled=false;
 $("finish").hidden=active;
 if(!active){
  $("finish-title").textContent=game.status==="won"?(game.complete?"¡Has restaurado el invernadero!":"¡Jardín restaurado!"):"Ciclo agotado";
  $("finish-text").textContent=game.status==="won"?"Has reunido el agua y encontrado la tierra fértil. Puntuación acumulada: "+game.score+".":"Puedes reiniciar este jardín y probar una ruta distinta.";
  $("next").textContent=game.complete?"Volver a empezar ↻":game.status==="lost"?"Reintentar jardín ↻":"Siguiente jardín →";
 }
}
function refresh(){game=parse(call("get_state"));update();}
function move(dx,dy){if(!py||game.status!=="playing")return;game=parse(call("move",dx,dy));update();}
async function init(){
 try{
  const source=await(await fetch("codigo.py")).text();$("source-code").textContent=source;
  py=await loadPyodide();await py.runPythonAsync(source);
  game=parse(call("start_game"));$("engine").textContent="● MOTOR PYTHON CONECTADO";update();
 }catch(e){$("engine").textContent="● ERROR AL INICIAR";$("message").textContent="No se pudo cargar Pyodide. Comprueba la conexión y recarga la página.";console.error(e);}
}
document.querySelectorAll("[data-move]").forEach(button=>button.addEventListener("click",()=>{const [x,y]=button.dataset.move.split(",").map(Number);move(x,y);}));
$("wait").addEventListener("click",()=>{if(py){game=parse(call("wait_turn"));update();}});
$("restart").addEventListener("click",()=>{if(py){game=parse(call("restart_level"));update();}});
$("next").addEventListener("click",()=>{if(!py)return;if(game.status==="lost"||game.complete){game=parse(call("start_game"));}else{game=parse(call("next_level"));}update();});
document.addEventListener("keydown",event=>{
 const keys={ArrowUp:[0,-1],w:[0,-1],W:[0,-1],ArrowDown:[0,1],s:[0,1],S:[0,1],ArrowLeft:[-1,0],a:[-1,0],A:[-1,0],ArrowRight:[1,0],d:[1,0],D:[1,0]};
 if(keys[event.key]){event.preventDefault();move(...keys[event.key]);}
});
init();
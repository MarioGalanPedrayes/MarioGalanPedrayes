let py=null,game=null;
const $=id=>document.getElementById(id);
const parse=value=>JSON.parse(value);
const call=(name,...args)=>{const result=py.globals.get(name)(...args);return typeof result==="string"?result:result.toJs();};
function glyph(mask){
 const glyphs={1:"╵",2:"╶",3:"└",4:"╷",5:"│",6:"┌",7:"├",8:"╴",9:"┘",10:"─",11:"┴",12:"┐",13:"┤",14:"┬",15:"┼"};
 return glyphs[mask]||"·";
}
function render(){
 if(!game)return;
 $("level").textContent="SECTOR "+String(game.level+1).padStart(2,"0")+" / "+String(game.total).padStart(2,"0");
 $("relays").textContent=game.relays_powered+" / "+game.relays_total;
 $("rotations").textContent=game.rotations;
 $("score").textContent=String(game.score).padStart(4,"0");
 $("name").textContent=game.name;$("message").textContent=game.message;
 const board=$("board");board.innerHTML="";
 const map=new Map(game.tiles.map(tile=>[tile.x+","+tile.y,tile]));
 for(let y=0;y<5;y++)for(let x=0;x<5;x++){
  const tile=map.get(x+","+y),cell=document.createElement("button");
  cell.type="button";cell.className="cell"+(tile?"":" empty");
  if(tile){
   cell.classList.add(tile.kind);
   if(tile.powered)cell.classList.add("powered");
   if(tile.kind==="source"){cell.textContent="S";cell.title="Fuente de energía";}
   else if(tile.kind==="target"){cell.textContent="◎";cell.title="Núcleo de salida";}
   else {cell.textContent=glyph(tile.mask);cell.title=(tile.kind==="relay"?"Relé":"Conducto")+" — girar 90°";}
   if(tile.kind==="relay"){const tag=document.createElement("span");tag.className="tag";tag.textContent="◆";cell.appendChild(tag);}
   cell.disabled=!tile.rotatable||game.status!=="playing";
   if(tile.rotatable)cell.addEventListener("click",()=>rotate(x,y));
  }else{cell.disabled=true;cell.setAttribute("aria-label","Casilla vacía");}
  board.appendChild(cell);
 }
 $("restart").disabled=false;
 $("finish").hidden=game.status==="playing";
 if(game.status!=="playing"){
  $("finish-title").textContent=game.complete?"¡La mina vuelve a tener energía!":"¡Sector conectado!";
  $("finish-text").textContent="Todos los relés y el núcleo reciben energía. Puntuación acumulada: "+game.score+".";
  $("next").textContent=game.complete?"Volver a empezar ↻":"Siguiente sector →";
 }
}
function rotate(x,y){if(!py||game.status!=="playing")return;game=parse(call("rotate_tile",x,y));render();}
async function init(){
 try{
  const source=await(await fetch("codigo.py")).text();$("source-code").textContent=source;
  py=await loadPyodide();await py.runPythonAsync(source);
  game=parse(call("start_game"));$("engine").textContent="● MOTOR PYTHON CONECTADO";render();
 }catch(e){$("engine").textContent="● ERROR AL INICIAR";$("message").textContent="No se pudo cargar Pyodide. Comprueba la conexión y recarga la página.";console.error(e);}
}
$("restart").addEventListener("click",()=>{if(py){game=parse(call("restart_level"));render();}});
$("next").addEventListener("click",()=>{if(!py)return;game=parse(game.complete?call("start_game"):call("next_level"));render();});
init();
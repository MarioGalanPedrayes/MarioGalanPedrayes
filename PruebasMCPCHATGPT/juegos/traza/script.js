let py, game, busy=false;
const $=id=>document.getElementById(id);
async function boot(){
  try{
    py=await loadPyodide();
    const response=await fetch("codigo.py");
    if(!response.ok)throw new Error("No se pudo descargar codigo.py");
    const source=await response.text();
    $("source").textContent=source;
    py.runPython(source);
    game=JSON.parse(py.globals.get("new_game")());
    render();
  }catch(error){$("message").textContent="No se ha podido iniciar Python. Comprueba tu conexión y recarga la página.";console.error(error);}
}
function render(){
  const s=game.state;
  $("level").textContent=String(s.level+1).padStart(2,"0")+" / "+game.total_levels;
  $("energy").textContent=s.energy;
  $("cores").textContent=s.cores.length+" / "+game.total_cores;
  $("moves").textContent=s.moves;
  $("mission-title").textContent=game.level_name;
  $("message").textContent=s.message;
  const board=$("board");board.innerHTML="";
  const symbols={R:"R",C:"◆",E:"◎","#":"", "!":"✕",".":""};
  game.grid.forEach(row=>row.forEach(cell=>{
    const el=document.createElement("div");
    el.className="tile "+({R:"robot",C:"core",E:"exit","#":"wall","!":"hazard",".":"floor"}[cell]||"floor");
    el.textContent=symbols[cell];
    if(cell==="R")el.setAttribute("aria-label","Robot");
    board.appendChild(el);
  }));
  $("next").hidden=s.status!=="level_complete";
  $("next").textContent=s.level===game.total_levels-1?"Operación completada":"Siguiente sector →";
  if(s.status==="failed"||s.status==="won"){$("restart").textContent=s.status==="won"?"Jugar de nuevo":"Reintentar sector";}
}
async function move(dir){
  if(!py||busy||game.state.status!=="playing")return;
  busy=true;
  try{game=JSON.parse(py.globals.get("act")(JSON.stringify(game.state),dir));render();}
  finally{busy=false;}
}
document.querySelectorAll("[data-dir]").forEach(b=>b.addEventListener("click",()=>move(b.dataset.dir)));
document.addEventListener("keydown",e=>{
  const dirs={ArrowUp:"up",w:"up",ArrowDown:"down",s:"down",ArrowLeft:"left",a:"left",ArrowRight:"right",d:"right"};
  const dir=dirs[e.key];
  if(dir){e.preventDefault();move(dir);}
});
$("restart").addEventListener("click",()=>{if(!py)return;game=JSON.parse(py.globals.get("new_game")());render();});
$("next").addEventListener("click",()=>{if(!py)return;game=JSON.parse(py.globals.get("next_level")(JSON.stringify(game.state)));render();});
boot();
let pyodide=null,py=null,game=null,selection=[];
const $=id=>document.getElementById(id);
const call=(name,...args)=>{const result=py.globals.get(name)(...args);return typeof result==="string"?result:result.toJs({dict_converter:Object.fromEntries});};
function parseResult(value){return JSON.parse(value);}
function setMessage(text){$("message").textContent=text;}
function render(){
  if(!game)return;
  $("score").textContent=String(game.score).padStart(4,"0");
  $("tries").textContent=game.tries_left+" / "+game.max_tries;
  $("sector").textContent=String(game.level+1).padStart(2,"0")+" / "+String(game.total_levels).padStart(2,"0");
  $("level-label").textContent="TRANSMISIÓN "+String(game.level+1).padStart(2,"0")+" / 05";
  $("mission-name").textContent=game.level_name;
  $("sequence-size").textContent=game.length+" SÍMBOLOS";
  setMessage(game.message);
  const history=$("history");
  history.innerHTML="";
  if(!game.history.length){history.innerHTML='<p class="empty">Las lecturas aparecerán aquí.</p>';}
  game.history.forEach((row,i)=>{
    const el=document.createElement("div");el.className="attempt";
    const left=document.createElement("div");left.className="attempt-left";
    const number=document.createElement("span");number.className="attempt-num";number.textContent=String(i+1).padStart(2,"0");
    const symbols=document.createElement("div");symbols.className="mini-symbols";
    row.guess.forEach(v=>{const s=document.createElement("span");s.textContent=game.symbols[v];symbols.appendChild(s);});
    left.append(number,symbols);
    const feedback=document.createElement("div");feedback.className="feedback";
    const exact=document.createElement("span");exact.className="good";exact.textContent="● "+row.exact;
    const near=document.createElement("span");near.className="near";near.textContent="◆ "+row.misplaced;
    feedback.append(exact,near);el.append(left,feedback);history.appendChild(el);
  });
  if(game.secret){
    const reveal=document.createElement("p");reveal.className="empty";
    reveal.textContent="Código: "+game.secret.map(v=>game.symbols[v]).join(" ");
    history.appendChild(reveal);
  }
  $("slots").innerHTML="";
  for(let i=0;i<game.length;i++){
    const btn=document.createElement("button");btn.className="slot"+(selection[i]!==undefined?" filled":"");
    btn.textContent=selection[i]===undefined?"＋":game.symbols[selection[i]];
    btn.title="Quitar símbolo "+(i+1);btn.disabled=game.status!=="playing";
    btn.addEventListener("click",()=>{selection.splice(i,1);renderSelection();});
    $("slots").appendChild(btn);
  }
  $("palette").innerHTML="";
  game.symbols.forEach((symbol,i)=>{
    const btn=document.createElement("button");btn.className="symbol";btn.textContent=symbol;
    btn.title=game.labels[i];btn.disabled=game.status!=="playing"||selection.includes(i)||selection.length>=game.length;
    btn.addEventListener("click",()=>{selection.push(i);renderSelection();});
    $("palette").appendChild(btn);
  });
  $("send").disabled=game.status!=="playing"||selection.length!==game.length;
  $("hint").disabled=game.status!=="playing"||game.hint_used;
  $("end-actions").hidden=game.status==="playing";
  $("advance").textContent=game.level===game.total_levels-1&&game.status==="won"?"Jugar otra vez ↻":"Siguiente transmisión →";
}
function renderSelection(){
  $("slots").innerHTML="";
  for(let i=0;i<game.length;i++){
    const btn=document.createElement("button");btn.className="slot"+(selection[i]!==undefined?" filled":"");
    btn.textContent=selection[i]===undefined?"＋":game.symbols[selection[i]];
    btn.title="Quitar símbolo "+(i+1);
    btn.addEventListener("click",()=>{selection.splice(i,1);renderSelection();});
    $("slots").appendChild(btn);
  }
  [...$("palette").children].forEach((btn,i)=>{btn.disabled=selection.includes(i)||selection.length>=game.length;});
  $("send").disabled=selection.length!==game.length;
}
async function refresh(){game=parseResult(await call("get_state"));selection=[];render();}
async function init(){
  try{
    const source=await (await fetch("codigo.py")).text();
    $("python-source").textContent=source;
    pyodide=await loadPyodide();
    await pyodide.runPythonAsync(source);
    py=pyodide;
    game=parseResult(await call("start_game"));
    $("connection").textContent="● MOTOR PYTHON CONECTADO";
    $("connection").style.color="var(--mint)";
    render();
  }catch(error){
    $("connection").textContent="● ERROR DE CONEXIÓN";
    $("connection").style.color="var(--red)";
    setMessage("No se pudo iniciar Pyodide. Comprueba tu conexión y recarga la página.");
    console.error(error);
  }
}
$("send").addEventListener("click",async()=>{
  if(!py||selection.length!==game.length)return;
  game=parseResult(await call("submit_guess",pyodide.toPy(selection)));
  selection=[];render();
});
$("hint").addEventListener("click",async()=>{game=parseResult(await call("request_hint"));selection=[];render();});
$("advance").addEventListener("click",async()=>{game=parseResult(await call("next_level"));selection=[];render();});
$("retry").addEventListener("click",async()=>{game=parseResult(await call("retry_level"));selection=[];render();});
document.addEventListener("keydown",e=>{if(e.key==="Backspace"&&selection.length){selection.pop();renderSelection();}});
init();
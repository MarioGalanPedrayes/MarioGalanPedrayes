(() => {
"use strict";
const $=id=>document.getElementById(id), marks=["●","◆","▲"];
const names=["Musgario","Lúgora","Trenzal","Brezaluz","Nubrote","Hojalba","Tiznillo","Velaria","Raizonte","Péndula","Brumel","Cendal","Rocíofer","Salmuera","Nacarín","Espumel","Mareta","Alguario","Coralba","Burbujón","Litorna","Ventalga","Crisalia","Ondario","Pedernal","Ventisca","Cuarzón","Altífero","Nevaira","Riscón","Auralta","Granizo","Picaluz","Umbrafín","Crestal","Nivaluz","Cenizal","Brasaul","Obsidia","Fumarol","Escoriel","Lumbreta","Azufral","Magmario","Pavesa","Calderín","Ígnea","Tizoria","Dunario","Arenis","Siroco","Oasín","Miraluz","Dunavelo","Cactilio","Solmara","Yesquín","Salitral","Calíope","Vidrial","Noctil","Eclipsa","Susurial","Velumbría","Ombrel","Lunario","Silencia","Eteria","Parpadeo","Sombraciel"];
let py=null,busy=false,timer;
async function init(){
 try{
  py=await loadPyodide();
  const r=await fetch("codigo.py");if(!r.ok)throw Error("No se pudo cargar codigo.py");
  const source=await r.text();$("python-source").textContent=source;
  await py.runPythonAsync(source);
  const saved=localStorage.getItem("bestiario-ecos-save")||"";
  const fn=py.globals.get(saved?"restore":"start");
  render(JSON.parse(fn(...(saved?[saved]:[]))));
  $("save-status").textContent="● EXPEDICIÓN LISTA";
 }catch(e){console.error(e);$("save-status").textContent="● ERROR DE CARGA";$("encounter-description").textContent="No se ha podido cargar el motor Python. Comprueba tu conexión y recarga la página.";}
}
function call(name,...args){
 if(!py||busy)return;busy=true;
 try{const s=JSON.parse(py.globals.get(name)(...args));render(s);save(s);
  if(s.result==="captured")toast("Nueva criatura registrada en el bestiario");
  if(s.result==="escaped")toast("El rastro se ha perdido. Puedes intentarlo de nuevo.");
 }catch(e){console.error(e);toast("Error al procesar el turno.");}finally{busy=false;}
}
function save(s){localStorage.setItem("bestiario-ecos-save",JSON.stringify({collection:s.collection,encounters:s.encounters,seals:s.seals}));}
function render(s){
 $("collection-count").textContent=`${s.collection.length} / 70`;
 $("collection-progress").style.width=`${s.collection.length/70*100}%`;
 $("encounter-count").textContent=s.encounters;$("seal-count").textContent=s.seals;
 const list=$("collection-list");
 if(!s.collection.length){list.innerHTML='<p class="muted">Las criaturas que encuentres aparecerán aquí.</p>';}
 else{list.replaceChildren(...s.collection.map(id=>{const row=document.createElement("div");row.className="collection-entry";const a=document.createElement("span"),b=document.createElement("span"),c=document.createElement("small");a.textContent="✦";b.textContent=names[id];c.textContent=`#${String(id+1).padStart(2,"0")}`;row.append(a,b,c);return row;}));}
 const c=s.creature;
 $("creature-name").textContent=c?c.name:"Aún no has encontrado nada";$("creature-mood").textContent=c?c.mood:"—";
 $("creature-glyph").textContent=c?c.glyph:"✳";$("biome-chip").textContent=c?c.biome.toUpperCase():"SIN RASTRO";
 $("encounter-title").textContent=c?"Una presencia entre las sombras":"El bosque contiene el aliento";
 $("encounter-description").textContent=c?s.description:"Pulsa «Explorar» para adentrarte en un bioma. Cada criatura responde a una secuencia única de cuatro pulsos.";
 $("listen-button").disabled=!c||s.heard||s.finished;$("explore-button").disabled=!!c&&!s.finished;
 $("instruction").textContent=!c?"Primero encuentra una criatura y escucha sus cuatro pulsos.":!s.heard?"La presencia está cerca. Escucha su patrón antes de responder.":s.finished?"El encuentro ha terminado. Continúa hacia otro rastro.":"Devuelve los tonos en el mismo orden, uno por turno.";
 $("echo-line").hidden=!s.heard;$("echo-pattern").textContent=s.echo.join("  →  ");
 $("pulse-display").replaceChildren(...[0,1,2,3].map(i=>{const d=document.createElement("div");d.className="pulse-slot"+(i<s.answers.length?" done":"");d.textContent=i<s.answers.length?marks[s.answers[i]]:(s.heard?"?":"·");return d;}));
 document.querySelectorAll(".tone-button").forEach(b=>b.disabled=!c||!s.heard||s.finished);
 $("turn-label").textContent=`TURNO ${c?Math.min(s.turn+1,4):"—"} / 4`;$("feedback").textContent=s.feedback;
 $("agitation-value").textContent=`${s.agitation}%`;$("agitation-bar").style.width=`${s.agitation}%`;
 $("agitation-bar").style.background=s.agitation>65?"var(--rust)":"var(--mint)";
 $("result-box").hidden=!s.finished;
 if(s.finished){$("result-title").textContent=s.result==="captured"?"Resonancia estable":"El eco se desvanece";$("result-text").textContent=s.result==="captured"?`${c.name} ha quedado registrado. Tu colección cuenta con ${s.collection.length} especies.`:`${c.name} se ha retirado. La agitación fue demasiado alta para completar el vínculo.`;}
}
function toast(msg){const e=$("toast");e.textContent=msg;e.classList.add("show");clearTimeout(timer);timer=setTimeout(()=>e.classList.remove("show"),2300);}
$("explore-button").addEventListener("click",()=>call("explore"));
$("listen-button").addEventListener("click",()=>call("listen"));
document.querySelectorAll(".tone-button").forEach(b=>b.addEventListener("click",()=>call("answer",Number(b.dataset.tone))));
$("result-button").addEventListener("click",()=>call("next_encounter"));
$("reset-button").addEventListener("click",()=>{if(!confirm("¿Reiniciar toda la expedición? Se perderá la colección guardada en este navegador."))return;localStorage.removeItem("bestiario-ecos-save");call("start");toast("Expedición reiniciada");});
init();
})();
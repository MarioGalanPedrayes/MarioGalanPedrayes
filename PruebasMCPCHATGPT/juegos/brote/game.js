'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const SAVE_KEY = 'brote-ecosistema-v1';
  const plants = {
    luna:{name:'Flor de luna',emoji:'🌙',cost:{seeds:1},days:2,reward:{dew:2}},
    amber:{name:'Caléndula ámbar',emoji:'🌼',cost:{seeds:1,dew:1},days:3,reward:{seeds:2}},
    fern:{name:'Helecho susurrante',emoji:'🌿',cost:{seeds:2,dew:1},days:3,reward:{wood:1,dew:1}}
  };
  const creatures = [
    {id:'moth',name:'Polilla farol',emoji:'🦋',hint:'Le atraen las flores nocturnas.'},
    {id:'fox',name:'Zorrito musgo',emoji:'🦊',hint:'Busca rincones tranquilos y refugios.'},
    {id:'frog',name:'Ranita lluvia',emoji:'🐸',hint:'Aparece cuando el suelo está húmedo.'},
    {id:'bird',name:'Pájaro brisa',emoji:'🐦',hint:'Visita jardines llenos de brotes.'}
  ];
  const weatherTypes = ['Brisa','Llovizna','Sol suave','Niebla luminosa'];
  function freshGame() {
    return {day:1,energy:8,max_energy:8,resources:{dew:5,seeds:5,wood:2,petals:0},
      plots:Array(9).fill(null),shelter:0,creatures:[],weather:'Brisa',
      log:['El claro está en silencio. Es hora de devolverle la vida.'],
      mission:{text:'Planta 2 brotes para despertar el jardín.',target:2,progress:0,done:false,reward:{dew:3,seeds:2}},score:0};
  }
  function loadGame() {
    const initial = freshGame();
    try {
      const saved = JSON.parse(localStorage.getItem(SAVE_KEY) || 'null');
      if (!saved || typeof saved !== 'object') return initial;
      return {
        ...initial, ...saved,
        resources:{...initial.resources,...(saved.resources || {})},
        plots:Array.from({length:9},(_,i)=>Array.isArray(saved.plots)?(saved.plots[i] || null):null),
        creatures:Array.isArray(saved.creatures)?saved.creatures:[],
        log:Array.isArray(saved.log)?saved.log:initial.log,
        mission:{...initial.mission,...(saved.mission || {}),reward:{...initial.mission.reward,...((saved.mission||{}).reward||{})}}
      };
    } catch (_) { return initial; }
  }
  let game = loadGame(), selectedPlot = 0, selectedSeed = 'luna', toastTimer = null;
  function save() {
    try { localStorage.setItem(SAVE_KEY, JSON.stringify(game)); }
    catch (_) { notify('El navegador no permite guardar la partida; puedes seguir jugando mientras esta página esté abierta.'); }
  }
  function notify(message) {
    const t=$('toast'); if(!t) { window.alert(message); return; }
    t.textContent=message; t.classList.add('show');
    window.clearTimeout(toastTimer); toastTimer=window.setTimeout(()=>t.classList.remove('show'),2600);
  }
  function log(message) { game.log.unshift(message); game.log=game.log.slice(0,7); }
  function spend(cost) {
    for(const [k,n] of Object.entries(cost)) if((game.resources[k]||0)<n) throw Error('No tienes suficientes recursos.');
    for(const [k,n] of Object.entries(cost)) game.resources[k]-=n;
  }
  function useEnergy(n=1) { if(game.energy<n) throw Error('Te falta energía. Pasa el día para recuperarla.'); game.energy-=n; }
  function grow(i) { const p=game.plots[i]; if(!p)return; p.grown=true;p.watered=false;log(plants[p.kind].name+' ha florecido. ¡Puedes cosecharla!'); }
  function meetCreature() {
    const found=creatures.filter(c=>!game.creatures.some(x=>x.id===c.id));
    if(found.length){const c=found[Math.floor(Math.random()*found.length)];game.creatures.push(c);game.score+=25;log('¡Ha llegado '+c.name+' '+c.emoji+'! '+c.hint);}
    else {game.resources.petals+=2;log('El claro está lleno de vida. Has recogido 2 pétalos.');}
  }
  function checkMission() {
    const m=game.mission;
    if(!m.done&&m.progress>=m.target){m.done=true;for(const[k,n]of Object.entries(m.reward))game.resources[k]+=n;log('Encargo completado: el jardín despierta. Recompensa recibida.');}
  }
  function perform(action,data={}) {
    switch(action) {
      case 'gather': {
        useEnergy();const r=Math.random()*100,k=r<40?'dew':r<70?'seeds':r<90?'wood':'petals',n=(k==='dew'||k==='seeds')?2:1;
        game.resources[k]+=n;log('Has reunido '+n+' de '+({dew:'rocío',seeds:'semillas',wood:'madera',petals:'pétalos'}[k])+' en el claro.');break;
      }
      case 'plant': {
        const i=data.plot,k=data.kind;
        if(!Number.isInteger(i)||i<0||i>8||game.plots[i])throw Error('Selecciona una parcela vacía.');
        if(!plants[k])throw Error('Selecciona una semilla válida.');
        if(game.energy<1)throw Error('Te falta energía. Pasa el día para recuperarla.');
        spend(plants[k].cost);useEnergy();game.plots[i]={kind:k,days_left:plants[k].days,watered:false,grown:false};
        game.mission.progress++;log('Has plantado '+plants[k].name.toLowerCase()+'.');checkMission();break;
      }
      case 'water': {
        const i=data.plot,p=game.plots[i];
        if(!p||p.grown)throw Error('No hay una planta que necesite agua en esa parcela.');
        if(p.watered)throw Error('Esa planta ya está regada hoy.');
        if(game.resources.dew<1)throw Error('No tienes rocío suficiente.');
        if(game.energy<1)throw Error('Te falta energía. Pasa el día para recuperarla.');
        spend({dew:1});useEnergy();p.watered=true;p.days_left=Math.max(0,p.days_left-1);
        log('Una gota de rocío acelera el crecimiento.');if(p.days_left===0)grow(i);break;
      }
      case 'harvest': {
        const i=data.plot,p=game.plots[i];if(!p||!p.grown)throw Error('Todavía no hay nada que recolectar.');
        for(const[k,n]of Object.entries(plants[p.kind].reward))game.resources[k]+=n;
        game.resources.petals++;game.score+=10;log('¡Cosecha conseguida! '+plants[p.kind].name+' te ha dado recursos.');game.plots[i]=null;break;
      }
      case 'explore': {
        useEnergy(2);const r=Math.random();
        if(r<.42){game.resources.seeds+=2;log('Entre las raíces has encontrado 2 semillas.');}
        else if(r<.72){game.resources.wood+=2;log('Has encontrado madera seca: +2.');}
        else if(r<.9){game.resources.dew+=3;log('Un pequeño manantial te regala 3 de rocío.');}
        else meetCreature();break;
      }
      case 'build': {
        if(game.shelter>=3)throw Error('Ya has construido todos los refugios disponibles.');
        if(game.resources.wood<3||game.resources.petals<2)throw Error('Necesitas 3 maderas y 2 pétalos para construir.');
        useEnergy(2);spend({wood:3,petals:2});game.shelter++;log('Has construido un refugio acogedor. Quizá alguien venga a visitarlo.');break;
      }
      case 'end_day': {
        game.plots.forEach((p,i)=>{if(p&&!p.grown){p.days_left--;p.watered=false;if(p.days_left<=0)grow(i);}});
        game.day++;game.energy=game.max_energy;game.weather=weatherTypes[Math.floor(Math.random()*weatherTypes.length)];
        if(game.weather==='Llovizna')game.plots.forEach((p,i)=>{if(p&&!p.grown){p.days_left=Math.max(0,p.days_left-1);if(p.days_left===0)grow(i);}});
        if(game.shelter&&Math.random()<Math.min(.35+game.shelter*.18,.85))meetCreature();
        log('Amanece el día '+game.day+'. El tiempo: '+game.weather.toLowerCase()+'.');break;
      }
      default: throw Error('Acción no reconocida.');
    }
    save();render();
  }
  function act(action,data) { try { perform(action,data); } catch(e) { notify(e.message || 'No se pudo realizar esa acción.'); } }
  function setText(id,value) { const el=$(id);if(el)el.textContent=value; }
  function render() {
    setText('day-label','DÍA '+game.day);setText('weather-label',game.weather);
    for(const k of ['dew','seeds','wood','petals'])setText(k,game.resources[k]||0);
    setText('energy-label',game.energy+' / '+game.max_energy);
    const energyFill=$('energy-fill');if(energyFill)energyFill.style.width=(100*game.energy/game.max_energy)+'%';
    setText('weather-note',({'Brisa':'Una brisa recorre las hojas','Llovizna':'La lluvia acaricia la tierra','Sol suave':'El sol calienta el claro','Niebla luminosa':'La niebla trae calma'})[game.weather]||'El claro respira');
    const grid=$('garden-grid');
    if(grid) {
      grid.replaceChildren();
      game.plots.forEach((p,i)=>{
        const b=document.createElement('button');b.type='button';b.className='plot '+(!p?'empty ':'')+(selectedPlot===i?'selected':'');
        b.setAttribute('aria-label',p?plants[p.kind].name+', parcela '+(i+1):'Parcela vacía '+(i+1));
        if(p){const e=document.createElement('span');e.className='plant-emoji';e.textContent=p.grown?'🌸':plants[p.kind].emoji;
          const c=document.createElement('span');c.className='plot-caption';c.textContent=p.grown?'LISTA':p.days_left+' DÍA(S)';b.append(e,c);
          if(p.grown){const r=document.createElement('span');r.className='ready';r.textContent='✦';b.append(r);}}
        b.addEventListener('click',()=>{selectedPlot=i;render();});grid.append(b);
      });
    }
    const p=game.plots[selectedPlot];
    setText('plot-hint',p?(p.grown?'¡Ha florecido! Ya puedes recoger tu cosecha.':p.watered?'Esta planta ya ha recibido agua hoy.':'Tu brote está creciendo. Puedes regarlo para acelerar el proceso.'):'Parcela '+(selectedPlot+1)+': un pequeño espacio listo para una nueva vida.');
    const setDisabled=(id,value)=>{const el=$(id);if(el)el.disabled=value;};
    setDisabled('plant-button',!!p||game.energy<1);setDisabled('water-button',!p||p.grown||p.watered||game.energy<1||game.resources.dew<1);
    setDisabled('harvest-button',!p||!p.grown);setDisabled('gather-button',game.energy<1);setDisabled('explore-button',game.energy<2);setDisabled('build-button',game.energy<2||game.shelter>=3||game.resources.wood<3||game.resources.petals<2);
    const m=game.mission;setText('mission-text',m.text);setText('mission-count',Math.min(m.progress,m.target)+' / '+m.target);
    const mf=$('mission-fill');if(mf)mf.style.width=Math.min(100,100*m.progress/m.target)+'%';setText('mission-status',m.done?'COMPLETADO':'EN CURSO');
    setText('shelter-count',game.shelter+' refugios · 3 madera + 2 pétalos');
    const dots=$('shelter-dots');if(dots)Array.from(dots.children).forEach((d,i)=>d.classList.toggle('active',i<game.shelter));
    setText('visitor-count',game.creatures.length+' / 4');
    const list=$('visitor-list');if(list){list.replaceChildren();if(!game.creatures.length){const e=document.createElement('p');e.className='empty-visitors';e.textContent='Todavía no hay huellas. La naturaleza tiene su propio ritmo.';list.append(e);}
      else game.creatures.forEach(c=>{const row=document.createElement('div');row.className='visitor';const icon=document.createElement('span');icon.className='visitor-emoji';icon.textContent=c.emoji;
        const info=document.createElement('span'),name=document.createElement('b'),hint=document.createElement('small');name.textContent=c.name;hint.textContent=c.hint;info.append(name,hint);row.append(icon,info);list.append(row);});}
    const journal=$('journal-list');if(journal){journal.replaceChildren();game.log.slice(0,4).forEach(entry=>{const e=document.createElement('div');e.className='journal-entry';e.textContent=entry;journal.append(e);});}
    setText('score',game.score);
  }
  function bind(id,event,fn){const el=$(id);if(el)el.addEventListener(event,fn);}
  function init() {
    bind('plant-button','click',()=>act('plant',{plot:selectedPlot,kind:selectedSeed}));
    bind('water-button','click',()=>act('water',{plot:selectedPlot}));
    bind('harvest-button','click',()=>act('harvest',{plot:selectedPlot}));
    bind('gather-button','click',()=>act('gather'));
    bind('explore-button','click',()=>act('explore'));
    bind('build-button','click',()=>act('build'));
    bind('end-day-button','click',()=>act('end_day'));
    document.querySelectorAll('.seed-choice').forEach(b=>b.addEventListener('click',()=>{
      selectedSeed=b.dataset.kind;document.querySelectorAll('.seed-choice').forEach(x=>x.classList.toggle('selected',x===b));
    }));
    bind('help-button','click',()=>{const d=$('help-dialog');if(d&&typeof d.showModal==='function')d.showModal();else notify('Cuida el jardín: planta, riega, cosecha y pasa de día para recuperar energía.');});
    bind('close-help','click',()=>{const d=$('help-dialog');if(d&&d.close)d.close();});
    bind('got-it','click',()=>{const d=$('help-dialog');if(d&&d.close)d.close();});
    bind('reset-button','click',()=>{if(!window.confirm('¿Seguro que quieres empezar una partida nueva? Se reiniciará tu progreso actual.'))return;game=freshGame();selectedPlot=0;save();render();notify('El claro vuelve a empezar. ¡A cuidarlo!');});
    render();
    document.documentElement.classList.add('game-ready');
  }
  window.addEventListener('error',e=>{notify('Error del juego: '+(e.message||'comprueba la carga de game.js'));});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
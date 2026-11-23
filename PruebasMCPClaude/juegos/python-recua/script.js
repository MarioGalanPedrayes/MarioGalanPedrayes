// Recua: interfaz. Las reglas viven en codigo.py (Python con Pyodide);
// este archivo solo dibuja el estado que devuelve Python y le pasa las acciones.
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const CLAVE = "recua-v1";
  const NS = "http://www.w3.org/2000/svg";

  let py = null;
  const fn = {};
  let st = null;              // ultimo estado devuelto por Python
  let modo = "diario";
  let diarioISO = "";
  let nivel = "normal";       // nivel de la practica
  let sel = 0;                // sitio elegido en el mapa (para ver su ficha)
  let confirmaReiniciar = false;
  let idMapa = "";
  let premioNuevo = {};       // sellos nuevos ganados en esta sesion, por viaje
  let cargado = false;

  const DESC = {
    valle: "Último sitio barato antes de subir: pan y sacos a precio fijo.",
    aldea: "Pan y descanso para las mulas, a cambio de monedas.",
    almacen: "Aquí se cargan sacos de mercancía para venderlos más arriba.",
    feria: "Se venden sacos, normalmente a mejor precio que en la cumbre.",
    paso: "Hay que decidir cómo pasar antes de seguir: cruzar cuesta ánimo y rodear cuesta panes.",
    encuentro: "Alguien sale al camino. Ves lo que cuesta, pero no cómo acaba: puede salir bien o mal.",
    ermita: "Descanso gratis, pero solo puedes elegir una cosa.",
  };

  // ---------- utilidades ----------
  function el(tag, clase, texto) {
    const e = document.createElement(tag);
    if (clase) e.className = clase;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }
  const pad = (n) => String(n).padStart(2, "0");
  function hoyISO() {
    const d = new Date();
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  }
  function fechaLarga(iso) {
    const [y, m, d] = iso.split("-").map(Number);
    return new Date(y, m - 1, d).toLocaleDateString("es-ES", { day: "numeric", month: "long", year: "numeric" });
  }
  function leer() {
    try { return JSON.parse(localStorage.getItem(CLAVE)) || {}; } catch (e) { return {}; }
  }
  function escribir(datos) {
    try { localStorage.setItem(CLAVE, JSON.stringify(datos)); } catch (e) { /* sin almacenamiento */ }
  }
  const llamar = (nombre, ...args) => JSON.parse(fn[nombre](...args));
  function mensaje(texto, error) {
    const m = $("mensaje");
    m.textContent = texto || "";
    m.classList.toggle("error", !!error);
  }
  const plural = (n, uno, varios) => (n === 1 ? uno : varios);
  const nodo = (id) => st.nodos[id];

  // ---------- mapa ----------
  function centro(n) {
    return { x: (n.col + 0.5) / 3 * 300, y: (st.ultima_etapa - n.etapa + 0.5) * 100 };
  }

  function construirMapa() {
    const m = $("mapa");
    m.replaceChildren();
    const filas = st.ultima_etapa + 1;
    m.style.setProperty("--filas", String(filas));
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 300 ${filas * 100}`);
    svg.setAttribute("preserveAspectRatio", "none");
    svg.setAttribute("aria-hidden", "true");
    st.nodos.forEach((n) => {
      n.salidas.forEach((s) => {
        const a = centro(n), b = centro(nodo(s));
        const l = document.createElementNS(NS, "line");
        l.setAttribute("x1", a.x); l.setAttribute("y1", a.y);
        l.setAttribute("x2", b.x); l.setAttribute("y2", b.y);
        l.dataset.a = String(n.id);
        l.dataset.b = String(s);
        svg.append(l);
      });
    });
    m.append(svg);
    st.nodos.forEach((n) => {
      const b = el("button", `nodo tipo-${n.tipo}`);
      b.type = "button";
      b.dataset.id = String(n.id);
      b.style.setProperty("--col", String(n.col));
      b.style.setProperty("--r", String(st.ultima_etapa - n.etapa));
      const ins = el("span", "ins", n.letra);
      ins.setAttribute("aria-hidden", "true");
      const et = el("span", "et", n.etiqueta);
      const marca = el("span", "marca");
      marca.setAttribute("aria-hidden", "true");
      b.append(ins, et, marca);
      m.append(b);
    });
    idMapa = st.id_partida;
  }

  function descripcionNodo(n) {
    let estado;
    if (n.id === st.actual) estado = "Estás aquí";
    else if (st.ruta.includes(n.id)) estado = "Ya pasaste por aquí";
    else if (st.destinos.some((d) => d.id === n.id)) estado = "Hay sendero desde donde estás";
    else estado = "No hay sendero directo desde donde estás";
    return `${n.etiqueta}: ${n.nombre}. Etapa ${n.etapa} de ${st.ultima_etapa}. ${estado}.`;
  }

  function pintarMapa() {
    if (idMapa !== st.id_partida || $("mapa").querySelectorAll(".nodo").length !== st.nodos.length) construirMapa();
    const vecinos = new Set(st.destinos.map((d) => d.id));
    const legales = new Set(st.destinos.filter((d) => d.legal).map((d) => d.id));
    const visitados = new Set(st.ruta);
    $("mapa").querySelectorAll(".nodo").forEach((b) => {
      const id = Number(b.dataset.id);
      const n = nodo(id);
      const visitado = visitados.has(id) && id !== st.actual;
      b.className = `nodo tipo-${n.tipo}`;
      if (id === st.actual) b.classList.add("actual");
      else if (visitado) b.classList.add("visitado");
      else if (vecinos.has(id)) b.classList.add("alcanzable");
      else b.classList.add("lejano");
      if (id === sel) b.classList.add("seleccionado");
      if (st.pista === `m${id}`) b.classList.add("pista-nodo");
      b.querySelector(".marca").textContent = id === st.actual ? "aquí" : (visitado ? "✓" : "");
      b.setAttribute("aria-label", descripcionNodo(n) + (st.pista === `m${id}` ? " Sitio sugerido." : ""));
      b.setAttribute("aria-pressed", String(id === sel));
      b.tabIndex = id === sel ? 0 : -1;
    });
    const hechos = new Set();
    for (let i = 0; i + 1 < st.ruta.length; i++) hechos.add(`${st.ruta[i]}-${st.ruta[i + 1]}`);
    $("mapa").querySelectorAll("line").forEach((l) => {
      const a = Number(l.dataset.a), b = Number(l.dataset.b);
      l.setAttribute("class", hechos.has(`${a}-${b}`) ? "hecho" : (a === st.actual && legales.has(b) ? "posible" : ""));
    });
  }

  // ---------- ficha del sitio elegido ----------
  function filaOferta(o, i, esActual, fin) {
    const li = el("li");
    if (esActual && st.pista === `o${o.k}`) li.classList.add("pista-oferta");
    li.append(el("span", "oferta-txt", `${esActual && i < 9 ? `${i + 1}. ` : ""}${o.txt}`));
    li.append(el("span", "efecto", `(${o.efecto})`));
    if (o.azar) li.append(el("span", "azar", o.adivina || "Resultado oculto: puede salir bien o mal."));
    if (esActual && !fin) {
      const e = st.ofertas_estado[o.k];
      if (e.usada) {
        li.append(el("span", "hecho", "✓ Hecho"));
      } else {
        const b = el("button", "boton chico", "Hacer");
        b.type = "button";
        b.dataset.accion = `o${o.k}`;
        b.dataset.foco = `o${o.k}`;
        b.disabled = !e.legal;
        b.setAttribute("aria-label", `Hacer: ${o.txt} (${o.efecto})`);
        li.append(b);
        if (!e.legal && e.motivo) li.append(el("span", "no", e.motivo));
      }
    }
    return li;
  }

  function pintarFicha() {
    const f = $("ficha");
    f.replaceChildren();
    const n = nodo(sel);
    const esActual = sel === st.actual;
    const fin = st.resultado !== "jugando";
    f.append(el("h3", "", n.nombre));
    const estado = esActual ? " · estás aquí" : (st.ruta.includes(sel) ? " · ya pasaste por aquí" : "");
    f.append(el("p", "tipo-linea", `${n.etiqueta} · etapa ${n.etapa} de ${st.ultima_etapa}${estado}`));
    f.append(el("p", "", n.tipo === "cumbre"
      ? `El mercado final compra cada saco a ${st.precio_cumbre} monedas. Ganas si monedas + sacos × ${st.precio_cumbre} llega a ${st.objetivo}.`
      : DESC[n.tipo]));
    if (n.ofertas.length) {
      if (n.obligatorio && esActual && !fin) f.append(el("p", "pequeno", "Hay que elegir una de las dos opciones para poder seguir."));
      const ul = el("ul");
      n.ofertas.forEach((o, i) => ul.append(filaOferta(o, i, esActual, fin)));
      f.append(ul);
    }
    if (esActual && !fin && st.destinos.length) {
      f.append(el("h3", "", "Seguir el viaje"));
      const ul = el("ul");
      st.destinos.forEach((d) => {
        const dn = nodo(d.id);
        const li = el("li");
        if (st.pista === `m${d.id}`) li.classList.add("pista-oferta");
        li.append(el("span", "oferta-txt", `${dn.etiqueta}: ${dn.nombre}`));
        const b = el("button", "boton chico", "Ir allí");
        b.type = "button";
        b.dataset.accion = `m${d.id}`;
        b.dataset.foco = `m${d.id}`;
        b.disabled = !d.legal;
        b.setAttribute("aria-label", `Ir a ${dn.nombre} (${dn.etiqueta})`);
        li.append(b);
        if (!d.legal && d.motivo) li.append(el("span", "no", d.motivo));
        ul.append(li);
      });
      f.append(ul);
      f.append(el("p", "pequeno", "Cada tramo gasta 1 pan. Si no queda, la recua pierde 2 de ánimo."));
    } else if (!esActual && !fin) {
      const d = st.destinos.find((x) => x.id === sel);
      if (d) {
        const b = el("button", "boton chico principal", "Ir a este sitio");
        b.type = "button";
        b.dataset.accion = `m${sel}`;
        b.dataset.foco = `m${sel}`;
        b.disabled = !d.legal;
        f.append(b);
        if (!d.legal && d.motivo) f.append(el("p", "no pequeno", d.motivo));
      } else if (st.ruta.includes(sel)) {
        f.append(el("p", "pequeno", "Ya lo has dejado atrás: no se puede volver."));
      } else if (n.etapa <= nodo(st.actual).etapa) {
        f.append(el("p", "pequeno", "Está en una etapa que ya has pasado."));
      } else {
        f.append(el("p", "pequeno", "No hay sendero directo desde donde estás. Mira qué sitios de la etapa siguiente llevan hasta aquí."));
      }
    }
  }

  // ---------- dibujo general ----------
  function pintar() {
    const r = st.recursos;
    const fin = st.resultado !== "jugando";
    $("c-pan").textContent = `${r.pan}/${r.pan_max}`;
    $("c-animo").textContent = `${r.animo}/${r.animo_max}`;
    $("c-monedas").textContent = String(r.monedas);
    $("c-carga").textContent = `${r.carga}/${r.capacidad}`;
    $("c-valor").textContent = String(st.valor_ahora);
    $("c-objetivo").textContent = String(st.objetivo);
    $("c-ref").textContent = String(st.ref);
    $("c-pistas").textContent = `${st.pistas}/${st.max_pistas}`;
    $("c-pan").closest("div").classList.toggle("bajo", r.pan === 0);
    $("c-animo").closest("div").classList.toggle("bajo", r.animo <= 3);
    $("titulo-partida").textContent = st.modo === "diario"
      ? `Reto diario del ${fechaLarga(st.fecha)} · ${st.nombre_nivel} · sin mejoras`
      : `Práctica · ${st.nombre_nivel}${Object.keys(st.mejoras).length ? " · con tus mejoras" : ""}`;
    $("alerta-viable").hidden = fin || st.viable !== false;
    $("pista").disabled = fin || st.pistas >= st.max_pistas;
    $("reiniciar").disabled = false;

    pintarMapa();
    pintarFicha();

    const aqui = nodo(st.actual);
    $("resumen").textContent = fin
      ? st.motivo
      : `Estás en ${aqui.nombre}, etapa ${aqui.etapa} de ${st.ultima_etapa}. Tienes ${r.pan} ${plural(r.pan, "pan", "panes")}, ${r.animo} de ánimo, ${r.monedas} monedas y ${r.carga} ${plural(r.carga, "saco", "sacos")}. Valor si llegas ya: ${st.valor_ahora}; objetivo: ${st.objetivo}.`;
    mostrarResultado();
  }

  function mostrarResultado() {
    const r = $("resultado");
    if (st.resultado === "jugando") { r.hidden = true; return; }
    r.hidden = false;
    const gana = st.resultado === "ganada";
    r.classList.toggle("derrota", !gana);
    $("resultado-titulo").textContent = gana
      ? "★".repeat(st.estrellas) + "☆".repeat(3 - st.estrellas) + " ¡Cumbre!"
      : "No ha podido ser";
    $("resultado-texto").textContent = gana
      ? `${st.motivo} El objetivo era ${st.objetivo} y la referencia, ${st.ref}.${st.pistas ? " Con pistas, la nota máxima es de dos estrellas." : ""}`
      : `${st.motivo} Puedes reiniciar el viaje: el mapa y los encuentros salen igual, así que ya sabes algo más.`;
    const nuevos = premioNuevo[st.id_partida] || 0;
    $("resultado-sellos").textContent = st.sellos > 0
      ? `Sellos de este viaje: ${st.sellos}${nuevos ? ` (${nuevos} ${plural(nuevos, "nuevo", "nuevos")} para tu cuadra)` : " (ya contados)"}.`
      : "Este viaje no da sellos.";
    $("bloque-compartir").hidden = false;
    $("compartir-texto").textContent = fn.compartir();
    $("otra").hidden = st.modo === "diario";
  }

  // ---------- guardado ----------
  function guardarProgreso() {
    if (!cargado) return;
    const datos = leer();
    const base = { acciones: st.acciones, pistas: st.pistas, terminado: st.resultado !== "jugando", gano: st.resultado === "ganada", estrellas: st.estrellas };
    if (st.modo === "diario") {
      datos.diario = datos.diario || {};
      const ya = datos.diario[st.fecha];
      // Un reto ganado queda fijado: no se sobrescribe con una repeticion.
      if (ya && ya.terminado && ya.gano && st.resultado !== "ganada") return;
      datos.diario[st.fecha] = base;
    } else {
      datos.practica = Object.assign({ semilla: st.semilla, nivel: st.nivel, mejoras: st.mejoras }, base);
    }
    escribir(datos);
  }

  function registrarFin() {
    const datos = leer();
    if (st.modo === "diario") {
      datos.diario = datos.diario || {};
      const ya = datos.diario[st.fecha];
      if (!ya || !ya.terminado) {
        datos.diario[st.fecha] = { acciones: st.acciones, pistas: st.pistas, terminado: true, gano: st.resultado === "ganada", estrellas: st.estrellas };
      }
    }
    datos.premios = datos.premios || {};
    const previo = datos.premios[st.id_partida] || 0;
    if (st.sellos > previo) {
      const nuevos = st.sellos - previo;
      premioNuevo[st.id_partida] = (premioNuevo[st.id_partida] || 0) + nuevos;
      datos.premios[st.id_partida] = st.sellos;
      datos.sellos = (datos.sellos || 0) + nuevos;
      const claves = Object.keys(datos.premios);
      if (claves.length > 60) delete datos.premios[claves[0]];
    }
    escribir(datos);
    pintarStats();
    pintarMejoras();
    mostrarResultado();
  }

  // ---------- acciones ----------
  function reenfocar(clave) {
    if (!clave) return;
    const b = $("ficha").querySelector(`[data-foco="${clave}"]`);
    if (b && !b.disabled) { b.focus(); return; }
    const otro = $("ficha").querySelector("button:not(:disabled)");
    if (otro) otro.focus();
    else {
      const n = $("mapa").querySelector(`.nodo[data-id="${sel}"]`);
      if (n) n.focus();
    }
  }

  function ejecutar(codigo) {
    if (!st || st.resultado !== "jugando") return;
    confirmaReiniciar = false;
    const antes = st.actual;
    const nuevo = llamar("accion", codigo);
    st = nuevo;
    if (st.actual !== antes) sel = st.actual;
    pintar();
    mensaje(st.error || st.mensaje, !!st.error);
    guardarProgreso();
    if (st.resultado !== "jugando") {
      registrarFin();
      const n = $("mapa").querySelector(`.nodo[data-id="${sel}"]`);
      if (n) n.focus();
    } else {
      reenfocar(codigo.startsWith("m") ? `o0` : codigo);
    }
  }

  function pedirPista() {
    if (!st || st.resultado !== "jugando") return;
    const nuevo = llamar("pista");
    st = nuevo;
    if (st.pista && st.pista.startsWith("m")) sel = Number(st.pista.slice(1));
    pintar();
    guardarProgreso();
    if (st.error) { mensaje(st.error, true); return; }
    if (st.pista.startsWith("m")) {
      mensaje(`Pista: sigue hacia ${nodo(Number(st.pista.slice(1))).nombre}. Con pistas la nota máxima es de dos estrellas.`);
    } else {
      const o = nodo(st.actual).ofertas.find((x) => `o${x.k}` === st.pista);
      mensaje(`Pista: prueba «${o ? o.txt : "esa oferta"}» antes de seguir. Con pistas la nota máxima es de dos estrellas.`);
    }
  }

  function nuevaPartida(forzarNueva) {
    confirmaReiniciar = false;
    mensaje("");
    const datos = leer();
    if (modo === "diario") {
      diarioISO = hoyISO();
      const g = datos.diario && datos.diario[diarioISO];
      st = g
        ? llamar("reconstruir", "diario", "normal", diarioISO, JSON.stringify(g.acciones), g.pistas)
        : llamar("nueva", "diario", "normal", diarioISO);
    } else {
      const g = datos.practica;
      if (!forzarNueva && g && !g.terminado && g.nivel === nivel) {
        st = llamar("reconstruir", "practica", nivel, String(g.semilla), JSON.stringify(g.acciones), g.pistas, JSON.stringify(g.mejoras || {}));
      } else {
        const semilla = Math.floor(Math.random() * 4294967296);
        st = llamar("nueva", "practica", nivel, String(semilla), JSON.stringify(datos.mejoras || {}));
      }
    }
    sel = st.actual;
    construirMapa();
    pintar();
    pintarStats();
    pintarMejoras();
    guardarProgreso();
  }

  function pintarStats() {
    const datos = leer();
    const dias = Object.entries(datos.diario || {}).filter(([, v]) => v.gano).map(([k]) => k);
    const r = llamar("racha", JSON.stringify(dias), hoyISO());
    $("st-racha").textContent = String(r.actual);
    $("st-mejor-racha").textContent = String(r.mejor);
    $("st-completados").textContent = String(dias.length);
    $("st-tres").textContent = String(Object.values(datos.diario || {}).filter((v) => v.gano && v.estrellas === 3).length);
  }

  // ---------- la cuadra (mejoras permanentes) ----------
  function pintarMejoras() {
    const datos = leer();
    const sellos = datos.sellos || 0;
    $("sellos").textContent = String(sellos);
    const ul = $("mejoras");
    ul.replaceChildren();
    llamar("catalogo_mejoras", JSON.stringify(datos.mejoras || {})).forEach((m) => {
      const li = el("li");
      const info = el("div", "m-info");
      const t = el("strong", "", m.nombre);
      info.append(t, el("span", "nivel", ` · nivel ${m.nivel}/${m.max}`), el("small", "", m.desc));
      const b = el("button", "boton chico", m.coste === null ? "Al máximo" : `Comprar · ${m.coste} ${plural(m.coste, "sello", "sellos")}`);
      b.type = "button";
      b.disabled = m.coste === null || sellos < m.coste;
      b.setAttribute("aria-label", m.coste === null ? `${m.nombre}: al máximo` : `Comprar ${m.nombre}, nivel ${m.nivel + 1}, cuesta ${m.coste} sellos`);
      b.addEventListener("click", () => comprar(m.clave, m.nombre));
      li.append(info, b);
      ul.append(li);
    });
  }

  function comprar(clave, nombre) {
    const datos = leer();
    const r = llamar("comprar_mejora", JSON.stringify(datos.mejoras || {}), clave, datos.sellos || 0);
    const m = $("mensaje-mejoras");
    if (!r.ok) {
      m.textContent = r.error;
      m.classList.add("error");
      return;
    }
    datos.mejoras = r.mejoras;
    datos.sellos = r.sellos;
    escribir(datos);
    m.classList.remove("error");
    m.textContent = `${nombre} mejorada. Vale desde el próximo viaje de práctica.`;
    pintarMejoras();
  }

  function cambiarModo(m) {
    modo = m;
    $("modo-diario").classList.toggle("activo", m === "diario");
    $("modo-practica").classList.toggle("activo", m === "practica");
    $("modo-diario").setAttribute("aria-pressed", String(m === "diario"));
    $("modo-practica").setAttribute("aria-pressed", String(m === "practica"));
    $("fila-nivel").hidden = m !== "practica";
    nuevaPartida(false);
  }

  // ---------- eventos ----------
  function moverSeleccion(tecla) {
    const n = nodo(sel);
    let candidatos;
    if (tecla === "ArrowUp") candidatos = st.nodos.filter((x) => x.etapa === n.etapa + 1);
    else if (tecla === "ArrowDown") candidatos = st.nodos.filter((x) => x.etapa === n.etapa - 1);
    else if (tecla === "ArrowLeft") candidatos = st.nodos.filter((x) => x.etapa === n.etapa && x.col < n.col).sort((a, b) => b.col - a.col);
    else candidatos = st.nodos.filter((x) => x.etapa === n.etapa && x.col > n.col).sort((a, b) => a.col - b.col);
    if (!candidatos.length) return;
    if (tecla === "ArrowUp" || tecla === "ArrowDown") candidatos.sort((a, b) => Math.abs(a.col - n.col) - Math.abs(b.col - n.col));
    sel = candidatos[0].id;
    pintar();
    const b = $("mapa").querySelector(`.nodo[data-id="${sel}"]`);
    if (b) b.focus();
  }

  function enlazar() {
    $("mapa").addEventListener("click", (e) => {
      const b = e.target.closest(".nodo");
      if (!b || !st) return;
      sel = Number(b.dataset.id);
      pintar();
      b.focus();
    });
    $("mapa").addEventListener("keydown", (e) => {
      if (!st || !e.target.closest(".nodo")) return;
      if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.key)) {
        e.preventDefault();
        moverSeleccion(e.key);
      }
    });
    $("ficha").addEventListener("click", (e) => {
      const b = e.target.closest("button[data-accion]");
      if (b && !b.disabled) ejecutar(b.dataset.accion);
    });
    document.addEventListener("keydown", (e) => {
      if (e.ctrlKey || e.metaKey || e.altKey || !st) return;
      const tag = (e.target.tagName || "").toLowerCase();
      if (tag === "select" || tag === "input" || tag === "textarea") return;
      if (e.key === "p" || e.key === "P") { pedirPista(); return; }
      if (st.resultado !== "jugando") return;
      if (e.key === "i" || e.key === "I") {
        const d = st.destinos.find((x) => x.id === sel);
        if (d && d.legal) ejecutar(`m${sel}`);
        else mensaje(d ? d.motivo : "Elige primero un sitio con sendero desde donde estás.", true);
      } else if (/^[1-9]$/.test(e.key)) {
        const o = nodo(st.actual).ofertas[Number(e.key) - 1];
        if (!o) return;
        const est = st.ofertas_estado[o.k];
        if (est.legal) ejecutar(`o${o.k}`);
        else mensaje(est.motivo || "Eso no se puede hacer ahora.", true);
      }
    });
    $("pista").addEventListener("click", pedirPista);
    $("reiniciar").addEventListener("click", () => {
      if (!st) return;
      if (st.acciones.length > 0 && st.resultado === "jugando" && !confirmaReiniciar) {
        confirmaReiniciar = true;
        mensaje("Pulsa «Reiniciar viaje» otra vez para volver al valle. El mapa y los encuentros serán los mismos.");
        return;
      }
      confirmaReiniciar = false;
      st = llamar("reiniciar");
      sel = st.actual;
      pintar();
      mensaje("Viaje reiniciado.");
      guardarProgreso();
    });
    $("modo-diario").addEventListener("click", () => cambiarModo("diario"));
    $("modo-practica").addEventListener("click", () => cambiarModo("practica"));
    $("nivel").addEventListener("change", (e) => { nivel = e.target.value; nuevaPartida(true); });
    $("otra").addEventListener("click", () => nuevaPartida(true));
    $("copiar").addEventListener("click", async () => {
      const texto = $("compartir-texto").textContent;
      try {
        await navigator.clipboard.writeText(texto);
        mensaje("Resultado copiado.");
      } catch (e) {
        mensaje("No se ha podido copiar solo; selecciona el texto y cópialo a mano.", true);
      }
    });
  }

  // ---------- arranque ----------
  let arrancado = false;
  async function iniciar() {
    if (arrancado) return;   // por si el evento de carga llegara dos veces
    arrancado = true;
    const aviso = $("estado-carga");
    try {
      if (typeof loadPyodide !== "function") throw new Error("pyodide.js no se ha cargado");
      py = await loadPyodide();
      const resp = await fetch("codigo.py");
      if (!resp.ok) throw new Error("no se pudo leer codigo.py");
      const codigo = await resp.text();
      $("python-source").textContent = codigo;
      py.runPython(codigo);
      ["nueva", "reconstruir", "accion", "reiniciar", "pista", "compartir", "racha", "catalogo_mejoras", "comprar_mejora"].forEach((n) => { fn[n] = py.globals.get(n); });
      aviso.hidden = true;
      ["modo-diario", "modo-practica"].forEach((id) => { $(id).disabled = false; });
      enlazar();
      cambiarModo("diario");
      cargado = true;
      guardarProgreso();
    } catch (err) {
      aviso.hidden = false;
      aviso.textContent = "No se ha podido cargar el motor de Python (Pyodide). Hace falta conexión para descargarlo desde su CDN. Recarga la página o prueba más tarde. Detalle: " + err.message;
      try {
        const r = await fetch("codigo.py");
        if (r.ok) $("python-source").textContent = await r.text();
      } catch (e) { /* sin red */ }
    }
  }

  window.addEventListener("DOMContentLoaded", iniciar);
})();

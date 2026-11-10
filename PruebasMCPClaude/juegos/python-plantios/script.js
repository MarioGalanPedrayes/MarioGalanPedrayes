// Plantíos: interfaz. Las reglas viven en codigo.py (Python con Pyodide);
// este archivo solo dibuja el estado que devuelve Python y le pasa las acciones.
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const CLAVE = "plantios-v1";
  const PLURAL = { semilla: "semillas", brote: "brotes", "plantón": "plantones", manzano: "manzanos", pumar: "pumares", pumarada: "pumaradas" };

  let py = null;
  const fn = {};
  let st = null;              // último estado devuelto por Python
  let modo = "diario";
  let diarioISO = "";
  let nivel = "normal";       // nivel de la práctica
  let foco = 0;               // casilla con el foco del teclado
  let pistaVista = null;      // {tipo, fila, col}, hasta la siguiente acción
  let confirmaReiniciar = null;
  let verFusiones = true;

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
  const nombrePieza = (v) => st.piezas[String(v)].nombre;
  const plural = (nombre) => PLURAL[nombre] || nombre + "s";

  // ---------- dibujo ----------
  function pieza(valor) {
    const cod = st.codigos;
    if (valor === cod.savia) {
      const s = el("span", "pieza savia", "S");
      s.setAttribute("aria-hidden", "true");
      return s;
    }
    if (valor === cod.piedra) {
      const s = el("span", "pieza piedra", "piedra");
      s.setAttribute("aria-hidden", "true");
      return s;
    }
    const d = st.piezas[String(valor)];
    const s = el("span", `pieza ${d.forma}`, String(valor));
    s.style.setProperty("--c", d.color);
    s.style.setProperty("--t", d.tinta);
    s.setAttribute("aria-hidden", "true");
    return s;
  }
  function describir(valor) {
    const cod = st.codigos;
    if (valor === 0) return "vacía";
    if (valor === cod.savia) return "savia";
    if (valor === cod.piedra) return "piedra";
    return `${nombrePieza(valor)}, nivel ${valor}`;
  }
  const nombreActual = () => describir(st.actual);

  function construirTablero() {
    const t = $("tablero");
    t.replaceChildren();
    t.style.setProperty("--cols", String(st.cols));
    for (let i = 0; i < st.filas * st.cols; i++) {
      const b = el("button", "casilla");
      b.type = "button";
      b.dataset.i = String(i);
      b.tabIndex = i === foco ? 0 : -1;
      t.append(b);
    }
  }

  function textoFusiones(eventos) {
    return eventos.map((e) => {
      let t = `${e.n} ${plural(nombrePieza(e.desde))} se funden en ${e.hasta - e.desde === 2 ? "un injerto doble: " : ""}${nombrePieza(e.hasta)}`;
      if (e.piedras) t += `; se ${e.piedras === 1 ? "deshace 1 piedra" : "deshacen " + e.piedras + " piedras"}`;
      return t;
    }).join(". Después, ");
  }

  function pintar() {
    if ($("tablero").children.length !== st.filas * st.cols) { foco = 0; construirTablero(); }
    const jugando = st.estado === "jugando";
    const nuevas = new Set((st.ultimo || []).map((e) => e.casilla));
    const prev = st.previsiones || [];

    [...$("tablero").children].forEach((b, i) => {
      b.replaceChildren();
      const v = st.tab[i];
      const f = Math.floor(i / st.cols), c = i % st.cols;
      if (v !== 0) b.append(pieza(v));
      const fusiona = jugando && verFusiones && v === 0 && prev[i] > 0;
      if (fusiona) b.append(el("span", "fusion", `→${prev[i]}`));
      b.classList.toggle("ocupada", v !== 0);
      b.classList.toggle("nueva", nuevas.has(i));
      b.classList.toggle("fusiona", fusiona);
      b.classList.toggle("pista-casilla", !!pistaVista && pistaVista.fila === f && pistaVista.col === c);
      let etiqueta = `Fila ${f + 1}, columna ${c + 1}: ${describir(v)}`;
      if (jugando && v === 0 && prev[i] > 0) etiqueta += `. Si pones aquí ${nombreActual()}, se funde en ${nombrePieza(prev[i])}`;
      b.setAttribute("aria-label", etiqueta);
    });
    $("tablero").classList.toggle("fin", !jugando);

    // mano
    $("actual").replaceChildren(pieza(st.actual));
    $("actual-nombre").textContent = nombreActual();
    $("actual").setAttribute("aria-label", `Pieza actual: ${nombreActual()}`);
    $("siguientes").replaceChildren(...st.siguientes.map((v) => {
      const s = pieza(v);
      s.setAttribute("aria-hidden", "false");
      s.setAttribute("role", "img");
      s.setAttribute("aria-label", `Siguiente: ${describir(v)}`);
      return s;
    }));
    const cesto = $("cesto");
    cesto.replaceChildren(st.cesto === null ? el("span", "", "vacío") : pieza(st.cesto));
    cesto.disabled = !st.puede_cambiar;
    cesto.setAttribute("aria-label", st.cesto === null
      ? "Cesto vacío. Guardar la pieza actual y recibir la siguiente"
      : `Cesto con ${describir(st.cesto)}. Cambiar por la pieza actual`);

    $("c-turnos").textContent = st.turnos;
    $("c-ref").textContent = st.referencia === null ? "–" : st.referencia;
    $("c-objetivo").textContent = nombrePieza(st.objetivo);
    $("c-pistas").textContent = `${st.pistas}/${st.pistas_max}`;

    const libres = st.tab.filter((x) => x === 0).length;
    $("resumen").textContent =
      `Pieza actual: ${nombreActual()}. Turno ${st.turnos}. ${libres} casillas libres. Objetivo: ${nombrePieza(st.objetivo)}.`;

    $("cambiar").disabled = !st.puede_cambiar;
    $("deshacer").disabled = !st.puede_deshacer;
    $("pista").disabled = !jugando || st.pistas >= st.pistas_max;
    $("reiniciar").disabled = !(st.historial && st.historial.length);
    if (!jugando) quitarConfirmacion();

    $("titulo-partida").textContent = modo === "diario"
      ? `Reto del ${fechaLarga(diarioISO)} (${st.nivel_nombre.toLowerCase()}, ${st.filas}×${st.cols}): las mismas piezas para todo el mundo. Objetivo: criar un ${nombrePieza(st.objetivo)}.`
      : `Práctica · ${st.nivel_nombre} (${st.filas}×${st.cols}). Objetivo: criar un ${nombrePieza(st.objetivo)}.`;

    const fin = st.estado !== "jugando";
    $("resultado").hidden = !fin;
    $("resultado").classList.toggle("derrota", st.estado === "perdida");
    $("bloque-compartir").hidden = st.estado !== "completada";
    $("copiar").hidden = st.estado !== "completada";
    if (st.estado === "completada") {
      const est = "★".repeat(st.estrellas) + "☆".repeat(3 - st.estrellas);
      $("resultado-titulo").textContent = `Has criado un ${nombrePieza(st.objetivo)}`;
      $("resultado-texto").textContent =
        `${est} ${st.turnos} turnos` + (st.referencia === null ? "." : `; la referencia era ${st.referencia}.`) +
        (st.pistas ? ` Con ${st.pistas} ${st.pistas === 1 ? "pista" : "pistas"} la nota máxima es de dos estrellas.` : "") +
        (st.estrellas === 3 ? " Muy cerca de la mejor marca del programa." : " ¿Puedes hacerlo en menos? Prueba otra partida.");
      $("compartir-texto").textContent = fn.compartir_texto();
    } else if (st.estado === "perdida") {
      $("resultado-titulo").textContent = "El huerto se ha llenado";
      $("resultado-texto").textContent =
        "No cabe ninguna pieza más. Puedes deshacer las últimas jugadas (U) y probar otro camino, o empezar otra partida.";
    }
    if (fin) $("otra").textContent = modo === "diario" ? "Jugar una de práctica" : "Otra partida de práctica";

    $("modo-diario").classList.toggle("activo", modo === "diario");
    $("modo-practica").classList.toggle("activo", modo === "practica");
    $("modo-diario").setAttribute("aria-pressed", String(modo === "diario"));
    $("modo-practica").setAttribute("aria-pressed", String(modo === "practica"));
    $("fila-nivel").hidden = modo !== "practica";
  }

  function renderStats() {
    const e = leer().estadisticas || {};
    $("st-racha").textContent = fn.racha_vigente ? fn.racha_vigente(JSON.stringify(e), hoyISO()) : (e.racha || 0);
    $("st-mejor-racha").textContent = e.mejor_racha || 0;
    $("st-completados").textContent = e.completados || 0;
    $("st-tres").textContent = e.tres_estrellas || 0;
  }

  // ---------- guardado del reto diario ----------
  function guardarDiario() {
    if (modo !== "diario") return;
    const datos = leer();
    const previo = datos.diario && datos.diario.fecha === diarioISO ? datos.diario : {};
    datos.diario = { fecha: diarioISO, historial: st.historial, pistas: st.pistas, contada: !!previo.contada };
    if (st.estado === "completada" && !datos.diario.contada) {
      datos.estadisticas = llamar(
        "actualizar_estadisticas",
        JSON.stringify(datos.estadisticas || {}), diarioISO, st.turnos, st.estrellas
      );
      datos.diario.contada = true;
    }
    escribir(datos);
    renderStats();
  }

  // ---------- acciones ----------
  function aplicar(nuevo) {
    if (nuevo.error) { mensaje(nuevo.error, true); return false; }
    st = nuevo;
    return true;
  }

  function colocar(i) {
    if (!st || st.estado !== "jugando") return;
    if (st.tab[i] !== 0) { mensaje("Esa casilla está ocupada.", true); return; }
    pistaVista = null;
    let anuncio = "";
    if (aplicar(llamar("colocar", Math.floor(i / st.cols), i % st.cols))) {
      quitarConfirmacion();
      const ev = st.ultimo || [];
      anuncio = ev.length ? "Fusión: " + textoFusiones(ev) + "." : "";
      if (st.estado === "perdida") mensaje("El huerto está lleno.", true);
      else mensaje(anuncio);
      guardarDiario();
    }
    pintar();
    if (anuncio) $("resumen").textContent = `${anuncio} ${$("resumen").textContent}`;
  }

  function cambiarCesto() {
    if (!st || st.estado !== "jugando") return;
    pistaVista = null;
    if (aplicar(llamar("cambiar"))) { mensaje(""); guardarDiario(); }
    pintar();
  }

  function deshacer() {
    if (!st) return;
    pistaVista = null;
    if (aplicar(llamar("deshacer"))) { mensaje(""); guardarDiario(); }
    pintar();
  }

  function pedirPista() {
    if (!st || st.estado !== "jugando") return;
    const nuevo = llamar("pista");
    if (nuevo.error) { mensaje(nuevo.error, true); return; }
    st = nuevo;
    pistaVista = nuevo.pista;
    const donde = `fila ${pistaVista.fila + 1}, columna ${pistaVista.col + 1}`;
    mensaje(pistaVista.tipo === "cesto"
      ? `Pista: cambia primero con el cesto y coloca la pieza en la ${donde}.`
      : `Pista: coloca la pieza actual en la ${donde}.`);
    guardarDiario();
    pintar();
  }

  function quitarConfirmacion() {
    if (confirmaReiniciar) { clearTimeout(confirmaReiniciar); confirmaReiniciar = null; }
    $("reiniciar").textContent = "Reiniciar";
  }
  function reiniciar() {
    if (!st || !(st.historial && st.historial.length)) return;
    if (!confirmaReiniciar) {
      $("reiniciar").textContent = "¿Seguro? Pulsa otra vez";
      confirmaReiniciar = setTimeout(quitarConfirmacion, 3500);
      return;
    }
    quitarConfirmacion();
    pistaVista = null;
    st = llamar("reiniciar");
    mensaje("");
    guardarDiario();
    pintar();
  }

  function iniciarDiario() {
    modo = "diario";
    pistaVista = null;
    diarioISO = hoyISO();
    const semilla = fn.semilla_del_dia(diarioISO);
    const etiqueta = `${diarioISO} · reto diario`;
    const guardada = leer().diario;
    if (guardada && guardada.fecha === diarioISO) {
      st = llamar("restaurar", semilla, "diario", etiqueta, "normal",
        JSON.stringify(guardada.historial || []), guardada.pistas || 0);
    } else {
      st = llamar("nueva_partida", semilla, "diario", etiqueta, "normal");
    }
    mensaje("");
    quitarConfirmacion();
    guardarDiario();
    pintar();
  }
  function iniciarPractica() {
    modo = "practica";
    pistaVista = null;
    st = llamar("nueva_partida", Math.floor(Math.random() * 2147483647), "practica", "práctica", nivel);
    mensaje("");
    quitarConfirmacion();
    pintar();
  }

  async function copiar() {
    const texto = $("compartir-texto").textContent;
    let ok = false;
    try { await navigator.clipboard.writeText(texto); ok = true; } catch (e) {
      const area = el("textarea"); area.value = texto; document.body.append(area); area.select();
      try { ok = document.execCommand("copy"); } catch (e2) { ok = false; }
      area.remove();
    }
    const b = $("copiar");
    b.textContent = ok ? "Copiado" : "Selecciona el texto y cópialo";
    setTimeout(() => { b.textContent = "Copiar resultado"; }, 2200);
  }

  // ---------- leyenda ----------
  function construirLeyenda() {
    const items = Object.keys(st.piezas).map((k) => {
      const li = el("li");
      li.append(pieza(Number(k)), el("span", "", `Nivel ${k}: ${st.piezas[k].nombre} (${st.piezas[k].forma})`));
      return li;
    });
    const savia = el("li");
    savia.append(pieza(st.codigos.savia), el("span", "", "Savia: comodín"));
    const piedra = el("li");
    piedra.append(pieza(st.codigos.piedra), el("span", "", "Piedra: ocupa casilla"));
    $("leyenda").replaceChildren(...items, savia, piedra);
  }

  // ---------- controles ----------
  function enfocar(i) {
    const hijos = [...$("tablero").children];
    if (i < 0 || i >= hijos.length) return;
    hijos.forEach((b) => { b.tabIndex = -1; });
    hijos[i].tabIndex = 0;
    foco = i;
    hijos[i].focus();
  }

  function construirControles() {
    const tab = $("tablero");
    tab.addEventListener("click", (ev) => {
      const b = ev.target.closest(".casilla");
      if (b) colocar(Number(b.dataset.i));
    });
    tab.addEventListener("focusin", (ev) => {
      const b = ev.target.closest(".casilla");
      if (!b) return;
      foco = Number(b.dataset.i);
      [...tab.children].forEach((x) => { x.tabIndex = -1; });
      b.tabIndex = 0;
    });

    $("juego").addEventListener("keydown", (ev) => {
      if (ev.ctrlKey || ev.metaKey || ev.altKey || !st) return;
      const t = ev.target;
      if (t.closest && t.closest("select, input, textarea")) return;
      const b = t.closest ? t.closest(".casilla") : null;
      if (b) {
        const i = Number(b.dataset.i);
        const c = i % st.cols;
        if (ev.key === "ArrowLeft") { ev.preventDefault(); if (c > 0) enfocar(i - 1); return; }
        if (ev.key === "ArrowRight") { ev.preventDefault(); if (c < st.cols - 1) enfocar(i + 1); return; }
        if (ev.key === "ArrowUp") { ev.preventDefault(); enfocar(i - st.cols); return; }
        if (ev.key === "ArrowDown") { ev.preventDefault(); enfocar(i + st.cols); return; }
        if (ev.key === "Home") { ev.preventDefault(); enfocar(i - c); return; }
        if (ev.key === "End") { ev.preventDefault(); enfocar(i - c + st.cols - 1); return; }
        // Espacio e Intro activan el botón y llegan como "click".
      }
      if (ev.key === "c" || ev.key === "C") { ev.preventDefault(); cambiarCesto(); }
      else if (ev.key === "u" || ev.key === "U") { ev.preventDefault(); deshacer(); }
      else if (ev.key === "p" || ev.key === "P") { ev.preventDefault(); pedirPista(); }
    });

    $("cesto").addEventListener("click", cambiarCesto);
    $("cambiar").addEventListener("click", cambiarCesto);
    $("deshacer").addEventListener("click", deshacer);
    $("pista").addEventListener("click", pedirPista);
    $("reiniciar").addEventListener("click", reiniciar);
    $("copiar").addEventListener("click", copiar);
    $("otra").addEventListener("click", iniciarPractica);
    $("modo-diario").addEventListener("click", iniciarDiario);
    $("modo-practica").addEventListener("click", iniciarPractica);
    $("nivel").addEventListener("change", () => {
      nivel = $("nivel").value;
      iniciarPractica();
    });
    $("ver-fusiones").addEventListener("change", () => {
      verFusiones = $("ver-fusiones").checked;
      const datos = leer();
      datos.opciones = Object.assign({}, datos.opciones, { fusiones: verFusiones });
      escribir(datos);
      if (st) pintar();
    });
    ["modo-diario", "modo-practica"].forEach((id) => { $(id).disabled = false; });
  }

  async function init() {
    const opciones = leer().opciones || {};
    verFusiones = opciones.fusiones !== false;
    $("ver-fusiones").checked = verFusiones;
    renderStats();
    try {
      if (typeof loadPyodide === "undefined") throw new Error("Pyodide no se ha cargado");
      const r = await fetch("codigo.py");
      if (!r.ok) throw new Error("No se pudo cargar codigo.py");
      const fuente = await r.text();
      $("python-source").textContent = fuente;
      py = await loadPyodide();
      await py.runPythonAsync(fuente);
      ["nueva_partida", "restaurar", "colocar", "cambiar", "deshacer", "reiniciar", "pista", "compartir_texto",
        "actualizar_estadisticas", "racha_vigente", "semilla_del_dia"]
        .forEach((n) => { fn[n] = py.globals.get(n); });
      construirControles();
      $("estado-carga").hidden = true;
      renderStats();
      iniciarDiario();
      construirLeyenda();
    } catch (e) {
      console.error(e);
      $("estado-carga").textContent = "No se ha podido cargar el motor de Python. Comprueba tu conexión y recarga la página.";
    }
  }

  init();
})();

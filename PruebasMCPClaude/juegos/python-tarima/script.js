// Tarima: interfaz. Las reglas viven en codigo.py (Python con Pyodide);
// este archivo solo dibuja el estado que devuelve Python y le pasa las acciones.
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const CLAVE = "tarima-v1";
  const N = 8;

  let py = null;
  const fn = {};
  let st = null;              // último estado devuelto por Python
  let modo = "diario";
  let diarioISO = "";
  let nivel = "normal";       // nivel de la práctica
  let sel = 0;                // pieza elegida del lote (0 a 2)
  let foco = 27;              // casilla con el foco del teclado
  let pistaVista = null;      // {slot, fila, col, celdas}, hasta la siguiente acción
  let confirmaReiniciar = null;
  let verLineas = true;
  let previa = null;          // vista previa vigente: {i, valida, celdas, filas, cols}

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
  const plural = (n, uno, varios) => `${n} ${n === 1 ? uno : varios}`;
  const jugando = () => !!st && st.estado === "jugando";

  // Esquina superior izquierda de la pieza elegida si su centro va en la casilla i.
  function esquina(i) {
    const p = st.bandeja[sel];
    return [Math.floor(i / N) - p.pivote[0], (i % N) - p.pivote[1]];
  }
  function celdasDeLinea(filas, cols) {
    const s = new Set();
    filas.forEach((f) => { for (let c = 0; c < N; c++) s.add(f * N + c); });
    cols.forEach((c) => { for (let f = 0; f < N; f++) s.add(f * N + c); });
    return s;
  }
  function textoLineas(filas, cols) {
    const t = [];
    if (filas.length) t.push(plural(filas.length, "fila", "filas"));
    if (cols.length) t.push(plural(cols.length, "columna", "columnas"));
    return t.join(" y ");
  }

  // ---------- dibujo ----------
  function construirTablero() {
    const t = $("tablero");
    t.replaceChildren();
    for (let i = 0; i < N * N; i++) {
      const b = el("button", "casilla");
      b.type = "button";
      b.dataset.i = String(i);
      b.tabIndex = i === foco ? 0 : -1;
      t.append(b);
    }
  }

  function mini(p, esPista) {
    const cuadro = el("span", "mini");
    cuadro.style.gridTemplateColumns = `repeat(${p.ancho}, var(--u))`;
    cuadro.setAttribute("aria-hidden", "true");
    const llenas = new Set(p.celdas.map(([f, c]) => f * p.ancho + c));
    for (let k = 0; k < p.alto * p.ancho; k++) cuadro.append(el("span", llenas.has(k) ? "lleno" : "vacio"));
    return cuadro;
  }
  function describirPieza(p) {
    return `${p.nombre} de ${p.celdas.length} ${p.celdas.length === 1 ? "casilla" : "casillas"}, ${p.alto} de alto por ${p.ancho} de ancho`;
  }

  function pintarTablero() {
    const nuevas = new Set((st.ultimo && st.ultimo.pieza) || []);
    const pistas = new Set((pistaVista && pistaVista.celdas) || []);
    const hay = jugando();
    const limpias = previa && previa.valida && verLineas ? celdasDeLinea(previa.filas, previa.cols) : new Set();
    const fantasma = new Set(previa ? previa.celdas : []);
    [...$("tablero").children].forEach((b, i) => {
      const v = st.tab[i];
      const f = Math.floor(i / N), c = i % N;
      b.classList.toggle("tabla", v === 1);
      b.classList.toggle("nudo", v === st.codigos.nudo);
      b.classList.toggle("nueva", nuevas.has(i) && v === 1);
      b.classList.toggle("fantasma", hay && fantasma.has(i) && previa.valida);
      b.classList.toggle("fantasma-mal", hay && fantasma.has(i) && !previa.valida);
      b.classList.toggle("limpia", hay && limpias.has(i));
      b.classList.toggle("pista-casilla", hay && pistas.has(i));
      const estado = v === 0 ? "vacía" : v === 1 ? "con tabla" : "con nudo";
      let etiqueta = `Fila ${f + 1}, columna ${c + 1}: ${estado}`;
      if (hay && st.bandeja[sel] && !st.bandeja[sel].usada) {
        const [f0, c0] = esquina(i);
        const r = JSON.parse(fn.vista_previa(sel, f0, c0));
        if (r.valida) {
          const l = textoLineas(r.filas, r.cols);
          etiqueta += `. Si pones aquí el centro de la pieza elegida, cabe${l ? " y despeja " + l : ""}`;
        } else {
          etiqueta += `. Si pones aquí el centro de la pieza elegida, no cabe: ${r.motivo.toLowerCase()}`;
        }
      }
      b.setAttribute("aria-label", etiqueta);
    });
    $("tablero").classList.toggle("fin", !hay);
  }

  function pintarBandeja() {
    const hay = jugando();
    $("bandeja").replaceChildren(...st.bandeja.map((p) => {
      const b = el("button", "pieza-boton");
      b.type = "button";
      b.dataset.slot = String(p.slot);
      b.disabled = !hay || p.usada;
      b.setAttribute("aria-pressed", String(hay && sel === p.slot));
      b.classList.toggle("no-cabe", hay && !p.usada && !p.cabe);
      b.classList.toggle("pista-pieza", hay && !!pistaVista && pistaVista.slot === p.slot);
      if (p.usada) {
        b.append(el("span", "", "puesta"));
        b.setAttribute("aria-label", `Pieza ${p.slot + 1}: ya colocada`);
      } else {
        b.append(mini(p), el("span", "", `Pieza ${p.slot + 1}`));
        b.setAttribute("aria-label",
          `Pieza ${p.slot + 1}: ${describirPieza(p)}${p.cabe ? "" : ". No cabe en ningún sitio"}. Atajo: tecla ${p.slot + 1}`);
      }
      return b;
    }));
    $("siguiente").replaceChildren(...(st.siguiente.length
      ? st.siguiente.map((p, k) => {
        const b = el("button", "pieza-boton");
        b.type = "button";
        b.disabled = true;
        b.append(mini(p));
        b.setAttribute("aria-label", `Siguiente lote, pieza ${k + 1}: ${describirPieza(p)}`);
        return b;
      })
      : [el("p", "pequeno", "No quedan más lotes.")]));
  }

  function pintar() {
    if ($("tablero").children.length !== N * N) construirTablero();
    const hay = jugando();
    if (hay && (!st.bandeja[sel] || st.bandeja[sel].usada)) sel = elegirPieza();
    pintarTablero();
    pintarBandeja();

    $("c-lineas").textContent = st.lineas;
    $("c-objetivo").textContent = st.objetivo;
    $("c-lote").textContent = st.lote;
    $("c-lotes").textContent = st.lotes;
    $("c-puntos").textContent = st.puntos;
    $("c-ref").textContent = st.referencia === null ? "–" : st.referencia;
    $("c-pistas").textContent = `${st.pistas}/${st.pistas_max}`;

    const libres = st.tab.filter((x) => x === 0).length;
    $("resumen").textContent =
      `Lote ${st.lote} de ${st.lotes}. ${plural(st.lineas, "línea despejada", "líneas despejadas")} de ${st.objetivo}. ` +
      `${plural(libres, "casilla libre", "casillas libres")}.` +
      (hay && st.bandeja[sel] ? ` Pieza elegida: ${sel + 1}.` : "");

    $("deshacer").disabled = !st.puede_deshacer;
    $("pista").disabled = !hay || st.pistas >= st.pistas_max;
    $("reiniciar").disabled = !(st.historial && st.historial.length);
    if (!hay) quitarConfirmacion();

    $("titulo-partida").textContent = modo === "diario"
      ? `Reto del ${fechaLarga(diarioISO)} (${st.nivel_nombre.toLowerCase()}): el mismo suelo y las mismas piezas para todo el mundo. Objetivo: ${plural(st.objetivo, "línea", "líneas")} en ${st.lotes} lotes.`
      : `Práctica · ${st.nivel_nombre}. Objetivo: ${plural(st.objetivo, "línea", "líneas")} en ${st.lotes} lotes.`;

    const fin = st.estado !== "jugando";
    $("resultado").hidden = !fin;
    $("resultado").classList.toggle("derrota", st.estado === "perdida");
    $("bloque-compartir").hidden = st.estado !== "completada";
    $("copiar").hidden = st.estado !== "completada";
    if (st.estado === "completada") {
      const est = "★".repeat(st.estrellas) + "☆".repeat(3 - st.estrellas);
      $("resultado-titulo").textContent = "Objetivo cumplido";
      $("resultado-texto").textContent =
        `${est} ${plural(st.lineas, "línea despejada", "líneas despejadas")} (objetivo ${st.objetivo}, referencia ${st.referencia}).` +
        (st.pistas ? ` Con ${plural(st.pistas, "pista", "pistas")} la nota máxima es de dos estrellas.` : "") +
        (st.estrellas === 3 ? " Has igualado o superado al programa." : " ¿Puedes despejar más? Prueba otra partida.");
      $("compartir-texto").textContent = fn.compartir_texto();
    } else if (st.estado === "perdida") {
      $("resultado-titulo").textContent = "No se llega al objetivo";
      $("resultado-texto").textContent =
        (st.motivo_fin === "sin_sitio" ? "Ninguna de las piezas que quedan cabe en el suelo. " : "Se han acabado los lotes. ") +
        `Has despejado ${plural(st.lineas, "línea", "líneas")} de ${st.objetivo}. Puedes deshacer las últimas colocaciones (U) y probar otro camino, o empezar otra partida.`;
    }
    if (fin) $("otra").textContent = modo === "diario" ? "Jugar una de práctica" : "Otra partida de práctica";

    $("modo-diario").classList.toggle("activo", modo === "diario");
    $("modo-practica").classList.toggle("activo", modo === "practica");
    $("modo-diario").setAttribute("aria-pressed", String(modo === "diario"));
    $("modo-practica").setAttribute("aria-pressed", String(modo === "practica"));
    $("fila-nivel").hidden = modo !== "practica";
  }

  function elegirPieza() {
    const libres = st.bandeja.filter((p) => !p.usada);
    const quepan = libres.filter((p) => p.cabe);
    const p = quepan[0] || libres[0];
    return p ? p.slot : 0;
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
        JSON.stringify(datos.estadisticas || {}), diarioISO, st.lineas, st.estrellas
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

  function actualizarPrevia(i) {
    previa = null;
    if (!jugando() || i === null || !st.bandeja[sel] || st.bandeja[sel].usada) return;
    const [f0, c0] = esquina(i);
    const r = JSON.parse(fn.vista_previa(sel, f0, c0));
    previa = Object.assign({ i }, r);
  }

  function colocar(i) {
    if (!jugando()) return;
    const p = st.bandeja[sel];
    if (!p || p.usada) { mensaje("Elige primero una pieza del lote.", true); return; }
    const [f0, c0] = esquina(i);
    pistaVista = null;
    const lotePrevio = st.lote;
    let anuncio = "";
    if (aplicar(llamar("colocar", sel, f0, c0))) {
      quitarConfirmacion();
      const u = st.ultimo;
      const l = u ? textoLineas(u.filas, u.cols) : "";
      anuncio = l ? `Despejas ${l}: +${u.puntos} puntos.` : "";
      if (st.estado === "jugando" && st.lote !== lotePrevio) anuncio += ` Llega el lote ${st.lote}.`;
      mensaje(anuncio.trim());
      guardarDiario();
    }
    actualizarPrevia(jugando() ? i : null);
    pintar();
    if (anuncio) $("resumen").textContent = `${anuncio.trim()} ${$("resumen").textContent}`;
  }

  function elegir(slot) {
    if (!jugando() || !st.bandeja[slot] || st.bandeja[slot].usada) return;
    sel = slot;
    pistaVista = null;
    actualizarPrevia(previa ? previa.i : null);
    pintar();
  }

  function deshacer() {
    if (!st) return;
    pistaVista = null;
    previa = null;
    if (aplicar(llamar("deshacer"))) { mensaje(""); guardarDiario(); }
    pintar();
  }

  function pedirPista() {
    if (!jugando()) return;
    const nuevo = llamar("pista");
    if (nuevo.error) { mensaje(nuevo.error, true); return; }
    st = nuevo;
    const h = nuevo.pista;
    const r = JSON.parse(fn.vista_previa(h.slot, h.fila, h.col));
    pistaVista = { slot: h.slot, fila: h.fila, col: h.col, celdas: r.celdas };
    sel = h.slot;
    const p = st.bandeja[h.slot];
    mensaje(`Pista: pon la pieza ${h.slot + 1} con su centro en la fila ${h.fila + p.pivote[0] + 1}, columna ${h.col + p.pivote[1] + 1}.`);
    guardarDiario();
    previa = null;
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
    previa = null;
    st = llamar("reiniciar");
    mensaje("");
    guardarDiario();
    pintar();
  }

  function iniciarDiario() {
    modo = "diario";
    pistaVista = null;
    previa = null;
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
    sel = elegirPieza();
    mensaje("");
    quitarConfirmacion();
    guardarDiario();
    pintar();
  }
  function iniciarPractica() {
    modo = "practica";
    pistaVista = null;
    previa = null;
    st = llamar("nueva_partida", Math.floor(Math.random() * 2147483647), "practica", "práctica", nivel);
    sel = elegirPieza();
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
    const filas = [
      ["", "Casilla libre"],
      ["tabla", "Casilla con tabla (ya colocada)"],
      ["nudo", "Nudo: casilla ocupada desde el principio"],
      ["fantasma", "Verde con borde discontinuo: la pieza cabe aquí"],
      ["fantasma-mal", "Rojo con borde discontinuo: la pieza no cabe aquí"],
      ["limpia tabla", "Rayas verdes: línea que se despejaría"],
    ];
    $("leyenda").replaceChildren(...filas.map(([clase, texto]) => {
      const li = el("li");
      const c = el("span", "casilla " + clase);
      c.setAttribute("aria-hidden", "true");
      li.append(c, el("span", "", texto));
      return li;
    }));
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
    tab.addEventListener("mouseover", (ev) => {
      const b = ev.target.closest(".casilla");
      if (!b || !jugando()) return;
      const i = Number(b.dataset.i);
      if (previa && previa.i === i) return;
      actualizarPrevia(i);
      pintarTablero();
    });
    tab.addEventListener("mouseleave", () => {
      if (!previa) return;
      previa = null;
      if (st) pintarTablero();
    });
    tab.addEventListener("focusin", (ev) => {
      const b = ev.target.closest(".casilla");
      if (!b) return;
      foco = Number(b.dataset.i);
      [...tab.children].forEach((x) => { x.tabIndex = -1; });
      b.tabIndex = 0;
      if (jugando()) { actualizarPrevia(foco); pintarTablero(); }
    });
    tab.addEventListener("focusout", (ev) => {
      if (tab.contains(ev.relatedTarget)) return;
      previa = null;
      if (st) pintarTablero();
    });

    $("bandeja").addEventListener("click", (ev) => {
      const b = ev.target.closest(".pieza-boton");
      if (b && !b.disabled) elegir(Number(b.dataset.slot));
    });

    $("juego").addEventListener("keydown", (ev) => {
      if (ev.ctrlKey || ev.metaKey || ev.altKey || !st) return;
      const t = ev.target;
      if (t.closest && t.closest("select, input, textarea")) return;
      const b = t.closest ? t.closest(".casilla") : null;
      if (b) {
        const i = Number(b.dataset.i);
        const c = i % N;
        if (ev.key === "ArrowLeft") { ev.preventDefault(); if (c > 0) enfocar(i - 1); return; }
        if (ev.key === "ArrowRight") { ev.preventDefault(); if (c < N - 1) enfocar(i + 1); return; }
        if (ev.key === "ArrowUp") { ev.preventDefault(); enfocar(i - N); return; }
        if (ev.key === "ArrowDown") { ev.preventDefault(); enfocar(i + N); return; }
        if (ev.key === "Home") { ev.preventDefault(); enfocar(i - c); return; }
        if (ev.key === "End") { ev.preventDefault(); enfocar(i - c + N - 1); return; }
        // Espacio e Intro activan el botón y llegan como "click".
      }
      if (ev.key === "1" || ev.key === "2" || ev.key === "3") { ev.preventDefault(); elegir(Number(ev.key) - 1); }
      else if (ev.key === "u" || ev.key === "U") { ev.preventDefault(); deshacer(); }
      else if (ev.key === "p" || ev.key === "P") { ev.preventDefault(); pedirPista(); }
    });

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
    $("ver-lineas").addEventListener("change", () => {
      verLineas = $("ver-lineas").checked;
      const datos = leer();
      datos.opciones = Object.assign({}, datos.opciones, { lineas: verLineas });
      escribir(datos);
      if (st) pintarTablero();
    });
    ["modo-diario", "modo-practica"].forEach((id) => { $(id).disabled = false; });
  }

  async function init() {
    const opciones = leer().opciones || {};
    verLineas = opciones.lineas !== false;
    $("ver-lineas").checked = verLineas;
    renderStats();
    construirLeyenda();
    try {
      if (typeof loadPyodide === "undefined") throw new Error("Pyodide no se ha cargado");
      const r = await fetch("codigo.py");
      if (!r.ok) throw new Error("No se pudo cargar codigo.py");
      const fuente = await r.text();
      $("python-source").textContent = fuente;
      py = await loadPyodide();
      await py.runPythonAsync(fuente);
      ["nueva_partida", "restaurar", "colocar", "vista_previa", "deshacer", "reiniciar", "pista", "compartir_texto",
        "actualizar_estadisticas", "racha_vigente", "semilla_del_dia"]
        .forEach((n) => { fn[n] = py.globals.get(n); });
      construirControles();
      $("estado-carga").hidden = true;
      renderStats();
      iniciarDiario();
    } catch (e) {
      console.error(e);
      $("estado-carga").textContent = "No se ha podido cargar el motor de Python. Comprueba tu conexión y recarga la página.";
    }
  }

  init();
})();

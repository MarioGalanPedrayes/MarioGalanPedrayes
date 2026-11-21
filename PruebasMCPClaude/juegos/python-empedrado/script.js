// Empedrado: interfaz. Las reglas viven en codigo.py (Python con Pyodide);
// este archivo solo dibuja el estado que devuelve Python y le pasa las acciones.
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const CLAVE = "empedrado-v1";
  const PIEDRA = 1, HUECO = 2;

  let py = null;
  const fn = {};
  let st = null;              // último estado devuelto por Python
  let modo = "diario";
  let diarioISO = "";
  let nivel = "normal";       // nivel de la práctica
  let herramienta = "piedra"; // "piedra" | "hueco"
  let foco = 0;               // casilla con el foco del teclado
  let pistaVista = null;      // índice de la casilla de la última pista
  let confirmaReiniciar = null;
  let arrastre = null;        // {estado, borrar, desde, primero}
  let celdas = [];            // botones de la calle

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
  const valorHerramienta = (h) => (h === "piedra" ? PIEDRA : HUECO);
  const otraHerramienta = (h) => (h === "piedra" ? "hueco" : "piedra");

  // ---------- dibujo ----------
  function construirCalle() {
    const n = st.lado;
    const cont = $("calle");
    cont.replaceChildren();
    cont.style.setProperty("--n", String(n));
    cont.append(el("div", "esquina"));
    for (let j = 0; j < n; j++) cont.append(el("div", "cifras col"));
    celdas = [];
    for (let i = 0; i < n; i++) {
      cont.append(el("div", "cifras fila"));
      for (let j = 0; j < n; j++) {
        const b = el("button", "celda");
        b.type = "button";
        b.dataset.i = String(i * n + j);
        b.tabIndex = i * n + j === foco ? 0 : -1;
        if ((j + 1) % 5 === 0 && j < n - 1) b.classList.add("g-der");
        if ((i + 1) % 5 === 0 && i < n - 1) b.classList.add("g-abajo");
        celdas.push(b);
        cont.append(b);
      }
    }
  }

  function pintarCifras(div, cifras, ok) {
    div.replaceChildren(...cifras.map((x) => el("span", "n", String(x))));
    if (ok) div.append(el("span", "visto", "✓"));
    div.classList.toggle("ok", ok);
  }

  const textoCifras = (c) => (c.length === 1 && c[0] === 0 ? "sin piedras" : c.join(" "));

  function pintar() {
    const n = st.lado;
    if (celdas.length !== n * n) { foco = 0; construirCalle(); }
    const jugando = st.estado === "jugando";
    const malas = new Set(st.malas || []);
    const cont = $("calle");
    const cols = [...cont.querySelectorAll(".cifras.col")];
    const filas = [...cont.querySelectorAll(".cifras.fila")];
    st.pistas_col.forEach((c, j) => {
      pintarCifras(cols[j], c, st.cols_ok[j]);
      cols[j].setAttribute("aria-hidden", "true");
    });
    st.pistas_fila.forEach((c, i) => {
      pintarCifras(filas[i], c, st.filas_ok[i]);
      filas[i].setAttribute("aria-hidden", "true");
    });

    celdas.forEach((b, i) => {
      const v = st.celdas[i];
      const f = Math.floor(i / n), c = i % n;
      b.classList.toggle("piedra", v === PIEDRA);
      b.classList.toggle("hueco", v === HUECO);
      b.classList.toggle("mala", malas.has(i));
      b.classList.toggle("pista", pistaVista === i);
      b.replaceChildren();
      if (v === HUECO) b.append(el("span", "", "×"));
      if (malas.has(i)) b.append(el("span", "marca-mala", "!"));
      let etiqueta = `Fila ${f + 1}, columna ${c + 1}: ${v === PIEDRA ? "piedra" : v === HUECO ? "hueco" : "vacía"}`;
      if (malas.has(i)) etiqueta += ", mal puesta";
      if (c === 0) etiqueta += `. Cifras de la fila ${f + 1}: ${textoCifras(st.pistas_fila[f])}${st.filas_ok[f] ? ", cumplida" : ""}`;
      if (f === 0) etiqueta += `. Cifras de la columna ${c + 1}: ${textoCifras(st.pistas_col[c])}${st.cols_ok[c] ? ", cumplida" : ""}`;
      b.setAttribute("aria-label", etiqueta);
    });
    cont.classList.toggle("fin", !jugando);

    $("c-piedras").textContent = `${st.piedras}/${st.piedras_total}`;
    $("c-filas").textContent = `${st.filas_ok.filter(Boolean).length}/${n}`;
    $("c-cols").textContent = `${st.cols_ok.filter(Boolean).length}/${n}`;
    $("c-ayudas").textContent = `${st.pistas + st.revisiones}`;
    $("resumen").textContent =
      `${st.piedras} de ${st.piedras_total} piedras. ` +
      `${st.filas_ok.filter(Boolean).length} filas y ${st.cols_ok.filter(Boolean).length} columnas cumplidas de ${n}.`;

    $("deshacer").disabled = !st.puede_deshacer;
    $("pista").disabled = !jugando || st.pistas >= st.ayudas_max;
    $("revisar").disabled = !jugando || st.revisiones >= st.ayudas_max;
    $("reiniciar").disabled = !(st.piedras || st.celdas.some((x) => x) || st.pistas || st.revisiones);
    $("pista").textContent = `Pista (${st.ayudas_max - st.pistas})`;
    $("revisar").textContent = `Revisar (${st.ayudas_max - st.revisiones})`;
    if (!jugando) quitarConfirmacion();

    $("titulo-partida").textContent = modo === "diario"
      ? `Reto del ${fechaLarga(diarioISO)} (${st.nivel_nombre.toLowerCase()}, ${n}×${n}): la misma calle para todo el mundo.`
      : `Práctica · ${st.nivel_nombre} (${n}×${n}).`;

    const fin = st.estado === "completada";
    $("resultado").hidden = !fin;
    if (fin) {
      const est = "★".repeat(st.estrellas) + "☆".repeat(3 - st.estrellas);
      const ayudas = st.pistas + st.revisiones;
      $("resultado-titulo").textContent = "Calle empedrada";
      $("resultado-texto").textContent =
        `${est} ` + (ayudas ? `Has usado ${ayudas} ${ayudas === 1 ? "ayuda" : "ayudas"}.` : "Sin ninguna ayuda.") +
        (st.estrellas === 3 ? " Lógica limpia." : " ¿La haces sin ayudas en otra calle?");
      $("compartir-texto").textContent = fn.compartir_texto();
      $("otra").textContent = modo === "diario" ? "Jugar una de práctica" : "Otra calle de práctica";
    }

    $("modo-diario").classList.toggle("activo", modo === "diario");
    $("modo-practica").classList.toggle("activo", modo === "practica");
    $("modo-diario").setAttribute("aria-pressed", String(modo === "diario"));
    $("modo-practica").setAttribute("aria-pressed", String(modo === "practica"));
    $("fila-nivel").hidden = modo !== "practica";
    ponerHerramienta(herramienta);
  }

  function ponerHerramienta(h) {
    herramienta = h;
    $("h-piedra").classList.toggle("activa", h === "piedra");
    $("h-hueco").classList.toggle("activa", h === "hueco");
    $("h-piedra").setAttribute("aria-pressed", String(h === "piedra"));
    $("h-hueco").setAttribute("aria-pressed", String(h === "hueco"));
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
    datos.diario = {
      fecha: diarioISO, celdas: st.celdas, pistas: st.pistas, revisiones: st.revisiones, contada: !!previo.contada,
    };
    if (st.estado === "completada" && !datos.diario.contada) {
      datos.estadisticas = llamar(
        "actualizar_estadisticas", JSON.stringify(datos.estadisticas || {}), diarioISO, st.estrellas
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

  // Pone un estado (0, 1 o 2) en una casilla. `paso` es true en la primera casilla de un arrastre.
  function poner(i, estado, paso) {
    if (!st) return;
    if (st.estado !== "jugando") { mensaje("La calle ya está empedrada. Puedes deshacer o empezar otra."); return; }
    pistaVista = null;
    if (aplicar(llamar("poner", Math.floor(i / st.lado), i % st.lado, estado, paso))) {
      mensaje("");
      quitarConfirmacion();
      guardarDiario();
    }
    pintar();
  }

  // Qué hacer al tocar una casilla con la herramienta (o la otra): si ya tiene esa marca, se quita.
  function objetivo(i, alterna) {
    const h = alterna ? otraHerramienta(herramienta) : herramienta;
    const v = valorHerramienta(h);
    return st.celdas[i] === v ? { estado: 0, borrar: true, desde: v } : { estado: v, borrar: false, desde: 0 };
  }

  function alternaPorEvento(ev) { return ev.button === 2 || ev.shiftKey; }

  function empezarArrastre(ev) {
    const b = ev.target.closest(".celda");
    if (!b || !st || st.estado !== "jugando") return;
    if (ev.button !== undefined && ev.button !== 0 && ev.button !== 2) return;
    ev.preventDefault();
    try { if (b.hasPointerCapture && b.hasPointerCapture(ev.pointerId)) b.releasePointerCapture(ev.pointerId); } catch (e) { /* sin captura */ }
    const i = Number(b.dataset.i);
    foco = i;
    celdas.forEach((x) => { x.tabIndex = -1; });
    b.tabIndex = 0;
    const o = objetivo(i, alternaPorEvento(ev));
    arrastre = o;
    poner(i, o.estado, true);
    if (!ev.pointerType) arrastre = null;   // sin puntero real (p. ej. pruebas): no hay arrastre
  }

  function seguirArrastre(ev) {
    if (!arrastre) return;
    const b = ev.target.closest && ev.target.closest(".celda");
    if (!b) return;
    const i = Number(b.dataset.i);
    const actual = st.celdas[i];
    if (arrastre.borrar ? actual !== arrastre.desde : actual !== 0) return;
    if (actual === arrastre.estado) return;
    poner(i, arrastre.estado, false);
  }

  function terminarArrastre() { arrastre = null; }

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
    const h = nuevo.pista;
    if (h) {
      pistaVista = h.fila * st.lado + h.col;
      mensaje(`Pista: ${h.estado === PIEDRA ? "piedra" : "hueco"} en la fila ${h.fila + 1}, columna ${h.col + 1}.`);
    }
    guardarDiario();
    pintar();
  }

  function revisar() {
    if (!st || st.estado !== "jugando") return;
    pistaVista = null;
    const nuevo = llamar("revisar");
    if (nuevo.error) { mensaje(nuevo.error, true); return; }
    st = nuevo;
    const n = st.malas.length;
    mensaje(n === 0 ? "Todo lo que has puesto está bien."
      : `Hay ${n} ${n === 1 ? "casilla mal puesta" : "casillas mal puestas"}, marcadas con !.`, n > 0);
    guardarDiario();
    pintar();
  }

  function quitarConfirmacion() {
    if (confirmaReiniciar) { clearTimeout(confirmaReiniciar); confirmaReiniciar = null; }
    $("reiniciar").textContent = "Vaciar";
  }
  function reiniciar() {
    if (!st) return;
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
        JSON.stringify(guardada.celdas || []), guardada.pistas || 0, guardada.revisiones || 0);
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

  // ---------- controles ----------
  function enfocar(i) {
    if (i < 0 || i >= celdas.length) return;
    celdas.forEach((b) => { b.tabIndex = -1; });
    celdas[i].tabIndex = 0;
    foco = i;
    celdas[i].focus();
  }

  function construirControles() {
    const calle = $("calle");
    calle.addEventListener("pointerdown", empezarArrastre);
    calle.addEventListener("pointerover", seguirArrastre);
    calle.addEventListener("contextmenu", (ev) => ev.preventDefault());
    window.addEventListener("pointerup", terminarArrastre);
    window.addEventListener("pointercancel", terminarArrastre);
    // Activación con teclado (Espacio o Intro llegan como "click" sin puntero, detail 0).
    calle.addEventListener("click", (ev) => {
      if (ev.detail !== 0) return;
      const b = ev.target.closest(".celda");
      if (!b) return;
      const i = Number(b.dataset.i);
      const o = objetivo(i, false);
      poner(i, o.estado, true);
    });
    calle.addEventListener("focusin", (ev) => {
      const b = ev.target.closest(".celda");
      if (!b) return;
      foco = Number(b.dataset.i);
      celdas.forEach((x) => { x.tabIndex = -1; });
      b.tabIndex = 0;
    });

    $("juego").addEventListener("keydown", (ev) => {
      if (ev.ctrlKey || ev.metaKey || ev.altKey || !st) return;
      const t = ev.target;
      if (t.closest && t.closest("select, input, textarea")) return;
      const b = t.closest ? t.closest(".celda") : null;
      const k = ev.key;
      if (b) {
        const n = st.lado;
        const i = Number(b.dataset.i);
        const c = i % n;
        if (k === "ArrowLeft") { ev.preventDefault(); if (c > 0) enfocar(i - 1); return; }
        if (k === "ArrowRight") { ev.preventDefault(); if (c < n - 1) enfocar(i + 1); return; }
        if (k === "ArrowUp") { ev.preventDefault(); enfocar(i - n); return; }
        if (k === "ArrowDown") { ev.preventDefault(); enfocar(i + n); return; }
        if (k === "Home") { ev.preventDefault(); enfocar(i - c); return; }
        if (k === "End") { ev.preventDefault(); enfocar(i - c + n - 1); return; }
        if (k === "x" || k === "X") {            // la tecla X pone o quita siempre un hueco
          ev.preventDefault();
          poner(i, st.celdas[i] === HUECO ? 0 : HUECO, true);
          return;
        }
        if (k === "Backspace" || k === "Delete") { ev.preventDefault(); poner(i, 0, true); return; }
        // Espacio e Intro activan el botón y llegan como "click".
      }
      if (k === "t" || k === "T") { ev.preventDefault(); ponerHerramienta(otraHerramienta(herramienta)); }
      else if (k === "u" || k === "U") { ev.preventDefault(); deshacer(); }
      else if (k === "p" || k === "P") { ev.preventDefault(); pedirPista(); }
      else if (k === "v" || k === "V") { ev.preventDefault(); revisar(); }
    });

    $("h-piedra").addEventListener("click", () => ponerHerramienta("piedra"));
    $("h-hueco").addEventListener("click", () => ponerHerramienta("hueco"));
    $("deshacer").addEventListener("click", deshacer);
    $("pista").addEventListener("click", pedirPista);
    $("revisar").addEventListener("click", revisar);
    $("reiniciar").addEventListener("click", reiniciar);
    $("copiar").addEventListener("click", copiar);
    $("otra").addEventListener("click", iniciarPractica);
    $("modo-diario").addEventListener("click", iniciarDiario);
    $("modo-practica").addEventListener("click", iniciarPractica);
    $("nivel").addEventListener("change", () => {
      nivel = $("nivel").value;
      iniciarPractica();
    });
    ["modo-diario", "modo-practica"].forEach((id) => { $(id).disabled = false; });
  }

  async function init() {
    renderStats();
    try {
      if (typeof loadPyodide === "undefined") throw new Error("Pyodide no se ha cargado");
      const r = await fetch("codigo.py");
      if (!r.ok) throw new Error("No se pudo cargar codigo.py");
      const fuente = await r.text();
      $("python-source").textContent = fuente;
      py = await loadPyodide();
      await py.runPythonAsync(fuente);
      ["nueva_partida", "restaurar", "poner", "deshacer", "reiniciar", "pista", "revisar", "compartir_texto",
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

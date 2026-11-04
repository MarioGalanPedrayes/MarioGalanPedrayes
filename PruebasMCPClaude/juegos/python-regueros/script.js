// Regueros: interfaz. Las reglas viven en codigo.py (Python con Pyodide);
// este archivo solo dibuja el estado que devuelve Python y le pasa las acciones.
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const CLAVE = "regueros-v1";
  // bit del brazo, clase CSS, nombre
  const BRAZOS = [[1, "n", "norte"], [2, "e", "este"], [4, "s", "sur"], [8, "w", "oeste"]];

  let py = null;
  const fn = {};            // funciones de Python ya cargadas
  let st = null;            // último estado devuelto por Python
  let modo = "diario";
  let diarioISO = "";       // fecha del reto diario en curso
  let sentido = 1;          // 1 horario, -1 antihorario
  let casillas = [];        // elementos de las 36 casillas del prado
  let foco = 0;             // casilla que recibe el foco con Tab
  let confirmaReiniciar = null;

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
  function mensaje(texto) { $("mensaje").textContent = texto || ""; }

  // ---------- casillas ----------
  function construirCasilla(etiqueta) {
    const b = el(etiqueta, "casilla");
    if (etiqueta === "button") b.type = "button";
    const brazos = {}, gotas = {};
    BRAZOS.forEach(([bit, c]) => {
      brazos[bit] = el("span", `brazo ${c}`);
      b.append(brazos[bit]);
    });
    const centro = el("span", "centro");
    b.append(centro);
    BRAZOS.forEach(([bit, c]) => {
      gotas[bit] = el("span", `gota ${c}`);
      b.append(gotas[bit]);
    });
    const fonte = el("span", "fonte");
    const clavo = el("span", "clavo");
    b.append(fonte, clavo);
    [fonte, clavo, centro, ...Object.values(brazos), ...Object.values(gotas)]
      .forEach((x) => x.setAttribute("aria-hidden", "true"));
    return { b, brazos, gotas, centro, fonte, clavo };
  }

  // Dibuja una casilla a partir de su máscara de brazos y su estado.
  function pintarCasilla(c, mascara, { regada, fugas, fija, fuente }) {
    BRAZOS.forEach(([bit]) => {
      c.brazos[bit].hidden = !(mascara & bit);
      c.gotas[bit].hidden = !(fugas & bit);
    });
    c.centro.hidden = mascara === 0;
    c.fonte.hidden = !fuente;
    c.clavo.hidden = !fija;
    c.b.classList.toggle("regada", !!regada);
    c.b.classList.toggle("fija", !!fija);
  }

  function nombreForma(m) {
    const n = BRAZOS.filter(([bit]) => m & bit).length;
    if (n === 2) return m === 5 || m === 10 ? "recto" : "codo";
    return { 0: "vacía", 1: "final", 3: "T", 4: "cruce" }[n];
  }
  function lista(m) {
    return BRAZOS.filter(([bit]) => m & bit).map(([, , nombre]) => nombre);
  }
  function descripcion(i) {
    const n = st.n;
    const m = st.mascaras[i];
    const partes = [
      `Fila ${Math.floor(i / n) + 1}, columna ${(i % n) + 1}`,
      `${nombreForma(m)}, brazos ${lista(m).join(" y ")}`,
      st.regados[i] ? "regada" : "seca",
    ];
    if (st.fugas[i]) partes.push(`fuga por ${lista(st.fugas[i]).join(" y ")}`);
    if (i === st.fuente) partes.push("con la fonte");
    if (st.fijas.includes(i)) partes.push("fija, no gira");
    return partes.join(", ");
  }

  function construirPrado(n) {
    const prado = $("prado");
    prado.replaceChildren();
    prado.style.gridTemplateColumns = `repeat(${n}, minmax(0, 1fr))`;
    prado.setAttribute("aria-label", `Prado de ${n} por ${n} casillas`);
    casillas = [];
    for (let i = 0; i < n * n; i++) {
      const c = construirCasilla("button");
      c.b.dataset.i = String(i);
      c.b.tabIndex = i === foco ? 0 : -1;
      prado.append(c.b);
      casillas.push(c);
    }
  }

  // ---------- dibujo ----------
  function resumenTexto() {
    const base = `${st.n_regados} de ${st.total} casillas regadas, ${st.n_fugas} fugas, ${st.giros} giros.`;
    return st.estado === "completada" ? `Reguero completo. ${base}` : base;
  }

  function pintar() {
    if (casillas.length !== st.total) { foco = 0; construirPrado(st.n); }
    casillas.forEach((c, i) => {
      pintarCasilla(c, st.mascaras[i], {
        regada: st.regados[i],
        fugas: st.fugas[i],
        fija: st.fijas.includes(i),
        fuente: i === st.fuente,
      });
      c.b.setAttribute("aria-label", descripcion(i));
      c.b.setAttribute("aria-disabled", String(st.fijas.includes(i) || st.estado !== "jugando"));
    });
    const jugando = st.estado === "jugando";
    $("prado").classList.toggle("fin", !jugando);

    $("c-giros").textContent = st.giros;
    $("c-ref").textContent = st.referencia;
    $("c-regadas").textContent = `${st.n_regados}/${st.total}`;
    $("c-fugas").textContent = st.n_fugas;
    $("resumen").textContent = resumenTexto();

    $("deshacer").disabled = !st.puede_deshacer;
    $("reiniciar").disabled = !jugando || st.giros === 0;
    if (jugando === false) quitarConfirmacion();

    $("titulo-partida").textContent = modo === "diario"
      ? `Reto del ${fechaLarga(diarioISO)}: el mismo prado para todo el mundo.`
      : `Práctica con el prado número ${st.semilla}.`;

    const fin = st.estado === "completada";
    $("resultado").hidden = !fin;
    if (fin) {
      const estrellas = "★".repeat(st.estrellas) + "☆".repeat(3 - st.estrellas);
      $("resultado-titulo").textContent = "Prado regado";
      $("resultado-texto").textContent =
        `${estrellas} ${st.giros} giros; la referencia era ${st.referencia}. ` +
        (st.estrellas === 3 ? "Muy cerca del trazado más corto." : "¿Puedes hacerlo con menos giros? Prueba otra partida.");
      $("compartir-texto").textContent = fn.compartir_texto();
      $("otra").textContent = modo === "diario" ? "Jugar una de práctica" : "Otra partida de práctica";
    }

    $("modo-diario").classList.toggle("activo", modo === "diario");
    $("modo-practica").classList.toggle("activo", modo === "practica");
    $("modo-diario").setAttribute("aria-pressed", String(modo === "diario"));
    $("modo-practica").setAttribute("aria-pressed", String(modo === "practica"));
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
    datos.diario = { fecha: diarioISO, historial: st.historial, contada: !!previo.contada };
    if (st.estado === "completada" && !datos.diario.contada) {
      datos.estadisticas = llamar(
        "actualizar_estadisticas",
        JSON.stringify(datos.estadisticas || {}), diarioISO, st.giros, st.estrellas
      );
      datos.diario.contada = true;
    }
    escribir(datos);
    renderStats();
  }

  // ---------- acciones ----------
  function girar(i, s) {
    if (!st) return;
    const nuevo = llamar("girar", i, s);
    if (nuevo.error) { mensaje(nuevo.error); return; }
    st = nuevo;
    mensaje("");
    quitarConfirmacion();
    guardarDiario();
    pintar();
  }
  function deshacer() {
    if (!st) return;
    const nuevo = llamar("deshacer");
    if (nuevo.error) { mensaje(nuevo.error); return; }
    st = nuevo;
    mensaje("");
    guardarDiario();
    pintar();
  }
  function quitarConfirmacion() {
    if (confirmaReiniciar) { clearTimeout(confirmaReiniciar); confirmaReiniciar = null; }
    $("reiniciar").textContent = "Reiniciar";
  }
  function reiniciar() {
    if (!st || st.estado !== "jugando") return;
    if (!confirmaReiniciar) {          // primera pulsación: pedir confirmación
      $("reiniciar").textContent = "¿Seguro? Pulsa otra vez";
      confirmaReiniciar = setTimeout(quitarConfirmacion, 3500);
      return;
    }
    quitarConfirmacion();
    st = llamar("reiniciar");
    mensaje("");
    guardarDiario();
    pintar();
  }
  function cambiarSentido() {
    sentido = -sentido;
    const b = $("sentido");
    b.textContent = sentido === 1 ? "Sentido: ↻ horario" : "Sentido: ↺ antihorario";
    b.setAttribute("aria-pressed", String(sentido === -1));
    b.setAttribute("aria-label",
      `Sentido de giro: ${sentido === 1 ? "horario" : "antihorario"}. Pulsa para cambiar a ${sentido === 1 ? "antihorario" : "horario"}`);
  }

  function iniciarDiario() {
    modo = "diario";
    diarioISO = hoyISO();
    const semilla = fn.semilla_del_dia(diarioISO);
    const etiqueta = `${diarioISO} · reto diario`;
    const guardada = leer().diario;
    if (guardada && guardada.fecha === diarioISO) {
      st = llamar("restaurar", semilla, "diario", etiqueta, JSON.stringify(guardada.historial || []));
    } else {
      st = llamar("nueva_partida", semilla, "diario", etiqueta);
    }
    mensaje("");
    quitarConfirmacion();
    guardarDiario();   // por si la partida restaurada ya estaba completa y sin contar
    pintar();
  }
  function iniciarPractica() {
    modo = "practica";
    st = llamar("nueva_partida", Math.floor(Math.random() * 2147483647), "practica", "práctica");
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
    const casos = [
      [6, {}, "Casilla seca: canal gris y liso. El agua aún no llega."],
      [6, { regada: true }, "Casilla regada: canal azul con rayas y fondo verdoso."],
      [10, { regada: true, fugas: 2 }, "Fuga: un anillo rojo en el extremo de un brazo abierto que no tiene continuación."],
      [7, { fija: true }, "Casilla fija: borde oscuro y un clavo en la esquina. No gira."],
      [6, { regada: true, fuente: true }, "La fonte: círculo blanco con un punto. De ahí sale el agua."],
    ];
    $("leyenda").replaceChildren(...casos.map(([m, opciones, texto]) => {
      const c = construirCasilla("span");
      c.b.setAttribute("aria-hidden", "true");
      pintarCasilla(c, m, { regada: false, fugas: 0, fija: false, fuente: false, ...opciones });
      const li = el("li");
      li.append(c.b, el("span", "", texto));
      return li;
    }));
  }

  // ---------- arranque ----------
  function enfocar(i) {
    if (i < 0 || i >= casillas.length) return;
    casillas.forEach((c) => { c.b.tabIndex = -1; });
    casillas[i].b.tabIndex = 0;
    foco = i;
    casillas[i].b.focus();
  }

  function construirControles() {
    const prado = $("prado");
    prado.addEventListener("click", (ev) => {
      const b = ev.target.closest(".casilla");
      if (!b) return;
      girar(Number(b.dataset.i), ev.shiftKey ? -sentido : sentido);
    });
    prado.addEventListener("contextmenu", (ev) => {
      const b = ev.target.closest(".casilla");
      if (!b) return;
      ev.preventDefault();
      girar(Number(b.dataset.i), -sentido);
    });
    prado.addEventListener("focusin", (ev) => {
      const b = ev.target.closest(".casilla");
      if (!b) return;
      foco = Number(b.dataset.i);
      casillas.forEach((c) => { c.b.tabIndex = -1; });
      b.tabIndex = 0;
    });
    prado.addEventListener("keydown", (ev) => {
      if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
      const b = ev.target.closest(".casilla");
      if (!b || !st) return;
      const i = Number(b.dataset.i), n = st.n;
      let j = null;
      switch (ev.key) {
        case "ArrowLeft": if (i % n > 0) j = i - 1; break;
        case "ArrowRight": if (i % n < n - 1) j = i + 1; break;
        case "ArrowUp": if (i >= n) j = i - n; break;
        case "ArrowDown": if (i < n * (n - 1)) j = i + n; break;
        case "Home": j = i - (i % n); break;
        case "End": j = i - (i % n) + n - 1; break;
        case "e": case "E": ev.preventDefault(); girar(i, 1); return;
        case "q": case "Q": ev.preventDefault(); girar(i, -1); return;
        case "u": case "U": ev.preventDefault(); deshacer(); return;
        default: return;
      }
      ev.preventDefault();
      if (j !== null) enfocar(j);
    });

    $("sentido").addEventListener("click", cambiarSentido);
    $("deshacer").addEventListener("click", deshacer);
    $("reiniciar").addEventListener("click", reiniciar);
    $("copiar").addEventListener("click", copiar);
    $("otra").addEventListener("click", iniciarPractica);
    $("modo-diario").addEventListener("click", iniciarDiario);
    $("modo-practica").addEventListener("click", iniciarPractica);
    ["sentido", "modo-diario", "modo-practica"].forEach((id) => { $(id).disabled = false; });
  }

  async function init() {
    construirLeyenda();
    renderStats();
    try {
      if (typeof loadPyodide === "undefined") throw new Error("Pyodide no se ha cargado");
      const r = await fetch("codigo.py");
      if (!r.ok) throw new Error("No se pudo cargar codigo.py");
      const fuente = await r.text();
      $("python-source").textContent = fuente;
      py = await loadPyodide();
      await py.runPythonAsync(fuente);
      ["nueva_partida", "restaurar", "girar", "deshacer", "reiniciar", "compartir_texto",
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

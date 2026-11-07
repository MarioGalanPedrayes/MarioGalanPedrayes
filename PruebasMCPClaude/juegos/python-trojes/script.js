// Trojes: interfaz. Las reglas viven en codigo.py (Python con Pyodide);
// este archivo solo dibuja el estado que devuelve Python y le pasa las acciones.
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const CLAVE = "trojes-v1";

  let py = null;
  const fn = {};
  let st = null;             // último estado devuelto por Python
  let modo = "diario";
  let diarioISO = "";
  let dificultad = "normal"; // dificultad de la práctica
  let origen = null;         // troje de origen elegido
  let foco = 0;
  let pistaVista = null;     // {origen, destino} mostrada, hasta el siguiente movimiento
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

  // ---------- dibujo ----------
  function ficha(clase) {
    const f = el("span", `ficha ${clase.forma}`);
    f.style.setProperty("--c", clase.color);
    f.setAttribute("aria-hidden", "true");
    return f;
  }

  function nombreTroje(i) {
    const t = st.trojes[i];
    const partes = [`Troje ${i + 1}`];
    if (st.sellados[i]) partes.push(`sellado de ${st.clases[t[0]].nombre}`);
    else if (t.length === 0) partes.push("vacío");
    else partes.push("de abajo arriba: " + t.map((c) => st.clases[c].nombre).join(", "));
    if (st.candado === i && st.candado_cerrado) partes.push("con candado, cerrado");
    if (origen === i) partes.push("elegido como origen");
    return partes.join(". ");
  }

  function construirTrojes() {
    const cont = $("trojes");
    cont.replaceChildren();
    st.trojes.forEach((_, i) => {
      const b = el("button", "troje");
      b.type = "button";
      b.dataset.i = String(i);
      b.tabIndex = i === foco ? 0 : -1;
      cont.append(b);
    });
  }

  function pintar() {
    if ($("trojes").children.length !== st.trojes.length) { foco = 0; construirTrojes(); }
    const jugando = st.estado === "jugando";
    [...$("trojes").children].forEach((b, i) => {
      b.replaceChildren();
      const t = st.trojes[i];
      t.forEach((c) => b.append(ficha(st.clases[c])));
      const cerrado = st.candado === i && st.candado_cerrado;
      if (st.sellados[i]) b.append(el("span", "marca", "sellado"));
      if (cerrado) b.append(el("span", "marca", "candado"));
      b.append(el("span", "numero", String(i + 1)));
      b.classList.toggle("sellado", st.sellados[i]);
      b.classList.toggle("cerrado", cerrado);
      b.classList.toggle("origen", origen === i);
      b.classList.toggle("fin", !jugando);
      b.classList.toggle("pista-origen", !!pistaVista && pistaVista.origen === i);
      b.classList.toggle("pista-destino", !!pistaVista && pistaVista.destino === i);
      b.setAttribute("aria-label", nombreTroje(i));
      b.setAttribute("aria-pressed", String(origen === i));
    });

    $("c-movs").textContent = st.movimientos;
    $("c-ref").textContent = st.referencia;
    $("c-sellados").textContent = `${st.n_sellados}/${st.total_clases}`;
    $("c-pistas").textContent = `${st.pistas}/${st.pistas_max}`;
    $("resumen").textContent =
      `${st.n_sellados} de ${st.total_clases} productos sellados, ${st.movimientos} movimientos.` +
      (jugando ? "" : " Cosecha completa.");

    $("deshacer").disabled = !st.puede_deshacer;
    $("pista").disabled = !jugando || st.pistas >= st.pistas_max;
    $("reiniciar").disabled = !jugando || st.movimientos === 0;
    if (!jugando) quitarConfirmacion();
    if (jugando && st.sin_movimientos) mensaje("No quedan movimientos posibles: deshaz alguno o reinicia.");

    $("titulo-partida").textContent = modo === "diario"
      ? `Reto del ${fechaLarga(diarioISO)} (difícil): el mismo reparto para todo el mundo.`
      : `Práctica ${st.dificultad_nombre.toLowerCase()}, reparto número ${st.semilla}.`;

    const fin = st.estado === "completada";
    $("resultado").hidden = !fin;
    if (fin) {
      const est = "★".repeat(st.estrellas) + "☆".repeat(3 - st.estrellas);
      $("resultado-titulo").textContent = "Cosecha guardada";
      $("resultado-texto").textContent =
        `${est} ${st.movimientos} movimientos; la referencia era ${st.referencia}.` +
        (st.pistas ? ` Con ${st.pistas} ${st.pistas === 1 ? "pista" : "pistas"} la nota máxima es de dos estrellas.` : "") +
        (st.estrellas === 3 ? " Muy cerca de la mejor solución." : " ¿Puedes hacerlo con menos? Prueba otra partida.");
      $("compartir-texto").textContent = fn.compartir_texto();
      $("otra").textContent = modo === "diario" ? "Jugar una de práctica" : "Otra partida de práctica";
    }

    $("modo-diario").classList.toggle("activo", modo === "diario");
    $("modo-practica").classList.toggle("activo", modo === "practica");
    $("modo-diario").setAttribute("aria-pressed", String(modo === "diario"));
    $("modo-practica").setAttribute("aria-pressed", String(modo === "practica"));
    $("fila-dificultad").hidden = modo !== "practica";
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
        JSON.stringify(datos.estadisticas || {}), diarioISO, st.movimientos, st.estrellas
      );
      datos.diario.contada = true;
    }
    escribir(datos);
    renderStats();
  }

  // ---------- acciones ----------
  function aplicar(nuevo) {
    if (nuevo.error) { mensaje(nuevo.error); pintar(); return false; }
    st = nuevo;
    mensaje("");
    return true;
  }

  function elegir(i) {
    if (!st || st.estado !== "jugando") return;
    if (origen === null) {
      if (!st.trojes[i].length) { mensaje("Ese troje está vacío."); return; }
      origen = i;
      mensaje("");
      pintar();
      return;
    }
    if (origen === i) { origen = null; mensaje(""); pintar(); return; }
    const o = origen;
    origen = null;
    pistaVista = null;
    const nuevo = llamar("mover", o, i);
    if (aplicar(nuevo)) { quitarConfirmacion(); guardarDiario(); }
    pintar();
  }

  function deshacer() {
    if (!st) return;
    origen = null; pistaVista = null;
    if (aplicar(llamar("deshacer"))) guardarDiario();
    pintar();
  }

  function pedirPista() {
    if (!st || st.estado !== "jugando") return;
    origen = null;
    const nuevo = llamar("pista");
    if (nuevo.error) { mensaje(nuevo.error); return; }
    st = nuevo;
    pistaVista = nuevo.pista;
    mensaje(`Pista: pasa del troje ${pistaVista.origen + 1} al troje ${pistaVista.destino + 1}.`);
    guardarDiario();
    pintar();
  }

  function quitarConfirmacion() {
    if (confirmaReiniciar) { clearTimeout(confirmaReiniciar); confirmaReiniciar = null; }
    $("reiniciar").textContent = "Reiniciar";
  }
  function reiniciar() {
    if (!st || st.estado !== "jugando") return;
    if (!confirmaReiniciar) {
      $("reiniciar").textContent = "¿Seguro? Pulsa otra vez";
      confirmaReiniciar = setTimeout(quitarConfirmacion, 3500);
      return;
    }
    quitarConfirmacion();
    origen = null; pistaVista = null;
    st = llamar("reiniciar");
    mensaje("");
    guardarDiario();
    pintar();
  }

  function iniciarDiario() {
    modo = "diario";
    origen = null; pistaVista = null;
    diarioISO = hoyISO();
    const semilla = fn.semilla_del_dia(diarioISO);
    const etiqueta = `${diarioISO} · reto diario`;
    const guardada = leer().diario;
    if (guardada && guardada.fecha === diarioISO) {
      st = llamar("restaurar", semilla, "diario", etiqueta, "dificil",
        JSON.stringify(guardada.historial || []), guardada.pistas || 0);
    } else {
      st = llamar("nueva_partida", semilla, "diario", etiqueta, "dificil");
    }
    mensaje("");
    quitarConfirmacion();
    guardarDiario();
    pintar();
  }
  function iniciarPractica() {
    modo = "practica";
    origen = null; pistaVista = null;
    st = llamar("nueva_partida", Math.floor(Math.random() * 2147483647), "practica", "práctica", dificultad);
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
    // Los datos de los productos vienen de Python en cada estado; aquí se usan los de la primera partida.
    $("leyenda").replaceChildren(...st.clases.map((c) => {
      const li = el("li");
      li.append(ficha(c), el("span", "", `${c.nombre} (${c.forma})`));
      return li;
    }));
  }

  // ---------- controles ----------
  function enfocar(i) {
    const hijos = [...$("trojes").children];
    if (i < 0 || i >= hijos.length) return;
    hijos.forEach((b) => { b.tabIndex = -1; });
    hijos[i].tabIndex = 0;
    foco = i;
    hijos[i].focus();
  }

  function construirControles() {
    const cont = $("trojes");
    cont.addEventListener("click", (ev) => {
      const b = ev.target.closest(".troje");
      if (b) elegir(Number(b.dataset.i));
    });
    cont.addEventListener("focusin", (ev) => {
      const b = ev.target.closest(".troje");
      if (!b) return;
      foco = Number(b.dataset.i);
      [...cont.children].forEach((x) => { x.tabIndex = -1; });
      b.tabIndex = 0;
    });
    cont.addEventListener("keydown", (ev) => {
      if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
      const b = ev.target.closest(".troje");
      if (!b || !st) return;
      const i = Number(b.dataset.i);
      if (ev.key === "ArrowLeft") { ev.preventDefault(); enfocar(i - 1); }
      else if (ev.key === "ArrowRight") { ev.preventDefault(); enfocar(i + 1); }
      else if (ev.key === "Home") { ev.preventDefault(); enfocar(0); }
      else if (ev.key === "End") { ev.preventDefault(); enfocar(st.trojes.length - 1); }
      else if (ev.key === "Escape") { origen = null; mensaje(""); pintar(); }
      else if (ev.key === "u" || ev.key === "U") { ev.preventDefault(); deshacer(); }
      else if (ev.key === "p" || ev.key === "P") { ev.preventDefault(); pedirPista(); }
      else if (/^[1-9]$/.test(ev.key)) {
        const j = Number(ev.key) - 1;
        if (j < st.trojes.length) { ev.preventDefault(); enfocar(j); elegir(j); }
      }
      // Espacio e Intro activan el botón y llegan como "click".
    });

    $("deshacer").addEventListener("click", deshacer);
    $("pista").addEventListener("click", pedirPista);
    $("reiniciar").addEventListener("click", reiniciar);
    $("copiar").addEventListener("click", copiar);
    $("otra").addEventListener("click", iniciarPractica);
    $("modo-diario").addEventListener("click", iniciarDiario);
    $("modo-practica").addEventListener("click", iniciarPractica);
    $("dificultad").addEventListener("change", () => {
      dificultad = $("dificultad").value;
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
      ["nueva_partida", "restaurar", "mover", "deshacer", "reiniciar", "pista", "compartir_texto",
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

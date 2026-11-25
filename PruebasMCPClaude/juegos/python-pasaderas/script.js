// Pasaderas: interfaz. Las reglas viven en codigo.py (Python con Pyodide);
// este archivo solo dibuja el estado que devuelve Python y le pasa las acciones.
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const CLAVE = "pasaderas-v1";

  let py = null;
  const fn = {};
  let st = null;            // último estado devuelto por Python
  let modo = "diario";
  let diarioISO = "";
  let nivel = "corriente";
  let semillaActual = 0;
  let confirma = null;      // temporizador de confirmación de "Rendirme"/"Reiniciar"
  let pistaVista = "";

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

  // ---------- dibujo ----------
  function piedraEl(palabra, cambio, clases) {
    const s = el("span", "piedra" + (clases ? " " + clases : ""));
    s.setAttribute("aria-label", palabra.split("").join(" ") + (cambio >= 0 ? `, cambia la letra ${cambio + 1}` : ""));
    [...palabra].forEach((ch, j) => {
      s.append(el("span", j === cambio ? "cambio" : "", ch));
    });
    return s;
  }

  function pintar() {
    const jugando = st.estado === "jugando";
    $("o-inicio").textContent = st.inicio;
    $("o-fin").textContent = st.fin;
    $("info-par").textContent =
      `Par: ${st.par} ${st.par === 1 ? "paso" : "pasos"}` +
      (st.bloqueadas.length ? ` (con ${st.bloqueadas.length === 1 ? "la crecida" : "las crecidas"} ya contadas).` : ".");

    const bl = $("bloqueadas");
    bl.replaceChildren();
    if (!st.bloqueadas.length) bl.append(el("li", "ninguna", "Ninguna: el río va bajo."));
    st.bloqueadas.forEach((w) => bl.append(el("li", "", w)));
    $("bloqueadas").parentElement.removeAttribute("aria-hidden");

    const cam = $("camino");
    cam.replaceChildren();
    st.piedras.forEach((p, i) => {
      const li = el("li");
      const esActual = i === st.piedras.length - 1;
      li.append(piedraEl(p.palabra, p.cambio, (esActual ? "actual " : "") + (p.palabra === st.fin ? "meta" : "")));
      cam.append(li);
    });

    $("c-pasos").textContent = String(st.pasos);
    $("c-par").textContent = String(st.par);
    $("c-pistas").textContent = `${st.pistas}/${st.ayudas_max}`;
    $("resumen").textContent =
      `Estás en ${st.actual}. ${st.pasos} ${st.pasos === 1 ? "paso" : "pasos"} de un par de ${st.par}.`;

    $("entrada").disabled = !jugando;
    $("pisar").disabled = !jugando;
    $("deshacer").disabled = !st.puede_deshacer;
    $("pista").disabled = !jugando || st.pistas >= st.ayudas_max || st.sin_salida;
    $("reiniciar").disabled = !jugando || st.pasos === 0;
    $("rendirse").disabled = !jugando;
    $("pista").textContent = `Pista (${st.ayudas_max - st.pistas})`;
    if (!jugando) quitarConfirmacion();

    $("titulo-partida").textContent = modo === "diario"
      ? `Reto del ${fechaLarga(diarioISO)} (${st.nivel_nombre}): el mismo río para todo el mundo.`
      : `Práctica · ${st.nivel_nombre}.`;

    if (jugando && st.sin_salida) {
      mensaje("Desde esta piedra no hay salida: deshaz algún paso.", true);
    }

    const fin = st.estado !== "jugando";
    const res = $("resultado");
    res.hidden = !fin;
    res.classList.toggle("rendida", st.estado === "rendida");
    $("solucion").hidden = st.estado !== "rendida";
    $("solucion").replaceChildren();
    if (st.estado === "completada") {
      const est = "★".repeat(st.estrellas) + "☆".repeat(3 - st.estrellas);
      $("resultado-titulo").textContent = "Orilla alcanzada";
      $("resultado-texto").textContent =
        `${est} ${st.pasos} ${st.pasos === 1 ? "paso" : "pasos"} con un par de ${st.par}` +
        (st.pistas ? ` y ${st.pistas} ${st.pistas === 1 ? "pista" : "pistas"}.` : " y sin pistas.") +
        (st.estrellas === 3 ? " Ruta limpia." : "");
      $("compartir-texto").textContent = fn.compartir_texto();
      $("copiar").hidden = false;
    } else if (st.estado === "rendida") {
      $("resultado-titulo").textContent = "Un camino mínimo";
      $("resultado-texto").textContent = `Así se llegaba en ${st.par} pasos. Esta partida no cuenta para la racha.`;
      st.solucion.forEach((w, i) => {
        const li = el("li");
        li.append(piedraEl(w, i ? [...w].findIndex((c, j) => c !== st.solucion[i - 1][j]) : -1, w === st.fin ? "meta" : ""));
        $("solucion").append(li);
      });
      $("compartir-texto").textContent = "";
      $("copiar").hidden = true;
    }
    if (fin) $("otra").textContent = modo === "diario" ? "Jugar una de práctica" : "Otra de práctica";

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
    datos.diario = {
      fecha: diarioISO, camino: st.camino, pistas: st.pistas,
      rendida: st.estado === "rendida", contada: !!previo.contada,
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
  function tras(okMensaje) {
    pintar();
    guardarDiario();
    const atascado = st.estado === "jugando" && st.sin_salida;
    if (okMensaje !== undefined && !atascado) mensaje(okMensaje);
  }

  function pisar(texto) {
    quitarConfirmacion();
    pistaVista = "";
    if (!aplicar(llamar("pisar", texto))) return false;
    tras("");
    return true;
  }

  function enviar(ev) {
    ev.preventDefault();
    if (!st || st.estado !== "jugando") return;
    const campo = $("entrada");
    const valor = campo.value.trim();
    if (!valor) { mensaje("Escribe una palabra de cuatro letras.", true); return; }
    if (pisar(valor)) campo.value = "";
    if (st.estado === "jugando") campo.focus();
  }

  function deshacer() {
    if (!st || !st.puede_deshacer) return;
    quitarConfirmacion();
    if (aplicar(llamar("deshacer"))) tras("Vuelves a la piedra anterior.");
    $("entrada").focus();
  }

  function pedirPista() {
    if (!st || st.estado !== "jugando") return;
    const r = llamar("pista");
    if (r.error) { mensaje(r.error, true); return; }
    st = r;
    pintar();
    guardarDiario();
    mensaje(`Pista: pisa «${r.pista}» (te quedarán ${r.pasos_restantes - 1} ${r.pasos_restantes - 1 === 1 ? "paso" : "pasos"} tras ella).`);
  }

  function quitarConfirmacion() {
    if (confirma) { clearTimeout(confirma.t); confirma.boton.textContent = confirma.texto; confirma = null; }
  }
  function conConfirmacion(boton, texto, accion) {
    if (confirma && confirma.boton === boton) { quitarConfirmacion(); accion(); return; }
    quitarConfirmacion();
    confirma = { boton, texto: boton.textContent, t: setTimeout(quitarConfirmacion, 4000) };
    boton.textContent = texto;
  }

  function reiniciar() {
    conConfirmacion($("reiniciar"), "¿Seguro? Pulsa otra vez", () => {
      if (aplicar(llamar("reiniciar"))) tras("Vuelves a la orilla de salida.");
    });
  }
  function rendirse() {
    conConfirmacion($("rendirse"), "¿Seguro? Pulsa otra vez", () => {
      if (aplicar(llamar("rendirse"))) tras("");
    });
  }

  async function copiar() {
    const texto = $("compartir-texto").textContent;
    try {
      await navigator.clipboard.writeText(texto);
      mensaje("Resultado copiado.");
    } catch (e) {
      mensaje("No se ha podido copiar: selecciona el texto y cópialo a mano.", true);
    }
  }

  // ---------- partidas ----------
  function iniciarDiario() {
    modo = "diario";
    quitarConfirmacion();
    diarioISO = hoyISO();
    semillaActual = fn.semilla_del_dia(diarioISO);
    const g = leer().diario;
    let nuevo;
    if (g && g.fecha === diarioISO && Array.isArray(g.camino)) {
      nuevo = llamar("restaurar", semillaActual, "corriente", JSON.stringify(g.camino), g.pistas || 0, !!g.rendida, diarioISO);
    } else {
      nuevo = llamar("nueva_partida", semillaActual, "corriente", diarioISO);
    }
    if (aplicar(nuevo)) { mensaje(""); pintar(); guardarDiario(); }
  }

  function iniciarPractica() {
    modo = "practica";
    quitarConfirmacion();
    semillaActual = (Math.floor(Math.random() * 0xFFFFFFFF)) >>> 0;
    if (aplicar(llamar("nueva_partida", semillaActual, nivel, "práctica"))) { mensaje(""); pintar(); }
    $("entrada").value = "";
  }

  // ---------- arranque ----------
  function construirControles() {
    $("form-paso").addEventListener("submit", enviar);
    $("deshacer").addEventListener("click", deshacer);
    $("pista").addEventListener("click", pedirPista);
    $("reiniciar").addEventListener("click", reiniciar);
    $("rendirse").addEventListener("click", rendirse);
    $("copiar").addEventListener("click", copiar);
    $("otra").addEventListener("click", iniciarPractica);
    $("modo-diario").addEventListener("click", iniciarDiario);
    $("modo-practica").addEventListener("click", iniciarPractica);
    $("nivel").addEventListener("change", () => { nivel = $("nivel").value; iniciarPractica(); });
    document.addEventListener("keydown", (ev) => {
      if (ev.altKey || !st) return;
      const enCampo = ev.target === $("entrada");
      if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === "z") { ev.preventDefault(); deshacer(); return; }
      if (ev.ctrlKey || ev.metaKey || enCampo) return;
      const t = ev.target.tagName;
      if (t === "INPUT" || t === "SELECT" || t === "TEXTAREA") return;
      if (ev.key.toLowerCase() === "u") deshacer();
      else if (ev.key.toLowerCase() === "p") pedirPista();
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
      ["nueva_partida", "restaurar", "pisar", "deshacer", "reiniciar", "pista", "rendirse", "compartir_texto",
        "actualizar_estadisticas", "racha_vigente", "semilla_del_dia"]
        .forEach((n) => { fn[n] = py.globals.get(n); });
      construirControles();
      $("estado-carga").hidden = true;
      renderStats();
      iniciarDiario();
      $("entrada").focus();
    } catch (e) {
      console.error(e);
      $("estado-carga").textContent = "No se ha podido cargar el motor de Python. Comprueba tu conexión y recarga la página.";
    }
  }

  init();
})();

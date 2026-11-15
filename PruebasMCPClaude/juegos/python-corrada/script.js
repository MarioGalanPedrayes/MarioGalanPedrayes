// Corrada: interfaz. Las reglas viven en codigo.py (Python con Pyodide);
// este archivo solo dibuja el estado que devuelve Python y le pasa las acciones.
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const CLAVE = "corrada-v1";

  let py = null;
  const fn = {};
  let st = null;              // ultimo estado devuelto por Python
  let modo = "diario";
  let diarioISO = "";
  let nivel = "normal";       // nivel de la practica
  let semillaPractica = 0;
  let foco = 0;               // casilla con el foco del teclado
  let pistaVista = null;      // casilla sugerida, hasta la siguiente accion
  let confirmaReiniciar = null;
  let verRuta = true;
  let cargado = false;

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

  // ---------- dibujo ----------
  function posicion(i) {
    return { f: Math.floor(i / st.cols), c: i % st.cols };
  }
  function describir(i) {
    const { f, c } = posicion(i);
    const lugar = `Fila ${f + 1}, columna ${c + 1}`;
    const borde = st.borde.includes(i) ? ", borde" : "";
    let que;
    if (i === st.ternero) que = "ternero";
    else if (st.celdas[i] === 1) que = "piedra de partida";
    else if (st.celdas[i] === 2) que = `tu piedra, turno ${st.turnos_piedra[String(i)]}`;
    else que = "libre";
    let extra = "";
    if (pistaVista === i) extra = ", casilla sugerida";
    else if (verRuta && st.camino.includes(i) && i !== st.ternero) extra = ", en la ruta del ternero";
    return `${lugar}${borde}, ${que}${extra}`;
  }

  function construirTablero() {
    const t = $("tablero");
    t.replaceChildren();
    t.style.setProperty("--cols", String(st.cols));
    for (let f = 0; f < st.filas; f++) {
      const fila = el("div", "fila-hex" + (f % 2 ? " impar" : ""));
      for (let c = 0; c < st.cols; c++) {
        const i = f * st.cols + c;
        const b = el("button", "casilla");
        b.type = "button";
        b.dataset.i = String(i);
        b.tabIndex = i === foco ? 0 : -1;
        b.append(el("span", "dentro"));
        fila.append(b);
      }
      t.append(fila);
    }
  }

  function pintar() {
    const t = $("tablero");
    if (t.children.length !== st.filas || Number(t.style.getPropertyValue("--cols")) !== st.cols) construirTablero();
    const fin = st.resultado !== "jugando";
    t.classList.toggle("fin", fin);
    const botones = t.querySelectorAll(".casilla");
    const rastro = new Set(st.rastro.slice(0, -1));
    const ruta = new Set(verRuta ? st.camino : []);
    botones.forEach((b) => {
      const i = Number(b.dataset.i);
      b.className = "casilla";
      const dentro = b.firstChild;
      dentro.replaceChildren();
      if (st.borde.includes(i)) b.classList.add("borde");
      if (i === st.ternero) {
        b.classList.add("ternero");
        dentro.append(el("span", "", "T"));
        if (st.resultado === "ganada") b.classList.add("acorralado");
      } else if (st.celdas[i] === 1) {
        b.classList.add("piedra");
        dentro.append(el("span", "", "▪"));
      } else if (st.celdas[i] === 2) {
        b.classList.add("puesta");
        dentro.append(el("span", "", String(st.turnos_piedra[String(i)])));
      } else {
        if (rastro.has(i)) b.classList.add("rastro");
        if (ruta.has(i)) b.classList.add("ruta");
        if (pistaVista === i) b.classList.add("pista-casilla");
      }
      const ocupada = i === st.ternero || st.celdas[i] !== 0;
      b.setAttribute("aria-label", describir(i));
      b.disabled = false;
      b.setAttribute("aria-disabled", ocupada || fin ? "true" : "false");
      b.tabIndex = i === foco ? 0 : -1;
    });

    $("c-usadas").textContent = String(st.usadas);
    $("c-restantes").textContent = String(st.restantes);
    $("c-distancia").textContent = st.distancia >= 0 ? `${st.distancia} ${plural(st.distancia, "paso", "pasos")}` : "–";
    $("c-ref").textContent = String(st.ref);
    $("c-pistas").textContent = `${st.pistas}/${st.max_pistas}`;
    $("deshacer").disabled = !(st.acciones.length > 0);
    $("pista").disabled = fin || st.pistas >= st.max_pistas;
    $("reiniciar").disabled = false;
    $("titulo-partida").textContent = st.modo === "diario"
      ? `Reto diario del ${fechaLarga(st.fecha)} · ${st.nombre_nivel}`
      : `Práctica · ${st.nombre_nivel}`;

    const resumen = fin
      ? st.motivo
      : `Has puesto ${st.usadas} ${plural(st.usadas, "piedra", "piedras")}; te quedan ${st.restantes}. El ternero está a ${st.distancia} ${plural(st.distancia, "paso", "pasos")} de la salida.`;
    $("resumen").textContent = resumen;
    mostrarResultado();
  }

  function mostrarResultado() {
    const r = $("resultado");
    if (st.resultado === "jugando") { r.hidden = true; return; }
    r.hidden = false;
    const gana = st.resultado === "ganada";
    r.classList.toggle("derrota", !gana);
    $("resultado-titulo").textContent = gana
      ? "★".repeat(st.estrellas) + "☆".repeat(3 - st.estrellas) + " ¡Ternero acorralado!"
      : "Se ha escapado";
    $("resultado-texto").textContent = gana
      ? `Lo acorralaste con ${st.usadas} piedras (referencia: ${st.ref}).${st.pistas ? " Con pistas, la nota máxima es de dos estrellas." : ""}`
      : `${st.motivo} Puedes deshacer piedras o reiniciar la partida.`;
    $("bloque-compartir").hidden = false;
    $("compartir-texto").textContent = fn.compartir();
    $("otra").hidden = st.modo === "diario";
  }

  // ---------- acciones ----------
  function aplicar(nuevo, mover) {
    st = nuevo;
    pistaVista = nuevo.pista;
    if (typeof mover === "number") foco = mover;
    pintar();
    mensaje(st.error, !!st.error);
    guardarProgreso();
  }

  function colocar(i) {
    if (!st || st.resultado !== "jugando") return;
    confirmaReiniciar = null;
    const antes = st.resultado;
    const nuevo = llamar("colocar", i);
    aplicar(nuevo, i);
    if (nuevo.resultado !== "jugando" && antes === "jugando") registrarFin();
  }

  function registrarFin() {
    if (st.modo !== "diario") return;
    const datos = leer();
    datos.diario = datos.diario || {};
    const ya = datos.diario[st.fecha];
    if (!ya || !ya.terminado) {
      datos.diario[st.fecha] = { acciones: st.acciones, pistas: st.pistas, terminado: true, gano: st.resultado === "ganada", estrellas: st.estrellas };
      escribir(datos);
    }
    pintarStats();
  }

  function guardarProgreso() {
    if (!cargado || st.modo !== "diario") return;
    const datos = leer();
    datos.diario = datos.diario || {};
    const ya = datos.diario[st.fecha];
    // Un reto ganado queda fijado: no se sobrescribe con una repeticion.
    if (ya && ya.terminado && ya.gano && st.resultado !== "ganada") return;
    datos.diario[st.fecha] = { acciones: st.acciones, pistas: st.pistas, terminado: st.resultado !== "jugando", gano: st.resultado === "ganada", estrellas: st.estrellas };
    escribir(datos);
  }

  function nuevaPartida() {
    pistaVista = null;
    confirmaReiniciar = null;
    mensaje("");
    if (modo === "diario") {
      diarioISO = hoyISO();
      const datos = leer();
      const guardado = datos.diario && datos.diario[diarioISO];
      if (guardado) {
        st = llamar("reconstruir", "diario", "normal", diarioISO, JSON.stringify(guardado.acciones), guardado.pistas);
      } else {
        st = llamar("nueva", "diario", "normal", diarioISO);
      }
    } else {
      semillaPractica = Math.floor(Math.random() * 4294967296);
      st = llamar("nueva", "practica", nivel, String(semillaPractica));
    }
    foco = (Math.floor(st.filas / 2)) * st.cols + Math.floor(st.cols / 2) + 1;
    construirTablero();
    pintar();
    pintarStats();
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

  function cambiarModo(m) {
    modo = m;
    $("modo-diario").classList.toggle("activo", m === "diario");
    $("modo-practica").classList.toggle("activo", m === "practica");
    $("modo-diario").setAttribute("aria-pressed", String(m === "diario"));
    $("modo-practica").setAttribute("aria-pressed", String(m === "practica"));
    $("fila-nivel").hidden = m !== "practica";
    nuevaPartida();
  }

  // ---------- eventos ----------
  function enlazar() {
    $("tablero").addEventListener("click", (e) => {
      const b = e.target.closest(".casilla");
      if (!b) return;
      colocar(Number(b.dataset.i));
    });
    $("tablero").addEventListener("keydown", (e) => {
      const b = e.target.closest(".casilla");
      if (!b || !st) return;
      let i = Number(b.dataset.i);
      const f = Math.floor(i / st.cols), c = i % st.cols;
      let n = i;
      if (e.key === "ArrowLeft" && c > 0) n = i - 1;
      else if (e.key === "ArrowRight" && c < st.cols - 1) n = i + 1;
      else if (e.key === "ArrowUp" && f > 0) n = i - st.cols;
      else if (e.key === "ArrowDown" && f < st.filas - 1) n = i + st.cols;
      else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); colocar(i); return; }
      else return;
      e.preventDefault();
      foco = n;
      pintar();
      $("tablero").querySelector(`[data-i="${n}"]`).focus();
    });
    document.addEventListener("keydown", (e) => {
      if (e.ctrlKey || e.metaKey || e.altKey || !st) return;
      const tag = (e.target.tagName || "").toLowerCase();
      if (tag === "select" || tag === "input") return;
      if (e.key === "u" || e.key === "U") $("deshacer").click();
      else if (e.key === "p" || e.key === "P") $("pista").click();
    });
    $("deshacer").addEventListener("click", () => {
      if (!st || !st.acciones.length) return;
      confirmaReiniciar = null;
      aplicar(llamar("deshacer"));
      mensaje("Última piedra quitada.");
    });
    $("pista").addEventListener("click", () => {
      if (!st || st.resultado !== "jugando") return;
      const nuevo = llamar("pista");
      aplicar(nuevo);
      if (nuevo.pista !== null && nuevo.pista !== undefined) {
        foco = nuevo.pista;
        pintar();
        mensaje(`Pista: prueba con ${describir(nuevo.pista)}. Con pistas la nota máxima es de dos estrellas.`);
      }
    });
    $("reiniciar").addEventListener("click", () => {
      if (!st) return;
      if (st.usadas > 0 && st.resultado === "jugando" && confirmaReiniciar !== st.semilla) {
        confirmaReiniciar = st.semilla;
        mensaje("Pulsa «Reiniciar» otra vez para empezar de cero.");
        return;
      }
      confirmaReiniciar = null;
      aplicar(llamar("reiniciar"));
      mensaje("Partida reiniciada.");
    });
    $("modo-diario").addEventListener("click", () => cambiarModo("diario"));
    $("modo-practica").addEventListener("click", () => cambiarModo("practica"));
    $("nivel").addEventListener("change", (e) => { nivel = e.target.value; nuevaPartida(); });
    $("otra").addEventListener("click", nuevaPartida);
    $("ver-ruta").addEventListener("change", (e) => { verRuta = e.target.checked; if (st) pintar(); });
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
  async function iniciar() {
    const aviso = $("estado-carga");
    try {
      if (typeof loadPyodide !== "function") throw new Error("pyodide.js no se ha cargado");
      py = await loadPyodide();
      const resp = await fetch("codigo.py");
      if (!resp.ok) throw new Error("no se pudo leer codigo.py");
      const codigo = await resp.text();
      $("python-source").textContent = codigo;
      py.runPython(codigo);
      ["nueva", "reconstruir", "colocar", "deshacer", "reiniciar", "pista", "compartir", "racha"].forEach((n) => { fn[n] = py.globals.get(n); });
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

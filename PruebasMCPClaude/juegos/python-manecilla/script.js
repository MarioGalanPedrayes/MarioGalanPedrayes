// MANECILLA: interfaz. Las reglas viven en codigo.py (Python con Pyodide);
// este archivo mide el tiempo, dibuja la esfera (SVG) y avisa a Python de cada pulsación.
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const CLAVE = "manecilla-v1";
  const FN = ["nueva_partida", "estado", "avanzar", "tocar", "texto_compartir", "registrar_partida"];
  const CX = 150, CY = 150, R_SECTOR = 112, R_AGUJA = 122, R_TIEMPO = 140;
  const CIRC_TIEMPO = 2 * Math.PI * R_TIEMPO;
  const FRACCION_PERFECTO = 0.2;   // igual que en codigo.py (solo para dibujar la zona central)
  const BLOQUEO_FIN_MS = 700;      // tras perder, el espacio no reinicia al instante

  const fn = {};
  let st = null;
  let ultimo = performance.now();
  let eventoVisto = 0;
  let registrada = false;
  let finMs = 0;
  let aviso = 0;

  const el = (id) => $(id);
  const SVGNS = "http://www.w3.org/2000/svg";
  const llamar = (nombre, ...a) => JSON.parse(fn[nombre](...a));
  const miles = (n) => Number(n).toLocaleString("es-ES");

  // ---------- geometría ----------
  function punto(grados, r) {
    const a = (grados * Math.PI) / 180;
    return [CX + r * Math.sin(a), CY - r * Math.cos(a)];
  }
  function arco(centro, ancho, r) {
    const [x1, y1] = punto(centro - ancho / 2, r);
    const [x2, y2] = punto(centro + ancho / 2, r);
    return `M ${x1.toFixed(2)} ${y1.toFixed(2)} A ${r} ${r} 0 ${ancho > 180 ? 1 : 0} 1 ${x2.toFixed(2)} ${y2.toFixed(2)}`;
  }
  function construirMarcas() {
    const g = el("marcas");
    for (let i = 0; i < 60; i++) {
      const grande = i % 5 === 0;
      const [x1, y1] = punto(i * 6, grande ? 82 : 88);
      const [x2, y2] = punto(i * 6, 95);
      const l = document.createElementNS(SVGNS, "line");
      l.setAttribute("x1", x1.toFixed(2)); l.setAttribute("y1", y1.toFixed(2));
      l.setAttribute("x2", x2.toFixed(2)); l.setAttribute("y2", y2.toFixed(2));
      l.setAttribute("class", grande ? "marca grande" : "marca");
      g.append(l);
    }
  }

  // ---------- guardado ----------
  function leerStats() {
    try { const d = JSON.parse(localStorage.getItem(CLAVE)); return d && typeof d.estadisticas === "string" ? d.estadisticas : "{}"; }
    catch (e) { return "{}"; }
  }
  function guardarStats(texto) {
    try { localStorage.setItem(CLAVE, JSON.stringify({ estadisticas: texto })); } catch (e) { /* sin almacenamiento */ }
  }
  function pintarStats(texto) {
    let e = {};
    try { e = JSON.parse(texto) || {}; } catch (x) { e = {}; }
    el("st-partidas").textContent = miles(e.partidas || 0);
    el("st-mejor").textContent = miles(e.mejor || 0);
    el("st-combo").textContent = miles(e.mejor_combo || 0);
    el("st-aciertos").textContent = miles(e.aciertos || 0);
    el("st-perfectos").textContent = miles(e.perfectos || 0);
    el("record").textContent = miles(e.mejor || 0);
  }

  // ---------- dibujo ----------
  function decir(texto, clase) {
    const a = el("aviso");
    a.textContent = texto;
    a.className = "aviso " + (clase || "");
    clearTimeout(aviso);
    aviso = setTimeout(() => { a.textContent = ""; a.className = "aviso"; }, 1400);
  }

  function reaccionar() {
    if (st.evento_n === eventoVisto) return;
    eventoVisto = st.evento_n;
    const caja = el("esfera");
    caja.classList.remove("ok", "mal");
    void caja.getBoundingClientRect();           // reinicia la animación
    if (st.evento === "perfecto") { decir(`¡Perfecto! +${st.ganado}`, "bien"); caja.classList.add("ok"); }
    else if (st.evento === "acierto") { decir(`Bien +${st.ganado}`, "bien"); caja.classList.add("ok"); }
    else if (st.evento === "fallo") { decir("Fallo: pierdes una vida", "mal"); caja.classList.add("mal"); }
    else if (st.evento === "tiempo") { decir("Se acabó el tiempo: pierdes una vida", "mal"); caja.classList.add("mal"); }
    if (st.vida_extra) setTimeout(() => decir("Vida recuperada", "bien"), 450);
  }

  function pintar() {
    const svg = el("dial");
    svg.setAttribute("data-angulo", st.angulo);
    svg.setAttribute("data-centro", st.centro);
    svg.setAttribute("data-ancho", st.ancho);
    svg.setAttribute("data-estado", st.estado);
    el("sector").setAttribute("d", arco(st.centro, st.ancho, R_SECTOR));
    el("perfecto").setAttribute("d", arco(st.centro, st.ancho * FRACCION_PERFECTO * 2, R_SECTOR));
    const [ax, ay] = punto(st.angulo, R_AGUJA);
    el("aguja").setAttribute("x2", ax.toFixed(2));
    el("aguja").setAttribute("y2", ay.toFixed(2));
    el("tiempo").setAttribute("stroke-dasharray", `${(CIRC_TIEMPO * st.tiempo_frac).toFixed(1)} ${CIRC_TIEMPO.toFixed(1)}`);

    el("puntos").textContent = miles(st.puntos);
    el("combo").textContent = st.combo;
    el("mult").textContent = `×${st.mult}`;
    el("aciertos").textContent = st.aciertos;
    let vidas = "";
    for (let i = 0; i < st.vidas_max; i++) vidas += i < st.vidas ? "●" : "○";
    el("vidas").textContent = vidas;
    el("vidas").setAttribute("aria-label", `${st.vidas} de ${st.vidas_max} vidas`);

    const jugando = st.estado === "jugando", listo = st.estado === "listo", fin = st.estado === "fin";
    el("parar").hidden = fin;
    el("parar").textContent = listo ? "Empezar" : "Parar";
    el("ayuda-inicio").hidden = !listo;
    el("resultado").hidden = !fin;
    reaccionar();
    if (fin && !registrada) terminar();
    return jugando;
  }

  function terminar() {
    registrada = true;
    finMs = performance.now();
    const previo = leerStats();
    const nuevo = JSON.parse(fn.registrar_partida(previo, st.puntos, st.aciertos, st.perfectos, st.mejor_combo));
    const texto = JSON.stringify(nuevo);
    guardarStats(texto);
    pintarStats(texto);
    el("resultado-titulo").textContent = nuevo.nuevo_record && st.puntos > 0 ? "Nuevo récord" : "Fin de la partida";
    el("resultado-texto").textContent = `Has sumado ${miles(st.puntos)} puntos con ${st.aciertos} aciertos.`;
    el("compartir-texto").textContent = fn.texto_compartir();
    el("jugar-otra").focus();
  }

  // ---------- bucle y acciones ----------
  function tick(ahora) {
    const dt = (ahora - ultimo) / 1000;
    ultimo = ahora;
    if (st && st.estado === "jugando") { st = llamar("avanzar", dt); pintar(); }
    requestAnimationFrame(tick);
  }

  function tocar() {
    if (!st) return;
    const ahora = performance.now();
    if (st.estado === "jugando") { st = llamar("avanzar", (ahora - ultimo) / 1000); ultimo = ahora; }
    if (st.estado === "fin") return;
    if (st.estado === "listo") ultimo = ahora;
    st = llamar("tocar");
    pintar();
  }

  function nueva() {
    st = llamar("nueva_partida", Math.floor(Math.random() * 2147483647));
    registrada = false;
    eventoVisto = st.evento_n;
    el("aviso").textContent = "";
    pintar();
    el("parar").focus();
  }

  async function copiar() {
    const texto = el("compartir-texto").textContent;
    let ok = false;
    try { await navigator.clipboard.writeText(texto); ok = true; } catch (e) {
      const area = document.createElement("textarea");
      area.value = texto; document.body.append(area); area.select();
      try { ok = document.execCommand("copy"); } catch (e2) { ok = false; }
      area.remove();
    }
    const b = el("copiar");
    b.textContent = ok ? "Copiado" : "Selecciona el texto y cópialo";
    setTimeout(() => { b.textContent = "Copiar resultado"; }, 2200);
  }

  function enlazar() {
    el("parar").addEventListener("click", tocar);
    el("dial").addEventListener("pointerdown", (ev) => { ev.preventDefault(); tocar(); });
    el("jugar-otra").addEventListener("click", nueva);
    el("copiar").addEventListener("click", copiar);
    document.addEventListener("keydown", (ev) => {
      if (ev.code !== "Space" || ev.repeat || ev.ctrlKey || ev.metaKey || ev.altKey) return;
      const activo = document.activeElement;
      if (activo && activo.tagName === "BUTTON") return;   // el botón enfocado ya reacciona al espacio
      ev.preventDefault();
      if (st && st.estado === "fin") {
        if (performance.now() - finMs > BLOQUEO_FIN_MS) nueva();
      } else tocar();
    });
    document.addEventListener("visibilitychange", () => { ultimo = performance.now(); });
  }

  async function init() {
    construirMarcas();
    pintarStats(leerStats());
    try {
      const r = await fetch("codigo.py");
      if (!r.ok) throw new Error("No se pudo cargar codigo.py");
      const fuente = await r.text();
      el("python-source").textContent = fuente;
      const py = await loadPyodide();
      await py.runPythonAsync(fuente);
      FN.forEach((n) => { fn[n] = py.globals.get(n); });
      enlazar();
      el("estado-carga").hidden = true;
      el("parar").disabled = false;
      nueva();
      ultimo = performance.now();
      requestAnimationFrame(tick);
    } catch (e) {
      console.error(e);
      el("estado-carga").textContent = "No se ha podido cargar el motor de Python. Comprueba tu conexión y recarga la página.";
    }
  }

  init();
})();

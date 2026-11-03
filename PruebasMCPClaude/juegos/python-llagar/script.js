// LLAGAR: interfaz. Las reglas viven en codigo.py (Python con Pyodide);
// este archivo mide el tiempo, dibuja el estado que devuelve Python y guarda la partida.
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const CLAVE = "llagar-v1";
  const TICK_MS = 100;
  const AUTOGUARDADO_MS = 5000;
  const FN = ["nuevo_juego", "estado", "recoger", "avanzar", "avanzar_fuera", "comprar",
              "comprar_mejora", "prestigio", "exportar", "cargar"];

  const fn = {};
  let py = null;
  let st = null;
  let cantidad = 1;           // 1, 10 o 0 (= máximo)
  let ultimo = Date.now();
  let claveMejoras = "";
  const filas = {};           // id de edificio -> elementos de su fila

  function el(tag, clase, texto) {
    const e = document.createElement(tag);
    if (clase) e.className = clase;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }
  const llamar = (nombre, ...args) => JSON.parse(fn[nombre](...args));
  function mensaje(t) { $("mensaje").textContent = t || ""; }

  // ---------- guardado ----------
  function guardar() {
    if (!py || !st) return;
    try {
      localStorage.setItem(CLAVE, JSON.stringify({ estado: fn.exportar(), ts: Date.now() }));
    } catch (e) { /* sin almacenamiento disponible */ }
  }
  function leerGuardado() {
    try { return JSON.parse(localStorage.getItem(CLAVE)); } catch (e) { return null; }
  }

  // ---------- dibujo ----------
  function construirEdificios() {
    const lista = $("edificios");
    lista.replaceChildren();
    st.edificios.forEach((e) => {
      const li = el("li");
      const b = el("button", "item");
      b.type = "button";
      const izq = el("span", "item-texto");
      const nombre = el("strong", "", e.nombre);
      const cant = el("span", "cantidad");
      const desc = el("small", "", e.desc);
      const prod = el("small", "prod");
      izq.append(nombre, cant, desc, prod);
      const coste = el("span", "coste");
      b.append(izq, coste);
      b.addEventListener("click", () => comprar(e.id));
      li.append(b);
      lista.append(li);
      filas[e.id] = { li, b, cant, prod, coste };
    });
  }

  function actualizar() {
    $("manzanas").textContent = st.manzanas_txt;
    $("prod").textContent = st.prod_txt;
    $("click").textContent = st.click_txt;

    st.edificios.forEach((e) => {
      const f = filas[e.id];
      f.li.hidden = !e.visible;
      f.cant.textContent = ` · ${e.cantidad}`;
      f.prod.textContent = e.cantidad
        ? `${e.unidad_txt} cada uno · ${e.total_txt} por segundo en total`
        : `${e.unidad_txt} manzanas por segundo cada uno`;
      f.coste.textContent = `Coste ${e.coste_txt}`;
      f.b.disabled = !e.comprable;
    });

    // mejoras: se reconstruye la lista solo si cambia qué mejoras hay disponibles
    const clave = st.mejoras.map((m) => m.id).join(",");
    const lista = $("mejoras");
    if (clave !== claveMejoras) {
      claveMejoras = clave;
      lista.replaceChildren(...st.mejoras.map((m) => {
        const li = el("li");
        li.dataset.id = m.id;
        const b = el("button", "item");
        b.type = "button";
        const t = el("span", "item-texto");
        t.append(el("strong", "", m.nombre), el("small", "", m.desc));
        b.append(t, el("span", "coste", `Coste ${m.coste_txt}`));
        b.addEventListener("click", () => comprarMejora(m.id));
        li.append(b);
        return li;
      }));
    }
    st.mejoras.forEach((m) => {
      const b = lista.querySelector(`li[data-id="${m.id}"] button`);
      if (b) b.disabled = !m.comprable;
    });
    $("sin-mejoras").hidden = st.mejoras.length > 0;

    // prestigio
    $("sellos").textContent = st.sellos;
    $("bono").textContent = st.bono_txt;
    $("run").textContent = st.total_run_txt;
    $("prestigio-info").textContent = st.puede_prestigio
      ? `Si reinicias ahora ganas ${st.sellos_ganables} Sello(s) y tu bono pasa a ${st.bono_tras_txt}.`
      : `Necesitas haber recogido 1 M de manzanas en esta cosecha para tu primer Sello (llevas ${st.total_run_txt}).`;
    $("prestigio").disabled = !st.puede_prestigio;
    $("prestigio").textContent = st.puede_prestigio
      ? `Nueva cosecha (+${st.sellos_ganables} Sello${st.sellos_ganables === 1 ? "" : "s"})`
      : "Nueva cosecha";
    $("siguiente-sello").textContent = st.siguiente_sello_txt;

    // estadísticas
    $("st-tiempo").textContent = st.tiempo_txt;
    $("st-recogidas").textContent = st.recogidas;
    $("st-total").textContent = st.total_hist_txt;
    $("st-cosechas").textContent = st.cosechas;
  }

  function mostrarFuera(f) {
    if (!f || !f.ganado) return;
    $("fuera-texto").textContent =
      `Mientras no estabas (${f.tiempo_txt}${f.tope ? ", tope de 8 horas" : ""}) tu llagar produjo ${f.ganado_txt} manzanas.`;
    $("fuera").hidden = false;
  }

  // ---------- acciones ----------
  function aplicar(nuevo) {
    if (nuevo.error) { mensaje(nuevo.error); return false; }
    st = nuevo;
    mensaje("");
    return true;
  }
  function recoger() { st = llamar("recoger"); actualizar(); }
  function comprar(id) { if (aplicar(llamar("comprar", id, cantidad))) { guardar(); } actualizar(); }
  function comprarMejora(id) { if (aplicar(llamar("comprar_mejora", id))) { guardar(); } actualizar(); }
  function nuevaCosecha() {
    if (!st.puede_prestigio) return;
    const ok = window.confirm(
      `¿Empezar una nueva cosecha? Perderás manzanas, edificios y mejoras, y ganarás ${st.sellos_ganables} Sello(s) con un bono permanente.`);
    if (!ok) return;
    if (aplicar(llamar("prestigio"))) { claveMejoras = ""; guardar(); }
    actualizar();
  }
  function borrarTodo() {
    if (!window.confirm("¿Borrar toda la partida, incluidos los Sellos? No se puede deshacer.")) return;
    try { localStorage.removeItem(CLAVE); } catch (e) { /* nada */ }
    st = llamar("nuevo_juego");
    claveMejoras = "";
    $("fuera").hidden = true;
    actualizar();
    mensaje("Partida borrada.");
  }
  function tick() {
    const ahora = Date.now();
    const dt = (ahora - ultimo) / 1000;
    ultimo = ahora;
    st = llamar("avanzar", dt);
    actualizar();
  }

  // ---------- arranque ----------
  function enlazar() {
    $("recoger").addEventListener("click", recoger);
    $("prestigio").addEventListener("click", nuevaCosecha);
    $("borrar").addEventListener("click", borrarTodo);
    $("cerrar-fuera").addEventListener("click", () => { $("fuera").hidden = true; });
    document.querySelectorAll("[data-cantidad]").forEach((b) => {
      b.addEventListener("click", () => {
        cantidad = Number(b.dataset.cantidad);
        document.querySelectorAll("[data-cantidad]").forEach((o) => {
          const activo = o === b;
          o.classList.toggle("activo", activo);
          o.setAttribute("aria-pressed", String(activo));
        });
      });
    });
    document.addEventListener("keydown", (ev) => {
      if (ev.code === "Space" && document.activeElement === document.body) {
        ev.preventDefault();
        recoger();
      }
    });
    document.addEventListener("visibilitychange", () => { if (document.hidden) guardar(); });
    window.addEventListener("pagehide", guardar);
  }

  async function init() {
    try {
      const r = await fetch("codigo.py");
      if (!r.ok) throw new Error("No se pudo cargar codigo.py");
      const fuente = await r.text();
      $("python-source").textContent = fuente;
      py = await loadPyodide();
      await py.runPythonAsync(fuente);
      FN.forEach((n) => { fn[n] = py.globals.get(n); });

      const guardado = leerGuardado();
      let fuera = null;
      if (guardado && typeof guardado.estado === "string") {
        st = llamar("cargar", guardado.estado);
        const segundos = (Date.now() - Number(guardado.ts || Date.now())) / 1000;
        if (segundos >= 30) {
          st = llamar("avanzar_fuera", segundos);
          fuera = st.fuera;
        }
      } else {
        st = llamar("nuevo_juego");
      }
      enlazar();
      construirEdificios();
      actualizar();
      mostrarFuera(fuera);
      $("estado-carga").hidden = true;
      $("recoger").disabled = false;
      ultimo = Date.now();
      setInterval(tick, TICK_MS);
      setInterval(guardar, AUTOGUARDADO_MS);
    } catch (e) {
      console.error(e);
      $("estado-carga").textContent =
        "No se ha podido cargar el motor de Python. Comprueba tu conexión y recarga la página.";
    }
  }

  init();
})();

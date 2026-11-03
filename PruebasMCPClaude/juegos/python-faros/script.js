// Faros de Niebla: interfaz. Las reglas viven en codigo.py (Python con Pyodide);
// este archivo solo dibuja el estado que devuelve Python y le pasa las acciones.
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const SIMBOLOS = [
    { n: "Círculo", g: "●" }, { n: "Rombo", g: "◆" }, { n: "Triángulo", g: "▲" },
    { n: "Cuadrado", g: "■" }, { n: "Estrella", g: "★" }, { n: "Cruz", g: "✚" },
  ];
  const CLAVE = "faros-niebla-v1";
  const LONGITUD = 4;

  let py = null;
  const fn = {};          // funciones de Python ya cargadas
  let st = null;          // último estado devuelto por Python
  let fila = [];          // símbolos de la fila actual (aún sin probar)
  let modo = "diario";

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
  const semillaDe = (iso) => Number(iso.replaceAll("-", ""));
  function fechaDeSemilla(s) {
    s = String(s);
    return `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}`;
  }
  function leer() {
    try { return JSON.parse(localStorage.getItem(CLAVE)) || {}; } catch (e) { return {}; }
  }
  function escribir(datos) {
    try { localStorage.setItem(CLAVE, JSON.stringify(datos)); } catch (e) { /* sin almacenamiento */ }
  }
  const llamar = (nombre, ...args) => JSON.parse(fn[nombre](...args));

  function mensaje(texto) { $("mensaje").textContent = texto || ""; }

  // ---------- elementos del tablero ----------
  function faro(simbolo, boton) {
    const e = el(boton ? "button" : "span", `faro s${simbolo}`, SIMBOLOS[simbolo].g);
    if (boton) e.type = "button";
    else { e.setAttribute("role", "img"); e.setAttribute("aria-label", SIMBOLOS[simbolo].n); }
    return e;
  }
  function vacio() {
    const e = el("span", "faro vacio");
    e.setAttribute("aria-hidden", "true");
    return e;
  }
  function pistas(intento) {
    const cont = el("div", "pistas");
    if (!intento) { cont.setAttribute("aria-hidden", "true"); }
    else cont.setAttribute("aria-label", `${intento.exactos} en su sitio, ${intento.desplazados} en otro sitio`);
    for (let i = 0; i < LONGITUD; i++) {
      let clase = "pista";
      if (intento) {
        if (i < intento.exactos) clase += " exacto";
        else if (i < intento.exactos + intento.desplazados) clase += " desp";
      }
      cont.append(el("i", clase));
    }
    return cont;
  }

  // ---------- dibujo ----------
  function render() {
    const jugando = st.estado === "jugando";

    const tablero = $("tablero");
    tablero.replaceChildren();
    for (let i = 0; i < st.max_intentos; i++) {
      const fil = el("div", "fila");
      fil.append(el("span", "num", String(i + 1)));
      const cas = el("div", "casillas");
      const hecho = st.intentos[i];
      if (hecho) {
        hecho.intento.forEach((s) => cas.append(faro(s)));
      } else if (jugando && i === st.intentos.length) {
        fil.classList.add("actual");
        for (let k = 0; k < LONGITUD; k++) {
          if (k < fila.length) {
            const b = faro(fila[k], true);
            b.setAttribute("aria-label", `Quitar ${SIMBOLOS[fila[k]].n} de la posición ${k + 1}`);
            b.addEventListener("click", () => quitar(k));
            cas.append(b);
          } else cas.append(vacio());
        }
      } else {
        for (let k = 0; k < LONGITUD; k++) cas.append(vacio());
      }
      fil.append(cas, pistas(hecho));
      tablero.append(fil);
    }

    [...$("paleta").children].forEach((b, i) => {
      b.disabled = !jugando || fila.length >= LONGITUD || fila.includes(i);
    });
    $("probar").disabled = !jugando || fila.length !== LONGITUD;
    $("borrar").disabled = !jugando || fila.length === 0;

    // sondas
    $("sondas-quedan").textContent = `(quedan ${st.sondas_restantes} de ${st.max_sondas})`;
    const usadas = new Set(st.sondas.map((s) => s.simbolo));
    [...$("sondas").children].forEach((b, i) => {
      b.disabled = !jugando || st.sondas_restantes === 0 || usadas.has(i);
    });
    const lista = $("sondas-resultados");
    lista.replaceChildren(...st.sondas.map((s) => {
      const li = el("li");
      const f = faro(s.simbolo);
      f.classList.add("pequeno-faro");
      li.append(f, el("span", s.presente ? "si" : "no", s.presente ? "Sí está en el código" : "No está en el código"));
      return li;
    }));

    // resultado
    const fin = !jugando;
    $("resultado").hidden = !fin;
    if (fin) {
      const ganada = st.estado === "ganada";
      $("resultado-titulo").textContent = ganada ? "Código descifrado" : "Te has quedado sin intentos";
      $("resultado-texto").textContent = ganada
        ? `Lo has resuelto en ${st.intentos.length} de ${st.max_intentos} intentos, con ${st.sondas.length} sonda(s) usadas. Puntuación: ${st.puntos}.`
        : "El código oculto era:";
      $("codigo-revelado").replaceChildren(...st.codigo.map((s) => faro(s)));
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
    $("st-racha").textContent = e.racha || 0;
    $("st-mejor-racha").textContent = e.mejor_racha || 0;
    $("st-jugadas").textContent = e.jugadas || 0;
    $("st-ganadas").textContent = e.ganadas || 0;
    $("st-puntos").textContent = e.mejor_puntuacion || 0;
  }

  // ---------- guardado del reto diario ----------
  function guardarDiario() {
    if (modo !== "diario") return;
    const iso = fechaDeSemilla(st.semilla);
    const datos = leer();
    const previo = datos.diario && datos.diario.fecha === iso ? datos.diario : {};
    datos.diario = {
      fecha: iso,
      intentos: st.intentos.map((i) => i.intento),
      sondas: st.sondas.map((s) => s.simbolo),
      contada: !!previo.contada,
    };
    if (st.estado !== "jugando" && !datos.diario.contada) {
      datos.estadisticas = llamar(
        "actualizar_estadisticas",
        JSON.stringify(datos.estadisticas || {}), iso, st.estado === "ganada", st.puntos
      );
      datos.diario.contada = true;
    }
    escribir(datos);
    renderStats();
  }

  // ---------- acciones ----------
  function aplicar(nuevo) {
    if (nuevo.error) { mensaje(nuevo.error); return false; }
    st = nuevo;
    mensaje("");
    return true;
  }
  function anadir(s) {
    if (!st || st.estado !== "jugando") return;
    if (fila.length >= LONGITUD) { mensaje("La fila ya está completa."); return; }
    if (fila.includes(s)) { mensaje("Ese símbolo ya está en la fila."); return; }
    fila.push(s);
    mensaje("");
    render();
  }
  function quitar(k) { fila.splice(k, 1); mensaje(""); render(); }
  function probar() {
    if (!st || st.estado !== "jugando") return;
    if (aplicar(llamar("enviar_intento", JSON.stringify(fila)))) {
      fila = [];
      guardarDiario();
    }
    render();
  }
  function sondear(s) {
    if (aplicar(llamar("usar_sonda", s))) guardarDiario();
    render();
  }

  function iniciarDiario() {
    modo = "diario";
    const iso = hoyISO();
    const guardada = leer().diario;
    if (guardada && guardada.fecha === iso) {
      st = llamar("restaurar", semillaDe(iso), "diario",
        JSON.stringify(guardada.intentos || []), JSON.stringify(guardada.sondas || []));
    } else {
      st = llamar("nueva_partida", semillaDe(iso), "diario");
    }
    fila = [];
    mensaje("");
    guardarDiario();   // por si la partida restaurada ya estaba terminada y sin contar
    render();
  }
  function iniciarPractica() {
    modo = "practica";
    st = llamar("nueva_partida", Math.floor(Math.random() * 2147483647), "practica");
    fila = [];
    mensaje("");
    render();
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

  // ---------- arranque ----------
  function construirControles() {
    const paleta = $("paleta");
    const sondas = $("sondas");
    SIMBOLOS.forEach((s, i) => {
      const b = faro(i, true);
      b.setAttribute("aria-label", `${s.n} (tecla ${i + 1})`);
      b.append(el("small", "", String(i + 1)));
      b.addEventListener("click", () => anadir(i));
      paleta.append(b);

      const sb = el("button", "sonda", `¿Está ${s.g}?`);
      sb.type = "button";
      sb.setAttribute("aria-label", `Sondear ${s.n}: ¿está en el código?`);
      sb.addEventListener("click", () => sondear(i));
      sondas.append(sb);
    });
    $("probar").addEventListener("click", probar);
    $("borrar").addEventListener("click", () => { fila = []; mensaje(""); render(); });
    $("copiar").addEventListener("click", copiar);
    $("otra").addEventListener("click", iniciarPractica);
    $("modo-diario").addEventListener("click", iniciarDiario);
    $("modo-practica").addEventListener("click", iniciarPractica);
    document.addEventListener("keydown", (ev) => {
      if (!st || ev.ctrlKey || ev.metaKey || ev.altKey) return;
      if (ev.key >= "1" && ev.key <= "6") anadir(Number(ev.key) - 1);
      else if (ev.key === "Backspace" && fila.length) { fila.pop(); mensaje(""); render(); }
      else if (ev.key === "Enter" && document.activeElement === document.body) probar();
    });
  }

  async function init() {
    renderStats();
    try {
      const r = await fetch("codigo.py");
      if (!r.ok) throw new Error("No se pudo cargar codigo.py");
      const fuente = await r.text();
      $("python-source").textContent = fuente;
      py = await loadPyodide();
      await py.runPythonAsync(fuente);
      ["nueva_partida", "restaurar", "enviar_intento", "usar_sonda", "compartir_texto", "actualizar_estadisticas"]
        .forEach((n) => { fn[n] = py.globals.get(n); });
      construirControles();
      $("estado-carga").hidden = true;
      iniciarDiario();
    } catch (e) {
      console.error(e);
      $("estado-carga").textContent = "No se ha podido cargar el motor de Python. Comprueba tu conexión y recarga la página.";
    }
  }

  init();
})();

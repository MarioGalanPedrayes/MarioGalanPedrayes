// Tejar: interfaz. Las reglas viven en codigo.py (Python con Pyodide);
// este archivo solo dibuja el estado que devuelve Python y le pasa las acciones.
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const CLAVE = "tejar-v1";
  const PROF = 4; // píxeles que se desplaza cada capa hacia arriba y a la izquierda

  let py = null;
  const fn = {};
  let st = null;             // último estado devuelto por Python
  let modo = "diario";
  let diarioISO = "";
  let dificultad = "normal"; // dificultad de la práctica
  let elegida = null;        // id de la ficha elegida
  let foco = null;           // id de la ficha con el foco del teclado
  let pistaVista = null;     // {a, b} mostrada hasta la siguiente acción
  let confirmaReiniciar = null;
  let temporizadorAjuste = null;

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
  const ficha = (id) => st.fichas.find((f) => f.id === id);

  // ---------- dibujo ----------
  function dibujo(s) {
    const d = el("span", "dibujo");
    d.setAttribute("aria-hidden", "true");
    const forma = el("span", `forma ${s.forma}`);
    forma.style.setProperty("--c", s.color);
    if (s.familia) {
      forma.textContent = s.letra;
      d.append(forma);
    } else {
      d.append(forma, el("span", "letra", s.letra));
    }
    return d;
  }

  function medidas() {
    const caja = $("caja");
    const disponible = (caja.clientWidth || 600) - 18; // quita el relleno lateral de la caja
    const u = Math.max(13, Math.min(32, Math.floor((disponible - (st.capas - 1) * PROF - 6) / st.ancho)));
    return { u, anchoPx: st.ancho * u + (st.capas - 1) * PROF + 6, altoPx: st.alto * u + (st.capas - 1) * PROF + 6 };
  }

  function nombreFicha(f) {
    const s = st.simbolos[f.s];
    const partes = [s.nombre, `capa ${f.z + 1}`, `fila ${Math.floor(f.y / 2) + 1}`, `columna ${Math.floor(f.x / 2) + 1}`,
      f.libre ? "libre" : "tapada"];
    if (elegida === f.id) partes.push("elegida");
    return partes.join(", ");
  }

  function pintarTablero() {
    const tablero = $("tablero");
    const teniaFoco = tablero.contains(document.activeElement);
    const { u, anchoPx, altoPx } = medidas();
    const jugando = st.estado === "jugando";

    if (foco === null || !ficha(foco)) {
      const libres = st.fichas.filter((f) => f.libre);
      const base = libres.length ? libres : st.fichas;
      foco = base.length ? base[0].id : null;
    }

    tablero.style.width = `${anchoPx}px`;
    tablero.style.height = `${altoPx}px`;
    tablero.style.setProperty("--fl", `${Math.max(9, Math.round(u * 0.42))}px`);
    tablero.style.setProperty("--fe", `${Math.max(9, Math.round(u * 0.5))}px`);
    tablero.replaceChildren();

    // Se pintan de abajo arriba para que las fichas de arriba queden encima.
    [...st.fichas].sort((a, b) => a.z - b.z || a.y - b.y || a.x - b.x).forEach((f) => {
      const b = el("button", "ficha-tejar");
      b.type = "button";
      b.dataset.id = String(f.id);
      b.style.left = `${f.x * u + (st.capas - 1 - f.z) * PROF}px`;
      b.style.top = `${f.y * u + (st.capas - 1 - f.z) * PROF}px`;
      b.style.width = `${2 * u}px`;
      b.style.height = `${2 * u}px`;
      b.style.zIndex = String(f.z + 1);
      b.tabIndex = f.id === foco ? 0 : -1;
      b.classList.toggle("tapada", !f.libre);
      b.classList.toggle("elegida", elegida === f.id);
      b.classList.toggle("pista", !!pistaVista && (pistaVista.a === f.id || pistaVista.b === f.id));
      b.classList.toggle("fin", !jugando);
      b.setAttribute("aria-label", nombreFicha(f));
      b.setAttribute("aria-pressed", String(elegida === f.id));
      b.append(dibujo(st.simbolos[f.s]));
      tablero.append(b);
    });

    if (teniaFoco && foco !== null) {
      const b = tablero.querySelector(`[data-id="${foco}"]`);
      if (b) b.focus({ preventScroll: true });
    }
  }

  function pintar() {
    pintarTablero();
    const jugando = st.estado === "jugando";

    $("c-parejas").textContent = `${st.parejas_hechas}/${st.parejas_total}`;
    $("c-libres").textContent = jugando ? st.parejas_libres : "–";
    $("c-fallos").textContent = st.fallos;
    $("c-pistas").textContent = `${st.pistas}/${st.pistas_max}`;
    $("c-barajas").textContent = `${st.barajas}/${st.barajas_max}`;
    $("resumen").textContent =
      `${st.parejas_hechas} de ${st.parejas_total} parejas retiradas, ${st.parejas_libres} parejas libres, ${st.fallos} fallos.` +
      (jugando ? "" : " Almacén vacío.");

    $("deshacer").disabled = !jugando || !st.puede_deshacer;
    $("pista").disabled = !jugando || st.pistas >= st.pistas_max;
    $("barajar").disabled = !jugando || st.barajas >= st.barajas_max;
    $("reiniciar").disabled = !jugando || st.historial.length === 0;
    if (!jugando) quitarConfirmacion();
    if (jugando && st.sin_movimientos) {
      mensaje(st.barajas < st.barajas_max
        ? "No quedan parejas libres: deshaz la última pareja o baraja."
        : "No quedan parejas libres ni barajas: deshaz parejas o reinicia.");
    }

    $("titulo-partida").textContent = modo === "diario"
      ? `Reto del ${fechaLarga(diarioISO)} (difícil, almacén «${st.diseno_nombre}»): el mismo tablero para todo el mundo.`
      : `Práctica ${st.dificultad_nombre.toLowerCase()}, almacén «${st.diseno_nombre}», tablero número ${st.semilla}.`;

    const fin = st.estado === "completada";
    $("resultado").hidden = !fin;
    if (fin) {
      const est = "★".repeat(st.estrellas) + "☆".repeat(3 - st.estrellas);
      $("resultado-titulo").textContent = "Almacén vacío";
      $("resultado-texto").textContent =
        `${est} ${st.fallos} ${st.fallos === 1 ? "fallo" : "fallos"}, ${st.pistas} ${st.pistas === 1 ? "pista" : "pistas"}, ` +
        `${st.barajas} ${st.barajas === 1 ? "baraja" : "barajas"}.` +
        (st.estrellas === 3 ? " Limpio y sin ayudas." : " Con menos fallos y ayudas llegan las tres estrellas.");
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
    datos.diario = {
      fecha: diarioISO, historial: st.historial, pistas: st.pistas, fallos: st.fallos,
      barajas_extra: st.barajas_extra, contada: !!previo.contada,
    };
    if (st.estado === "completada" && !datos.diario.contada) {
      datos.estadisticas = llamar(
        "actualizar_estadisticas", JSON.stringify(datos.estadisticas || {}), diarioISO, st.fallos, st.estrellas
      );
      datos.diario.contada = true;
    }
    escribir(datos);
    renderStats();
  }

  // ---------- acciones ----------
  function aplicar(nuevo) {
    st = nuevo; // Python siempre devuelve el estado completo, también con error
    mensaje(nuevo.error || "");
  }

  function elegir(id) {
    if (!st || st.estado !== "jugando") return;
    const f = ficha(id);
    if (!f) return;
    foco = id;
    if (!f.libre) {
      mensaje("Esa ficha está tapada o encajonada. Solo valen las libres: sin nada encima y con un lado despejado.");
      pintar();
      return;
    }
    if (elegida === null) {
      elegida = id;
      mensaje("");
      pintar();
      return;
    }
    if (elegida === id) { elegida = null; mensaje(""); pintar(); return; }
    const a = elegida;
    elegida = null;
    pistaVista = null;
    quitarConfirmacion();
    aplicar(llamar("emparejar", a, id));
    guardarDiario();
    pintar();
  }

  function deshacer() {
    if (!st || st.estado !== "jugando") return;
    elegida = null; pistaVista = null;
    aplicar(llamar("deshacer"));
    guardarDiario();
    pintar();
  }

  function pedirPista() {
    if (!st || st.estado !== "jugando") return;
    elegida = null;
    const nuevo = llamar("pista");
    aplicar(nuevo);
    if (nuevo.pista) {
      pistaVista = nuevo.pista;
      foco = nuevo.pista.a;
      mensaje("Pista: mira las dos fichas marcadas con trazo discontinuo.");
    }
    guardarDiario();
    pintar();
  }

  function barajar() {
    if (!st || st.estado !== "jugando") return;
    elegida = null; pistaVista = null;
    aplicar(llamar("barajar"));
    if (!st.error) mensaje("Fichas recolocadas: la nueva distribución tiene salida.");
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
    elegida = null; pistaVista = null;
    aplicar(llamar("reiniciar"));
    mensaje("Tablero inicial. Los fallos, pistas y barajas que ya gastaste se conservan.");
    guardarDiario();
    pintar();
  }

  function nuevaPartidaEstado(partida) {
    st = partida;
    elegida = null; pistaVista = null; foco = null;
    mensaje("");
    quitarConfirmacion();
  }

  function iniciarDiario() {
    modo = "diario";
    diarioISO = hoyISO();
    const semilla = fn.semilla_del_dia(diarioISO);
    const etiqueta = `${diarioISO} · reto diario`;
    const guardada = leer().diario;
    if (guardada && guardada.fecha === diarioISO) {
      nuevaPartidaEstado(llamar("restaurar", semilla, "diario", etiqueta, "dificil",
        JSON.stringify(guardada.historial || []), guardada.pistas || 0, guardada.fallos || 0, guardada.barajas_extra || 0));
    } else {
      nuevaPartidaEstado(llamar("nueva_partida", semilla, "diario", etiqueta, "dificil"));
    }
    guardarDiario();
    pintar();
  }
  function iniciarPractica() {
    modo = "practica";
    nuevaPartidaEstado(llamar("nueva_partida", Math.floor(Math.random() * 2147483647), "practica", "práctica", dificultad));
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
    const item = (s) => {
      const li = el("li");
      const m = el("span", "muestra");
      m.append(dibujo(s));
      li.append(m, el("span", "", s.nombre));
      return li;
    };
    $("leyenda").replaceChildren(...st.simbolos.filter((s) => !s.familia).map(item));
    $("leyenda-estaciones").replaceChildren(...st.simbolos.filter((s) => s.familia).map(item));
  }

  // ---------- teclado ----------
  function moverFoco(dx, dy) {
    const actual = ficha(foco);
    if (!actual) return;
    let mejor = null, mejorPuntos = Infinity;
    st.fichas.forEach((f) => {
      if (f.id === foco) return;
      const ddx = f.x - actual.x, ddy = f.y - actual.y;
      if (dx && Math.sign(ddx) !== dx) return;
      if (dy && Math.sign(ddy) !== dy) return;
      const puntos = (dx ? Math.abs(ddx) + 2 * Math.abs(ddy) : Math.abs(ddy) + 2 * Math.abs(ddx)) - f.z * 0.1;
      if (puntos < mejorPuntos) { mejorPuntos = puntos; mejor = f; }
    });
    if (mejor) enfocar(mejor.id);
  }
  function enfocar(id) {
    foco = id;
    const tablero = $("tablero");
    [...tablero.children].forEach((b) => { b.tabIndex = Number(b.dataset.id) === id ? 0 : -1; });
    const b = tablero.querySelector(`[data-id="${id}"]`);
    if (b) b.focus();
  }
  function siguienteLibre() {
    const libres = st.fichas.filter((f) => f.libre).sort((a, b) => a.y - b.y || a.x - b.x || a.z - b.z);
    if (!libres.length) return;
    const pos = libres.findIndex((f) => f.id === foco);
    enfocar(libres[(pos + 1) % libres.length].id);
  }

  function construirControles() {
    const tablero = $("tablero");
    tablero.addEventListener("click", (ev) => {
      const b = ev.target.closest(".ficha-tejar");
      if (b) elegir(Number(b.dataset.id));
    });
    tablero.addEventListener("focusin", (ev) => {
      const b = ev.target.closest(".ficha-tejar");
      if (!b) return;
      foco = Number(b.dataset.id);
      [...tablero.children].forEach((x) => { x.tabIndex = x === b ? 0 : -1; });
    });
    tablero.addEventListener("keydown", (ev) => {
      if (ev.ctrlKey || ev.metaKey || ev.altKey || !st) return;
      const tecla = ev.key;
      if (tecla === "ArrowLeft") { ev.preventDefault(); moverFoco(-1, 0); }
      else if (tecla === "ArrowRight") { ev.preventDefault(); moverFoco(1, 0); }
      else if (tecla === "ArrowUp") { ev.preventDefault(); moverFoco(0, -1); }
      else if (tecla === "ArrowDown") { ev.preventDefault(); moverFoco(0, 1); }
      else if (tecla === "n" || tecla === "N") { ev.preventDefault(); siguienteLibre(); }
      else if (tecla === "Escape") { elegida = null; mensaje(""); pintar(); }
      else if (tecla === "u" || tecla === "U") { ev.preventDefault(); deshacer(); }
      else if (tecla === "p" || tecla === "P") { ev.preventDefault(); pedirPista(); }
      else if (tecla === "b" || tecla === "B") { ev.preventDefault(); barajar(); }
      // Espacio e Intro activan el botón y llegan como "click".
    });

    $("deshacer").addEventListener("click", deshacer);
    $("pista").addEventListener("click", pedirPista);
    $("barajar").addEventListener("click", barajar);
    $("reiniciar").addEventListener("click", reiniciar);
    $("copiar").addEventListener("click", copiar);
    $("otra").addEventListener("click", iniciarPractica);
    $("modo-diario").addEventListener("click", iniciarDiario);
    $("modo-practica").addEventListener("click", iniciarPractica);
    $("dificultad").addEventListener("change", () => {
      dificultad = $("dificultad").value;
      iniciarPractica();
    });
    window.addEventListener("resize", () => {
      clearTimeout(temporizadorAjuste);
      temporizadorAjuste = setTimeout(() => { if (st) pintarTablero(); }, 150);
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
      ["nueva_partida", "restaurar", "emparejar", "deshacer", "barajar", "reiniciar", "pista",
        "compartir_texto", "actualizar_estadisticas", "racha_vigente", "semilla_del_dia"]
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

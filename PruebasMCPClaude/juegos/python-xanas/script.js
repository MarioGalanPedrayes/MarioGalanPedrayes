// Montaña de Xanas: interfaz. Las reglas viven en codigo.py (Python con Pyodide);
// este archivo solo dibuja el estado que devuelve Python y le pasa las acciones.
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const CLAVE = "xanas-v1";
  const VW = 15, VH = 11;                  // casillas visibles
  const LETRA = ["B", "R", "N"];
  const COLOR_ELEM = ["#4f7a3b", "#7a7f88", "#6f93ad"];
  const DUR_PASO = 110;

  const fn = {};
  let dat = null;      // datos estáticos (mapa, especies...)
  let st = null;       // último estado devuelto por Python
  let ts = 32, dpr = 1, ctx = null;
  let anim = null;     // paso animado {fx, fy, tx, ty, t0}
  let sacudida = null; // {lado, t0}
  let raf = 0;
  let ultimoPaso = 0;
  let ultimoPuntero = 0;
  let repetir = null;
  let confirmaNueva = null;
  const reducido = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

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
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const semillaNueva = () => Math.floor(Math.random() * 2147483646) + 1;
  function mensaje(t) { $("mensaje").textContent = t || ""; }
  const nombreElem = (i) => dat.elementos[i];
  function efecto(att, def) {
    if ((att + 1) % 3 === def) return "ventaja";
    if ((def + 1) % 3 === att) return "desventaja";
    return "efecto neutro";
  }

  // ---------- dibujo de criaturas ----------
  function oscurecer(hex, k) {
    const n = parseInt(hex.slice(1), 16);
    const f = (v) => Math.round(clamp(v * k, 0, 255));
    return `rgb(${f(n >> 16)}, ${f((n >> 8) & 255)}, ${f(n & 255)})`;
  }

  function sprite(c, esp, cx, cy, r, t, opciones) {
    const op = opciones || {};
    const col = esp.color, oscuro = oscurecer(col, 0.68);
    const flota = reducido ? 0 : Math.sin((t || 0) / 320 + esp.id) * r * 0.05;
    c.save();
    c.translate(cx, cy + flota);
    c.lineWidth = Math.max(1.5, r * 0.06);
    c.strokeStyle = "#1f2933";
    c.lineJoin = "round";
    c.lineCap = "round";
    c.fillStyle = col;
    let ojosY = -0.05;
    const elipse = (x, y, rx, ry, relleno) => {
      c.beginPath(); c.ellipse(x * r, y * r, rx * r, ry * r, 0, 0, Math.PI * 2);
      if (relleno) { c.fillStyle = relleno; }
      c.fill(); c.stroke();
    };
    switch (esp.forma) {
      case "duende":
        elipse(0, 0.2, 0.62, 0.68, col);
        c.beginPath(); c.moveTo(-0.6 * r, -0.2 * r); c.lineTo(0, -1.15 * r); c.lineTo(0.6 * r, -0.2 * r); c.closePath();
        c.fillStyle = oscuro; c.fill(); c.stroke();
        ojosY = 0.1;
        break;
      case "guijarro":
        elipse(0, 0.15, 0.88, 0.72, col);
        c.beginPath(); c.moveTo(-0.3 * r, -0.35 * r); c.lineTo(-0.1 * r, -0.15 * r); c.lineTo(-0.28 * r, 0.05 * r); c.stroke();
        ojosY = 0.1;
        break;
      case "nube":
        elipse(-0.45, 0.1, 0.45, 0.4, col); elipse(0.5, 0.1, 0.45, 0.4, col);
        elipse(0, -0.12, 0.6, 0.55, col); elipse(0, 0.25, 0.9, 0.32, col);
        ojosY = 0.02;
        break;
      case "luz":
        elipse(-0.55, -0.4, 0.4, 0.22, "rgba(255,255,255,0.8)"); elipse(0.55, -0.4, 0.4, 0.22, "rgba(255,255,255,0.8)");
        elipse(0, 0.1, 0.55, 0.62, col);
        c.beginPath(); c.moveTo(-0.5 * r, 0.1 * r); c.lineTo(0.5 * r, 0.1 * r); c.moveTo(-0.45 * r, 0.4 * r); c.lineTo(0.45 * r, 0.4 * r); c.stroke();
        ojosY = -0.2;
        break;
      case "seta":
        c.fillStyle = "#efe6d0"; c.beginPath(); c.rect(-0.28 * r, 0.1 * r, 0.56 * r, 0.8 * r); c.fill(); c.stroke();
        c.beginPath(); c.ellipse(0, 0.05 * r, 0.98 * r, 0.75 * r, 0, Math.PI, 0); c.closePath(); c.fillStyle = col; c.fill(); c.stroke();
        c.fillStyle = "#f4efe0";
        [[-0.4, -0.3], [0.1, -0.5], [0.45, -0.2]].forEach(([x, y]) => { c.beginPath(); c.arc(x * r, y * r, 0.1 * r, 0, 7); c.fill(); });
        ojosY = 0.45;
        break;
      case "raiz":
        c.strokeStyle = oscuro; c.lineWidth = Math.max(2, r * 0.12);
        [-0.5, -0.17, 0.17, 0.5].forEach((x) => { c.beginPath(); c.moveTo(x * r * 0.9, 0.5 * r); c.quadraticCurveTo(x * r * 1.5, 0.85 * r, x * r * 1.3, 1.0 * r); c.stroke(); });
        c.strokeStyle = "#1f2933"; c.lineWidth = Math.max(1.5, r * 0.06);
        elipse(0, -0.1, 0.58, 0.68, col);
        ojosY = -0.2;
        break;
      case "gota":
        c.beginPath(); c.moveTo(0, -1.0 * r); c.bezierCurveTo(0.9 * r, -0.1 * r, 0.8 * r, 0.8 * r, 0, 0.85 * r);
        c.bezierCurveTo(-0.8 * r, 0.8 * r, -0.9 * r, -0.1 * r, 0, -1.0 * r); c.fillStyle = col; c.fill(); c.stroke();
        ojosY = 0.2;
        break;
      case "serpiente":
        c.strokeStyle = "#1f2933"; c.lineWidth = r * 0.58;
        c.beginPath(); c.moveTo(-0.8 * r, 0.6 * r); c.bezierCurveTo(-0.2 * r, 0.9 * r, -0.3 * r, 0.1 * r, 0.3 * r, 0.3 * r); c.bezierCurveTo(0.9 * r, 0.5 * r, 0.7 * r, -0.4 * r, 0.3 * r, -0.5 * r); c.stroke();
        c.strokeStyle = col; c.lineWidth = r * 0.46;
        c.beginPath(); c.moveTo(-0.8 * r, 0.6 * r); c.bezierCurveTo(-0.2 * r, 0.9 * r, -0.3 * r, 0.1 * r, 0.3 * r, 0.3 * r); c.bezierCurveTo(0.9 * r, 0.5 * r, 0.7 * r, -0.4 * r, 0.3 * r, -0.5 * r); c.stroke();
        c.lineWidth = Math.max(1.5, r * 0.06); c.strokeStyle = "#1f2933";
        c.beginPath(); c.arc(0.3 * r, -0.62 * r, 0.3 * r, 0, 7); c.fillStyle = col; c.fill(); c.stroke();
        c.fillStyle = "#fff"; c.beginPath(); c.arc(0.22 * r, -0.66 * r, 0.08 * r, 0, 7); c.arc(0.4 * r, -0.66 * r, 0.08 * r, 0, 7); c.fill();
        c.fillStyle = "#1f2933"; c.beginPath(); c.arc(0.22 * r, -0.66 * r, 0.035 * r, 0, 7); c.arc(0.4 * r, -0.66 * r, 0.035 * r, 0, 7); c.fill();
        ojosY = null;
        break;
      case "piedra":
        c.beginPath();
        for (let i = 0; i < 6; i++) { const a = Math.PI / 6 + i * Math.PI / 3; c.lineTo(Math.cos(a) * 0.9 * r, Math.sin(a) * 0.85 * r); }
        c.closePath(); c.fillStyle = col; c.fill(); c.stroke();
        c.beginPath(); c.ellipse(0, 0.5 * r, 0.62 * r, 0.38 * r, 0, 0, Math.PI); c.fillStyle = "#6f9a5a"; c.fill(); c.stroke();
        ojosY = -0.15;
        break;
      case "eco":
        c.strokeStyle = "rgba(125,111,168,0.55)"; c.lineWidth = Math.max(2, r * 0.1);
        [1.0, 0.8].forEach((k) => { c.beginPath(); c.arc(0, 0, k * r, -0.9, 0.9); c.stroke(); c.beginPath(); c.arc(0, 0, k * r, Math.PI - 0.9, Math.PI + 0.9); c.stroke(); });
        c.strokeStyle = "#1f2933"; c.lineWidth = Math.max(1.5, r * 0.06);
        elipse(0, 0, 0.55, 0.55, col);
        ojosY = -0.08;
        break;
      case "musgo":
        [[-0.55, 0.3, 0.4], [0.55, 0.3, 0.4], [-0.25, -0.1, 0.5], [0.3, -0.05, 0.45], [0, 0.4, 0.5]].forEach(([x, y, k]) => elipse(x, y, k, k * 0.85, col));
        ojosY = 0.1;
        break;
      case "xana":
        elipse(-0.55, -0.15, 0.4, 0.6, "rgba(190,230,245,0.8)"); elipse(0.55, -0.15, 0.4, 0.6, "rgba(190,230,245,0.8)");
        c.beginPath(); c.moveTo(0, -0.1 * r); c.lineTo(0.55 * r, 0.9 * r); c.lineTo(-0.55 * r, 0.9 * r); c.closePath(); c.fillStyle = col; c.fill(); c.stroke();
        elipse(0, -0.4, 0.4, 0.42, "#f0d8b8");
        c.beginPath(); c.ellipse(0, -0.62 * r, 0.44 * r, 0.26 * r, 0, Math.PI, 0); c.fillStyle = "#3a5a78"; c.fill(); c.stroke();
        ojosY = -0.35;
        break;
      default:
        elipse(0, 0, 0.7, 0.7, col);
    }
    if (ojosY !== null) {
      [-0.2, 0.2].forEach((x) => {
        c.fillStyle = "#fff"; c.beginPath(); c.arc(x * r, ojosY * r, 0.13 * r, 0, 7); c.fill(); c.stroke();
        c.fillStyle = "#1f2933"; c.beginPath(); c.arc(x * r, ojosY * r, 0.06 * r, 0, 7); c.fill();
      });
    }
    // insignia del elemento: letra dentro de un círculo (no depende solo del color)
    c.fillStyle = COLOR_ELEM[esp.elem]; c.lineWidth = Math.max(1.5, r * 0.06); c.strokeStyle = "#1f2933";
    c.beginPath(); c.arc(0.78 * r, -0.8 * r, 0.3 * r, 0, 7); c.fill(); c.stroke();
    c.fillStyle = "#fff"; c.font = `bold ${Math.max(8, Math.round(r * 0.34))}px system-ui, sans-serif`;
    c.textAlign = "center"; c.textBaseline = "middle";
    c.fillText(LETRA[esp.elem], 0.78 * r, -0.79 * r);
    c.restore();
    if (op.silueta) {
      c.save(); c.globalCompositeOperation = "source-atop"; c.fillStyle = "#b9b2a0";
      c.fillRect(cx - r * 1.3, cy - r * 1.3, r * 2.6, r * 2.6); c.restore();
    }
  }

  function miniatura(esp, silueta) {
    const cv = el("canvas");
    cv.width = 112; cv.height = 112;
    cv.setAttribute("aria-hidden", "true");
    let c = null;
    try { c = cv.getContext("2d"); } catch (e) { c = null; }
    if (c) sprite(c, esp, 56, 60, 34, 0, { silueta });
    return cv;
  }

  // ---------- dibujo del mundo ----------
  function hash(x, y) { return ((x * 73856093) ^ (y * 19349663)) >>> 0; }

  function casilla(ch, x, y, px, py) {
    const s = ts, h = hash(x, y);
    const base = { ",": "#a9c27a", ".": "#dccb9b", p: "#7aa24d", b: "#5f8b52", c: "#8d8a99", F: "#a9c27a", D: "#a9c27a", T: "#a9c27a", "#": "#a9c27a", W: "#5b8db0", H: "#a9c27a" }[ch] || "#a9c27a";
    ctx.fillStyle = base;
    ctx.fillRect(px, py, s + 1, s + 1);
    if (ch === "." || ch === ",") {
      ctx.fillStyle = ch === "." ? "#cdbb88" : "#9bb66c";
      ctx.fillRect(px + (h % (s - 4)), py + ((h >> 8) % (s - 4)), 3, 2);
    } else if (ch === "p" || ch === "b") {
      ctx.strokeStyle = ch === "p" ? "#4e7a30" : "#35603a"; ctx.lineWidth = Math.max(1.5, s * 0.07);
      for (let i = 0; i < 4; i++) {
        const bx = px + ((h >> (i * 4)) % (s - 6)) + 3, by = py + ((h >> (i * 3 + 2)) % (s - 10)) + 8;
        ctx.beginPath(); ctx.moveTo(bx, by + 5); ctx.lineTo(bx - 2, by - 3); ctx.moveTo(bx, by + 5); ctx.lineTo(bx + 2, by - 4); ctx.stroke();
      }
    } else if (ch === "c") {
      ctx.fillStyle = "#6f8c6a";
      for (let i = 0; i < 3; i++) { ctx.beginPath(); ctx.arc(px + ((h >> (i * 5)) % (s - 8)) + 4, py + ((h >> (i * 4 + 1)) % (s - 8)) + 4, s * 0.09, 0, 7); ctx.fill(); }
    } else if (ch === "T") {
      ctx.fillStyle = "#6b4a2a"; ctx.fillRect(px + s * 0.43, py + s * 0.55, s * 0.14, s * 0.4);
      ctx.fillStyle = "#3f6b3a"; ctx.beginPath(); ctx.arc(px + s * 0.5, py + s * 0.4, s * 0.42, 0, 7); ctx.fill();
      ctx.fillStyle = "#4f7f45"; ctx.beginPath(); ctx.arc(px + s * 0.4, py + s * 0.32, s * 0.2, 0, 7); ctx.fill();
    } else if (ch === "#") {
      ctx.fillStyle = "#6e7079"; ctx.beginPath(); ctx.moveTo(px + s * 0.1, py + s * 0.9); ctx.lineTo(px + s * 0.25, py + s * 0.25); ctx.lineTo(px + s * 0.6, py + s * 0.12); ctx.lineTo(px + s * 0.92, py + s * 0.9); ctx.closePath(); ctx.fill();
      ctx.fillStyle = "#8b8d96"; ctx.beginPath(); ctx.moveTo(px + s * 0.25, py + s * 0.25); ctx.lineTo(px + s * 0.6, py + s * 0.12); ctx.lineTo(px + s * 0.5, py + s * 0.5); ctx.closePath(); ctx.fill();
    } else if (ch === "W") {
      ctx.strokeStyle = "#8fb7d2"; ctx.lineWidth = 1.5;
      for (let i = 0; i < 2; i++) { const yy = py + s * (0.3 + i * 0.4); ctx.beginPath(); ctx.moveTo(px + s * 0.1, yy); ctx.quadraticCurveTo(px + s * 0.3, yy - 4, px + s * 0.5, yy); ctx.quadraticCurveTo(px + s * 0.7, yy + 4, px + s * 0.9, yy); ctx.stroke(); }
    } else if (ch === "H") {
      ctx.fillStyle = "#c9a77a"; ctx.fillRect(px + s * 0.08, py + s * 0.4, s * 0.84, s * 0.55);
      ctx.fillStyle = "#a8503a"; ctx.beginPath(); ctx.moveTo(px, py + s * 0.45); ctx.lineTo(px + s * 0.5, py + s * 0.05); ctx.lineTo(px + s, py + s * 0.45); ctx.closePath(); ctx.fill();
      ctx.fillStyle = "#5a3d24"; ctx.fillRect(px + s * 0.4, py + s * 0.62, s * 0.2, s * 0.33);
    } else if (ch === "F") {
      ctx.fillStyle = "#8f8f94"; ctx.beginPath(); ctx.arc(px + s * 0.5, py + s * 0.55, s * 0.4, 0, 7); ctx.fill();
      ctx.fillStyle = "#5b8db0"; ctx.beginPath(); ctx.arc(px + s * 0.5, py + s * 0.55, s * 0.29, 0, 7); ctx.fill();
      ctx.fillStyle = "#cfe3ef"; ctx.beginPath(); ctx.arc(px + s * 0.42, py + s * 0.47, s * 0.07, 0, 7); ctx.fill();
    } else if (ch === "D") {
      ctx.strokeStyle = "#8a7a52"; ctx.lineWidth = Math.max(2, s * 0.08); ctx.fillStyle = "#e6dcb8";
      ctx.beginPath(); ctx.arc(px + s * 0.5, py + s * 0.5, s * 0.42, 0, 7); ctx.fill(); ctx.stroke();
      ctx.beginPath();
      for (let i = 0; i < 5; i++) { const a = -Math.PI / 2 + i * 4 * Math.PI / 5; ctx.lineTo(px + s * 0.5 + Math.cos(a) * s * 0.26, py + s * 0.5 + Math.sin(a) * s * 0.26); }
      ctx.closePath(); ctx.stroke();
    }
  }

  function personaje(px, py, dir) {
    const s = ts, x = px + s / 2, y = py + s / 2;
    ctx.lineWidth = Math.max(1.5, s * 0.06); ctx.strokeStyle = "#1f2933";
    ctx.fillStyle = "#b5452f"; ctx.beginPath(); ctx.ellipse(x, y + s * 0.18, s * 0.26, s * 0.3, 0, 0, 7); ctx.fill(); ctx.stroke();
    ctx.fillStyle = "#f0d0a8"; ctx.beginPath(); ctx.arc(x, y - s * 0.17, s * 0.2, 0, 7); ctx.fill(); ctx.stroke();
    ctx.fillStyle = "#4a3320"; ctx.beginPath(); ctx.arc(x, y - s * 0.22, s * 0.2, Math.PI, 0); ctx.fill(); ctx.stroke();
    ctx.fillStyle = "#1f2933";
    const ox = dir === "E" ? s * 0.07 : (dir === "O" ? -s * 0.07 : 0);
    if (dir !== "N") { ctx.beginPath(); ctx.arc(x - s * 0.07 + ox, y - s * 0.15, s * 0.025, 0, 7); ctx.arc(x + s * 0.07 + ox, y - s * 0.15, s * 0.025, 0, 7); ctx.fill(); }
  }

  function dibujarMundo(t) {
    const W = VW * ts, H = VH * ts;
    let px = st.x, py = st.y;
    if (anim) {
      const k = Math.min(1, (t - anim.t0) / DUR_PASO);
      px = anim.fx + (anim.tx - anim.fx) * k; py = anim.fy + (anim.ty - anim.fy) * k;
      if (k >= 1) anim = null;
    }
    const cx = clamp(px - (VW - 1) / 2, 0, dat.ancho - VW), cy = clamp(py - (VH - 1) / 2, 0, dat.alto - VH);
    ctx.fillStyle = "#2f4a2e"; ctx.fillRect(0, 0, W, H);
    const x0 = Math.floor(cx), y0 = Math.floor(cy);
    for (let y = y0; y <= Math.min(dat.alto - 1, y0 + VH); y++) {
      for (let x = x0; x <= Math.min(dat.ancho - 1, x0 + VW); x++) {
        casilla(dat.mapa[y][x], x, y, Math.round((x - cx) * ts), Math.round((y - cy) * ts));
      }
    }
    personaje(Math.round((px - cx) * ts), Math.round((py - cy) * ts), st.dir);
    // rótulo del lugar
    ctx.font = `600 ${Math.max(11, Math.round(ts * 0.42))}px system-ui, sans-serif`;
    const txt = st.lugar, ancho = ctx.measureText(txt).width + 16;
    ctx.fillStyle = "rgba(255,253,248,0.88)"; ctx.fillRect(8, 8, ancho, Math.round(ts * 0.7));
    ctx.fillStyle = "#1f2933"; ctx.textAlign = "left"; ctx.textBaseline = "middle"; ctx.fillText(txt, 16, 8 + Math.round(ts * 0.35));
  }

  function dibujarDuelo(t) {
    const W = VW * ts, H = VH * ts, du = st.duelo;
    const fondo = [["#dfe9c2", "#9bb86a"], ["#cfe0c4", "#6f9a5a"], ["#d9d6e2", "#8d8a99"]][du.zona];
    ctx.fillStyle = fondo[0]; ctx.fillRect(0, 0, W, H * 0.58);
    ctx.fillStyle = fondo[1]; ctx.fillRect(0, H * 0.58, W, H * 0.42);
    const sombra = (x, y, rx) => { ctx.fillStyle = "rgba(31,41,51,0.2)"; ctx.beginPath(); ctx.ellipse(x, y, rx, rx * 0.28, 0, 0, 7); ctx.fill(); };
    const sac = (lado) => {
      if (!sacudida || sacudida.lado !== lado) return 0;
      const k = (t - sacudida.t0) / 320;
      if (k >= 1) { sacudida = null; return 0; }
      return Math.sin(k * 30) * (1 - k) * ts * 0.25;
    };
    const w = du.salvaje, a = st.equipo[du.activo];
    const rs = H * 0.17, rj = H * 0.2;
    sombra(W * 0.7, H * 0.5, rs * 1.1);
    sprite(ctx, dat.especies[w.e], W * 0.7 + sac("s"), H * 0.34, rs, t);
    sombra(W * 0.28, H * 0.9, rj * 1.1);
    sprite(ctx, dat.especies[a.e], W * 0.28 + sac("j"), H * 0.7, rj, t);
  }

  function dibujar(t) {
    if (!ctx || !st || !dat) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (st.fase === "duelo" && st.duelo) dibujarDuelo(t); else if (st.fase !== "inicio") dibujarMundo(t);
  }

  function necesitaFrames() {
    return !!(anim || sacudida || (st && st.fase === "duelo" && !reducido));
  }
  function frame(t) {
    raf = 0;
    dibujar(t);
    if (necesitaFrames()) pedirFrame();
  }
  function pedirFrame() {
    if (!ctx || raf) return;
    raf = requestAnimationFrame(frame);
  }

  function ajustar() {
    const cv = $("lienzo");
    const caja = $("escena");
    const ancho = (caja.clientWidth || 600);
    ts = clamp(Math.floor(Math.min(ancho - 8, 720) / VW), 18, 48);
    dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
    cv.width = Math.round(VW * ts * dpr); cv.height = Math.round(VH * ts * dpr);
    cv.style.width = `${VW * ts}px`; cv.style.height = `${VH * ts}px`;
    try { ctx = cv.getContext("2d"); } catch (e) { ctx = null; }
    pedirFrame();
    if (ctx) dibujar(performance.now());
  }

  // ---------- paneles ----------
  function barra(valor, maximo, clase) {
    const b = el("div", "barra");
    const r = el("div", "relleno" + (clase ? " " + clase : ""));
    const p = maximo > 0 ? clamp(valor / maximo, 0, 1) : 0;
    r.style.width = `${Math.round(p * 100)}%`;
    if (!clase) { if (p <= 0.25) r.classList.add("critico"); else if (p <= 0.5) r.classList.add("bajo"); }
    b.append(r);
    return b;
  }

  function fichaDuelo(rol, cr) {
    const d = el("div", "ficha-duelo");
    d.append(el("div", "rol", rol));
    d.append(el("div", "nombre", `${cr.nombre} · nivel ${cr.n}`));
    d.append(el("div", "texto-barra", `Elemento: ${nombreElem(cr.elem)} (${LETRA[cr.elem]})`));
    d.append(barra(cr.hp, cr.hp_max));
    d.append(el("div", "texto-barra", `Ánimo ${cr.hp} de ${cr.hp_max}`));
    return d;
  }

  function boton(texto, clave, alPulsar, deshabilitado, etiqueta) {
    const b = el("button", "boton", texto);
    b.type = "button";
    b.dataset.k = clave;
    if (etiqueta) b.setAttribute("aria-label", etiqueta);
    b.disabled = !!deshabilitado;
    b.addEventListener("click", alPulsar);
    return b;
  }

  function renderDuelo() {
    const cont = $("duelo-cont");
    const activo = document.activeElement;
    const foco = activo && activo.dataset ? activo.dataset.k : null;
    cont.replaceChildren();
    const du = st.duelo, w = du.salvaje, a = st.equipo[du.activo];

    const info = el("div", "duelo-info");
    info.append(fichaDuelo(du.visitante ? "Visitante del día" : "Criatura salvaje", w), fichaDuelo("Tu criatura", a));
    cont.append(info);

    let ef = `${a.nombre} (${nombreElem(a.elem)}) contra ${w.nombre} (${nombreElem(w.elem)}): ${efecto(a.elem, w.elem)}.`;
    if (du.escudo_j) ef += " Tu resguardo está preparado.";
    if (du.escudo_s) ef += " La criatura salvaje está resguardada.";
    if (du.debe_cambiar) ef = `${a.nombre} se ha cansado. Elige a otra criatura del equipo.`;
    cont.append(el("p", "efecto", ef));

    const ops = el("div", "opciones");
    ops.append(el("h4", "", "Gestos"));
    du.gestos.forEach((g, i) => {
      const txt = `${i + 1} · ${g.nombre} ${g.poder ? "(fuerza " + g.poder + ")" : "(resguardo)"} · usos ${a.pp[i]}/${g.usos_max}`;
      ops.append(boton(txt, "g" + i, () => actuar("atacar", i), du.debe_cambiar || a.pp[i] <= 0, `Gesto ${i + 1}: ${g.nombre}, ${a.pp[i]} usos`));
    });
    ops.append(el("h4", "", "Otras acciones"));
    ops.append(boton(`O · Ofrenda (tienes ${st.ofrendas}) · acepta ~${du.prob_ofrenda}%`, "o", () => actuar("ofrecer"),
      du.debe_cambiar || st.ofrendas <= 0, `Hacer una ofrenda, tienes ${st.ofrendas}, probabilidad aproximada ${du.prob_ofrenda} por ciento`));
    st.equipo.forEach((c, i) => {
      if (i === du.activo) return;
      ops.append(boton(`${4 + i} · Cambiar a ${c.nombre} (nivel ${c.n}, ánimo ${c.hp}/${c.hp_max})`, "c" + i,
        () => actuar("cambiar", i), c.hp <= 0, c.hp <= 0 ? `${c.nombre} está cansada` : `Cambiar a ${c.nombre}`));
    });
    ops.append(boton("F · Huir", "f", () => actuar("huir"), du.debe_cambiar, "Huir del encuentro"));
    cont.append(ops);

    if (foco) {
      const b = cont.querySelector(`[data-k="${foco}"]`);
      if (b && !b.disabled) b.focus({ preventScroll: true });
    }
  }

  function tarjeta(cr, enEquipo) {
    const esp = dat.especies[cr.e];
    const t = el("div", "tarjeta");
    t.append(miniatura(esp, false));
    const datos = el("div");
    datos.append(el("div", "nombre", cr.nombre));
    datos.append(el("div", "texto-barra", `Nivel ${cr.n} · ${nombreElem(cr.elem)} (${LETRA[cr.elem]})`));
    datos.append(barra(cr.hp, cr.hp_max));
    datos.append(el("div", "texto-barra", `Ánimo ${cr.hp}/${cr.hp_max}`));
    datos.append(barra(cr.xp, cr.xp_sig, "xp"));
    datos.append(el("div", "texto-barra", `Experiencia ${cr.xp}/${cr.xp_sig}`));
    t.append(datos);
    const acc = el("div", "acciones-t");
    const libre = st.fase === "mundo";
    if (enEquipo) {
      const b = boton("Mandar a la reserva", "q" + cr.id, () => aplicar(llamar("quitar_del_equipo", st.equipo.findIndex((x) => x.id === cr.id))),
        !libre || st.equipo.length <= 1, `Mandar a ${cr.nombre} a la reserva`);
      acc.append(b);
    } else {
      const sel = el("select");
      sel.setAttribute("aria-label", `Con quién cambiar a ${cr.nombre}`);
      st.equipo.forEach((x, i) => { const o = el("option", "", `Cambiar por ${x.nombre}`); o.value = String(i); sel.append(o); });
      if (st.equipo.length < 3) { const o = el("option", "", "Añadir al equipo"); o.value = String(st.equipo.length); sel.prepend(o); sel.value = String(st.equipo.length); }
      const b = boton("Al equipo", "r" + cr.id, () => aplicar(llamar("poner_en_equipo", cr.id, Number(sel.value))), !libre, `Meter a ${cr.nombre} en el equipo`);
      acc.append(sel, b);
    }
    t.append(acc);
    return t;
  }

  function renderEquipo() {
    const eq = $("equipo"), re = $("reserva");
    eq.replaceChildren(...st.equipo.map((c) => tarjeta(c, true)));
    if (!st.equipo.length) eq.append(el("p", "vacio", "Aún no tienes ninguna criatura."));
    re.replaceChildren(...st.reserva.map((c) => tarjeta(c, false)));
    if (!st.reserva.length) re.append(el("p", "vacio", "La reserva está vacía. Las amigas que no caben en el equipo esperan aquí."));
  }

  function renderRegistro() {
    const cont = $("registro");
    cont.replaceChildren(...dat.especies.map((esp) => {
      const r = st.registro[esp.id];
      const d = el("div", "especie" + (r === 2 ? " amiga" : ""));
      d.append(miniatura(esp, r === 0));
      const nombre = el("div", "nombre", r === 0 ? "???" : esp.nombre);
      d.append(nombre);
      const estado = r === 2 ? "Amiga" : (r === 1 ? "Vista" : "Sin ver");
      const extra = r === 0 ? "" : ` · ${nombreElem(esp.elem)} (${LETRA[esp.elem]})`;
      d.append(el("div", "estado", `${estado}${extra} · vive en ${dat.zonas[esp.zona].toLowerCase()}`));
      if (r === 2) d.append(el("p", "desc", esp.desc));
      else if (r === 1) d.append(el("p", "desc", "La has visto. Tranquilízala para que sea tu amiga."));
      return d;
    }));
  }

  function renderStats() {
    const e = leer().estadisticas || {};
    $("st-racha").textContent = fn.racha_vigente ? fn.racha_vigente(JSON.stringify(e), hoyISO()) : (e.racha || 0);
    $("st-mejor-racha").textContent = e.mejor_racha || 0;
    $("st-completados").textContent = e.completados || 0;
  }

  function contarDia() {
    if (!st || !st.dia.hecho || !st.dia.fecha) return;
    const datos = leer();
    const est = datos.estadisticas || {};
    if (est.ultimo_dia === st.dia.fecha) return;
    datos.estadisticas = llamar("actualizar_estadisticas", JSON.stringify(est), st.dia.fecha);
    escribir(datos);
  }

  function guardarLocal() {
    const datos = leer();
    datos.partida = fn.guardar();
    escribir(datos);
  }

  function pintar() {
    const fase = st.fase;
    $("elegir").hidden = fase !== "inicio";
    $("escena").hidden = fase === "inicio";
    $("dpad").hidden = fase !== "mundo";
    $("duelo").hidden = fase !== "duelo";
    $("contadores").hidden = fase === "inicio";
    $("ayuda-teclas").hidden = fase === "inicio";
    if (fase !== "inicio") {
      $("c-registro").textContent = `${st.amigas}/${st.total}`;
      $("c-ofrendas").textContent = `${st.ofrendas}/${st.ofrendas_max}`;
      $("c-pasos").textContent = st.pasos;
      $("c-duelos").textContent = st.duelos;
      const cv = $("lienzo");
      const resumen = fase === "duelo"
        ? `Encuentro con ${st.duelo.salvaje.nombre}, nivel ${st.duelo.salvaje.n}.`
        : `Estás en: ${st.lugar}.`;
      cv.setAttribute("aria-label", `Mapa de la montaña. ${resumen}`);
      $("lugar").textContent = fase === "duelo" ? resumen : `Estás en: ${st.lugar}. Registro ${st.amigas} de ${st.total}.`;
      if (!ctx) ajustar();
    }
    if (fase === "duelo") renderDuelo();
    $("fila-dia").textContent = st.dia.fecha
      ? `Hoy, ${fechaLarga(st.dia.fecha)}: ` + (st.dia.hecho
        ? "has recibido al visitante del día."
        : "un visitante te espera en el claro de la cumbre (sigue el camino central hacia el norte).")
      : "";
    $("diario").replaceChildren(...st.log.slice(-6).map((m) => el("li", "", m)));
    renderEquipo();
    renderRegistro();
    renderStats();
    $("compartir-texto").textContent = fn.compartir_texto();
    pedirFrame();
    if (ctx) dibujar(performance.now());
  }

  // ---------- acciones ----------
  function aplicar(nuevo) {
    const antes = st;
    st = nuevo;
    if (nuevo.error) mensaje(nuevo.error); else mensaje("");
    // animación del paso
    if (antes && antes.fase === "mundo" && st.fase !== "inicio" && !reducido) {
      const dist = Math.abs(antes.x - st.x) + Math.abs(antes.y - st.y);
      if (dist === 1) anim = { fx: antes.x, fy: antes.y, tx: st.x, ty: st.y, t0: performance.now() };
      else anim = null;
    } else if (!antes || antes.fase !== "mundo") {
      anim = null;
    }
    // sacudida del que recibe el golpe
    if (antes && antes.duelo && st.duelo && !reducido) {
      if (st.duelo.salvaje.hp < antes.duelo.salvaje.hp) sacudida = { lado: "s", t0: performance.now() };
      else if (st.equipo[st.duelo.activo] && antes.equipo[antes.duelo.activo] &&
        st.duelo.activo === antes.duelo.activo && st.equipo[st.duelo.activo].hp < antes.equipo[antes.duelo.activo].hp) sacudida = { lado: "j", t0: performance.now() };
    }
    $("anuncio").textContent = (nuevo.nuevos || []).join(" ");
    contarDia();
    guardarLocal();
    // si pasa la medianoche con la página abierta, llega otro visitante
    if (st.fase === "mundo" && st.dia.fecha && st.dia.fecha !== hoyISO()) { st = llamar("fijar_dia", hoyISO()); }
    pintar();
  }

  function mover(d) {
    if (!st || st.fase !== "mundo") return;
    const ahora = performance.now();
    if (!reducido && ahora - ultimoPaso < DUR_PASO * 0.8) return;
    ultimoPaso = ahora;
    aplicar(llamar("mover", d));
  }
  function actuar(tipo, arg) {
    if (!st || st.fase !== "duelo") return;
    aplicar(llamar("accion", tipo, arg === undefined ? 0 : arg));
  }

  function elegirInicial(i) { aplicar(llamar("elegir_inicial", i)); }

  function comenzarDeCero() {
    if (!confirmaNueva) {
      $("nueva").textContent = "¿Seguro? Pulsa otra vez";
      confirmaNueva = setTimeout(() => { confirmaNueva = null; $("nueva").textContent = "Empezar de cero"; }, 3500);
      return;
    }
    clearTimeout(confirmaNueva); confirmaNueva = null; $("nueva").textContent = "Empezar de cero";
    const datos = leer(); delete datos.partida; escribir(datos);
    anim = null; sacudida = null;
    st = llamar("nueva_partida", semillaNueva());
    st = llamar("fijar_dia", hoyISO());
    aplicar(st);
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
    setTimeout(() => { b.textContent = "Copiar mi progreso"; }, 2200);
  }

  // ---------- controles ----------
  const TECLAS_MOVER = { ArrowUp: "N", ArrowDown: "S", ArrowLeft: "O", ArrowRight: "E", w: "N", W: "N", s: "S", S: "S", a: "O", A: "O", d: "E", D: "E" };

  function construirControles() {
    document.addEventListener("keydown", (ev) => {
      if (!st || ev.ctrlKey || ev.metaKey || ev.altKey) return;
      const t = ev.target;
      if (t && t.closest && t.closest("select, textarea, input, pre")) return;
      if (st.fase === "mundo" && TECLAS_MOVER[ev.key]) { ev.preventDefault(); mover(TECLAS_MOVER[ev.key]); return; }
      if (st.fase === "duelo") {
        const k = ev.key;
        if (k === "1" || k === "2" || k === "3") { ev.preventDefault(); actuar("atacar", Number(k) - 1); }
        else if (k === "o" || k === "O") { ev.preventDefault(); actuar("ofrecer"); }
        else if (k === "f" || k === "F") { ev.preventDefault(); actuar("huir"); }
        else if (k === "4" || k === "5" || k === "6") { ev.preventDefault(); actuar("cambiar", Number(k) - 4); }
      }
    });

    document.querySelectorAll("#dpad button").forEach((b) => {
      const d = b.dataset.dir;
      b.addEventListener("pointerdown", () => {
        ultimoPuntero = Date.now();
        mover(d);
        clearInterval(repetir);
        repetir = setInterval(() => mover(d), 160);
      });
      ["pointerup", "pointerleave", "pointercancel"].forEach((n) => b.addEventListener(n, () => { clearInterval(repetir); repetir = null; }));
      b.addEventListener("click", () => { if (Date.now() - ultimoPuntero > 600) mover(d); });
    });

    $("copiar").addEventListener("click", copiar);
    $("nueva").addEventListener("click", comenzarDeCero);
    window.addEventListener("resize", () => { clearTimeout(construirControles.t); construirControles.t = setTimeout(() => { if (st && st.fase !== "inicio") ajustar(); }, 150); });
  }

  function construirIniciales() {
    const cont = $("iniciales");
    cont.replaceChildren(...[0, 1, 2].map((i) => {
      const esp = dat.especies[i];
      const b = el("button", "inicial");
      b.type = "button";
      b.setAttribute("aria-label", `Elegir a ${esp.nombre}, elemento ${nombreElem(esp.elem)}`);
      b.append(miniatura(esp, false), el("strong", "", esp.nombre), el("small", "", `Elemento ${nombreElem(esp.elem)} (${LETRA[esp.elem]})`), el("small", "", esp.desc));
      b.addEventListener("click", () => elegirInicial(i));
      return b;
    }));
  }

  async function init() {
    try {
      if (typeof loadPyodide === "undefined") throw new Error("Pyodide no se ha cargado");
      const r = await fetch("codigo.py");
      if (!r.ok) throw new Error("No se pudo cargar codigo.py");
      const fuente = await r.text();
      $("python-source").textContent = fuente;
      const py = await loadPyodide();
      await py.runPythonAsync(fuente);
      ["datos_estaticos", "nueva_partida", "elegir_inicial", "fijar_dia", "mover", "accion", "poner_en_equipo", "quitar_del_equipo",
        "guardar", "restaurar", "compartir_texto", "actualizar_estadisticas", "racha_vigente"]
        .forEach((n) => { fn[n] = py.globals.get(n); });
      dat = JSON.parse(fn.datos_estaticos());
      construirIniciales();
      construirControles();
      const guardada = leer().partida;
      st = guardada ? llamar("restaurar", guardada, semillaNueva()) : llamar("nueva_partida", semillaNueva());
      st = llamar("fijar_dia", hoyISO());
      $("estado-carga").hidden = true;
      $("escena").hidden = st.fase === "inicio";
      ajustar();
      contarDia();
      guardarLocal();
      pintar();
    } catch (e) {
      console.error(e);
      $("estado-carga").textContent = "No se ha podido cargar el motor de Python. Comprueba tu conexión y recarga la página.";
    }
  }

  init();
})();

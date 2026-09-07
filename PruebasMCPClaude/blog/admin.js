// Configuración fija del repositorio de destino
const GH_OWNER = "MarioGalanPedrayes";
const GH_REPO = "MarioGalanPedrayes";
const GH_BRANCH = "main";
const GH_BASE = "PruebasMCPClaude/blog";

const EXTENSIONES_PERMITIDAS = ["jpg", "jpeg", "png", "gif", "webp", "svg", "mp4", "webm", "mov", "mp3", "wav", "ogg"];
const TAMANO_MAXIMO_MB = 20;

let slugActual = null;
let portadaExistente = null;

function obtenerToken() {
  return document.getElementById("token").value.trim();
}

function mostrarMensaje(texto, tipo = "info") {
  const el = document.getElementById("mensaje");
  el.className = `mensaje ${tipo}`;
  el.textContent = texto;
}

function slugify(texto) {
  return texto
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60) || "entrada";
}

function obtenerSlug() {
  if (!slugActual) {
    const titulo = document.getElementById("titulo").value.trim() || "entrada";
    slugActual = `${slugify(titulo)}-${Date.now().toString(36).slice(-5)}`;
  }
  return slugActual;
}

function extensionDe(nombreArchivo) {
  return nombreArchivo.split(".").pop().toLowerCase();
}

async function fileABase64(file) {
  const buffer = await file.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunkSize));
  }
  return btoa(binary);
}

async function ghApi(path, options = {}) {
  const token = obtenerToken();
  const resp = await fetch(`https://api.github.com/repos/${GH_OWNER}/${GH_REPO}/contents/${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      ...(options.headers || {}),
    },
  });
  return resp;
}

async function ghGetFile(path) {
  const resp = await ghApi(`${path}?ref=${GH_BRANCH}`);
  if (resp.status === 404) return null;
  if (!resp.ok) throw new Error(`No se pudo leer ${path} (HTTP ${resp.status})`);
  const data = await resp.json();
  const contenido = decodeURIComponent(escape(atob(data.content)));
  return { sha: data.sha, contenido };
}

async function ghPutFile(path, contenidoBase64, mensaje, sha) {
  const body = { message: mensaje, content: contenidoBase64, branch: GH_BRANCH };
  if (sha) body.sha = sha;

  const resp = await ghApi(path, { method: "PUT", body: JSON.stringify(body) });

  if (!resp.ok) {
    const detalle = await resp.json().catch(() => ({}));
    if (resp.status === 401) throw new Error("Token inválido o caducado.");
    if (resp.status === 403) throw new Error("El token no tiene permiso de escritura (Contents: Read and write).");
    throw new Error(detalle.message || `Error subiendo ${path} (HTTP ${resp.status})`);
  }

  return resp.json();
}

async function ghDeleteFile(path, sha, mensaje) {
  const resp = await ghApi(path, {
    method: "DELETE",
    body: JSON.stringify({ message: mensaje, sha, branch: GH_BRANCH }),
  });
  if (!resp.ok) {
    const detalle = await resp.json().catch(() => ({}));
    if (resp.status === 401) throw new Error("Token inválido o caducado.");
    if (resp.status === 403) throw new Error("El token no tiene permiso de escritura.");
    throw new Error(detalle.message || `Error borrando ${path} (HTTP ${resp.status})`);
  }
  return resp.json();
}

function validarArchivo(file) {
  const ext = extensionDe(file.name);
  if (!EXTENSIONES_PERMITIDAS.includes(ext)) {
    throw new Error(`Tipo de archivo no permitido: .${ext}`);
  }
  if (file.size > TAMANO_MAXIMO_MB * 1024 * 1024) {
    throw new Error(`El archivo pesa demasiado (máx. ${TAMANO_MAXIMO_MB} MB).`);
  }
  return ext;
}

async function subirMedia(file) {
  const ext = validarArchivo(file);
  const slug = obtenerSlug();
  const nombreSeguro = `${Date.now()}-${slugify(file.name.replace(/\.[^.]+$/, ""))}.${ext}`;
  const rutaCompleta = `${GH_BASE}/media/${slug}/${nombreSeguro}`;
  const contenidoBase64 = await fileABase64(file);

  await ghPutFile(rutaCompleta, contenidoBase64, `Blog: sube media para ${slug}`);

  return `media/${slug}/${nombreSeguro}`;
}

async function insertarMedia() {
  const input = document.getElementById("archivoInline");
  const textarea = document.getElementById("contenido");

  if (!obtenerToken()) {
    mostrarMensaje("Pega primero tu token de GitHub.", "error");
    return;
  }
  if (!input.files[0]) {
    mostrarMensaje("Elige primero un archivo para insertar.", "error");
    return;
  }

  mostrarMensaje("Subiendo archivo…", "info");

  try {
    const rutaRelativa = await subirMedia(input.files[0]);
    const inicio = textarea.selectionStart;
    const fin = textarea.selectionEnd;
    const textoInsertar = `\n![${input.files[0].name}](${rutaRelativa})\n`;

    textarea.value = textarea.value.slice(0, inicio) + textoInsertar + textarea.value.slice(fin);
    input.value = "";
    actualizarPreview();
    mostrarMensaje("Archivo subido e insertado en el texto.", "ok");
  } catch (err) {
    mostrarMensaje(err.message, "error");
    console.error(err);
  }
}

function actualizarPreview() {
  const contenido = document.getElementById("contenido").value;
  document.getElementById("preview").innerHTML = markdownToHtml(contenido);
}

// ---- Listado, edición y borrado de entradas existentes ----

async function cargarListaAdmin() {
  const cont = document.getElementById("listaAdmin");
  cont.innerHTML = '<p class="ayuda">Cargando…</p>';
  try {
    const resp = await fetch(`posts.json?_=${Date.now()}`, { cache: "no-store" });
    if (!resp.ok) throw new Error();
    const posts = await resp.json();

    if (posts.length === 0) {
      cont.innerHTML = '<p class="ayuda">Todavía no hay entradas publicadas.</p>';
      return;
    }

    posts.sort((a, b) => (a.fecha < b.fecha ? 1 : -1));

    cont.innerHTML = posts.map(p => `
      <div class="item-existente">
        <div>
          <strong>${escapeHtml(p.titulo)}</strong>
          <div class="ayuda">${formatearFecha(p.fecha)}</div>
        </div>
        <div class="fila-botones">
          <button type="button" class="secundario btn-editar" data-slug="${escapeHtml(p.slug)}">Editar</button>
          <button type="button" class="secundario btn-borrar" data-slug="${escapeHtml(p.slug)}" data-titulo="${escapeHtml(p.titulo)}">Borrar</button>
        </div>
      </div>
    `).join("");

    cont.querySelectorAll(".btn-editar").forEach(btn =>
      btn.addEventListener("click", () => cargarParaEditar(btn.dataset.slug))
    );
    cont.querySelectorAll(".btn-borrar").forEach(btn =>
      btn.addEventListener("click", () => borrarPost(btn.dataset.slug, btn.dataset.titulo))
    );
  } catch (err) {
    cont.innerHTML = '<p class="ayuda">Todavía no hay entradas publicadas.</p>';
  }
}

async function cargarParaEditar(slug) {
  try {
    const resp = await fetch(`posts/${slug}.json?_=${Date.now()}`, { cache: "no-store" });
    if (!resp.ok) throw new Error("No se pudo cargar la entrada.");
    const post = await resp.json();

    document.getElementById("titulo").value = post.titulo;
    document.getElementById("contenido").value = post.contenido;
    document.getElementById("portada").value = "";

    slugActual = slug;
    portadaExistente = post.portada || null;

    const aviso = document.getElementById("modoEdicion");
    aviso.style.display = "block";
    aviso.textContent = `✏️ Editando "${post.titulo}". Publica para sobrescribir esta entrada, o pulsa "Nueva entrada" para cancelar.${post.portada ? " (Se conserva la portada actual si no subes una nueva.)" : ""}`;

    actualizarPreview();
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (err) {
    mostrarMensaje("No se pudo cargar la entrada para editar.", "error");
    console.error(err);
  }
}

function nuevaEntrada() {
  slugActual = null;
  portadaExistente = null;
  document.getElementById("titulo").value = "";
  document.getElementById("contenido").value = "";
  document.getElementById("portada").value = "";
  document.getElementById("modoEdicion").style.display = "none";
  document.getElementById("mensaje").textContent = "";
  actualizarPreview();
}

async function borrarCarpetaMediaSiExiste(slug) {
  try {
    const resp = await ghApi(`${GH_BASE}/media/${slug}?ref=${GH_BRANCH}`);
    if (!resp.ok) return; // no existe o no se puede listar: mejor esfuerzo, seguimos
    const archivos = await resp.json();
    if (!Array.isArray(archivos)) return;
    for (const archivo of archivos) {
      try {
        await ghDeleteFile(`${GH_BASE}/media/${slug}/${archivo.name}`, archivo.sha, `Blog: borra media de ${slug}`);
      } catch (e) {
        console.error(e);
      }
    }
  } catch (e) {
    console.error(e);
  }
}

async function borrarPost(slug, titulo) {
  if (!obtenerToken()) {
    mostrarMensaje("Pega primero tu token de GitHub.", "error");
    return;
  }
  if (!confirm(`¿Seguro que quieres borrar "${titulo}"? Esta acción no se puede deshacer.`)) {
    return;
  }

  mostrarMensaje("Borrando entrada…", "info");

  try {
    const postFile = await ghGetFile(`${GH_BASE}/posts/${slug}.json`);
    if (postFile) {
      await ghDeleteFile(`${GH_BASE}/posts/${slug}.json`, postFile.sha, `Blog: borra "${titulo}"`);
    }

    await borrarCarpetaMediaSiExiste(slug);

    const manifestActual = await ghGetFile(`${GH_BASE}/posts.json`);
    const posts = manifestActual ? JSON.parse(manifestActual.contenido) : [];
    const nuevas = posts.filter(p => p.slug !== slug);

    await ghPutFile(
      `${GH_BASE}/posts.json`,
      btoa(unescape(encodeURIComponent(JSON.stringify(nuevas, null, 2)))),
      `Blog: elimina "${titulo}" del índice`,
      manifestActual ? manifestActual.sha : undefined
    );

    mostrarMensaje(`🗑️ "${titulo}" borrada, junto con sus archivos multimedia.`, "ok");

    if (slugActual === slug) {
      nuevaEntrada();
    }
    cargarListaAdmin();
  } catch (err) {
    mostrarMensaje(`Error al borrar: ${err.message}`, "error");
    console.error(err);
  }
}

async function publicar(event) {
  const boton = event.target;
  const titulo = document.getElementById("titulo").value.trim();
  const contenido = document.getElementById("contenido").value.trim();
  const portadaInput = document.getElementById("portada");

  if (!obtenerToken()) {
    mostrarMensaje("Pega primero tu token de GitHub.", "error");
    return;
  }
  if (!titulo) {
    mostrarMensaje("Ponle un título a la entrada.", "error");
    return;
  }
  if (!contenido) {
    mostrarMensaje("El contenido no puede estar vacío.", "error");
    return;
  }

  boton.disabled = true;
  mostrarMensaje("Publicando…", "info");

  try {
    const slug = obtenerSlug();

    let rutaPortada = portadaExistente || null;
    if (portadaInput.files[0]) {
      mostrarMensaje("Subiendo imagen de portada…", "info");
      rutaPortada = await subirMedia(portadaInput.files[0]);
    }

    const fechaHoy = new Date().toISOString().slice(0, 10);

    const post = {
      titulo,
      fecha: fechaHoy,
      contenido,
      portada: rutaPortada,
    };

    mostrarMensaje("Guardando la entrada…", "info");
    const existente = await ghGetFile(`${GH_BASE}/posts/${slug}.json`);
    await ghPutFile(
      `${GH_BASE}/posts/${slug}.json`,
      btoa(unescape(encodeURIComponent(JSON.stringify(post, null, 2)))),
      `Blog: publica "${titulo}"`,
      existente ? existente.sha : undefined
    );

    mostrarMensaje("Actualizando el índice del blog…", "info");
    const manifestActual = await ghGetFile(`${GH_BASE}/posts.json`);
    const posts = manifestActual ? JSON.parse(manifestActual.contenido) : [];

    const entrada = {
      slug,
      titulo,
      fecha: fechaHoy,
      extracto: generarExtracto(contenido),
      portada: rutaPortada,
    };

    const yaExiste = posts.findIndex(p => p.slug === slug);
    if (yaExiste >= 0) {
      posts[yaExiste] = entrada;
    } else {
      posts.unshift(entrada);
    }

    await ghPutFile(
      `${GH_BASE}/posts.json`,
      btoa(unescape(encodeURIComponent(JSON.stringify(posts, null, 2)))),
      `Blog: actualiza índice con "${titulo}"`,
      manifestActual ? manifestActual.sha : undefined
    );

    const urlPublica = `https://${GH_OWNER}.github.io/${GH_REPO}/${GH_BASE}/post.html?slug=${slug}`;
    mostrarMensaje(`✅ Publicado. Puede tardar 1-2 minutos en verse. Link: ${urlPublica}`, "ok");
    portadaExistente = rutaPortada;
    cargarListaAdmin();
  } catch (err) {
    mostrarMensaje(`Error: ${err.message}`, "error");
    console.error(err);
  } finally {
    boton.disabled = false;
  }
}

document.getElementById("contenido").addEventListener("input", actualizarPreview);
cargarListaAdmin();

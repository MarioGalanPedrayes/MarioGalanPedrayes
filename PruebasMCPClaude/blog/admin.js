// Configuración fija del repositorio de destino
const GH_OWNER = "MarioGalanPedrayes";
const GH_REPO = "MarioGalanPedrayes";
const GH_BRANCH = "main";
const GH_BASE = "PruebasMCPClaude/blog";

const EXTENSIONES_PERMITIDAS = ["jpg", "jpeg", "png", "gif", "webp", "svg", "mp4", "webm", "mov", "mp3", "wav", "ogg"];
const TAMANO_MAXIMO_MB = 20;

let slugActual = null;

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

    let rutaPortada = null;
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
  } catch (err) {
    mostrarMensaje(`Error: ${err.message}`, "error");
    console.error(err);
  } finally {
    boton.disabled = false;
  }
}

document.getElementById("contenido").addEventListener("input", actualizarPreview);

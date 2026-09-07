// Utilidades compartidas por index.html y post.html

function escapeHtml(texto) {
  const div = document.createElement("div");
  div.textContent = texto;
  return div.innerHTML;
}

function formatearFecha(iso) {
  try {
    const d = new Date(iso + "T00:00:00");
    return d.toLocaleDateString("es-ES", { day: "numeric", month: "long", year: "numeric" });
  } catch {
    return iso;
  }
}

// Mini-conversor de Markdown a HTML (soporta lo básico: encabezados, negrita,
// cursiva, enlaces, imágenes, listas, código y párrafos). El texto de entrada
// ya se escapa como HTML antes de aplicar las sustituciones, así que es seguro.
function markdownToHtml(md) {
  let texto = escapeHtml(md).replace(/\r\n/g, "\n");

  // Bloques de código ```...```
  texto = texto.replace(/```([\s\S]*?)```/g, (_, codigo) => `<pre><code>${codigo.trim()}</code></pre>`);

  const lineas = texto.split("\n");
  const html = [];
  let enLista = false;
  let parrafoActual = [];

  function cerrarParrafo() {
    if (parrafoActual.length > 0) {
      html.push(`<p>${parrafoActual.join(" ")}</p>`);
      parrafoActual = [];
    }
  }

  function cerrarLista() {
    if (enLista) {
      html.push("</ul>");
      enLista = false;
    }
  }

  for (const lineaRaw of lineas) {
    const linea = lineaRaw.trim();

    if (linea.startsWith("<pre>")) {
      cerrarParrafo();
      cerrarLista();
      html.push(lineaRaw);
      continue;
    }

    if (linea === "") {
      cerrarParrafo();
      cerrarLista();
      continue;
    }

    const encabezado = linea.match(/^(#{1,4})\s+(.*)$/);
    if (encabezado) {
      cerrarParrafo();
      cerrarLista();
      const nivel = encabezado[1].length;
      html.push(`<h${nivel}>${aplicarInline(encabezado[2])}</h${nivel}>`);
      continue;
    }

    const imagen = linea.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
    if (imagen) {
      cerrarParrafo();
      cerrarLista();
      const [, alt, src] = imagen;
      const ext = src.split(".").pop().toLowerCase();
      if (["mp4", "webm", "mov"].includes(ext)) {
        html.push(`<video controls src="${src}"></video>`);
      } else if (["mp3", "wav", "ogg"].includes(ext)) {
        html.push(`<audio controls src="${src}"></audio>`);
      } else {
        html.push(`<img src="${src}" alt="${alt}">`);
      }
      continue;
    }

    const item = linea.match(/^-\s+(.*)$/);
    if (item) {
      cerrarParrafo();
      if (!enLista) {
        html.push("<ul>");
        enLista = true;
      }
      html.push(`<li>${aplicarInline(item[1])}</li>`);
      continue;
    }

    cerrarLista();
    parrafoActual.push(aplicarInline(linea));
  }

  cerrarParrafo();
  cerrarLista();

  return html.join("\n");
}

function aplicarInline(texto) {
  return texto
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
}

function generarExtracto(md, longitud = 160) {
  const textoPlano = md
    .replace(/```[\s\S]*?```/g, "")
    .replace(/!\[[^\]]*\]\([^)]+\)/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/[#*`_>-]/g, "")
    .replace(/\s+/g, " ")
    .trim();

  if (textoPlano.length <= longitud) return textoPlano;
  return textoPlano.slice(0, longitud).trim() + "…";
}

// Mismas reglas que validarNombre()/validarEmail()/validarMensaje() en codigo.php.
const REGEX_NOMBRE = /^[\p{L}\s'-]+$/u;

function validarNombre(nombre) {
  nombre = nombre.trim();
  if (nombre === "") return "El nombre no puede estar vacío.";
  if (nombre.length < 2) return "El nombre es demasiado corto.";
  if (!REGEX_NOMBRE.test(nombre)) {
    return "El nombre solo puede contener letras, espacios, guiones y apóstrofes.";
  }
  return null;
}

function validarEmail(email) {
  email = email.trim();
  if (email === "") return "El email no puede estar vacío.";
  // Comprobación equivalente a FILTER_VALIDATE_EMAIL para el caso general.
  const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!regexEmail.test(email)) return "El email no tiene un formato válido.";
  return null;
}

function validarMensaje(mensaje) {
  mensaje = mensaje.trim();
  if (mensaje.length < 10) return "El mensaje debe tener al menos 10 caracteres.";
  if (mensaje.length > 500) return "El mensaje no puede superar los 500 caracteres.";
  return null;
}

function mostrarError(campoId, errorId, error) {
  const campo = document.getElementById(campoId);
  const errorEl = document.getElementById(errorId);
  if (error) {
    campo.classList.add("campo-invalido");
    errorEl.textContent = error;
  } else {
    campo.classList.remove("campo-invalido");
    errorEl.textContent = "";
  }
  return error === null;
}

function validarCampo(campo) {
  if (campo === "nombre") {
    return mostrarError("nombre", "error-nombre", validarNombre(document.getElementById("nombre").value));
  }
  if (campo === "email") {
    return mostrarError("email", "error-email", validarEmail(document.getElementById("email").value));
  }
  if (campo === "mensaje") {
    return mostrarError("mensaje", "error-mensaje", validarMensaje(document.getElementById("mensaje").value));
  }
  return true;
}

function manejarEnvio(evento) {
  evento.preventDefault();

  const okNombre = validarCampo("nombre");
  const okEmail = validarCampo("email");
  const okMensaje = validarCampo("mensaje");

  const resultado = document.getElementById("resultado");

  if (okNombre && okEmail && okMensaje) {
    resultado.className = "resultado ok";
    resultado.textContent =
      "✔ Formulario válido. En un servidor real, aquí se enviaría el correo con PHP.";
  } else {
    resultado.className = "resultado mal";
    resultado.textContent = "✘ Revisa los campos marcados en rojo.";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("formularioContacto").addEventListener("submit", manejarEnvio);
  ["nombre", "email", "mensaje"].forEach((campo) => {
    document.getElementById(campo).addEventListener("input", () => validarCampo(campo));
  });
});

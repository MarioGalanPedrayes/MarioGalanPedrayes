<?php
declare(strict_types=1);

/**
 * Formulario de contacto con validación (demo de consola).
 * Autocontenida: sin dependencias externas, sin acceso a red ni a
 * ficheros del sistema. No envía correos de verdad.
 */

/** @return array{0: bool, 1: string} */
function validarNombre(string $nombre): array
{
    $nombre = trim($nombre);

    if ($nombre === '') {
        return [false, 'El nombre no puede estar vacío.'];
    }
    if (mb_strlen($nombre) < 2) {
        return [false, 'El nombre es demasiado corto.'];
    }
    if (!preg_match('/^[\p{L}\s\'-]+$/u', $nombre)) {
        return [false, 'El nombre solo puede contener letras, espacios, guiones y apóstrofes.'];
    }

    return [true, ''];
}

/** @return array{0: bool, 1: string} */
function validarEmail(string $email): array
{
    $email = trim($email);

    if ($email === '') {
        return [false, 'El email no puede estar vacío.'];
    }
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        return [false, 'El email no tiene un formato válido.'];
    }

    return [true, ''];
}

/** @return array{0: bool, 1: string} */
function validarMensaje(string $mensaje): array
{
    $mensaje = trim($mensaje);
    $longitud = mb_strlen($mensaje);

    if ($longitud < 10) {
        return [false, 'El mensaje debe tener al menos 10 caracteres.'];
    }
    if ($longitud > 500) {
        return [false, 'El mensaje no puede superar los 500 caracteres.'];
    }

    return [true, ''];
}

/** @return array<string, string> Errores por campo, vacío si todo es válido */
function validarFormulario(string $nombre, string $email, string $mensaje): array
{
    $errores = [];

    [$okNombre, $errorNombre] = validarNombre($nombre);
    if (!$okNombre) {
        $errores['nombre'] = $errorNombre;
    }

    [$okEmail, $errorEmail] = validarEmail($email);
    if (!$okEmail) {
        $errores['email'] = $errorEmail;
    }

    [$okMensaje, $errorMensaje] = validarMensaje($mensaje);
    if (!$okMensaje) {
        $errores['mensaje'] = $errorMensaje;
    }

    return $errores;
}

function procesarEnvio(string $nombre, string $email, string $mensaje): void
{
    echo "--- Enviando formulario ---\n";
    echo "Nombre:  {$nombre}\n";
    echo "Email:   {$email}\n";
    echo "Mensaje: {$mensaje}\n";

    $errores = validarFormulario($nombre, $email, $mensaje);

    if (empty($errores)) {
        echo "OK Formulario valido. En un servidor real, aqui se enviaria el correo.\n\n";
        return;
    }

    echo "X Formulario con errores:\n";
    foreach ($errores as $campo => $mensajeError) {
        echo "  - {$campo}: {$mensajeError}\n";
    }
    echo "\n";
}

function main(): void
{
    echo "=== Formulario de contacto con validacion (demo) ===\n\n";

    $casos = [
        ['Ana García', 'ana@example.com', 'Hola, quería preguntar por vuestros horarios de atención.'],
        ['', 'ana@example.com', 'Mensaje de prueba con el nombre vacío.'],
        ['Bruno', 'no-es-un-email', 'Otro mensaje de prueba para ver qué campo falla esta vez.'],
        ['Clara 3000', 'clara@example.com', 'Hola'],
        ['José Pérez', 'jose@example.com', 'Buenas tardes, me gustaría más información sobre el producto que anunciáis en la web.'],
    ];

    foreach ($casos as [$nombre, $email, $mensaje]) {
        procesarEnvio($nombre, $email, $mensaje);
    }
}

main();

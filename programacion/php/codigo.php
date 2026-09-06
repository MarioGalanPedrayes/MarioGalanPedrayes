<?php
/**
 * Adivina el número — juego de consola en PHP.
 * Genera un número aleatorio entre 1 y 100 y da pistas de "más alto" / "más bajo"
 * hasta que el jugador acierte o se le acaben los intentos.
 *
 * Ejecutar con: php codigo.php
 */

function pedirNumero(string $mensaje): int
{
    echo $mensaje;
    $linea = trim(fgets(STDIN));
    return (int) $linea;
}

function main(): void
{
    $secreto = random_int(1, 100);
    $intentosMaximos = 7;
    $intento = 0;

    echo "=== Adivina el número (1-100) ===\n";
    echo "Tienes {$intentosMaximos} intentos.\n\n";

    while ($intento < $intentosMaximos) {
        $intento++;
        $restantes = $intentosMaximos - $intento;

        $numero = pedirNumero("Intento {$intento}/{$intentosMaximos} — Escribe un número: ");

        if ($numero === $secreto) {
            echo "🎉 ¡Correcto! El número era {$secreto}. Lo lograste en {$intento} intentos.\n";
            return;
        }

        if ($numero < $secreto) {
            echo "Más alto. ";
        } else {
            echo "Más bajo. ";
        }

        if ($restantes > 0) {
            echo "Te quedan {$restantes} intentos.\n";
        }
    }

    echo "😢 Se acabaron los intentos. El número era {$secreto}.\n";
}

main();

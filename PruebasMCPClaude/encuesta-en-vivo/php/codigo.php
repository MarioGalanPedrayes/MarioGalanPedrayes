<?php
/**
 * Encuesta con resultados en vivo (consola).
 * Autocontenida: sin dependencias externas, sin acceso a red ni a
 * ficheros del sistema. Los votos solo existen durante la ejecución.
 */

function pedirNumero(string $mensaje): int
{
    echo $mensaje;
    $linea = trim(fgets(STDIN));
    return (int) $linea;
}

function dibujarBarra(int $valor, int $total, int $ancho = 30): string
{
    if ($total === 0) {
        return str_repeat('░', $ancho) . '   0.0%';
    }

    $porcentaje = $valor / $total;
    $llenas = (int) round($porcentaje * $ancho);
    $barra = str_repeat('█', $llenas) . str_repeat('░', $ancho - $llenas);

    return sprintf('%s  %5.1f%%', $barra, $porcentaje * 100);
}

function mostrarResultados(array $opciones, array $votos): void
{
    $total = array_sum($votos);
    echo "\n--- Resultados en vivo ({$total} votos) ---\n";

    foreach ($opciones as $i => $opcion) {
        $etiqueta = str_pad($opcion, 12);
        echo "{$etiqueta} " . dibujarBarra($votos[$i], $total) . " ({$votos[$i]})\n";
    }

    echo "\n";
}

function main(): void
{
    $opciones = ['Python', 'JavaScript', 'PHP', 'Java', 'Otro'];
    $votos = array_fill(0, count($opciones), 0);
    $salir = count($opciones) + 1;

    echo "=== Encuesta en vivo: tu lenguaje favorito ===\n\n";

    while (true) {
        foreach ($opciones as $i => $opcion) {
            echo ($i + 1) . ") {$opcion}\n";
        }
        echo "{$salir}) Terminar encuesta\n";

        $eleccion = pedirNumero("Vota (numero): ");

        if ($eleccion === $salir) {
            break;
        }

        $indice = $eleccion - 1;
        if ($indice < 0 || $indice >= count($opciones)) {
            echo "Opcion no valida, intentalo de nuevo.\n\n";
            continue;
        }

        $votos[$indice]++;
        mostrarResultados($opciones, $votos);
    }

    echo "=== Resultado final ===\n";
    mostrarResultados($opciones, $votos);
}

main();

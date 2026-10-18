import java.util.Random;
import java.util.Scanner;

/**
 * Ahorcado en consola. Practica: variables, arrays, bucles, condicionales,
 * métodos, String/StringBuilder y lectura con Scanner.
 */
public class Codigo {

    static final String[] PALABRAS = {
        "variable", "bucle", "funcion", "objeto", "clase",
        "compilador", "herencia", "excepcion", "interfaz", "paquete"
    };
    static final int MAX_FALLOS = 6;

    // Devuelve la palabra mostrando solo las letras ya acertadas.
    static String mostrar(String palabra, boolean[] acertadas) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < palabra.length(); i++) {
            sb.append(acertadas[i] ? palabra.charAt(i) : '_').append(' ');
        }
        return sb.toString().trim();
    }

    // Marca las posiciones donde aparece la letra; devuelve cuántas halló.
    static int probarLetra(String palabra, boolean[] acertadas, char letra) {
        int hallazgos = 0;
        for (int i = 0; i < palabra.length(); i++) {
            if (palabra.charAt(i) == letra && !acertadas[i]) {
                acertadas[i] = true;
                hallazgos++;
            }
        }
        return hallazgos;
    }

    static boolean completa(boolean[] acertadas) {
        for (boolean a : acertadas) {
            if (!a) return false;
        }
        return true;
    }

    public static void main(String[] args) {
        Scanner teclado = new Scanner(System.in);
        String palabra = PALABRAS[new Random().nextInt(PALABRAS.length)];
        boolean[] acertadas = new boolean[palabra.length()];
        StringBuilder usadas = new StringBuilder();
        int fallos = 0;

        System.out.println("=== AHORCADO (tema: programación) ===");

        while (fallos < MAX_FALLOS && !completa(acertadas)) {
            System.out.println("\nPalabra: " + mostrar(palabra, acertadas));
            System.out.println("Fallos: " + fallos + "/" + MAX_FALLOS
                    + "  Usadas: " + usadas);
            System.out.print("Escribe una letra: ");

            if (!teclado.hasNextLine()) break;
            String linea = teclado.nextLine().trim().toLowerCase();
            if (linea.length() != 1 || !Character.isLetter(linea.charAt(0))) {
                System.out.println("Escribe una sola letra.");
                continue;
            }
            char letra = linea.charAt(0);
            if (usadas.indexOf(String.valueOf(letra)) >= 0) {
                System.out.println("Esa letra ya la has probado.");
                continue;
            }
            usadas.append(letra);

            if (probarLetra(palabra, acertadas, letra) == 0) {
                fallos++;
                System.out.println("No está.");
            } else {
                System.out.println("¡Bien!");
            }
        }

        if (completa(acertadas)) {
            System.out.println("\n¡Ganaste! La palabra era: " + palabra);
        } else {
            System.out.println("\nPerdiste. La palabra era: " + palabra);
        }
    }
}

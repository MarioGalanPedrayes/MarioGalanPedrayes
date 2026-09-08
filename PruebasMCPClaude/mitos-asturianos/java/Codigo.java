import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Scanner;

/**
 * Quiz sobre mitos y seres de la mitología asturiana.
 * Juego de consola autocontenido: sin dependencias externas,
 * sin acceso a red ni a ficheros del sistema.
 */
public class Codigo {

    private static final class Pregunta {
        final String enunciado;
        final String[] opciones;
        final int correcta; // índice 0-based

        Pregunta(String enunciado, String[] opciones, int correcta) {
            this.enunciado = enunciado;
            this.opciones = opciones;
            this.correcta = correcta;
        }
    }

    private static List<Pregunta> crearPreguntas() {
        List<Pregunta> preguntas = new ArrayList<>();

        preguntas.add(new Pregunta(
            "¿Cómo se llama el ser protector de los bosques y las minas en la mitología asturiana, "
                + "descrito como un anciano pequeño y peludo?",
            new String[] {"El Nuberu", "El Busgosu", "El Cuélebre", "El Trasgu"},
            1
        ));

        preguntas.add(new Pregunta(
            "El Cuélebre es una gran serpiente alada que, según la leyenda, vigila un tesoro y "
                + "vive muchos años. ¿Qué guardián suele acompañarlo o enfrentarse a él?",
            new String[] {"La Xana", "El Sumiciu", "El Ñuberu", "El Diañu Burlón"},
            0
        ));

        preguntas.add(new Pregunta(
            "¿Qué es una Xana en el folclore asturiano?",
            new String[] {
                "Un gigante de piedra",
                "Un hada que habita en fuentes y ríos",
                "Un espíritu del fuego",
                "Un dragón marino"
            },
            1
        ));

        preguntas.add(new Pregunta(
            "El Trasgu es un duende travieso muy conocido en Asturias. ¿Qué se dice que hay que "
                + "hacer para librarse de sus travesuras en casa?",
            new String[] {
                "Regalarle un gorro rojo",
                "Dejarle miel en la puerta",
                "Barrer al revés o esparcir semillas de mijo para que las cuente",
                "Cantarle una nana"
            },
            2
        ));

        preguntas.add(new Pregunta(
            "¿A qué ser mitológico asturiano se le atribuye el control de las tormentas y el granizo?",
            new String[] {"El Nuberu", "El Busgosu", "La Guaxa", "El Trasgu"},
            0
        ));

        return preguntas;
    }

    private static void barajar(List<Pregunta> preguntas) {
        Collections.shuffle(preguntas);
    }

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        List<Pregunta> preguntas = crearPreguntas();
        barajar(preguntas);

        int aciertos = 0;

        System.out.println("=== Quiz de mitos asturianos ===");
        System.out.println("Responde con el número de la opción correcta.\n");

        for (int i = 0; i < preguntas.size(); i++) {
            Pregunta p = preguntas.get(i);
            System.out.println("Pregunta " + (i + 1) + "/" + preguntas.size() + ": " + p.enunciado);
            for (int j = 0; j < p.opciones.length; j++) {
                System.out.println("  " + (j + 1) + ") " + p.opciones[j]);
            }

            int respuesta = leerOpcion(scanner, p.opciones.length);

            if (respuesta - 1 == p.correcta) {
                System.out.println("¡Correcto!\n");
                aciertos++;
            } else {
                System.out.println("Incorrecto. La respuesta correcta era: "
                    + p.opciones[p.correcta] + "\n");
            }
        }

        System.out.println("=== Resultado final ===");
        System.out.println("Aciertos: " + aciertos + " de " + preguntas.size());
        System.out.println(mensajeFinal(aciertos, preguntas.size()));

        scanner.close();
    }

    private static int leerOpcion(Scanner scanner, int numOpciones) {
        int valor = -1;
        while (valor < 1 || valor > numOpciones) {
            System.out.print("Tu respuesta (1-" + numOpciones + "): ");
            String linea = scanner.nextLine().trim();
            try {
                valor = Integer.parseInt(linea);
            } catch (NumberFormatException e) {
                valor = -1;
            }
            if (valor < 1 || valor > numOpciones) {
                System.out.println("Opción no válida, inténtalo de nuevo.");
            }
        }
        return valor;
    }

    private static String mensajeFinal(int aciertos, int total) {
        double ratio = (double) aciertos / total;
        if (ratio == 1.0) {
            return "¡Excelente! Conoces bien la mitología asturiana.";
        } else if (ratio >= 0.6) {
            return "Buen resultado, pero aún hay mitos por descubrir.";
        } else {
            return "Te vendría bien repasar las leyendas asturianas.";
        }
    }
}

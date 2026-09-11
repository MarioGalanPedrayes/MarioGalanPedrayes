import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;

/**
 * Gestor de tareas (to-do list) de consola.
 * Autocontenido: sin dependencias externas, sin acceso a red ni a
 * ficheros del sistema. Las tareas solo existen mientras el programa
 * está en ejecución.
 */
public class Codigo {

    private static final class Tarea {
        final String descripcion;
        boolean completada;

        Tarea(String descripcion) {
            this.descripcion = descripcion;
            this.completada = false;
        }

        @Override
        public String toString() {
            String marca = completada ? "[x]" : "[ ]";
            return marca + " " + descripcion;
        }
    }

    private final List<Tarea> tareas = new ArrayList<>();
    private final Scanner scanner = new Scanner(System.in);

    public static void main(String[] args) {
        new Codigo().ejecutar();
    }

    private void ejecutar() {
        System.out.println("=== Gestor de tareas ===");
        boolean seguir = true;

        while (seguir) {
            mostrarMenu();
            String opcion = scanner.nextLine().trim();

            switch (opcion) {
                case "1":
                    agregarTarea();
                    break;
                case "2":
                    listarTareas();
                    break;
                case "3":
                    marcarCompletada();
                    break;
                case "4":
                    eliminarTarea();
                    break;
                case "5":
                    seguir = false;
                    System.out.println("¡Hasta luego!");
                    break;
                default:
                    System.out.println("Opción no válida, inténtalo de nuevo.\n");
            }
        }

        scanner.close();
    }

    private void mostrarMenu() {
        System.out.println("\n1) Añadir tarea");
        System.out.println("2) Ver tareas");
        System.out.println("3) Marcar tarea como completada");
        System.out.println("4) Eliminar tarea");
        System.out.println("5) Salir");
        System.out.print("Elige una opción: ");
    }

    private void agregarTarea() {
        System.out.print("Descripción de la tarea: ");
        String descripcion = scanner.nextLine().trim();

        if (descripcion.isEmpty()) {
            System.out.println("La descripción no puede estar vacía.\n");
            return;
        }

        tareas.add(new Tarea(descripcion));
        System.out.println("Tarea añadida.\n");
    }

    private void listarTareas() {
        if (tareas.isEmpty()) {
            System.out.println("No hay tareas todavía.\n");
            return;
        }

        System.out.println("\n--- Tareas ---");
        for (int i = 0; i < tareas.size(); i++) {
            System.out.println((i + 1) + ". " + tareas.get(i));
        }
        System.out.println();
    }

    private void marcarCompletada() {
        listarTareas();
        if (tareas.isEmpty()) {
            return;
        }

        int indice = leerIndiceValido("Número de la tarea a completar: ");
        if (indice == -1) {
            return;
        }

        tareas.get(indice).completada = true;
        System.out.println("Tarea marcada como completada.\n");
    }

    private void eliminarTarea() {
        listarTareas();
        if (tareas.isEmpty()) {
            return;
        }

        int indice = leerIndiceValido("Número de la tarea a eliminar: ");
        if (indice == -1) {
            return;
        }

        Tarea eliminada = tareas.remove(indice);
        System.out.println("Tarea eliminada: " + eliminada.descripcion + "\n");
    }

    private int leerIndiceValido(String mensaje) {
        System.out.print(mensaje);
        String entrada = scanner.nextLine().trim();

        int numero;
        try {
            numero = Integer.parseInt(entrada);
        } catch (NumberFormatException e) {
            System.out.println("Eso no es un número válido.\n");
            return -1;
        }

        int indice = numero - 1;
        if (indice < 0 || indice >= tareas.size()) {
            System.out.println("No existe una tarea con ese número.\n");
            return -1;
        }

        return indice;
    }
}

      *> Demostracion de la estructura de control secuencial:
      *> cada instruccion se ejecuta exactamente una vez, en el orden
      *> en que esta escrita, sin bucles ni condicionales.
      *> Autocontenido: sin ficheros externos ni entrada de usuario.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. CALCULO-SECUENCIAL.

       ENVIRONMENT DIVISION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-PRECIO-UNITARIO     PIC 9(4)V99 VALUE 12.50.
       01 WS-CANTIDAD            PIC 9(3)    VALUE 4.
       01 WS-SUBTOTAL            PIC 9(6)V99 VALUE 0.
       01 WS-PORCENTAJE-IVA      PIC 9V99    VALUE 0.21.
       01 WS-IMPORTE-IVA         PIC 9(6)V99 VALUE 0.
       01 WS-TOTAL               PIC 9(6)V99 VALUE 0.

       PROCEDURE DIVISION.
           DISPLAY "=== Calculo secuencial de un pedido ===".
           DISPLAY " ".

           DISPLAY "Paso 1: Datos de entrada".
           DISPLAY "  Precio unitario: " WS-PRECIO-UNITARIO.
           DISPLAY "  Cantidad:        " WS-CANTIDAD.
           DISPLAY " ".

           DISPLAY "Paso 2: Calcular el subtotal (precio x cantidad)".
           COMPUTE WS-SUBTOTAL = WS-PRECIO-UNITARIO * WS-CANTIDAD.
           DISPLAY "  Subtotal: " WS-SUBTOTAL.
           DISPLAY " ".

           DISPLAY "Paso 3: Calcular el IVA sobre el subtotal".
           COMPUTE WS-IMPORTE-IVA = WS-SUBTOTAL * WS-PORCENTAJE-IVA.
           DISPLAY "  IVA (21%): " WS-IMPORTE-IVA.
           DISPLAY " ".

           DISPLAY "Paso 4: Calcular el total (subtotal + IVA)".
           COMPUTE WS-TOTAL = WS-SUBTOTAL + WS-IMPORTE-IVA.
           DISPLAY "  TOTAL: " WS-TOTAL.
           DISPLAY " ".

           DISPLAY "=== Fin del calculo ===".

           STOP RUN.

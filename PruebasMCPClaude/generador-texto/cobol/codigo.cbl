      *> Generador de texto aleatorio: construye varias "palabras" sin
      *> sentido uniendo letras elegidas al azar, una por una.
      *> Autocontenido: sin ficheros externos ni entrada de usuario.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. GENERADOR-ALEATORIO.

       ENVIRONMENT DIVISION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-FECHA-HORA        PIC X(21).
       01 WS-SEMILLA           PIC 9(8).
       01 WS-ALFABETO          PIC X(26)
                                VALUE "ABCDEFGHIJKLMNOPQRSTUVWXYZ".
       01 WS-RANDOM            PIC 9V9(9).
       01 WS-INDICE-LETRA      PIC 9(2).
       01 WS-PALABRA           PIC X(12).
       01 WS-LONGITUD-PALABRA  PIC 9(2).
       01 WS-NUM-PALABRAS      PIC 9(2) VALUE 8.
       01 WS-CONTADOR-PALABRA  PIC 9(2).
       01 WS-CONTADOR-LETRA    PIC 9(2).

       PROCEDURE DIVISION.
           DISPLAY "=== Generador de texto aleatorio ===".
           DISPLAY " ".

      *>   Semilla distinta en cada ejecucion, tomada de la hora actual.
           MOVE FUNCTION CURRENT-DATE TO WS-FECHA-HORA.
           MOVE WS-FECHA-HORA(9:8) TO WS-SEMILLA.
           COMPUTE WS-RANDOM = FUNCTION RANDOM(WS-SEMILLA).

           PERFORM VARYING WS-CONTADOR-PALABRA FROM 1 BY 1
                   UNTIL WS-CONTADOR-PALABRA > WS-NUM-PALABRAS

               MOVE SPACES TO WS-PALABRA

      *>       Longitud aleatoria de la palabra, entre 3 y 10 letras.
               COMPUTE WS-RANDOM = FUNCTION RANDOM
               COMPUTE WS-LONGITUD-PALABRA =
                   FUNCTION MOD(FUNCTION INTEGER(WS-RANDOM * 1000000), 8)
                   + 3

               PERFORM VARYING WS-CONTADOR-LETRA FROM 1 BY 1
                       UNTIL WS-CONTADOR-LETRA > WS-LONGITUD-PALABRA

      *>           Una letra al azar del alfabeto, unida a la palabra.
                   COMPUTE WS-RANDOM = FUNCTION RANDOM
                   COMPUTE WS-INDICE-LETRA =
                       FUNCTION MOD(FUNCTION INTEGER(WS-RANDOM * 1000000), 26)
                       + 1
                   MOVE WS-ALFABETO(WS-INDICE-LETRA:1)
                       TO WS-PALABRA(WS-CONTADOR-LETRA:1)
               END-PERFORM

               DISPLAY WS-CONTADOR-PALABRA ") " WS-PALABRA
                   "  (" WS-LONGITUD-PALABRA " letras)"
           END-PERFORM.

           DISPLAY " ".
           DISPLAY "=== Fin ===".

           STOP RUN.

// Tres en raya en consola contra el ordenador.
// Practica: arrays, structs de datos simples, funciones, bucles, switch,
// math/rand y lectura de teclado con bufio.
package main

import (
	"bufio"
	"fmt"
	"math/rand"
	"os"
	"strconv"
	"strings"
)

// Tablero de 3x3 en un array de 9 posiciones: ' ' vacío, 'X' jugador, 'O' ordenador.
type Tablero [9]rune

// Las 8 líneas ganadoras (filas, columnas y diagonales).
var lineas = [8][3]int{
	{0, 1, 2}, {3, 4, 5}, {6, 7, 8},
	{0, 3, 6}, {1, 4, 7}, {2, 5, 8},
	{0, 4, 8}, {2, 4, 6},
}

func nuevoTablero() Tablero {
	var t Tablero
	for i := range t {
		t[i] = ' '
	}
	return t
}

func (t Tablero) mostrar() {
	fmt.Println()
	for f := 0; f < 3; f++ {
		fmt.Printf(" %c | %c | %c      %d | %d | %d\n",
			t[f*3], t[f*3+1], t[f*3+2], f*3+1, f*3+2, f*3+3)
		if f < 2 {
			fmt.Println("---+---+---    --+---+--")
		}
	}
	fmt.Println()
}

// ganador devuelve 'X', 'O' o 0 si todavía no ha ganado nadie.
func (t Tablero) ganador() rune {
	for _, l := range lineas {
		if t[l[0]] != ' ' && t[l[0]] == t[l[1]] && t[l[1]] == t[l[2]] {
			return t[l[0]]
		}
	}
	return 0
}

func (t Tablero) lleno() bool {
	for _, c := range t {
		if c == ' ' {
			return false
		}
	}
	return true
}

// jugadaQueCompleta busca una casilla libre que haría ganar a 'ficha'.
func (t Tablero) jugadaQueCompleta(ficha rune) int {
	for i := range t {
		if t[i] != ' ' {
			continue
		}
		t[i] = ficha // t es una copia: no modifica el tablero real
		gana := t.ganador() == ficha
		t[i] = ' '
		if gana {
			return i
		}
	}
	return -1
}

// jugadaOrdenador: 1) ganar si puede, 2) bloquear al jugador, 3) centro, 4) al azar.
func (t Tablero) jugadaOrdenador() int {
	if i := t.jugadaQueCompleta('O'); i >= 0 {
		return i
	}
	if i := t.jugadaQueCompleta('X'); i >= 0 {
		return i
	}
	if t[4] == ' ' {
		return 4
	}
	var libres []int
	for i, c := range t {
		if c == ' ' {
			libres = append(libres, i)
		}
	}
	return libres[rand.Intn(len(libres))]
}

func main() {
	lector := bufio.NewReader(os.Stdin)
	t := nuevoTablero()
	fmt.Println("=== TRES EN RAYA (tú eres X, el ordenador es O) ===")

	for {
		t.mostrar()
		fmt.Print("Tu casilla (1-9): ")
		linea, err := lector.ReadString('\n')
		if err != nil && linea == "" {
			fmt.Println("\nFin de la entrada.")
			return
		}
		n, errNum := strconv.Atoi(strings.TrimSpace(linea))
		if errNum != nil || n < 1 || n > 9 {
			fmt.Println("Escribe un número del 1 al 9.")
			continue
		}
		if t[n-1] != ' ' {
			fmt.Println("Esa casilla ya está ocupada.")
			continue
		}
		t[n-1] = 'X'

		if t.ganador() == 'X' {
			t.mostrar()
			fmt.Println("¡Ganaste!")
			return
		}
		if t.lleno() {
			t.mostrar()
			fmt.Println("Empate.")
			return
		}

		t[t.jugadaOrdenador()] = 'O'
		if t.ganador() == 'O' {
			t.mostrar()
			fmt.Println("Gana el ordenador.")
			return
		}
		if t.lleno() {
			t.mostrar()
			fmt.Println("Empate.")
			return
		}
	}
}

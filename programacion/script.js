function esPrimo(n) {
  if (n < 2) return false;
  for (let i = 2; i * i <= n; i++) {
    if (n % i === 0) return false;
  }
  return true;
}

function comprobarPrimo() {
  const input = document.getElementById("numInput");
  const resultado = document.getElementById("resultadoPrimo");
  const n = parseInt(input.value, 10);

  if (isNaN(n)) {
    resultado.textContent = "Escribe un número válido.";
    return;
  }

  resultado.textContent = esPrimo(n)
    ? `${n} es primo ✅`
    : `${n} no es primo ❌`;
}

function fibonacci(pos) {
  let a = 0, b = 1;
  for (let i = 0; i < pos; i++) {
    [a, b] = [b, a + b];
  }
  return a;
}

function calcularFibonacci() {
  const input = document.getElementById("fibInput");
  const resultado = document.getElementById("resultadoFib");
  const pos = parseInt(input.value, 10);

  if (isNaN(pos) || pos < 0) {
    resultado.textContent = "Escribe una posición válida (0 o más).";
    return;
  }

  resultado.textContent = `Fibonacci(${pos}) = ${fibonacci(pos)}`;
}

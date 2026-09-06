def criba_eratostenes(limite):
    """Devuelve la lista de números primos hasta 'limite' (incluido)."""
    if limite < 2:
        return []

    es_primo = [True] * (limite + 1)
    es_primo[0] = es_primo[1] = False

    i = 2
    while i * i <= limite:
        if es_primo[i]:
            for multiplo in range(i * i, limite + 1, i):
                es_primo[multiplo] = False
        i += 1

    return [n for n, primo in enumerate(es_primo) if primo]


if __name__ == "__main__":
    limite = int(input("Calcular primos hasta: "))
    primos = criba_eratostenes(limite)
    print(f"Hay {len(primos)} numeros primos hasta {limite}:")
    print(primos)

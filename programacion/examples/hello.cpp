#include <iostream>
using namespace std;

bool esPrimo(int n) {
    if (n < 2) return false;
    for (int i = 2; i * i <= n; i++) {
        if (n % i == 0) return false;
    }
    return true;
}

int main() {
    int numero;
    cout << "Introduce un numero: ";
    cin >> numero;

    if (esPrimo(numero))
        cout << numero << " es primo." << endl;
    else
        cout << numero << " no es primo." << endl;

    return 0;
}

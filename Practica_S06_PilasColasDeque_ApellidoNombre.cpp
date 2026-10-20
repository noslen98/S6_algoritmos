// =============================================================
// Practica N.o 06 - ACTIVIDAD 5 (C++17)
// Balanceo con std::stack, BFS con std::queue y benchmark de la STL
// Compilar: g++ -std=c++17 -O2 -Wall -Wextra -o s06 Practica_S06_PilasColasDeque_ApellidoNombre.cpp
// =============================================================
#include <stack>
#include <queue>
#include <deque>
#include <vector>
#include <unordered_set>
#include <chrono>
#include <iostream>
#include <iomanip>
#include <string>
#include <algorithm>
#include <cassert>

using Clock = std::chrono::high_resolution_clock;

double mediana(std::vector<double> v) {
    std::sort(v.begin(), v.end());
    return v[v.size() / 2];
}
double ms_desde(Clock::time_point t0) {
    return std::chrono::duration<double, std::milli>(Clock::now() - t0).count();
}
template <class F>
double medir(F f, int repeticiones) {
    std::vector<double> t;
    for (int r = 0; r < repeticiones; ++r) {
        auto t0 = Clock::now();
        f();
        t.push_back(ms_desde(t0));
    }
    return mediana(t);
}

// ---------- Balanceo de parentesis con std::stack ----------
bool estaBalanceado(const std::string& s) {
    std::stack<char> pila;
    for (char c : s) {
        if (c == '(' || c == '[' || c == '{') {
            pila.push(c);
        } else if (c == ')' || c == ']' || c == '}') {
            if (pila.empty()) return false;
            char tope = pila.top();
            pila.pop();
            if ((c == ')' && tope != '(') ||
                (c == ']' && tope != '[') ||
                (c == '}' && tope != '{')) return false;
        }
    }
    return pila.empty();
}

// ---------- BFS con std::queue ----------
std::vector<int> bfs(const std::vector<std::vector<int>>& g, int inicio,
                     std::vector<int>* niveles = nullptr) {
    int n = static_cast<int>(g.size());
    std::vector<bool> vis(n, false);
    std::vector<int> niv(n, -1);
    std::queue<int> cola;
    std::vector<int> orden;
    vis[inicio] = true;
    niv[inicio] = 0;
    cola.push(inicio);
    while (!cola.empty()) {
        int u = cola.front();
        cola.pop();
        orden.push_back(u);
        for (int v : g[u]) {
            if (!vis[v]) {
                vis[v] = true;
                niv[v] = niv[u] + 1;
                cola.push(v);
            }
        }
    }
    if (niveles) *niveles = niv;
    return orden;
}

// ---------- DFS con std::stack ----------
std::vector<int> dfs(const std::vector<std::vector<int>>& g, int inicio) {
    int n = static_cast<int>(g.size());
    std::vector<bool> vis(n, false);
    std::stack<int> pila;
    std::vector<int> orden;
    pila.push(inicio);
    while (!pila.empty()) {
        int u = pila.top();
        pila.pop();
        if (vis[u]) continue;
        vis[u] = true;
        orden.push_back(u);
        for (auto it = g[u].rbegin(); it != g[u].rend(); ++it) {
            if (!vis[*it]) pila.push(*it);
        }
    }
    return orden;
}

int main() {
    std::cout << std::fixed << std::setprecision(3);

    // ============ 1. Balanceo ============
    assert(estaBalanceado("([{}])") == true);
    assert(estaBalanceado("([)]") == false);
    assert(estaBalanceado("{[()]}") == true);
    assert(estaBalanceado("(((") == false);
    assert(estaBalanceado("") == true);
    assert(estaBalanceado(")(") == false);
    assert(estaBalanceado("a(b[c]{d})e") == true);
    std::cout << "1. BALANCEO CON std::stack: OK (7 casos)\n\n";

    // ============ 2. BFS y DFS sobre la red de ciudades de Puno ============
    const std::vector<std::string> CIUDADES = {
        "Puno", "Juliaca", "Ilave", "Desaguadero", "Yunguyo",
        "Juli", "Lampa", "Azangaro", "Huancane", "Ayaviri"
    };
    const std::vector<std::vector<int>> GRAFO = {
        {1, 2, 5}, {0, 6, 7}, {0, 3, 4}, {2, 4}, {2, 3, 5},
        {0, 4}, {1}, {1, 8, 9}, {7}, {7}
    };
    std::vector<int> niveles;
    auto orden_bfs = bfs(GRAFO, 0, &niveles);
    auto orden_dfs = dfs(GRAFO, 0);

    std::cout << "2. RECORRIDOS DESDE PUNO\n   BFS: ";
    for (int u : orden_bfs) std::cout << CIUDADES[u] << " ";
    std::cout << "\n   DFS: ";
    for (int u : orden_dfs) std::cout << CIUDADES[u] << " ";
    std::cout << "\n   Niveles BFS:\n";
    int maxNivel = *std::max_element(niveles.begin(), niveles.end());
    for (int l = 0; l <= maxNivel; ++l) {
        std::cout << "     Nivel " << l << ": ";
        for (size_t i = 0; i < niveles.size(); ++i)
            if (niveles[i] == l) std::cout << CIUDADES[i] << " ";
        std::cout << "\n";
    }
    // El resultado debe coincidir con el de Python
    assert(orden_bfs.size() == CIUDADES.size());
    assert(orden_bfs[0] == 0 && orden_bfs[1] == 1 && orden_bfs[2] == 2 && orden_bfs[3] == 5);
    assert(orden_dfs[1] == 1 && orden_dfs[9] == 5);
    std::cout << "   Coincide con la implementacion de Python: OK\n\n";

    // ============ 3. Benchmark: N encolados + N desencolados ============
    const int R = 7;
    volatile long long sumidero = 0;
    std::cout << "3. BENCHMARK: N encolados seguidos de N desencolados\n";
    std::cout << "   (mediana de " << R << " repeticiones, -O2)\n\n";
    std::cout << "        N  std::queue  std::deque  vector(erase)  vector(indice)"
                 "   ratio erase/queue\n";

    for (int N : {1000, 5000, 10000, 25000, 50000, 100000}) {
        // std::queue (adaptador sobre std::deque)
        double t_queue = medir([&] {
            std::queue<int> q;
            for (int i = 0; i < N; i++) q.push(i);
            for (int i = 0; i < N; i++) { sumidero += q.front(); q.pop(); }
        }, R);

        // std::deque usada directamente
        double t_deque = medir([&] {
            std::deque<int> dq;
            for (int i = 0; i < N; i++) dq.push_back(i);
            for (int i = 0; i < N; i++) { sumidero += dq.front(); dq.pop_front(); }
        }, R);

        // std::vector como cola: erase(begin) desplaza todo -> O(n) por operacion
        double t_vec_erase = medir([&] {
            std::vector<int> v;
            for (int i = 0; i < N; i++) v.push_back(i);
            for (int i = 0; i < N; i++) { sumidero += v.front(); v.erase(v.begin()); }
        }, R);

        // std::vector usada CORRECTAMENTE como cola: indice de cabeza, sin desplazar
        double t_vec_idx = medir([&] {
            std::vector<int> v;
            v.reserve(N);
            for (int i = 0; i < N; i++) v.push_back(i);
            for (size_t cabeza = 0; cabeza < v.size(); ++cabeza) sumidero += v[cabeza];
        }, R);

        std::cout << std::setw(9) << N
                  << std::setw(12) << t_queue
                  << std::setw(12) << t_deque
                  << std::setw(15) << t_vec_erase
                  << std::setw(16) << t_vec_idx
                  << std::setw(18) << t_vec_erase / t_queue << "x\n";
    }

    // ============ 4. Costo por elemento desplazado ============
    // Permite explicar por que el ratio NO es n/2: cada desplazamiento de
    // erase(begin) es un memmove sobre memoria contigua, mucho mas barato
    // que una operacion completa de push/pop.
    std::cout << "\n4. COSTO UNITARIO (N = 100 000)\n";
    const int N = 100000;
    double t_queue = medir([&] {
        std::queue<int> q;
        for (int i = 0; i < N; i++) q.push(i);
        for (int i = 0; i < N; i++) { sumidero += q.front(); q.pop(); }
    }, R);
    double t_vec_erase = medir([&] {
        std::vector<int> v;
        for (int i = 0; i < N; i++) v.push_back(i);
        for (int i = 0; i < N; i++) { sumidero += v.front(); v.erase(v.begin()); }
    }, R);
    double desplazamientos = 0.5 * double(N) * double(N - 1);   // n(n-1)/2
    std::cout << "   std::queue      : " << t_queue * 1e6 / (2.0 * N)
              << " ns por operacion (2N operaciones)\n";
    std::cout << "   vector(erase)   : " << t_vec_erase * 1e6 / desplazamientos
              << " ns por elemento desplazado (" << desplazamientos
              << " desplazamientos)\n";
    std::cout << "   ratio de costos unitarios: "
              << (t_queue * 1e6 / (2.0 * N)) / (t_vec_erase * 1e6 / desplazamientos)
              << "x a favor del desplazamiento\n";
    std::cout << "   (sumidero = " << sumidero << ")\n";
    return 0;
}

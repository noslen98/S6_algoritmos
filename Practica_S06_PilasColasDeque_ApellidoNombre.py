# =============================================================
# Practica N.o 06 - Pilas, Colas y Deque
# Curso: Algoritmos y Estructuras de Datos (SIS210) - UNAP Puno 2026
#
# Actividad 1: PilaEnlazada y ColaEnlazada desde cero
# Actividad 2: balanceo de parentesis con traza
# Actividad 3: evaluacion postfix y Shunting-Yard
# Actividad 4: BFS (cola) vs DFS (pila) sobre la red de ciudades de Puno
# Actividad 6: calculadora con historial
# Investigacion: Shunting-Yard extendido (funciones, potencia, unarios)
#
# Ejecutar todo:           python3 Practica_S06_PilasColasDeque_ApellidoNombre.py
# Una actividad concreta:  python3 Practica_S06_PilasColasDeque_ApellidoNombre.py 4
# Benchmark de O(1):       python3 Practica_S06_PilasColasDeque_ApellidoNombre.py bench
# =============================================================
import sys
import re
import math
import time
import statistics
from collections import deque
from dataclasses import dataclass
from typing import Optional, Any, Iterator


# =============================================================
# ACTIVIDAD 1 - Pila y Cola enlazadas
# =============================================================
@dataclass
class Nodo:
    """Nodo de la Practica 5: un dato y el enlace al siguiente."""
    dato: Any
    siguiente: 'Optional[Nodo]' = None


class PilaEnlazada:
    """Pila LIFO. El tope es la cabeza de la lista: push y pop son O(1)."""

    def __init__(self):
        self._tope: Optional[Nodo] = None
        self._n: int = 0

    def push(self, dato) -> None:
        nuevo = Nodo(dato)
        nuevo.siguiente = self._tope     # el nuevo nodo apunta al tope actual
        self._tope = nuevo               # y pasa a ser el nuevo tope
        self._n += 1

    def pop(self) -> Any:
        if self.es_vacia():
            raise IndexError('pop desde una pila vacia')
        dato = self._tope.dato
        self._tope = self._tope.siguiente   # el segundo nodo pasa a ser el tope
        self._n -= 1
        return dato

    def peek(self) -> Any:
        if self.es_vacia():
            raise IndexError('Pila vacia')
        return self._tope.dato

    def es_vacia(self) -> bool:
        return self._n == 0

    def __len__(self) -> int:
        return self._n

    def __iter__(self) -> Iterator:
        """Recorre desde el tope hacia la base (sin modificar la pila)."""
        actual = self._tope
        while actual is not None:
            yield actual.dato
            actual = actual.siguiente

    def __repr__(self) -> str:
        return 'tope -> ' + ' | '.join(str(d) for d in self) + ' -> base'


class ColaEnlazada:
    """Cola FIFO. Se saca por la cabeza y se inserta por la cola:
    el puntero _cola es lo que hace que enqueue sea O(1) y no O(n)."""

    def __init__(self):
        self._cabeza: Optional[Nodo] = None
        self._cola: Optional[Nodo] = None    # puntero tail para O(1) al final
        self._n = 0

    def enqueue(self, dato) -> None:
        nuevo = Nodo(dato)
        if self._cola is None:               # cola vacia: cabeza y cola coinciden
            self._cabeza = self._cola = nuevo
        else:
            self._cola.siguiente = nuevo     # O(1) gracias al puntero _cola
            self._cola = nuevo
        self._n += 1

    def dequeue(self) -> Any:
        if self.es_vacia():
            raise IndexError('dequeue desde una cola vacia')
        dato = self._cabeza.dato
        self._cabeza = self._cabeza.siguiente
        if self._cabeza is None:             # la cola quedo vacia
            self._cola = None                # hay que soltar tambien el tail
        self._n -= 1
        return dato

    def frente(self) -> Any:
        if self.es_vacia():
            raise IndexError('Cola vacia')
        return self._cabeza.dato

    def es_vacia(self) -> bool:
        return self._n == 0

    def __len__(self) -> int:
        return self._n

    def __iter__(self) -> Iterator:
        actual = self._cabeza
        while actual is not None:
            yield actual.dato
            actual = actual.siguiente

    def __repr__(self) -> str:
        return 'frente -> ' + ' | '.join(str(d) for d in self) + ' -> final'


# =============================================================
# ACTIVIDAD 2 - Balanceo de parentesis
# =============================================================
PARES = {')': '(', ']': '[', '}': '{'}
APERTURA = '([{'
CIERRE = ')]}'


def esta_balanceado(s: str, verbose: bool = False) -> bool:
    """
    Verifica si la cadena s tiene parentesis, corchetes y llaves
    correctamente anidados. Usa la PilaEnlazada de la Actividad 1.
    Si verbose=True, imprime la traza de la pila en cada paso.
    """
    pila = PilaEnlazada()
    for i, c in enumerate(s):
        if c in APERTURA:
            pila.push(c)
            if verbose:
                print(f'  [{i}] leo {c!r:4} push  -> pila = {_ver_simbolos(pila)}')
        elif c in CIERRE:
            if pila.es_vacia():
                if verbose:
                    print(f'  [{i}] leo {c!r:4} ERROR -> cierre sin apertura previa')
                return False
            if pila.peek() != PARES[c]:
                if verbose:
                    print(f'  [{i}] leo {c!r:4} ERROR -> el tope es {pila.peek()!r}, '
                          f'se esperaba {PARES[c]!r}')
                return False
            pila.pop()
            if verbose:
                print(f'  [{i}] leo {c!r:4} pop   -> pila = {_ver_simbolos(pila)}')
        # cualquier otro caracter se ignora
    balanceado = pila.es_vacia()
    if verbose:
        if balanceado:
            print(f'  fin        pila vacia -> BALANCEADO')
        else:
            print(f'  fin        quedan {len(pila)} sin cerrar {_ver_simbolos(pila)} -> NO BALANCEADO')
    return balanceado


def _ver_simbolos(pila: PilaEnlazada) -> str:
    """Representa la pila de base a tope, que es como se suele dibujar."""
    contenido = list(pila)[::-1]
    return '[' + ' '.join(contenido) + ']' if contenido else '[]'


# =============================================================
# ACTIVIDAD 3 - Postfix y Shunting-Yard
# =============================================================
# NOTA: en el codigo de la guia este diccionario usa la clave ',' en lugar
# de '+', por lo que la suma nunca se reconoce como operador y float('+')
# lanza ValueError. Aqui se corrige.
OPS = {
    '+': lambda a, b: a + b,
    '-': lambda a, b: a - b,
    '*': lambda a, b: a * b,
    '/': lambda a, b: a / b,
}
PRECEDENCIA = {'+': 1, '-': 1, '*': 2, '/': 2}


def es_numero(token: str) -> bool:
    try:
        float(token)
        return True
    except ValueError:
        return False


def evaluar_postfix(expr: str, verbose: bool = False) -> float:
    """Evalua una expresion en notacion postfix (RPN). Tokens separados por espacio."""
    pila = PilaEnlazada()
    for token in expr.split():
        if token in OPS:
            if len(pila) < 2:
                raise ValueError(f'faltan operandos para {token!r}')
            b = pila.pop()                  # b es el SEGUNDO operando
            a = pila.pop()                  # a es el PRIMERO
            resultado = OPS[token](a, b)
            pila.push(resultado)
            if verbose:
                print(f'  token {token!r:6} -> {a} {token} {b} = {resultado:<8g} '
                      f'pila = {_ver_valores(pila)}')
        elif es_numero(token):
            pila.push(float(token))
            if verbose:
                print(f'  token {token!r:6} -> push                 pila = {_ver_valores(pila)}')
        else:
            raise ValueError(f'token no reconocido: {token!r}')
    if len(pila) != 1:
        raise ValueError(f'Expresion invalida: la pila tiene {len(pila)} elementos al final')
    return pila.pop()


def infix_a_postfix(expr: str, verbose: bool = False) -> str:
    """Algoritmo Shunting-Yard: convierte infix con parentesis a postfix."""
    salida = []
    pila = PilaEnlazada()
    for token in expr.split():
        if es_numero(token):
            salida.append(token)
            accion = 'numero -> salida'
        elif token in PRECEDENCIA:
            # se extraen los operadores de precedencia mayor o igual (asociatividad izquierda)
            while (not pila.es_vacia() and pila.peek() in PRECEDENCIA
                   and PRECEDENCIA[pila.peek()] >= PRECEDENCIA[token]):
                salida.append(pila.pop())
            pila.push(token)
            accion = 'operador -> pila'
        elif token == '(':
            pila.push(token)
            accion = 'abre -> pila'
        elif token == ')':
            # se vacia la pila hasta el '(' correspondiente
            while not pila.es_vacia() and pila.peek() != '(':
                salida.append(pila.pop())
            if pila.es_vacia():
                raise ValueError('parentesis desbalanceados: sobra un ")"')
            pila.pop()                      # se descarta el '('
            accion = 'cierra -> vacia hasta ('
        else:
            raise ValueError(f'token no reconocido: {token!r}')
        if verbose:
            print(f'  {token!r:5} {accion:22} pila = {_ver_valores(pila):14} '
                  f'salida = {" ".join(salida)}')
    while not pila.es_vacia():
        tope = pila.pop()
        if tope == '(':
            raise ValueError('parentesis desbalanceados: falta un ")"')
        salida.append(tope)
    if verbose:
        print(f'  {"fin":5} {"vaciar la pila":22} pila = []             '
              f'salida = {" ".join(salida)}')
    return ' '.join(salida)


def _ver_valores(pila: PilaEnlazada) -> str:
    """Representa la pila de base a tope."""
    contenido = list(pila)[::-1]
    return '[' + ' '.join(f'{x:g}' if isinstance(x, float) else str(x)
                          for x in contenido) + ']'


# =============================================================
# ACTIVIDAD 4 - BFS y DFS sobre la red de ciudades de Puno
# =============================================================
# Red vial simplificada de la Region Puno - grafo no dirigido
CIUDADES = {
    0: 'Puno', 1: 'Juliaca', 2: 'Ilave', 3: 'Desaguadero',
    4: 'Yunguyo', 5: 'Juli', 6: 'Lampa', 7: 'Azangaro',
    8: 'Huancane', 9: 'Ayaviri',
}
GRAFO = {
    0: [1, 2, 5], 1: [0, 6, 7], 2: [0, 3, 4], 3: [2, 4], 4: [2, 3, 5],
    5: [0, 4], 6: [1], 7: [1, 8, 9], 8: [7], 9: [7],
}


def bfs(grafo, inicio):
    """BFS con cola - retorna el orden de visita, el nivel y el padre de cada nodo."""
    visitados = {inicio}
    cola = deque([(inicio, 0)])              # (nodo, nivel)
    orden, niveles, padre = [], {}, {inicio: None}
    while cola:
        nodo, nivel = cola.popleft()         # O(1) dequeue
        orden.append(nodo)
        niveles[nodo] = nivel
        for vecino in grafo[nodo]:
            if vecino not in visitados:
                visitados.add(vecino)
                padre[vecino] = nodo
                cola.append((vecino, nivel + 1))   # O(1) enqueue
    return orden, niveles, padre


def bfs_propia(grafo, inicio):
    """Mismo BFS, pero con la ColaEnlazada de la Actividad 1."""
    visitados = {inicio}
    cola = ColaEnlazada()
    cola.enqueue((inicio, 0))
    orden, niveles = [], {}
    while not cola.es_vacia():
        nodo, nivel = cola.dequeue()
        orden.append(nodo)
        niveles[nodo] = nivel
        for vecino in grafo[nodo]:
            if vecino not in visitados:
                visitados.add(vecino)
                cola.enqueue((vecino, nivel + 1))
    return orden, niveles


def dfs(grafo, inicio):
    """DFS con pila - retorna el orden de visita."""
    visitados = set()
    pila = [inicio]
    orden = []
    while pila:
        nodo = pila.pop()
        if nodo not in visitados:
            visitados.add(nodo)
            orden.append(nodo)
            for vecino in reversed(grafo[nodo]):   # reversed para orden consistente
                if vecino not in visitados:
                    pila.append(vecino)
    return orden


def dfs_propia(grafo, inicio):
    """Mismo DFS, pero con la PilaEnlazada de la Actividad 1."""
    visitados = set()
    pila = PilaEnlazada()
    pila.push(inicio)
    orden = []
    while not pila.es_vacia():
        nodo = pila.pop()
        if nodo not in visitados:
            visitados.add(nodo)
            orden.append(nodo)
            for vecino in reversed(grafo[nodo]):
                if vecino not in visitados:
                    pila.push(vecino)
    return orden


def camino(padre, destino):
    """Reconstruye el camino desde el origen hasta 'destino' usando los padres del BFS."""
    ruta = []
    while destino is not None:
        ruta.append(destino)
        destino = padre[destino]
    return ruta[::-1]


# =============================================================
# ACTIVIDAD 6 - Calculadora con historial
# =============================================================
# Un token es: un numero (con decimales), un operador o un parentesis.
TOKEN = re.compile(r'\d+\.?\d*|[+\-*/()]')


def tokenizar(expr: str) -> str:
    """Separa la expresion en tokens, acepte o no espacios en la entrada.
    Devuelve la forma canonica con un espacio entre tokens."""
    tokens = TOKEN.findall(expr)
    reconstruido = ''.join(tokens)
    if reconstruido != re.sub(r'\s+', '', expr):
        sobra = re.sub(r'\s+', '', expr)
        for t in tokens:
            sobra = sobra.replace(t, '', 1)
        raise ValueError(f'caracteres no reconocidos en la expresion: {sobra!r}')
    return ' '.join(tokens)


class CalculadoraConHistorial:
    """
    Mini-calculadora que:
      1) Valida la expresion (parentesis balanceados)
      2) Normaliza la expresion a su forma canonica (clave del historial)
      3) Convierte infix -> postfix (Shunting-Yard)
      4) Evalua el postfix
      5) Almacena en una tabla hash {expresion canonica: resultado}
    """

    def __init__(self, normalizar: bool = True):
        self.historial: dict = {}
        self.normalizar = normalizar
        self.aciertos = 0
        self.fallos = 0

    def _clave(self, expr: str) -> str:
        return tokenizar(expr) if self.normalizar else expr

    def calcular(self, expr: str, verbose: bool = True) -> float:
        # 1. Validar los parentesis con el algoritmo de la Actividad 2
        if not esta_balanceado(expr):
            raise ValueError(f'Parentesis no balanceados: {expr!r}')

        # 2. Normalizar y consultar el historial (tabla hash): O(1) promedio
        clave = self._clave(expr)
        if clave in self.historial:
            self.aciertos += 1
            if verbose:
                print(f'  [cache hit ] {expr!r:22} -> {self.historial[clave]}')
            return self.historial[clave]

        # 3. Convertir y evaluar
        self.fallos += 1
        postfix = infix_a_postfix(clave)
        resultado = evaluar_postfix(postfix)

        # 4. Guardar en el historial
        self.historial[clave] = resultado
        if verbose:
            print(f'  [calculado ] {expr!r:22} -> postfix {postfix!r:18} = {resultado:g}')
        return resultado

    def ver_historial(self):
        print('Historial de calculos:')
        for expr, res in self.historial.items():
            print(f'  {expr!r:28} = {res:g}')
        total = self.aciertos + self.fallos
        print(f'  Aciertos de cache: {self.aciertos}/{total}  '
              f'({100 * self.aciertos / total:.0f}%)')


# =============================================================
# INVESTIGACION - Shunting-Yard extendido
# =============================================================
IZQUIERDA, DERECHA = 'izq', 'der'

# operador -> (precedencia, asociatividad, aridad, funcion)
OPERADORES = {
    '+':  (2, IZQUIERDA, 2, lambda a, b: a + b),
    '-':  (2, IZQUIERDA, 2, lambda a, b: a - b),
    '*':  (3, IZQUIERDA, 2, lambda a, b: a * b),
    '/':  (3, IZQUIERDA, 2, lambda a, b: a / b),
    '%':  (3, IZQUIERDA, 2, lambda a, b: a % b),
    # El menos unario liga MAS flojo que la potencia y MAS fuerte que el producto:
    # -2 ** 2 es -(2**2) = -4, pero -2 * 3 es (-2)*3 = -6. Es la regla de Python.
    'u-': (4, DERECHA,   1, lambda a: -a),          # menos unario
    'u+': (4, DERECHA,   1, lambda a: +a),
    '**': (5, DERECHA,   2, lambda a, b: a ** b),   # asociativo por la DERECHA
}

# funcion -> (aridad, implementacion).  None = aridad variable
FUNCIONES = {
    'sin':  (1, math.sin),
    'cos':  (1, math.cos),
    'tan':  (1, math.tan),
    'sqrt': (1, math.sqrt),
    'log':  (1, math.log),
    'abs':  (1, abs),
    'max':  (None, max),
    'min':  (None, min),
    'pow':  (2, pow),
}

CONSTANTES = {'pi': math.pi, 'e': math.e}

TOKEN_EXT = re.compile(r'''
      \d+\.\d+|\d+          # numero
    | [A-Za-z_]\w*          # identificador: funcion o constante
    | \*\*                  # potencia (antes que '*' para no partirla)
    | [+\-*/%(),]           # operadores, parentesis y separador
''', re.VERBOSE)


def tokenizar_ext(expr: str) -> list:
    """Divide la expresion en tokens y marca los operadores unarios.
    Un '-' o '+' es unario si esta al inicio o despues de '(' , ',' u otro operador."""
    crudos = TOKEN_EXT.findall(expr)
    if ''.join(crudos) != re.sub(r'\s+', '', expr):
        raise ValueError(f'la expresion contiene caracteres no reconocidos: {expr!r}')
    tokens, anterior = [], None
    for t in crudos:
        if t in ('-', '+'):
            # es unario si no hay un operando a su izquierda
            unario = (anterior is None or anterior in OPERADORES
                      or anterior in ('(', ','))
            tokens.append('u' + t if unario else t)
        else:
            tokens.append(t)
        anterior = tokens[-1]
    return tokens


def a_postfix(expr: str, verbose: bool = False) -> list:
    """Shunting-Yard extendido. Devuelve la lista de tokens en notacion postfix."""
    salida, pila = [], PilaEnlazada()
    # cuenta de argumentos pendientes por cada funcion abierta
    args = PilaEnlazada()

    def precede(tope: str, token: str) -> bool:
        """True si hay que extraer 'tope' antes de apilar 'token'."""
        if tope in FUNCIONES:
            return True                       # las funciones ligan mas que cualquier operador
        if tope not in OPERADORES:
            return False                      # es un '(': nunca se extrae aqui
        p_tope, _, _, _ = OPERADORES[tope]
        p_tok, asoc_tok, _, _ = OPERADORES[token]
        if asoc_tok == IZQUIERDA:
            return p_tope >= p_tok            # <- izquierda: tambien con IGUAL precedencia
        return p_tope > p_tok                 # <- derecha: solo con precedencia MAYOR

    for token in tokenizar_ext(expr):
        if re.fullmatch(r'\d+\.?\d*', token):
            salida.append(float(token))
            accion = 'numero -> salida'
        elif token in CONSTANTES:
            salida.append(CONSTANTES[token])
            accion = 'constante -> salida'
        elif token in FUNCIONES:
            pila.push(token)
            accion = 'funcion -> pila'
        elif token == ',':
            while not pila.es_vacia() and pila.peek() != '(':
                salida.append(pila.pop())
            if pila.es_vacia():
                raise ValueError('coma fuera de una llamada a funcion')
            args.push(args.pop() + 1)         # un argumento mas para la funcion abierta
            accion = 'separador de argumentos'
        elif token in OPERADORES:
            # Un operador PREFIJO (unario) no compite por un operando a su
            # izquierda, asi que nunca extrae nada de la pila.
            if OPERADORES[token][2] > 1:
                while not pila.es_vacia() and precede(pila.peek(), token):
                    salida.append(pila.pop())
            pila.push(token)
            aridad_txt = 'unario' if OPERADORES[token][2] == 1 else OPERADORES[token][1]
            accion = f'operador ({aridad_txt}) -> pila'
        elif token == '(':
            pila.push(token)
            args.push(1)                      # al menos un argumento si es una funcion
            accion = 'abre -> pila'
        elif token == ')':
            while not pila.es_vacia() and pila.peek() != '(':
                salida.append(pila.pop())
            if pila.es_vacia():
                raise ValueError('parentesis desbalanceados: sobra un ")"')
            pila.pop()                        # descarta el '('
            n_args = args.pop()
            if not pila.es_vacia() and pila.peek() in FUNCIONES:
                nombre = pila.pop()
                aridad = FUNCIONES[nombre][0]
                if aridad is not None and aridad != n_args:
                    raise ValueError(f'{nombre} espera {aridad} argumento(s), '
                                     f'recibio {n_args}')
                # se anota la aridad real para las funciones variadicas
                salida.append((nombre, n_args))
            accion = 'cierra -> vacia hasta ('
        else:
            raise ValueError(f'token no reconocido: {token!r}')
        if verbose:
            print(f'  {token!r:6} {accion:28} pila={_ver_ext(pila):22} salida={_fmt_ext(salida)}')

    while not pila.es_vacia():
        tope = pila.pop()
        if tope == '(':
            raise ValueError('parentesis desbalanceados: falta un ")"')
        salida.append(tope)
    if verbose:
        print(f'  {"fin":6} {"vaciar la pila":28} pila=[]                   '
              f'salida={_fmt_ext(salida)}')
    return salida


def evaluar(postfix: list) -> float:
    """Evalua la lista postfix producida por a_postfix."""
    pila = PilaEnlazada()
    for token in postfix:
        if isinstance(token, float):
            pila.push(token)
        elif isinstance(token, tuple):                 # llamada a funcion
            nombre, n_args = token
            argumentos = [pila.pop() for _ in range(n_args)][::-1]
            pila.push(float(FUNCIONES[nombre][1](*argumentos)))
        else:                                          # operador
            _, _, aridad, fn = OPERADORES[token]
            operandos = [pila.pop() for _ in range(aridad)][::-1]
            pila.push(float(fn(*operandos)))
    if len(pila) != 1:
        raise ValueError(f'expresion invalida: quedan {len(pila)} valores en la pila')
    return pila.pop()


def calcular(expr: str, verbose: bool = False) -> float:
    return evaluar(a_postfix(expr, verbose))


def _fmt_ext(salida: list) -> str:
    partes = []
    for x in salida:
        if isinstance(x, tuple):
            partes.append(f'{x[0]}/{x[1]}')
        elif isinstance(x, float):
            partes.append(f'{x:g}')
        else:
            partes.append(str(x))
    return ' '.join(partes)


def _ver_ext(pila: PilaEnlazada) -> str:
    return '[' + ' '.join(str(x) for x in list(pila)[::-1]) + ']'


# =============================================================
# Verificacion empirica de que las operaciones son O(1)
# =============================================================
def mediana_ms(funcion, repeticiones=9) -> float:
    funcion()                       # calentamiento: no se mide
    tiempos = []
    for _ in range(repeticiones):
        t0 = time.perf_counter()
        funcion()
        tiempos.append((time.perf_counter() - t0) * 1000)
    return statistics.median(tiempos)


def pila_propia(n):
    p = PilaEnlazada()
    for i in range(n):
        p.push(i)
    for _ in range(n):
        p.pop()


def cola_propia(n):
    c = ColaEnlazada()
    for i in range(n):
        c.enqueue(i)
    for _ in range(n):
        c.dequeue()


def cola_deque(n):
    d = deque()
    for i in range(n):
        d.append(i)
    for _ in range(n):
        d.popleft()


def cola_list_insert0(n):
    """Forma INCORRECTA de usar list como cola: insert(0) es O(n)."""
    l = []
    for i in range(n):
        l.insert(0, i)      # O(n): desplaza todos los elementos
    for _ in range(n):
        l.pop()


def cola_list_pop0(n):
    """Otra forma incorrecta: append + pop(0), tambien O(n) al desencolar."""
    l = []
    for i in range(n):
        l.append(i)
    for _ in range(n):
        l.pop(0)            # O(n): desplaza todos los elementos


# =============================================================
# DEMOSTRACIONES
# =============================================================
def _titulo(t):
    print('\n' + '=' * 62)
    print(t)
    print('=' * 62)


def actividad1():
    _titulo('ACTIVIDAD 1 - PilaEnlazada y ColaEnlazada')
    # --- Pruebas de la guia ---
    p = PilaEnlazada()
    for v in [10, 20, 30]:
        p.push(v)
    assert p.peek() == 30
    assert p.pop() == 30
    assert len(p) == 2

    c = ColaEnlazada()
    for v in [10, 20, 30]:
        c.enqueue(v)
    assert c.frente() == 10
    assert c.dequeue() == 10
    assert len(c) == 2
    print('Pila y Cola: OK')

    # --- Comprobaciones adicionales ---
    p2 = PilaEnlazada()
    for v in [1, 2, 3, 4]:
        p2.push(v)
    print('Pila:', p2)
    print('Orden de salida (LIFO):', [p2.pop() for _ in range(len(p2))])

    c2 = ColaEnlazada()
    for v in [1, 2, 3, 4]:
        c2.enqueue(v)
    print('Cola:', c2)
    print('Orden de salida (FIFO):', [c2.dequeue() for _ in range(len(c2))])

    # La cola debe seguir siendo usable despues de vaciarse
    c2.enqueue(99)
    assert c2.frente() == 99 and len(c2) == 1
    print('Reutilizable tras vaciarse: OK')

    # Errores en estructuras vacias
    for estructura, metodo in [(PilaEnlazada(), 'pop'), (PilaEnlazada(), 'peek'),
                               (ColaEnlazada(), 'dequeue'), (ColaEnlazada(), 'frente')]:
        try:
            getattr(estructura, metodo)()
            print(f'ERROR: {metodo}() no lanzo excepcion')
        except IndexError:
            pass
    print('Excepciones en estructuras vacias: OK')

def actividad2():
    _titulo('ACTIVIDAD 2 - Balanceo de parentesis')
    casos = [
        ('([{}])', True),
        ('([)]', False),
        ('{[()]}', True),
        ('(((', False),
        ('', True),
        (')(', False),                                  # cierre antes de apertura
        ('a(b[c]{d})e', True),                          # con otros caracteres
        ('( 3 + 4 ) * ( 5 - 2 )', True),                # expresion valida
        ('( 3 + 4 ) * ( 5 - 2', False),                 # falta un cierre
    ]
    print(f"{'cadena':25} {'resultado':10} {'esperado':10}")
    todos_ok = True
    for s, esperado in casos:
        resultado = esta_balanceado(s)
        ok = resultado == esperado
        todos_ok = todos_ok and ok
        print(f'{s!r:25} {str(resultado):10} {str(esperado):10} {"OK" if ok else "ERROR"}')
    assert todos_ok, 'algun caso de prueba fallo'
    print('\nTodos los casos de prueba pasaron.')

    print('\nTraza para "([{}])":')
    esta_balanceado('([{}])', verbose=True)

    print('\nTraza para "([)]"  (caso que falla por desorden):')
    esta_balanceado('([)]', verbose=True)

    print('\nTraza para "((("   (caso que falla por falta de cierres):')
    esta_balanceado('(((', verbose=True)

def actividad3():
    _titulo('ACTIVIDAD 3 - Postfix y Shunting-Yard')
    print('--- Evaluacion de expresiones postfix ---')
    expresiones = [
        ('3 4 + 5 *', 35.0),                # (3+4)*5
        ('2 3 4 * +', 14.0),                # 2+(3*4)
        ('5 1 2 + 4 * + 3 -', 14.0),        # 5+((1+2)*4)-3
        ('10 2 /', 5.0),                    # division
        ('7 2 -', 5.0),                     # resta: el orden de operandos importa
    ]
    for expr, esperado in expresiones:
        resultado = evaluar_postfix(expr)
        ok = abs(resultado - esperado) < 1e-9
        print(f'{expr!r:22} = {resultado:<8g} esperado {esperado:<8g} {"OK" if ok else "ERROR"}')
        assert ok, f'fallo en {expr!r}'

    print('\n--- Conversion Shunting-Yard (infix -> postfix) ---')
    infixes = [
        ('3 + 4 * 5', '3 4 5 * +', 23.0),
        ('( 3 + 4 ) * 5', '3 4 + 5 *', 35.0),
        ('2 + 3 * 4 - 1', '2 3 4 * + 1 -', 13.0),
        ('( 1 + 2 ) * ( 3 + 4 )', '1 2 + 3 4 + *', 21.0),
        ('10 - 2 - 3', '10 2 - 3 -', 5.0),   # asociatividad por la izquierda
    ]
    for infix, postfix_esperado, valor_esperado in infixes:
        postfix = infix_a_postfix(infix)
        valor = evaluar_postfix(postfix)
        ok = postfix == postfix_esperado and abs(valor - valor_esperado) < 1e-9
        print(f'{infix!r:24} -> {postfix!r:18} = {valor:<8g} {"OK" if ok else "ERROR"}')
        assert ok, f'fallo en {infix!r}: se obtuvo {postfix!r}'

    print('\nTraza de la conversion de "( 3 + 4 ) * 5":')
    infix_a_postfix('( 3 + 4 ) * 5', verbose=True)

    print('\nTraza de la evaluacion de "3 4 + 5 *":')
    evaluar_postfix('3 4 + 5 *', verbose=True)

    print('\n--- Asociatividad por la izquierda: 10 - 2 - 3 ---')
    print(f'  infix       : 10 - 2 - 3')
    print(f'  postfix     : {infix_a_postfix("10 - 2 - 3")}')
    print(f'  evaluado    : {evaluar_postfix(infix_a_postfix("10 - 2 - 3"))}  '
          f'(es (10-2)-3 = 5, no 10-(2-3) = 11)')

def actividad4():
    _titulo('ACTIVIDAD 4 - BFS vs DFS sobre la red de Puno')
    orden_bfs, niveles, padre = bfs(GRAFO, 0)
    orden_dfs = dfs(GRAFO, 0)

    print('BFS desde Puno (nivel por nivel):')
    for nivel in range(max(niveles.values()) + 1):
        nodos_nivel = [CIUDADES[n] for n, l in niveles.items() if l == nivel]
        print(f'  Nivel {nivel}: {nodos_nivel}')

    print('\nBFS orden:', [CIUDADES[n] for n in orden_bfs])
    print('DFS orden:', [CIUDADES[n] for n in orden_dfs])

    # Las implementaciones propias deben dar exactamente el mismo resultado
    orden_bfs2, niveles2 = bfs_propia(GRAFO, 0)
    orden_dfs2 = dfs_propia(GRAFO, 0)
    assert orden_bfs2 == orden_bfs and niveles2 == niveles
    assert orden_dfs2 == orden_dfs
    print('\nColaEnlazada y PilaEnlazada propias: mismo resultado que deque/list  OK')

    # Propiedad que solo garantiza BFS: el nivel es la distancia minima en aristas
    print('\nDistancia minima desde Puno (en numero de tramos):')
    for n in sorted(niveles, key=lambda x: (niveles[x], x)):
        ruta = ' -> '.join(CIUDADES[c] for c in camino(padre, n))
        print(f'  {CIUDADES[n]:14} nivel {niveles[n]}   {ruta}')

    # Comparacion de las posiciones de visita
    print('\nPosicion de visita de cada ciudad:')
    print(f"  {'ciudad':14} {'BFS':>5} {'DFS':>5} {'nivel':>6}")
    for n in sorted(CIUDADES):
        print(f'  {CIUDADES[n]:14} {orden_bfs.index(n):>5} '
              f'{orden_dfs.index(n):>5} {niveles[n]:>6}')

    # DFS puede alcanzar un nodo cercano por un camino mas largo
    print('\nCaso que ilustra la diferencia:')
    print(f'  Juli esta a 1 tramo de Puno (nivel {niveles[5]}),')
    print(f'  pero DFS lo visita en la posicion {orden_dfs.index(5)} de 10,')
    print(f'  despues de recorrer toda la rama de Ilave.')

def actividad6():
    _titulo('ACTIVIDAD 6 - Calculadora con historial')
    print('--- Calculadora con historial ---')
    calc = CalculadoraConHistorial()
    expresiones = [
        '3 + 4 * 5',
        '( 3 + 4 ) * 5',
        '3 + 4 * 5',            # repetida: debe usar el cache
        '10 / 2 + 3',
        '3+4*5',                # MISMA expresion sin espacios
    ]
    for e in expresiones:
        r = calc.calcular(e)
        print(f'    Resultado: {r:g}')
    print()
    calc.ver_historial()

    # --- Pregunta 4: que pasa sin normalizar ---
    print('\n--- Sin normalizar la clave (comportamiento del codigo de la guia) ---')
    calc_sin = CalculadoraConHistorial(normalizar=False)
    for e in ['2 + 3', '2+3']:
        try:
            r = calc_sin.calcular(e)
            print(f'    Resultado: {r:g}')
        except Exception as ex:
            print(f'  [ERROR     ] {e!r:22} -> {type(ex).__name__}: {ex}')
    print(f'  Claves distintas almacenadas: {list(calc_sin.historial)}')

    print('\n--- Con normalizacion (solucion) ---')
    calc_con = CalculadoraConHistorial(normalizar=True)
    for e in ['2 + 3', '2+3', '2  +  3', ' 2+3 ']:
        r = calc_con.calcular(e)
        print(f'    Resultado: {r:g}')
    print(f'  Claves distintas almacenadas: {list(calc_con.historial)}')
    assert len(calc_con.historial) == 1, 'las cuatro formas deben compartir una sola entrada'
    assert calc_con.aciertos == 3
    print('  Las cuatro escrituras comparten una sola entrada del historial  OK')

    # --- Validacion de entradas incorrectas ---
    print('\n--- Entradas invalidas ---')
    for mala in ['( 3 + 4', '3 + 4 )', '3 $ 4']:
        try:
            calc_con.calcular(mala, verbose=False)
            print(f'  ERROR: {mala!r} no fue rechazada')
        except ValueError as ex:
            print(f'  {mala!r:12} rechazada -> {ex}')

def investigacion():
    _titulo('INVESTIGACION - Shunting-Yard extendido')
    print('--- 1. Asociatividad por la derecha de la potenciacion ---')
    casos_asoc = [
        ('2 ** 3 ** 2', 512.0, '2**(3**2) = 2**9'),
        ('2 ** 2 ** 3', 256.0, '2**(2**3) = 2**8'),
        ('( 2 ** 3 ) ** 2', 64.0, 'con parentesis explicitos'),
        ('2 ** 3 * 2', 16.0, '** liga mas que *'),
        ('2 * 3 ** 2', 18.0, '** liga mas que *'),
    ]
    for expr, esperado, nota in casos_asoc:
        postfix = a_postfix(expr)
        valor = evaluar(postfix)
        ok = abs(valor - esperado) < 1e-9
        print(f'{expr:18} -> {_fmt_ext(postfix):18} = {valor:<10g} {nota:28} '
              f'{"OK" if ok else "ERROR"}')
        assert ok, f'fallo en {expr}'

    print('\n--- 2. Comparacion con la asociatividad por la IZQUIERDA ---')
    print('  Si ** se tratara como asociativo por la izquierda:')
    print('    2 ** 3 ** 2  ->  2 3 ** 2 **  =  (2**3)**2  =  64')
    print('  Con la regla correcta (derecha):')
    print(f'    2 ** 3 ** 2  ->  {_fmt_ext(a_postfix("2 ** 3 ** 2"))}  =  2**(3**2)  =  '
          f'{calcular("2 ** 3 ** 2"):g}')
    print(f'  Python nativo da: {2 ** 3 ** 2}  (coincide)')

    print('\n--- 3. Funciones ---')
    casos_fn = [
        ('sqrt ( 16 )', 4.0),
        ('max ( 3 , 7 )', 7.0),
        ('max ( 3 , 7 , 5 )', 7.0),
        ('min ( 3 , 7 , 5 )', 3.0),
        ('abs ( 0 - 5 )', 5.0),
        ('sqrt ( 9 ) + max ( 1 , 2 )', 5.0),
        ('max ( 2 ** 3 , 3 ** 2 )', 9.0),
        ('pow ( 2 , 10 )', 1024.0),
        ('sqrt ( max ( 9 , 4 ) )', 3.0),
    ]
    for expr, esperado in casos_fn:
        valor = calcular(expr)
        ok = abs(valor - esperado) < 1e-9
        print(f'{expr:28} = {valor:<10g} {"OK" if ok else "ERROR"}')
        assert ok, f'fallo en {expr}'

    print('\n--- 4. Operadores unarios y constantes ---')
    casos_un = [
        ('- 5', -5.0),
        ('- 5 + 3', -2.0),
        ('3 * - 2', -6.0),
        ('- 2 ** 2', -4.0),            # se interpreta como -(2**2), igual que en Python
        ('( - 2 ) ** 2', 4.0),
        ('2 ** - 1', 0.5),             # unario a la derecha de la potencia
        ('- - 5', 5.0),                # doble negacion
        ('max ( - 3 , - 7 )', -3.0),
        ('cos ( 0 )', 1.0),
        ('sin ( 0 )', 0.0),
    ]
    for expr, esperado in casos_un:
        valor = calcular(expr)
        ok = abs(valor - esperado) < 1e-9
        print(f'{expr:22} = {valor:<12g} {"OK" if ok else "ERROR"}')
        assert ok, f'fallo en {expr}'
    print(f'{"pi":22} = {calcular("pi"):<12g} OK')

    print('\n--- 5. Verificacion contra el evaluador de Python ---')
    pruebas = [
        '2 ** 3 ** 2', '3 + 4 * 5', '( 3 + 4 ) * 5', '2 ** 2 ** 3',
        '10 / 4', '7 % 3', '- 2 ** 2', '2 * 3 ** 2 - 1',
        '( 1 + 2 ) ** ( 1 + 1 )', '100 / 5 / 2', '2 ** - 1', '- 2 * 3',
    ]
    for expr in pruebas:
        mio = calcular(expr)
        nativo = float(eval(expr.replace(' ', '')))
        ok = abs(mio - nativo) < 1e-9
        print(f'{expr:24} mio={mio:<12g} python={nativo:<12g} {"OK" if ok else "ERROR"}')
        assert ok, f'discrepancia en {expr}'

    print('\n--- 6. Traza de "2 ** 3 ** 2" ---')
    a_postfix('2 ** 3 ** 2', verbose=True)

    print('\n--- 7. Traza de "max ( 2 , 3 ** 2 ) + 1" ---')
    a_postfix('max ( 2 , 3 ** 2 ) + 1', verbose=True)
    print(f'  resultado = {calcular("max ( 2 , 3 ** 2 ) + 1"):g}')

    print('\n--- 8. Errores detectados ---')
    for mala, motivo in [('sqrt ( 1 , 2 )', 'aridad incorrecta'),
                         ('( 1 + 2', 'falta cerrar'),
                         ('1 + 2 )', 'sobra un cierre'),
                         ('1 , 2', 'coma fuera de funcion'),
                         ('1 $ 2', 'caracter no reconocido')]:
        try:
            calcular(mala)
            print(f'  ERROR: {mala!r} no fue rechazada')
        except ValueError as e:
            print(f'  {mala!r:18} -> {e}')

def benchmark():
    _titulo('BENCHMARK - Verificacion de que las operaciones son O(1)')
    tamanios = [1000, 2000, 5000, 10000, 20000, 40000]
    print('Tiempo total de n encolados seguidos de n desencolados (ms)\n')
    print(f"{'n':>7} {'PilaEnlazada':>14} {'ColaEnlazada':>14} {'deque':>10} "
          f"{'list.insert(0)':>16} {'list.pop(0)':>13}")
    filas = []
    for n in tamanios:
        tp = mediana_ms(lambda: pila_propia(n))
        tc = mediana_ms(lambda: cola_propia(n))
        td = mediana_ms(lambda: cola_deque(n))
        ti = mediana_ms(lambda: cola_list_insert0(n))
        tq = mediana_ms(lambda: cola_list_pop0(n))
        filas.append((n, tp, tc, td, ti, tq))
        print(f'{n:>7} {tp:>14.3f} {tc:>14.3f} {td:>10.3f} {ti:>16.3f} {tq:>13.3f}')

    print('\nCosto POR OPERACION en nanosegundos (tiempo total / 2n)\n')
    print(f"{'n':>7} {'PilaEnlazada':>14} {'ColaEnlazada':>14} {'deque':>10} "
          f"{'list.insert(0)':>16} {'list.pop(0)':>13}")
    for n, tp, tc, td, ti, tq in filas:
        f = 1e6 / (2 * n)
        print(f'{n:>7} {tp * f:>14.0f} {tc * f:>14.0f} {td * f:>10.0f} '
              f'{ti * f:>16.0f} {tq * f:>13.0f}')

    print('\nLas tres primeras columnas se mantienen constantes al crecer n: son O(1).')
    print('Las dos ultimas crecen proporcionalmente a n: son O(n) por operacion.')

    n0, nf = filas[0], filas[-1]
    factor = nf[0] / n0[0]
    print(f'\nAl multiplicar n por {factor:.0f} (de {n0[0]:,} a {nf[0]:,}):')
    for i, nombre in [(2, 'ColaEnlazada'), (3, 'deque'), (4, 'list.insert(0)')]:
        print(f'  {nombre:16} el tiempo total se multiplica por {nf[i] / n0[i]:7.1f}'
              f'   (lineal = {factor:.0f}, cuadratico = {factor ** 2:.0f})')


if __name__ == '__main__':
    opciones = {
        '1': actividad1, '2': actividad2, '3': actividad3,
        '4': actividad4, '6': actividad6,
        'investigacion': investigacion, 'bench': benchmark,
    }
    arg = sys.argv[1] if len(sys.argv) > 1 else 'todo'
    if arg in opciones:
        opciones[arg]()
    elif arg == 'todo':
        for fn in [actividad1, actividad2, actividad3, actividad4,
                   actividad6, investigacion]:
            fn()
        print('\nTODAS LAS ACTIVIDADES PASARON')
        print('Para el benchmark de rendimiento: '
              'python3 Practica_S06_PilasColasDeque_ApellidoNombre.py bench')
    else:
        print(f'Opcion no reconocida: {arg!r}')
        print(f'Use una de: {", ".join(opciones)}  o  todo')

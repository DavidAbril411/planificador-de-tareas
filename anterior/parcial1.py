"""
Parcial 1 - Planificador de tareas y asignacion de recursos.
David Ignacio Abril Perrig - Programacion Eficiente.

    python3 parcial1.py
"""

import cProfile
import heapq
import random
import threading
import time
import timeit
from functools import lru_cache




TAREAS = {
    "A": {"duracion": 2.0, "prioridad": 1, "depende_de": []},
    "B": {"duracion": 1.5, "prioridad": 2, "depende_de": ["A"]},
    "C": {"duracion": 1.0, "prioridad": 1, "depende_de": ["A"]},
    "D": {"duracion": 0.5, "prioridad": 3, "depende_de": ["B", "C"]},
}


def contar_dependencias(tareas):
    return {nombre: len(tareas[nombre]["depende_de"]) for nombre in tareas}


def armar_siguientes(tareas):
    siguientes = {nombre: [] for nombre in tareas}
    for nombre in tareas:
        for anterior in tareas[nombre]["depende_de"]:
            siguientes[anterior].append(nombre)
    return siguientes


def orden_lento(tareas):
    terminadas = set()
    orden = []
    while len(orden) < len(tareas):
        disponibles = [n for n in tareas if n not in terminadas
                       and all(a in terminadas for a in tareas[n]["depende_de"])]
        if not disponibles:
            return None
        elegido = min(disponibles, key=lambda n: (-tareas[n]["prioridad"], n))
        orden.append(elegido)
        terminadas.add(elegido)
    return orden


def orden_rapido(tareas):
    pendientes = contar_dependencias(tareas)
    siguientes = armar_siguientes(tareas)

    listas = [(-tareas[n]["prioridad"], n) for n in tareas if pendientes[n] == 0]
    heapq.heapify(listas)

    orden = []
    while listas:
        _, nombre = heapq.heappop(listas)
        orden.append(nombre)
        for siguiente in siguientes[nombre]:
            pendientes[siguiente] -= 1
            if pendientes[siguiente] == 0:
                heapq.heappush(listas, (-tareas[siguiente]["prioridad"], siguiente))

    if len(orden) < len(tareas):
        return None
    return orden


def niveles(tareas):
    pendientes = contar_dependencias(tareas)
    siguientes = armar_siguientes(tareas)

    actual = sorted(n for n in tareas if pendientes[n] == 0)
    resultado = []

    while actual:
        resultado.append(actual)
        proximo = []
        for nombre in actual:
            for siguiente in siguientes[nombre]:
                pendientes[siguiente] -= 1
                if pendientes[siguiente] == 0:
                    proximo.append(siguiente)
        actual = sorted(proximo)

    return resultado


def duracion_minima(tareas):
    fin = {}
    for nombre in orden_rapido(tareas):
        anteriores = [fin[a] for a in tareas[nombre]["depende_de"]]
        fin[nombre] = max(anteriores, default=0) + tareas[nombre]["duracion"]
    return max(fin.values())


def duracion_total(tareas):
    return sum(tareas[nombre]["duracion"] for nombre in tareas)


def duracion_con_recursos(tareas, recursos=None):
    """
    Calcula la duracion del plan considerando precedencias y limite de recursos.
    - Si recursos es None: equivale al camino critico CPM (recursos infinitos).
    - Si recursos < tareas en paralelo: contencion por recursos (RCPSP).
    """
    if recursos is None:
        return duracion_minima(tareas)

    pendientes = contar_dependencias(tareas)
    siguientes = armar_siguientes(tareas)

    listas = [(-tareas[n]["prioridad"], n) for n in tareas if pendientes[n] == 0]
    heapq.heapify(listas)

    eventos = []
    recursos_libres = recursos
    reloj = 0.0

    while listas or eventos:
        while listas and recursos_libres > 0:
            _, nombre = heapq.heappop(listas)
            recursos_libres -= 1
            heapq.heappush(eventos, (reloj + tareas[nombre]["duracion"], nombre))

        reloj, terminado = heapq.heappop(eventos)
        recursos_libres += 1

        for siguiente in siguientes[terminado]:
            pendientes[siguiente] -= 1
            if pendientes[siguiente] == 0:
                heapq.heappush(listas, (-tareas[siguiente]["prioridad"], siguiente))

    return reloj



def cuando_termina(tareas, nombre):
    anteriores = tareas[nombre]["depende_de"]
    if not anteriores:
        return tareas[nombre]["duracion"]
    return max(cuando_termina(tareas, a) for a in anteriores) + tareas[nombre]["duracion"]


def cuando_termina_memo(tareas, nombre):
    @lru_cache(maxsize=None)
    def resolver(n):
        anteriores = tareas[n]["depende_de"]
        if not anteriores:
            return tareas[n]["duracion"]
        return max(resolver(a) for a in anteriores) + tareas[n]["duracion"]

    return resolver(nombre)



def tareas_encadenadas(cantidad):
    tareas = {}
    for i in range(cantidad):
        if i == 0:
            depende = []
        elif i == 1:
            depende = ["T0"]
        else:
            depende = [f"T{i - 1}", f"T{i - 2}"]
        tareas[f"T{i}"] = {"duracion": 1.0, "prioridad": 1, "depende_de": depende}
    return tareas


planes_guardados = {}


def plan_con_cache(nombre, tareas):
    if nombre in planes_guardados:
        return planes_guardados[nombre]
    planes_guardados[nombre] = niveles(tareas)
    return planes_guardados[nombre]


def trabajar(tareas, nombre):
    time.sleep(tareas[nombre]["duracion"])


def ejecutar_secuencial(tareas):
    inicio = time.time()
    for nombre in orden_rapido(tareas):
        trabajar(tareas, nombre)
    return time.time() - inicio


def ejecutar_concurrente(tareas, recursos):
    inicio = time.time()
    semaforo = threading.Semaphore(recursos)

    def tarea_limitada(nombre):
        with semaforo:
            trabajar(tareas, nombre)

    for nivel in niveles(tareas):
        hilos = []
        for nombre in nivel:
            hilo = threading.Thread(target=tarea_limitada, args=(nombre,))
            hilos.append(hilo)
            hilo.start()
        for hilo in hilos:
            hilo.join()

    return time.time() - inicio



def medir(funcion, *argumentos, repeticiones=1):
    return timeit.timeit(lambda: funcion(*argumentos), number=repeticiones) / repeticiones



def tiempo(segundos):
    if segundos < 0.000001:
        return f"{segundos * 1_000_000_000:.0f} ns"
    if segundos < 0.001:
        return f"{segundos * 1_000_000:.1f} us"
    if segundos < 1:
        return f"{segundos * 1000:.2f} ms"
    return f"{segundos:.3f} s"


def tareas_al_azar(cantidad, dependencias=3):
    random.seed(42)
    tareas = {}
    for i in range(cantidad):
        cuantas = min(i, random.randint(0, dependencias))
        anteriores = random.sample(range(i), cuantas)
        tareas[f"T{i}"] = {
            "duracion": 1.0,
            "prioridad": random.randint(1, 10),
            "depende_de": [f"T{j}" for j in anteriores],
        }
    return tareas


def titulo(texto):
    print()
    print("=" * 70)
    print(texto)
    print("=" * 70)


def mostrar_problema():
    titulo("EL PROBLEMA")
    print("""
            +-- B --+
    A ------+       +--- D
            +-- C --+
""")
    print(f"{'Tarea':<8}{'Duracion':>10}{'Prioridad':>11}{'Depende de':>14}")
    print("-" * 70)
    for nombre in TAREAS:
        depende = ", ".join(TAREAS[nombre]["depende_de"]) or "-"
        print(f"{nombre:<8}{TAREAS[nombre]['duracion']:>9} s"
              f"{TAREAS[nombre]['prioridad']:>11}{depende:>14}")

    print()
    print(f"Orden de ejecucion  : {' -> '.join(orden_rapido(TAREAS))}")
    print(f"Se puede en paralelo: {niveles(TAREAS)}")
    print(f"Duracion (1 recurso): {duracion_con_recursos(TAREAS, 1):.1f} s  (secuencial por falta de recursos)")
    print(f"Duracion (2 rec.)   : {duracion_con_recursos(TAREAS, 2):.1f} s  (concurrente con recursos suficientes)")
    print(f"Duracion minima CPM : {duracion_minima(TAREAS):.1f} s  (camino critico teorico, recursos infinitos)")
    print()
    print("B y C no dependen entre si: con 2 recursos corren a la vez.")
    print("Con 1 solo recurso, una espera a la otra (B tiene prioridad 2 vs C con 1).")
    print("A, B y D si van en cadena: por eso el camino critico minimo son 4 s.")



def punto_1_complejidad():
    titulo("1. ANALIZAR LA COMPLEJIDAD ALGORITMICA")
    print()
    print("n = cantidad de tareas   d = cantidad de dependencias")
    print()
    print(f"{'Funcion':<20}{'Complejidad':<14}{'n=100':>12}{'n=1.000':>14}{'n=10.000':>14}")
    print("-" * 70)

    funciones = [
        ("orden_rapido", "O(n + d)", orden_rapido),
        ("niveles", "O(n + d)", niveles),
        ("duracion_minima", "O(n + d)", duracion_minima),
    ]
    tamanios = [(100, 2000), (1000, 200), (10000, 20)]

    tiempos = {}
    for nombre, complejidad, funcion in funciones:
        tiempos[nombre] = {}
        print(f"{nombre:<20}{complejidad:<14}", end="")
        for cantidad, repeticiones in tamanios:
            tareas = tareas_al_azar(cantidad)
            tiempos[nombre][cantidad] = medir(funcion, tareas, repeticiones=repeticiones)
            print(f"{tiempo(tiempos[nombre][cantidad]):>14}", end="")
        print()

    print("-" * 70)
    crece_1 = tiempos["niveles"][1000] / tiempos["niveles"][100]
    crece_2 = tiempos["niveles"][10000] / tiempos["niveles"][1000]
    print()
    print(f"Al multiplicar las tareas por 10, niveles tarda {crece_1:.0f} veces mas "
          f"y despues {crece_2:.0f} veces mas.")
    print("Crece en proporcion a n: nada que ver con el O(n^2) del proximo punto.")


def punto_2_algoritmo():
    titulo("2. SELECCIONAR EL ALGORITMO MAS ADECUADO")
    print()
    print("Las dos funciones dan el mismo orden porque desempatan igual: siempre")
    print("la tarea de mayor prioridad entre las que ya pueden empezar.")
    print()
    print("  orden_lento  : en cada vuelta recorre TODAS las tareas buscando cuales ya pueden empezar")
    print("  orden_rapido : anota cuantas dependencias le faltan a cada una y solo la vuelve a mirar")
    print("                 cuando ese numero llega a 0")
    print()
    print(f"{'Tareas':>10}{'orden_lento':>16}{'orden_rapido':>16}{'Diferencia':>16}")
    print("-" * 70)

    tamanios = [(250, 15, 1500), (500, 6, 700), (1000, 2, 200), (2000, 1, 80)]
    lentos, rapidos = {}, {}
    for cantidad, reps_lento, reps_rapido in tamanios:
        tareas = tareas_al_azar(cantidad)
        assert orden_lento(tareas) == orden_rapido(tareas)
        lentos[cantidad] = medir(orden_lento, tareas, repeticiones=reps_lento)
        rapidos[cantidad] = medir(orden_rapido, tareas, repeticiones=reps_rapido)
        print(f"{cantidad:>10,}{tiempo(lentos[cantidad]):>16}{tiempo(rapidos[cantidad]):>16}"
              f"{f'{lentos[cantidad] / rapidos[cantidad]:,.0f}x':>16}")

    print("-" * 70)
    crece_lento = lentos[2000] / lentos[1000]
    crece_rapido = rapidos[2000] / rapidos[1000]
    print()
    print(f"Al DUPLICAR las tareas (1.000 -> 2.000), orden_lento tarda "
          f"{crece_lento:.1f} veces mas: es O(n^2).")
    print(f"orden_rapido tarda {crece_rapido:.1f} veces mas: es O(n + d), lineal.")
    print()
    print("Por eso elijo orden_rapido: con muchas mas tareas el otro se vuelve impracticable.")


def punto_3_estructuras():
    titulo("3. ELEGIR ESTRUCTURAS DE DATOS EFICIENTES")
    print()
    print("La pregunta que mas se repite al planificar es '¿esta tarea ya termino?'.")
    print("Segun donde se guarden las terminadas, esa pregunta cuesta distinto.")
    print()
    print(f"{'Terminadas':>12}{'en una lista':>18}{'en un set':>16}{'Diferencia':>16}")
    print("-" * 70)

    for cantidad in (100, 1000, 10000):
        lista = [f"T{i}" for i in range(cantidad)]
        conjunto = set(lista)
        buscado = f"T{cantidad - 1}"
        con_lista = medir(lambda: buscado in lista, repeticiones=1500)
        con_set = medir(lambda: buscado in conjunto, repeticiones=300000)
        print(f"{cantidad:>12,}{tiempo(con_lista):>18}{tiempo(con_set):>16}"
              f"{f'{con_lista / con_set:,.0f}x':>16}")

    print("-" * 70)
    print()
    print("Buscar en una lista recorre elemento por elemento: O(n).")
    print("Buscar en un set va directo por el hash: O(1), no crece con el tamano.")
    print()
    print("Estructuras que usa el planificador y por que:")
    print()
    print("  dict    tareas y cuantas dependencias le faltan a cada una   O(1) por consulta")
    print("  list    que tareas esperan a cada tarea (siguientes)         O(n + d) en total")
    print("  heapq   sacar siempre la tarea de mayor prioridad            O(log n) por operacion")
    print("  set     que tareas ya terminaron, en orden_lento             O(1) por consulta")


def punto_4_memo_y_cache():
    titulo("4. APLICAR MEMOIZACION Y/O CACHING")
    print()
    print("Cuando termina una tarea depende de cuando terminan las dos anteriores:")
    print("T[i] depende de T[i-1] y T[i-2]. Sin memoria, para saber cuando termina")
    print("T[i] hay que recalcular T[i-1] y T[i-2] enteros: es el mismo arbol")
    print("exponencial del Fibonacci recursivo.")
    print()
    print(f"{'Tareas':>10}{'Sin memo':>16}{'Con memo':>16}{'Diferencia':>16}")
    print("-" * 70)

    tamanios = [(15, 2000), (20, 200), (25, 15), (30, 1)]
    sin_memo = {}
    for cantidad, reps in tamanios:
        tareas = tareas_encadenadas(cantidad)
        nombre = f"T{cantidad - 1}"
        sin_memo[cantidad] = medir(cuando_termina, tareas, nombre, repeticiones=reps)
        con_memo = medir(cuando_termina_memo, tareas, nombre, repeticiones=800)
        print(f"{cantidad:>10}{tiempo(sin_memo[cantidad]):>16}{tiempo(con_memo):>16}"
              f"{f'{sin_memo[cantidad] / con_memo:,.0f}x':>16}")

    print("-" * 70)
    crece_memo = sin_memo[30] / sin_memo[25]
    print()
    print(f"Sin memo, agregar 5 tareas multiplica el tiempo por {crece_memo:.0f}: exponencial,")
    print("O(2^n). Con memo (@lru_cache), cada tarea se calcula una sola vez: O(n + d).")
    print()
    print("El mismo problema aparece con el plan completo: si las tareas no cambiaron,")
    print("el plan tampoco, asi que conviene guardarlo con un nombre en vez de recalcularlo.")
    print()
    print(f"{'Tareas':>10}{'Planificar':>16}{'Con cache':>16}{'Diferencia':>16}")
    print("-" * 70)

    for cantidad in (100, 1000, 10000):
        tareas = tareas_al_azar(cantidad)
        planes_guardados.clear()
        sin_cache = medir(niveles, tareas, repeticiones=150)
        plan_con_cache("plan", tareas)
        con_cache = medir(lambda: plan_con_cache("plan", tareas), repeticiones=150000)
        print(f"{cantidad:>10,}{tiempo(sin_cache):>16}{tiempo(con_cache):>16}"
              f"{f'{sin_cache / con_cache:,.0f}x':>16}")

    print("-" * 70)
    print()
    print("La cache solo sirve si las tareas no cambiaron: con otro nombre de plan, o")
    print("con las mismas tareas modificadas, hay que planificar de nuevo igual.")


def punto_5_concurrencia():
    titulo("5. INCORPORAR CONCURRENCIA")
    print()
    print("Las tareas de un mismo nivel no dependen entre si: pueden correr juntas.")
    print("Se prueban tres casos con 12 tareas de 0,03 s cada una.")
    print()

    casos = {}
    casos["en cadena"] = {f"T{i}": {"duracion": 0.03, "prioridad": 1,
                                     "depende_de": [f"T{i - 1}"] if i else []}
                           for i in range(12)}
    casos["como el ejemplo"] = {
        "inicio": {"duracion": 0.03, "prioridad": 1, "depende_de": []},
        **{f"m{i}": {"duracion": 0.03, "prioridad": 1, "depende_de": ["inicio"]}
           for i in range(10)},
        "fin": {"duracion": 0.03, "prioridad": 1, "depende_de": [f"m{i}" for i in range(10)]},
    }
    casos["todas sueltas"] = {f"T{i}": {"duracion": 0.03, "prioridad": 1, "depende_de": []}
                               for i in range(12)}

    print(f"{'Caso':<20}{'Niveles':>9}{'Secuencial':>13}{'1 recurso':>12}"
          f"{'4 recursos':>12}{'8 recursos':>12}")
    print("-" * 70)

    resultados = {}
    for nombre, tareas in casos.items():
        secuencial = ejecutar_secuencial(tareas)
        con_recursos = {r: ejecutar_concurrente(tareas, r) for r in (1, 4, 8)}
        resultados[nombre] = (secuencial, con_recursos)
        print(f"{nombre:<20}{len(niveles(tareas)):>9}{f'{secuencial:.2f} s':>13}", end="")
        for r in (1, 4, 8):
            print(f"{f'{con_recursos[r]:.2f} s':>12}", end="")
        print()

    print("-" * 70)
    print()
    aceleracion_cadena = resultados["en cadena"][0] / resultados["en cadena"][1][8]
    aceleracion_ejemplo = resultados["como el ejemplo"][0] / resultados["como el ejemplo"][1][8]
    aceleracion_sueltas = resultados["todas sueltas"][0] / resultados["todas sueltas"][1][8]
    print(f"Aceleracion con 8 recursos: en cadena {aceleracion_cadena:.1f}x, "
          f"como el ejemplo {aceleracion_ejemplo:.1f}x, todas sueltas {aceleracion_sueltas:.1f}x.")
    print()
    print("En cadena no mejora nada: cada tarea espera a que termine la anterior.")
    print("Todas sueltas es lo que mas mejora: no hay ninguna espera entre ellas.")
    print("Al simular espera de E/S (time.sleep), el modulo threading permite")
    print("concurrencia real liberando el GIL de CPython.")
    return resultados


def punto_6_perfilado():
    titulo("6. PERFILADO DEL CODIGO")
    print()
    print("cProfile.run() mide en que funciones se va el tiempo. Se perfila orden_lento,")
    print("la version O(n^2), con 1.500 tareas:")
    print()

    tareas = tareas_al_azar(1500)
    cProfile.runctx("orden_lento(tareas)", globals(), locals(), sort="tottime")

    print()
    print("Casi todo el tiempo se va adentro de orden_lento, en la comprension de")
    print("lista que arma 'disponibles' en cada vuelta. Confirma lo del punto 2: el")
    print("problema es volver a mirar todas las tareas en cada vuelta.")



def punto_7_justificacion(resultados):
    titulo("7. MEDIR, COMPARAR Y JUSTIFICAR")
    print()
    print(f"{'Que se cambio':<30}{'Antes':>12}{'Despues':>12}{'Mejora':>14}")
    print("-" * 70)

    tareas = tareas_al_azar(2000)
    lento = medir(orden_lento, tareas, repeticiones=1)
    rapido = medir(orden_rapido, tareas, repeticiones=50)
    print(f"{'Algoritmo (2.000 tareas)':<30}{tiempo(lento):>12}{tiempo(rapido):>12}"
          f"{f'{lento / rapido:,.0f}x':>14}")

    lista = [f"T{i}" for i in range(10000)]
    conjunto = set(lista)
    con_lista = medir(lambda: "T9999" in lista, repeticiones=1500)
    con_set = medir(lambda: "T9999" in conjunto, repeticiones=300000)
    print(f"{'Estructura (buscar en 10.000)':<30}{tiempo(con_lista):>12}{tiempo(con_set):>12}"
          f"{f'{con_lista / con_set:,.0f}x':>14}")

    tareas = tareas_al_azar(10000)
    planes_guardados.clear()
    sin_cache = medir(niveles, tareas, repeticiones=100)
    plan_con_cache("plan", tareas)
    con_cache = medir(lambda: plan_con_cache("plan", tareas), repeticiones=100000)
    print(f"{'Cache (10.000 tareas)':<30}{tiempo(sin_cache):>12}{tiempo(con_cache):>12}"
          f"{f'{sin_cache / con_cache:,.0f}x':>14}")

    secuencial, con_recursos = resultados["todas sueltas"]
    print(f"{'Concurrencia (12 sueltas)':<30}{f'{secuencial:.2f} s':>12}"
          f"{f'{con_recursos[8]:.2f} s':>12}{f'{secuencial / con_recursos[8]:.1f}x':>14}")

    print("-" * 70)
    print()
    print("Conclusiones:")
    print()
    print("1. El algoritmo es lo que mas cambia: pasar de O(n^2) a O(n + d) es la")
    print("   diferencia entre terminar rapido y no terminar nunca con muchas tareas.")
    print()
    print("2. La estructura de datos importa tanto como el algoritmo: cambiar una")
    print("   lista por un set en la misma busqueda la vuelve independiente del tamano.")
    print()
    print("3. Memoizar y cachear sirven solo si el resultado se repite: la clave")
    print("   tiene que identificar exactamente el problema, ni mas ni menos.")
    print()
    print("4. La concurrencia mejora solo si hay tareas independientes Y recursos")
    print("   para correrlas: con una sola de las dos cosas, no cambia nada.")


def main():
    mostrar_problema()
    punto_1_complejidad()
    punto_2_algoritmo()
    punto_3_estructuras()
    punto_4_memo_y_cache()
    resultados = punto_5_concurrencia()
    punto_6_perfilado()
    punto_7_justificacion(resultados)


if __name__ == "__main__":
    main()

"""
Parcial 2 - Planificador de tareas y asignación de recursos.
David Ignacio Abril Perrig - Programación Eficiente.

Es el planificador del Parcial 1 con los temas del segundo parcial:
código sin redundancia, paralelismo con multiprocessing, archivos grandes
con buffer y lotes, perfilado, PEP 8, docstrings, tests, documentación y
un framework (Flask, en app.py).

    python3 parcial2.py
"""

import cProfile
import os
import random
import sys
import tempfile
import timeit
from pathlib import Path

import archivos
import paralelo
import planificador as pl

# Copia del Parcial 1 (en anterior/), para comparar antes y después.
sys.path.insert(0, str(Path(__file__).resolve().parent / "anterior"))
# pylint: disable-next=import-error,wrong-import-position,wrong-import-order
import parcial1

ANCHO = 79
CARPETA_REPORTES = Path(__file__).resolve().parent / "reportes"


# ---------------------------------------------------------------------------
#  Utilidades de medición y salida
# ---------------------------------------------------------------------------

def medir(funcion, *argumentos, repeticiones: int = 1) -> float:
    """Segundos promedio de una ejecución de ``funcion(*argumentos)``."""
    total = timeit.timeit(lambda: funcion(*argumentos), number=repeticiones)
    return total / repeticiones


def tiempo(segundos: float) -> str:
    """Muestra un tiempo en la unidad más legible."""
    if segundos < 0.000001:
        return f"{segundos * 1_000_000_000:.0f} ns"
    if segundos < 0.001:
        return f"{segundos * 1_000_000:.1f} us"
    if segundos < 1:
        return f"{segundos * 1000:.2f} ms"
    return f"{segundos:.3f} s"


def titulo(texto: str) -> None:
    """Imprime el encabezado de una sección."""
    print()
    print("=" * ANCHO)
    print(texto)
    print("=" * ANCHO)


def fila(*columnas, anchos=(30, 15, 15, 15)) -> None:
    """Imprime una fila de tabla: la primera columna a la izquierda."""
    texto = f"{columnas[0]:<{anchos[0]}}"
    for columna, ancho in zip(columnas[1:], anchos[1:]):
        texto += f"{columna:>{ancho}}"
    print(texto)


def tareas_al_azar(cantidad: int, dependencias: int = 3) -> pl.Tareas:
    """Genera ``cantidad`` tareas con hasta ``dependencias`` anteriores."""
    random.seed(42)
    tareas: pl.Tareas = {}
    for i in range(cantidad):
        cuantas = min(i, random.randint(0, dependencias))
        anteriores = random.sample(range(i), cuantas)
        tareas[f"T{i}"] = {
            "duracion": 1.0,
            "prioridad": random.randint(1, 10),
            "depende_de": [f"T{j}" for j in anteriores],
        }
    return tareas


def tareas_iguales(cantidad: int, duracion: float, en_cadena: bool):
    """Tareas de igual duración, todas sueltas o cada una detrás de otra."""
    return {f"T{i}": {"duracion": duracion, "prioridad": 1,
                      "depende_de": [f"T{i - 1}"] if en_cadena and i else []}
            for i in range(cantidad)}


# ---------------------------------------------------------------------------
#  Secciones
# ---------------------------------------------------------------------------

def mostrar_problema() -> None:
    """Las tareas del enunciado y lo que contesta el planificador."""
    titulo("EL PROBLEMA")
    print("""
            +-- B --+
    A ------+       +--- D
            +-- C --+
""")
    tareas = pl.TAREAS_EJEMPLO
    print(f"Orden de ejecucion  : {' -> '.join(pl.orden_rapido(tareas))}")
    print(f"Niveles paralelos   : {pl.niveles(tareas)}")
    print(f"Con 1 recurso       : {pl.duracion_con_recursos(tareas, 1):.1f} s")
    print(f"Con 2 recursos      : {pl.duracion_con_recursos(tareas, 2):.1f} s")
    print(f"Camino critico      : {pl.duracion_minima(tareas):.1f} s")


def punto_1_parcial_1() -> None:
    """Las mejoras del Parcial 1, medidas sobre el código nuevo."""
    titulo("1. LO DEL PARCIAL 1, CON EL CODIGO REFACTORIZADO")
    print()
    print("Complejidad, algoritmo, estructuras y memoizacion, medidos de")
    print("nuevo sobre planificador.py:")
    print()
    fila("Que se compara", "Antes", "Despues", "Mejora")
    print("-" * ANCHO)

    tareas = tareas_al_azar(2000)
    lento = medir(pl.orden_lento, tareas)
    rapido = medir(pl.orden_rapido, tareas, repeticiones=50)
    fila("Algoritmo O(n^2) -> O(n+d)", tiempo(lento), tiempo(rapido),
         f"{lento / rapido:,.0f}x")

    lista = [f"T{i}" for i in range(10_000)]
    conjunto = set(lista)
    en_lista = medir(lambda: "T9999" in lista, repeticiones=1500)
    en_set = medir(lambda: "T9999" in conjunto, repeticiones=300_000)
    fila("Buscar: list -> set", tiempo(en_lista), tiempo(en_set),
         f"{en_lista / en_set:,.0f}x")

    cadena = {f"T{i}": {"duracion": 1.0, "prioridad": 1,
                        "depende_de": [f"T{j}" for j in (i - 1, i - 2)
                                       if j >= 0]}
              for i in range(25)}
    sin_memo = medir(pl.cuando_termina, cadena, "T24", repeticiones=3)
    con_memo = medir(pl.cuando_termina_memo, cadena, "T24", repeticiones=500)
    fila("Memoizacion (25 tareas)", tiempo(sin_memo), tiempo(con_memo),
         f"{sin_memo / con_memo:,.0f}x")


def punto_2_codigo_redundante() -> None:
    """Compara el Parcial 1 con la versión sin código repetido."""
    titulo("2. ELIMINAR CODIGO REDUNDANTE")
    print("""
En el Parcial 1, orden_rapido, niveles y duracion_con_recursos repetian
las mismas dos tareas:

  * armar 'pendientes' y 'siguientes'      -> preparar_grafo()
  * restar una dependencia a las que        -> liberar_siguientes()
    esperaban y ver cuales quedaban libres
  * la clave (-prioridad, nombre) del heap  -> clave_de_prioridad()

Refactorizar no tiene que cambiar el resultado ni empeorar el tiempo:
""")
    fila("Funcion (10.000 tareas)", "Parcial 1", "Parcial 2", "Igual?")
    print("-" * ANCHO)
    tareas = tareas_al_azar(10_000)
    comparaciones = [
        ("orden_rapido", parcial1.orden_rapido, pl.orden_rapido),
        ("niveles", parcial1.niveles, pl.niveles),
        ("duracion_con_recursos(4)",
         lambda t: parcial1.duracion_con_recursos(t, 4),
         lambda t: pl.duracion_con_recursos(t, 4)),
    ]
    for nombre, antes, despues in comparaciones:
        igual = antes(tareas) == despues(tareas)
        fila(nombre, tiempo(medir(antes, tareas, repeticiones=20)),
             tiempo(medir(despues, tareas, repeticiones=20)),
             "si" if igual else "NO")
    print()
    print("Mismo resultado. La version refactorizada es algo mas lenta (una")
    print("llamada a funcion mas por tarea), pero sigue siendo O(n + d):")
    print("con 10.000 tareas son un par de milisegundos. A cambio, cada regla")
    print("esta en un solo lugar y un cambio se hace una vez y no tres. Es el")
    print("criterio de evitar la optimizacion prematura: primero claro y")
    print("correcto, y optimizar solo lo que el perfilado marca como critico.")


def punto_3_paralelismo() -> None:
    """Ejecuta las tareas en varios procesos con multiprocessing."""
    titulo("3. PARALELISMO CON MULTIPROCESSING")
    print("""
En el Parcial 1 las tareas esperaban con time.sleep (E/S) y alcanzaba con
hilos. Ahora cada tarea cuenta numeros primos: trabajo de CPU. Los hilos
no sirven para eso por el GIL. Con multiprocessing hay un proceso por
nucleo y una Queue (productor y consumidor): apenas termina una tarea,
sus siguientes van a la cola y las toma un proceso libre.
""")
    print(f"Nucleos de esta maquina: {os.cpu_count()}")
    print()
    casos = {
        "8 en cadena": tareas_iguales(8, 0.25, en_cadena=True),
        "8 sueltas": tareas_iguales(8, 0.25, en_cadena=False),
    }
    print("8 tareas de 0,25 s de CPU cada una. 1 proceso = sin paralelismo.")
    print()
    print(f"{'Caso':<16}{'1 proceso':>12}{'2 procesos':>12}"
          f"{'4 procesos':>12}{'8 procesos':>12}")
    print("-" * ANCHO)
    for nombre, tareas in casos.items():
        texto = f"{nombre:<16}"
        for procesos in (1, 2, 4, 8):
            segundos = paralelo.tiempo_total(tareas, procesos)
            texto += f"{tiempo(segundos):>12}"
        print(texto)
    print()
    print("En cadena no mejora: cada tarea espera a la anterior aunque sobren")
    print("procesos. Sueltas, el tiempo baja casi en proporcion a los")
    print("procesos, hasta llegar a los nucleos rapidos de la maquina.")


def punto_4_archivos_grandes() -> None:
    """Buffer, lotes y paralelo con un archivo de un millón de tareas."""
    titulo("4. ESCRITURA Y LECTURA DE ARCHIVOS GRANDES")
    cantidad = 1_000_000
    tareas = tareas_al_azar(cantidad)
    ruta = os.path.join(tempfile.gettempdir(), "tareas_parcial2.txt")

    print()
    print(f"Se guardan {cantidad:,} tareas, una por linea.")
    print()
    fila("Escritura", "Tiempo", "", "", anchos=(40, 15, 1, 1))
    print("-" * ANCHO)
    linea_por_linea = archivos.escribir_linea_por_linea(ruta, tareas)
    por_lotes = archivos.escribir_por_lotes(ruta, tareas)
    fila("Linea por linea (buffering=1)", tiempo(linea_por_linea), "", "",
         anchos=(40, 15, 1, 1))
    fila("Lotes de 10.000 + buffer de 1 MB", tiempo(por_lotes), "", "",
         anchos=(40, 15, 1, 1))
    tamanio = os.path.getsize(ruta) / 1024 / 1024
    print()
    print(f"El buffer es {linea_por_linea / por_lotes:.1f} veces mas rapido. "
          f"Archivo: {tamanio:.1f} MB.")

    print()
    fila("Lectura en lotes de 10.000", "Tiempo", "Igual?", "",
         anchos=(40, 15, 10, 1))
    print("-" * ANCHO)
    esperado = None
    for procesos in (None, 2, 4, 8):
        inicio = timeit.default_timer()
        if procesos is None:
            resumen = archivos.procesar_secuencial(ruta)
            nombre = "Secuencial"
        else:
            resumen = archivos.procesar_en_paralelo(ruta, procesos)
            nombre = f"En paralelo, {procesos} procesos"
        segundos = timeit.default_timer() - inicio
        esperado = esperado or resumen
        fila(nombre, tiempo(segundos), "si" if resumen == esperado else "NO",
             "", anchos=(40, 15, 10, 1))
    os.remove(ruta)
    print()
    print(f"Resumen: {esperado}")
    print()
    print("Leer por lotes mantiene en memoria un lote y no el archivo entero.")
    print("En paralelo, este proceso lee el archivo y pone los lotes en una")
    print("Queue; los otros los procesan (productor y consumidor). Mejora")
    print("hasta unos 4 procesos; despues manda la lectura, que es una sola.")


def punto_5_perfilado() -> None:
    """Perfila orden_lento con cProfile y guarda el archivo para SnakeViz."""
    titulo("5. PERFILADO: CPROFILE + SNAKEVIZ")
    CARPETA_REPORTES.mkdir(exist_ok=True)
    salida = CARPETA_REPORTES / "orden_lento.prof"
    tareas = tareas_al_azar(1500)
    # Como en el Parcial 1: cProfile ordenado por tiempo propio, y además se
    # guarda en un archivo para verlo con SnakeViz.
    cProfile.runctx("pl.orden_lento(tareas)", globals(), {"tareas": tareas},
                    filename=str(salida))
    print()
    print(f"Perfil guardado en reportes/{salida.name}. Para verlo:")
    print(f"    snakeviz reportes/{salida.name}")
    print()
    cProfile.runctx("pl.orden_lento(tareas)", globals(), {"tareas": tareas},
                    sort="tottime")
    print("Igual que en el Parcial 1, el tiempo se va en la comprension de")
    print("lista de orden_lento. Scalene lo confirma linea por linea:")
    print("    scalene run --cpu-only perfilar.py  (reportes/scalene.txt)")


def main() -> None:
    """Ejecuta todas las secciones en orden."""
    mostrar_problema()
    punto_1_parcial_1()
    punto_2_codigo_redundante()
    punto_3_paralelismo()
    punto_4_archivos_grandes()
    punto_5_perfilado()


if __name__ == "__main__":
    main()

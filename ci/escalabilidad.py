"""
Evaluación de eficiencia y Performance Gate.

Mide los algoritmos principales con entradas de distinto tamaño y relaciona
el crecimiento con la complejidad teórica:

* ``orden_rapido`` es O(n + d) más el log del heap: si la entrada se
  multiplica por 10, el tiempo debería crecer unas 10 a 13 veces.
* ``orden_lento`` es O(n²): por 10 de entrada, unas 100 veces de tiempo.

Performance Gate: ordenar 100.000 tareas tiene que tardar menos de
``LIMITE_SEGUNDOS``. Si no, imprime ``Performance Gate FAILED`` y falla.
"""

import json
import os
import statistics
import sys
import time
import tracemalloc

import optimizaciones
import planificador as pl

TAMANIOS = (1_000, 10_000, 100_000)
TAMANIOS_LENTO = (250, 500, 1_000, 2_000)
REPETICIONES = 5
GATE_TAMANIO = 100_000
LIMITE_SEGUNDOS = 1.0


def mediana(funcion, *argumentos, repeticiones=REPETICIONES):
    """Mediana de varias corridas: no se deja llevar por una corrida rara."""
    tiempos = []
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        funcion(*argumentos)
        tiempos.append(time.perf_counter() - inicio)
    return statistics.median(tiempos)


def memoria_mb(funcion, *argumentos):
    """Memoria máxima, en MB, durante una llamada."""
    tracemalloc.start()
    funcion(*argumentos)
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return pico / 1024 / 1024


def medir_serie(funcion, tamanios, repeticiones=REPETICIONES):
    """Tiempo y memoria para cada tamaño, y cuánto creció contra el anterior."""
    filas = []
    for tamanio in tamanios:
        tareas = optimizaciones.tareas_de_prueba(tamanio)
        segundos = mediana(funcion, tareas, repeticiones=repeticiones)
        anterior = filas[-1] if filas else None
        filas.append({
            "tareas": tamanio,
            "segundos": segundos,
            "memoria_mb": memoria_mb(funcion, tareas),
            "crecimiento": segundos / anterior["segundos"] if anterior else None,
        })
    return filas


def tabla(titulo, filas, esperado):
    """La tabla en Markdown, para la consola y el resumen de GitHub."""
    lineas = [f"### {titulo}", "",
              "| Tareas | Tiempo (mediana) | Memoria | Crecimiento |",
              "|---:|---:|---:|---:|"]
    for fila in filas:
        crecimiento = (f"{fila['crecimiento']:.1f}x"
                       if fila["crecimiento"] else "—")
        lineas.append(f"| {fila['tareas']:,} | {fila['segundos']:.4f} s "
                      f"| {fila['memoria_mb']:.1f} MB | {crecimiento} |")
    lineas += ["", f"Esperado: {esperado}", ""]
    return "\n".join(lineas)


def escribir_resumen(texto):
    """Agrega el texto al resumen de la corrida en GitHub Actions."""
    ruta = os.environ.get("GITHUB_STEP_SUMMARY")
    if ruta:
        with open(ruta, "a", encoding="utf-8") as resumen:
            resumen.write(texto + "\n")


def main():
    """Mide, escribe los reportes y aplica el Performance Gate."""
    rapido = medir_serie(pl.orden_rapido, TAMANIOS)
    cronograma = medir_serie(lambda t: pl.cronograma(t, 4), TAMANIOS)
    lento = medir_serie(pl.orden_lento, TAMANIOS_LENTO, repeticiones=1)

    gate = next(f for f in rapido if f["tareas"] == GATE_TAMANIO)
    aprobado = gate["segundos"] < LIMITE_SEGUNDOS
    veredicto = (
        f"Performance Gate {'PASSED' if aprobado else 'FAILED'}: "
        f"orden_rapido con {GATE_TAMANIO:,} tareas tardó "
        f"{gate['segundos']:.3f} s (límite {LIMITE_SEGUNDOS} s)")

    texto = "\n".join([
        "## Evaluación de eficiencia", "",
        tabla("orden_rapido · O(n + d)", rapido,
              "por 10 de entrada, ~10 a 13 veces (lineal más el log del "
              "heap). Con 100.000 tareas crece más porque las estructuras ya "
              "no entran en la caché del procesador y las dependencias al "
              "azar obligan a ir a la RAM: con dependencias consecutivas, "
              "el mismo salto crece 14 veces."),
        tabla("cronograma con 4 recursos · O((n + d) log n)", cronograma,
              "por 10 de entrada, algo más de 10 veces."),
        tabla("orden_lento · O(n²), solo para comparar", lento,
              "por 2 de entrada, ~4 veces de tiempo (cuadrático)."),
        f"**{veredicto}**"])
    print(texto)
    escribir_resumen(texto)

    os.makedirs("reportes", exist_ok=True)
    with open("reportes/escalabilidad.json", "w", encoding="utf-8") as salida:
        json.dump({"orden_rapido": rapido, "cronograma": cronograma,
                   "orden_lento": lento, "gate_aprobado": aprobado,
                   "limite_segundos": LIMITE_SEGUNDOS}, salida, indent=2)
    if not aprobado:
        sys.exit(1)


if __name__ == "__main__":
    main()

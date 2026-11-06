"""
Consumo de memoria: rechaza si leer por lotes supera el límite.

Leer de a lotes tiene que usar mucho menos que leer el archivo entero.
"""

import json
import os
import sys
import tempfile
import tracemalloc

import archivos
import optimizaciones

LIMITE_MB = 5


def pico_de(funcion, *argumentos):
    """Memoria máxima, en MB, durante una llamada."""
    tracemalloc.start()
    funcion(*argumentos)
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return pico / 1024 / 1024


def leer_todo(ruta):
    """La forma sin lotes, para comparar."""
    with open(ruta, encoding="utf-8") as archivo:
        return archivo.readlines()


if __name__ == "__main__":
    ruta = os.path.join(tempfile.gettempdir(), "memoria_ci.txt")
    archivos.escribir_por_lotes(ruta, optimizaciones.tareas_de_prueba(200_000))
    por_lotes = pico_de(archivos.procesar_secuencial, ruta)
    entero = pico_de(leer_todo, ruta)
    os.remove(ruta)
    print(f"por lotes {por_lotes:.1f} MB · archivo entero {entero:.1f} MB")
    with open("reportes/memoria.json", "w", encoding="utf-8") as salida:
        json.dump({"por_lotes_mb": por_lotes, "entero_mb": entero,
                   "limite_mb": LIMITE_MB}, salida, indent=2)
    if por_lotes > LIMITE_MB:
        sys.exit(f"RECHAZADO: {por_lotes:.1f} MB supera {LIMITE_MB} MB")

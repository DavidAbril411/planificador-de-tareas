"""
Interfaz web del planificador, con Flask (http://127.0.0.1:5050).

Si existe ELASTIC_APM_SERVER_URL, Elastic APM mide cada pedido a la web.
"""

import os
from functools import lru_cache

from flask import Flask, render_template, request

import ia
import optimizaciones
import paralelo
import planificador as pl

app = Flask(__name__)

if os.environ.get("ELASTIC_APM_SERVER_URL"):
    from elasticapm.contrib.flask import ElasticAPM
    app.config["ELASTIC_APM"] = {"SERVICE_NAME": "planificador-de-tareas",
                                 "ENVIRONMENT": "parcial2"}
    ElasticAPM(app)


def validar(tareas: pl.Tareas) -> str:
    """Devuelve un mensaje de error, o un texto vacío si las tareas sirven."""
    if not tareas:
        return "Cargá al menos una tarea."
    for nombre, tarea in tareas.items():
        if tarea["duracion"] > 5:
            return f"{nombre} dura más de 5 s: para la demo, usá menos."
        for anterior in tarea["depende_de"]:
            if anterior not in tareas:
                return f"{nombre} depende de {anterior}, que no existe."
    if pl.orden_rapido(tareas) is None:
        return "Hay un ciclo: ninguna tarea del ciclo puede empezar."
    return ""


@app.route("/")
def home():
    """La página con la interfaz."""
    return render_template("index.html")


@app.route("/plan", methods=["POST"])
def plan():
    """Lo que calcula el planificador, sin ejecutar nada."""
    datos = request.get_json()
    tareas, procesos = datos["tareas"], datos["procesos"]
    error = validar(tareas)
    if error:
        return {"error": error}
    return {
        "orden": pl.orden_rapido(tareas),
        "cronograma": pl.cronograma(tareas, procesos),
        "duracion": pl.duracion_con_recursos(tareas, procesos),
        "duracion_1_proceso": pl.duracion_con_recursos(tareas, 1),
    }


@app.route("/ejecutar", methods=["POST"])
def ejecutar():
    """Ejecuta las tareas de verdad y devuelve cuándo corrió cada una."""
    datos = request.get_json()
    tareas, procesos = datos["tareas"], datos["procesos"]
    error = validar(tareas)
    if error:
        return {"error": error}
    registro = paralelo.ejecutar(tareas, procesos)
    total = max(fin for _, fin, _ in registro.values())
    return {"registro": registro, "total": total}


@app.route("/pasos")
def pasos():
    """Los pasos del planificador y la optimización de cada uno."""
    campos = ("clave", "paso", "nombre", "biblioteca", "sin", "con")
    return [{campo: paso[campo] for campo in campos}
            for paso in optimizaciones.PASOS]


@app.route("/medir", methods=["POST"])
def medir():
    """Mide un paso del planificador con o sin su optimización."""
    datos = request.get_json()
    segundos = optimizaciones.medir_paso(datos["clave"], datos["con"])
    return {"segundos": segundos}


@app.route("/estimar", methods=["POST"])
def estimar():
    """Duración estimada de una tarea de producción, con y sin IA."""
    tarea = request.get_json()
    if (tarea.get("tipo") not in ia.TIPOS
            or tarea.get("maquina") not in ia.MAQUINAS):
        return {"error": "Tipo o máquina desconocidos."}
    if int(tarea.get("cantidad", 0)) < 1 or int(tarea.get("operarios", 0)) < 1:
        return {"error": "Unidades y operarios tienen que ser al menos 1."}
    return ia.estimar(tarea)


@app.route("/ia/comparacion")
def comparacion_ia():
    """Error, tiempo y memoria de los dos estimadores (se mide una vez)."""
    return comparacion_guardada()


@lru_cache(maxsize=1)
def comparacion_guardada() -> dict:
    """La comparación se calcula la primera vez y después se reutiliza."""
    return ia.comparar_estimadores()


if __name__ == "__main__":
    print("Preparando datos de prueba...")
    for cantidad in (2000, 5000, 200_000):
        optimizaciones.tareas_de_prueba(cantidad)
    # tracemalloc mide todo el proceso: se mide la IA antes de atender
    # pedidos, para que no se sume la memoria de otros pedidos simultáneos.
    comparacion_guardada()
    print("Abrí http://127.0.0.1:5050 en el navegador")
    app.run(port=5050)

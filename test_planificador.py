"""
Tests del planificador con unittest.

    python3 -m unittest -v
"""

import doctest
import os
import tempfile
import unittest

import app
import archivos
import optimizaciones
import paralelo
import planificador as pl

CICLO = {
    "X": {"duracion": 1.0, "prioridad": 1, "depende_de": ["Y"]},
    "Y": {"duracion": 1.0, "prioridad": 1, "depende_de": ["X"]},
}


class TestOrden(unittest.TestCase):
    """El orden de ejecución respeta dependencias y prioridades."""

    def test_ejemplo_del_enunciado(self):
        """El orden de las tareas A, B, C y D del enunciado."""
        self.assertEqual(pl.orden_rapido(pl.TAREAS_EJEMPLO),
                         ["A", "B", "C", "D"])

    def test_lento_y_rapido_dan_lo_mismo(self):
        """Los dos algoritmos dan el mismo orden."""
        self.assertEqual(pl.orden_lento(pl.TAREAS_EJEMPLO),
                         pl.orden_rapido(pl.TAREAS_EJEMPLO))

    def test_ninguna_tarea_antes_que_sus_dependencias(self):
        """Cada tarea va después de las que necesita."""
        orden = pl.orden_rapido(pl.TAREAS_EJEMPLO)
        for nombre, tarea in pl.TAREAS_EJEMPLO.items():
            for anterior in tarea["depende_de"]:
                self.assertLess(orden.index(anterior), orden.index(nombre))

    def test_ciclo_devuelve_none(self):
        """Con un ciclo no hay orden posible."""
        self.assertIsNone(pl.orden_rapido(CICLO))
        self.assertIsNone(pl.orden_lento(CICLO))


class TestDuracion(unittest.TestCase):
    """La duración depende de los recursos disponibles."""

    def test_camino_critico(self):
        """A, B y D en cadena suman 4 segundos."""
        self.assertEqual(pl.duracion_minima(pl.TAREAS_EJEMPLO), 4.0)

    def test_un_recurso_es_secuencial(self):
        """Con un recurso, B y C no se superponen."""
        self.assertEqual(pl.duracion_con_recursos(pl.TAREAS_EJEMPLO, 1),
                         pl.duracion_minima(pl.TAREAS_EJEMPLO) + 1.0)

    def test_sin_limite_es_el_camino_critico(self):
        """Sin límite de recursos, la duración es el camino crítico."""
        self.assertEqual(pl.duracion_con_recursos(pl.TAREAS_EJEMPLO),
                         pl.duracion_minima(pl.TAREAS_EJEMPLO))

    def test_memo_y_recursivo_coinciden(self):
        """La memoización no cambia el resultado."""
        for nombre in pl.TAREAS_EJEMPLO:
            self.assertEqual(pl.cuando_termina(pl.TAREAS_EJEMPLO, nombre),
                             pl.cuando_termina_memo(pl.TAREAS_EJEMPLO, nombre))


class TestCronograma(unittest.TestCase):
    """Cada tarea empieza cuando terminan sus dependencias."""

    def test_respeta_dependencias(self):
        """Ninguna tarea empieza antes de que terminen las que necesita."""
        plan = pl.cronograma(pl.TAREAS_EJEMPLO, 2)
        for nombre, tarea in pl.TAREAS_EJEMPLO.items():
            for anterior in tarea["depende_de"]:
                self.assertGreaterEqual(plan[nombre][0], plan[anterior][1])

    def test_b_y_c_a_la_vez_con_dos_recursos(self):
        """Con dos recursos, B y C empiezan juntas en recursos distintos."""
        plan = pl.cronograma(pl.TAREAS_EJEMPLO, 2)
        self.assertEqual(plan["B"][0], plan["C"][0])
        self.assertNotEqual(plan["B"][2], plan["C"][2])


class TestInterfaz(unittest.TestCase):
    """La interfaz web responde y valida las tareas."""

    def setUp(self):
        self.cliente = app.app.test_client()

    def test_pagina(self):
        """La página principal carga."""
        self.assertEqual(self.cliente.get("/").status_code, 200)

    def test_plan(self):
        """El plan del enunciado dura 4 s con dos recursos."""
        respuesta = self.cliente.post(
            "/plan", json={"tareas": pl.TAREAS_EJEMPLO, "procesos": 2})
        self.assertEqual(respuesta.get_json()["duracion"], 4.0)

    def test_medir_una_optimizacion(self):
        """Medir un paso devuelve un tiempo, con y sin la optimización."""
        for con in (True, False):
            respuesta = self.cliente.post(
                "/medir", json={"clave": "memo", "con": con})
            self.assertGreater(respuesta.get_json()["segundos"], 0)

    def test_ejecutar(self):
        """Ejecutar devuelve cuándo corrió cada tarea y el total."""
        tareas = {"A": {"duracion": 0.05, "prioridad": 1, "depende_de": []}}
        datos = self.cliente.post(
            "/ejecutar", json={"tareas": tareas, "procesos": 1}).get_json()
        self.assertEqual(list(datos["registro"]), ["A"])
        self.assertGreater(datos["total"], 0)

    def test_ejecutar_rechaza_ciclos(self):
        """Con un ciclo, ejecutar devuelve un error y no corre nada."""
        datos = self.cliente.post(
            "/ejecutar", json={"tareas": CICLO, "procesos": 1}).get_json()
        self.assertIn("ciclo", datos["error"])

    def test_sin_tareas_da_error(self):
        """Planificar sin tareas devuelve un error claro."""
        datos = self.cliente.post(
            "/plan", json={"tareas": {}, "procesos": 1}).get_json()
        self.assertIn("error", datos)

    def test_tarea_demasiado_larga_da_error(self):
        """La demo no acepta tareas de más de 5 segundos."""
        tareas = {"A": {"duracion": 6, "prioridad": 1, "depende_de": []}}
        datos = self.cliente.post(
            "/plan", json={"tareas": tareas, "procesos": 1}).get_json()
        self.assertIn("5 s", datos["error"])

    def test_pasos(self):
        """La web recibe los pasos del planificador."""
        pasos = self.cliente.get("/pasos").get_json()
        self.assertEqual(len(pasos), len(optimizaciones.PASOS))

    def test_dependencia_inexistente(self):
        """Depender de una tarea que no existe da un error claro."""
        tareas = {"A": {"duracion": 1, "prioridad": 1, "depende_de": ["Z"]}}
        respuesta = self.cliente.post(
            "/plan", json={"tareas": tareas, "procesos": 1})
        self.assertIn("no existe", respuesta.get_json()["error"])


class TestOptimizaciones(unittest.TestCase):
    """Cada paso se puede medir con y sin su optimización."""

    def test_todos_los_pasos(self):
        """Con y sin optimización, cada paso termina y devuelve un tiempo."""
        for paso in optimizaciones.PASOS:
            for con in (True, False):
                with self.subTest(paso=paso["clave"], con=con):
                    self.assertGreater(
                        optimizaciones.medir_paso(paso["clave"], con), 0)


class TestCache(unittest.TestCase):
    """La caché devuelve el plan guardado sin recalcularlo."""

    def setUp(self):
        pl.planes_guardados.clear()

    def test_segunda_llamada_devuelve_el_mismo_objeto(self):
        """La segunda vez no se recalcula el plan."""
        primero = pl.plan_con_cache("plan", pl.TAREAS_EJEMPLO)
        segundo = pl.plan_con_cache("plan", pl.TAREAS_EJEMPLO)
        self.assertIs(primero, segundo)


class TestArchivos(unittest.TestCase):
    """Escribir y leer por lotes no pierde ni cambia tareas."""

    def setUp(self):
        self.ruta = os.path.join(tempfile.gettempdir(), "test_parcial2.txt")
        self.tareas = {f"T{i}": {"duracion": 1.0, "prioridad": i % 5 + 1,
                                 "depende_de": [f"T{i - 1}"] if i else []}
                       for i in range(2_500)}

    def tearDown(self):
        os.remove(self.ruta)

    def test_escrituras_dan_el_mismo_archivo(self):
        """Con y sin buffer se escribe exactamente lo mismo."""
        archivos.escribir_linea_por_linea(self.ruta, self.tareas)
        with open(self.ruta, encoding="utf-8") as archivo:
            linea_por_linea = archivo.read()
        archivos.escribir_por_lotes(self.ruta, self.tareas, tamanio_lote=1000)
        with open(self.ruta, encoding="utf-8") as archivo:
            self.assertEqual(archivo.read(), linea_por_linea)

    def test_lotes_y_paralelo_dan_el_mismo_resumen(self):
        """Secuencial y en paralelo resumen igual."""
        archivos.escribir_por_lotes(self.ruta, self.tareas)
        secuencial = archivos.procesar_secuencial(self.ruta)
        self.assertEqual(secuencial["tareas"], 2_500)
        self.assertEqual(secuencial["dependencias"], 2_499)
        self.assertEqual(archivos.procesar_en_paralelo(self.ruta, 2),
                         secuencial)


class TestParalelo(unittest.TestCase):
    """El trabajo de CPU da lo mismo en paralelo que en secuencia."""

    def test_contar_primos(self):
        """Hay 25 primos menores que 100."""
        self.assertEqual(paralelo.contar_primos(100), 25)

    def test_paralelo_es_mas_rapido(self):
        """Dos tareas sueltas con 2 procesos tardan menos que de a una."""
        tareas = {f"T{i}": {"duracion": 0.2, "prioridad": 1, "depende_de": []}
                  for i in range(2)}
        self.assertLess(paralelo.tiempo_total(tareas, 2),
                        paralelo.tiempo_total(tareas, 1))

    def test_no_espera_tareas_que_no_necesita(self):
        """Una cadena corta no espera a una tarea larga que va por separado."""
        tareas = {
            "T1": {"duracion": 0.1, "prioridad": 1, "depende_de": []},
            "T2": {"duracion": 0.1, "prioridad": 1, "depende_de": ["T1"]},
            "T5": {"duracion": 0.4, "prioridad": 2, "depende_de": []},
        }
        registro = paralelo.ejecutar(tareas, 2)
        self.assertLess(registro["T2"][0], registro["T5"][1])

    def test_ejecutar_respeta_dependencias(self):
        """Ejecutando de verdad, B y C empiezan después de que termina A."""
        tareas = {nombre: dict(tarea, duracion=tarea["duracion"] / 10)
                  for nombre, tarea in pl.TAREAS_EJEMPLO.items()}
        registro = paralelo.ejecutar(tareas, 2)
        for nombre in ("B", "C"):
            self.assertGreaterEqual(registro[nombre][0], registro["A"][1])


def load_tests(_loader, tests, _ignore):
    """Suma los ejemplos de los docstrings (doctest) a la corrida."""
    for modulo in (pl, archivos, paralelo):
        tests.addTests(doctest.DocTestSuite(modulo))
    return tests


if __name__ == "__main__":
    unittest.main()

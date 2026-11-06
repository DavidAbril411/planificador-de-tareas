"""Benchmark: tiempo de las operaciones representativas del planificador."""

import pytest

import optimizaciones
import planificador as pl


@pytest.fixture(scope="module")
def tareas():
    """El proyecto de prueba de 2.000 tareas."""
    return optimizaciones.tareas_de_prueba(2000)


def test_orden_rapido(benchmark, tareas):
    """Ordenar con heapq."""
    assert len(benchmark(pl.orden_rapido, tareas)) == 2000


def test_niveles(benchmark, tareas):
    """Agrupar en niveles."""
    assert benchmark(pl.niveles, tareas)


def test_cronograma(benchmark, tareas):
    """Armar el cronograma con 4 recursos."""
    assert len(benchmark(pl.cronograma, tareas, 4)) == 2000

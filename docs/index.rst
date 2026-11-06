Planificador de tareas - Parcial 2
==================================

Planificador de tareas con dependencias. Cada tarea tiene una duración, una
prioridad y la lista de tareas de las que depende. El planificador ordena las
tareas respetando las dependencias, ejecuta por niveles en paralelo usando
``multiprocessing``, escribe y lee archivos grandes con buffer y por lotes, y
expone el resultado en una aplicación Flask.

Cómo generar esta documentación:

.. code-block:: bash

   sphinx-build -b html docs docs/_build/html

.. toctree::
   :maxdepth: 2
   :caption: Módulos

   planificador
   paralelo
   archivos
   app
   optimizaciones

# Pruebas

## Estrategia

| Tipo | Herramienta | Qué cubre |
|---|---|---|
| Unitarias | `unittest`, corridas con pytest | Orden, duración, cronograma, caché, archivos y paralelismo |
| De integración | Cliente de pruebas de Flask | Las rutas de la web |
| Documentación ejecutable | `doctest` | Los ejemplos de los docstrings |

## Casos de prueba

- Orden del enunciado, y lento y rápido dan lo mismo.
- Ninguna tarea va antes que sus dependencias.
- Un ciclo devuelve `None`, y en la web un error.
- Memoización y recursión coinciden.
- Con y sin buffer se escribe exactamente lo mismo.
- Secuencial y paralelo resumen igual un archivo.
- Una cadena corta no espera a una tarea larga que no necesita.
- Dependencia inexistente, tarea demasiado larga y lista vacía dan error.

## Resultados

| Métrica | Valor | Mínimo |
|---|---|---|
| Pruebas | 40, todas pasan | Todas |
| Cobertura | 97 % | 85 % |

La cobertura no cuenta `parcial2.py` ni `perfilar.py`, que son programas de demostración. Lo que no se cubre es el arranque del servidor y el caso con Elastic APM activo.

## Cómo correrlas

```bash
./ci/controles.sh pruebas
```

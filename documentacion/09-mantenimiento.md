# Mantenimiento

## Cómo contribuir

1. Crear una rama: `git switch -c feature/nombre`.
2. Hacer el cambio con sus pruebas.
3. Correr `./ci/controles.sh` antes de subirlo.
4. Abrir un pull request hacia `main`.
5. El cambio se integra solo si el check **Resultado final** pasa.

Si el cambio afecta el comportamiento, se actualiza esta documentación en el mismo pull request.

## Ejecutar los controles localmente

Los mismos comandos del CI están en `ci/controles.sh`, que usan tanto el pipeline como una computadora local:

```bash
./ci/controles.sh                # todos
./ci/controles.sh estatica       # Ruff, Pylint, mypy, Radon, Bandit, Gitleaks
./ci/controles.sh pruebas        # pytest y cobertura
./ci/controles.sh seguridad      # pip-audit
./ci/controles.sh documentacion  # Sphinx, markdownlint, Lychee
./ci/controles.sh rendimiento    # benchmark, profiling, memoria
```

Los reportes quedan en `reportes/`. En el CI se descargan como artefactos de cada corrida.

Fuera de Python hacen falta Gitleaks, Lychee y Node.js: `brew install gitleaks lychee node`.

## Resolver fallos del pipeline

| Falla | Qué hacer |
|---|---|
| Ruff | `ruff check --fix .` y revisar el cambio |
| Pylint | Leer el aviso; la nota mínima es 9,5 |
| mypy | Corregir el tipo; no silenciarlo sin motivo |
| Radon | Dividir la función con Extract Method |
| Bandit | Corregir, o documentar el falso positivo en [Seguridad](08-seguridad.md) |
| Gitleaks | Sacar el secreto del historial y cambiar la credencial |
| pytest o cobertura | Corregir el código o agregar pruebas |
| pip-audit | Actualizar la dependencia y regenerar `requirements-lock.txt` |
| Sphinx, markdownlint o Lychee | Corregir el docstring, el formato o el enlace |
| Benchmark | Comparar con `reportes/benchmark.json`; si el cambio de tiempo se justifica, actualizar la línea base |
| Memoria | Revisar `reportes/memoria.json`; no subir el límite sin medir |

## Actualizar dependencias

Dependabot abre un pull request por semana. Para hacerlo a mano:

```bash
.venv/bin/pip install --upgrade nombre
.venv/bin/pip freeze > requirements-lock.txt
```

## Actualizar la línea base del benchmark

Se descarga `benchmark.json` de una corrida del CI en `main` y se guarda como `.benchmarks/Linux-CPython-3.14-64bit/0001_base.json`. Tiene que venir del runner: una medición local no es comparable.

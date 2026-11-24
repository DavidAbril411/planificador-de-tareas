#!/usr/bin/env bash
# Los controles de calidad y eficiencia. El CI y una computadora local corren
# exactamente lo mismo:   ./ci/controles.sh [build|estatica|pruebas|seguridad|documentacion|rendimiento]
# Sin argumento corre todas las etapas. Los reportes quedan en reportes/.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=.
mkdir -p reportes
if [ -d .venv/bin ]; then export PATH="$PWD/.venv/bin:$PATH"; fi

CODIGO="planificador.py paralelo.py archivos.py optimizaciones.py app.py ia.py parcial2.py perfilar.py"

build() {
  echo "== Build: sintaxis, imports y arranque de la web"
  python -m compileall -q $CODIGO ci benchmarks
  python - <<'PY'
import app
respuesta = app.app.test_client().post("/plan", json={
    "tareas": {"A": {"duracion": 1, "prioridad": 1, "depende_de": []}},
    "procesos": 1})
assert respuesta.status_code == 200 and respuesta.get_json()["orden"] == ["A"]
print("la web arranca y planifica")
PY
}

estatica() {
  echo "== Ruff"; ruff check .
  echo "== Pylint (nota mínima 9,5)"; pylint $CODIGO test_planificador.py
  echo "== mypy"; mypy
  echo "== Radon (rechaza complejidad C o peor: más de 10)"
  radon cc -j $CODIGO > reportes/radon.json
  complejas=$(radon cc -n C -s $CODIGO)
  if [ -n "$complejas" ]; then echo "$complejas"; exit 1; fi
  echo "== Bandit (rechaza severidad media o alta)"
  bandit -q -c pyproject.toml -r $CODIGO --severity-level medium \
    -f json -o reportes/bandit.json
  echo "== Gitleaks (secretos)"
  gitleaks detect --no-banner --report-format sarif \
    --report-path reportes/gitleaks.sarif
}

pruebas() {
  echo "== pytest + cobertura (mínimo 80 %)"
  coverage erase
  set +e
  coverage run -m pytest --junitxml=reportes/pruebas.xml
  resultado=$?
  set -e
  python ci/resumen_pruebas.py reportes/pruebas.xml
  if [ "$resultado" -ne 0 ]; then echo "Hay tests fallidos"; exit "$resultado"; fi
  coverage combine -q
  coverage xml -o reportes/cobertura.xml
  coverage report
}

seguridad() {
  echo "== pip-audit (rechaza cualquier vulnerabilidad conocida)"
  pip-audit -r requirements-lock.txt --no-deps --disable-pip \
    -f json -o reportes/pip-audit.json
}

documentacion() {
  echo "== Sphinx (los avisos son errores)"
  sphinx-build -q -W -b html docs docs/_build/html
  echo "== markdownlint"
  npx --yes markdownlint-cli2@0.24.0 "documentacion/**/*.md"
  echo "== Lychee (enlaces)"
  lychee --no-progress --exclude-loopback documentacion
}

rendimiento() {
  echo "== Escalabilidad y Performance Gate"; python ci/escalabilidad.py
  echo "== Benchmark (rechaza si la mediana empeora más de 100 %)"
  comparar=()
  if [ "$(uname)" = "Linux" ] && ls .benchmarks/Linux-*/0001_* >/dev/null 2>&1; then
    comparar=(--benchmark-compare=0001 --benchmark-compare-fail=median:100%)
  fi
  pytest benchmarks --doctest-modules --benchmark-only \
    --benchmark-json=reportes/benchmark.json "${comparar[@]+"${comparar[@]}"}"
  echo "== Profiling de CPU"; python ci/perfil.py
  echo "== Memoria (límite 5 MB)"; python ci/memoria.py
}

etapa="${1:-todas}"
if [ "$etapa" = "todas" ]; then
  build; estatica; pruebas; seguridad; documentacion; rendimiento
else
  "$etapa"
fi
echo "OK: $etapa"

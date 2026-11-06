#!/bin/bash
# Parcial 2: el planificador con los temas del segundo parcial.
#   ./ejecutar_parcial2.sh            -> mediciones (parcial2.py)
#   ./ejecutar_parcial2.sh tests      -> unittest + doctest
#   ./ejecutar_parcial2.sh web        -> la app de Flask en http://127.0.0.1:5050
#   ./ejecutar_parcial2.sh docs       -> documentacion con Sphinx
#   ./ejecutar_parcial2.sh calidad    -> flake8 y pylint
#   ./ejecutar_parcial2.sh apm        -> la web monitoreada con Elastic APM (Docker)
#   ./ejecutar_parcial2.sh scalene    -> Scalene: CPU por linea (abre el reporte)
#   ./ejecutar_parcial2.sh snakeviz   -> cProfile + SnakeViz (abre el navegador)
#   ./ejecutar_parcial2.sh pyspy      -> py-spy (pide la clave: macOS exige root)

cd "$(dirname "$0")" || exit 1
export PATH="$PWD/.venv/bin:$HOME/Library/Python/3.14/bin:$PATH"

case "$1" in
  tests)   python3 -m unittest -v ;;
  web)     (sleep 1.5; open http://127.0.0.1:5050) & python3 app.py ;;
  apm)
    echo "Levantando Elastic APM con Docker (la primera vez tarda unos minutos)..."
    (cd apm && docker compose up -d)
    echo "Kibana: http://localhost:5601/app/apm  (puede tardar 1-2 minutos en abrir)"
    echo "Usá la web y los pedidos aparecen en Kibana > Observability > APM."
    (sleep 1.5; open http://127.0.0.1:5050) &
    ELASTIC_APM_SERVER_URL=http://localhost:8200 python3 app.py ;;
  pyspy)
    echo "py-spy mira el programa perfilar.py mientras corre (100 veces por segundo)"
    echo "y anota en que funcion esta. macOS pide tu clave para dejarlo mirar."
    sudo "$HOME/Library/Python/3.14/bin/py-spy" record -o reportes/pyspy.svg -- python3 perfilar.py
    echo
    echo "Listo: reportes/pyspy.svg (se abre en el navegador)."
    echo "Como leerlo: cada barra es una funcion; mas ancha = mas tiempo."
    echo "Las de abajo llaman a las de arriba."
    open reportes/pyspy.svg ;;
  scalene)  scalene run --cpu-only perfilar.py && scalene view ;;
  snakeviz)
    python3 -m cProfile -o reportes/perfilar.prof perfilar.py
    snakeviz reportes/perfilar.prof ;;
  docs)    sphinx-build -b html docs docs/_build/html ;;
  calidad) flake8 *.py; pylint *.py ;;
  *)       python3 parcial2.py ;;
esac

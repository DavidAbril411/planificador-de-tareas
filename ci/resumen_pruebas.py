"""Cuenta los tests del reporte JUnit y los publica en el resumen del CI."""

import os
import sys
import xml.etree.ElementTree as ET

if __name__ == "__main__":
    raiz = ET.parse(sys.argv[1]).getroot()
    suite = raiz if raiz.tag == "testsuite" else raiz.find("testsuite")
    # Se cuentan los tests listados: "tests" también suma los subtests.
    casos = list(suite.iter("testcase"))
    total = len(casos)
    fallidos = sum(1 for caso in casos
                   if caso.find("failure") is not None
                   or caso.find("error") is not None)
    omitidos = sum(1 for caso in casos if caso.find("skipped") is not None)
    exitosos = total - fallidos - omitidos
    texto = ("## Tests\n\n| Ejecutados | Exitosos | Fallidos | Omitidos |\n"
             "|---:|---:|---:|---:|\n"
             f"| {total} | {exitosos} | {fallidos} | {omitidos} |\n")
    print(texto)
    ruta = os.environ.get("GITHUB_STEP_SUMMARY")
    if ruta:
        with open(ruta, "a", encoding="utf-8") as resumen:
            resumen.write(texto)

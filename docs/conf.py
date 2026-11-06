# Configuración de Sphinx para la documentación del Parcial 2.

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "Planificador de tareas - Parcial 2"
author = "David Ignacio Abril Perrig"
language = "es"

extensions = ["sphinx.ext.autodoc"]

templates_path = []
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "alabaster"

autodoc_member_order = "bysource"

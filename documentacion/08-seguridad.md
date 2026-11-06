# Seguridad

## Riesgos identificados

| Riesgo | Severidad | Medida |
|---|---|---|
| La web no tiene autenticación | Media | Solo escucha en 127.0.0.1; no se publica en internet |
| Muchas tareas pueden consumir toda la CPU | Media | Cada tarea dura como máximo 5 s; solo uso local |
| Elasticsearch de la demo no tiene contraseña | Media | Los puertos solo se abren en 127.0.0.1 |
| Los nombres de tareas se insertan en la página sin escapar | Baja | Solo los escribe quien usa la web, en su máquina; pendiente de corregir si se publica |
| Dependencias con vulnerabilidades | Variable | pip-audit en cada cambio y Dependabot |
| Secretos en el repositorio | Alta | Gitleaks en cada cambio; el proyecto no usa credenciales |

## Controles

| Qué analiza | Herramienta | Reporte |
|---|---|---|
| Código fuente | Bandit | `bandit.json` |
| Dependencias | pip-audit | `pip-audit.json` |
| Secretos | Gitleaks | `gitleaks.sarif` |
| Actualizaciones | Dependabot | Pull requests automáticos |

## Política de bloqueo

| Severidad | Acción |
|---|---|
| Crítica o alta | Bloquea la integración |
| Media | Bloquea la integración (Bandit) |
| Baja | Se revisa y, si corresponde, se documenta abajo |
| Cualquier secreto detectado | Bloquea, y hay que cambiar la credencial |
| Vulnerabilidad en una dependencia | Bloquea hasta actualizarla o documentar la excepción |

## Falsos positivos y excepciones

| Regla | Motivo | Dónde |
|---|---|---|
| Bandit B311 (`random`) | Solo genera datos de prueba; no se usa para seguridad | `pyproject.toml` |
| Bandit B101 (`assert`) | Solo aparece en pruebas y controles | `pyproject.toml` |

## Medidas correctivas

Los puertos de `apm/docker-compose.yml` se abrían en todas las interfaces de red; ahora solo en 127.0.0.1.

## Estado actual

pip-audit no encuentra vulnerabilidades conocidas en las versiones fijadas.

# Instalación y ejecución

## Requisitos

- Python 3.14
- Docker Desktop, solo para Elastic APM
- Node.js, Gitleaks y Lychee, solo para correr todos los controles

## Instalación

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
```

## Comandos

| Comando | Qué hace |
|---|---|
| `./ejecutar_parcial2.sh web` | Abre la web en <http://127.0.0.1:5050> |
| `./ejecutar_parcial2.sh` | Mediciones por consola |
| `./ejecutar_parcial2.sh tests` | Pruebas |
| `./ejecutar_parcial2.sh docs` | Referencia del código con Sphinx |
| `./ejecutar_parcial2.sh apm` | Web monitoreada con Elastic APM |
| `./ci/controles.sh` | Los mismos controles que el CI |

## Configuración

| Variable | Efecto |
|---|---|
| `ELASTIC_APM_SERVER_URL` | Si existe, la web manda sus mediciones a ese servidor APM |

La web usa el puerto 5050 porque en macOS AirPlay ocupa el 5000.

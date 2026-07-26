"""
constants.py

Define rutas base y valores constantes usados en todo el proyecto.
Ningún otro módulo debería "hardcodear" una ruta o valor fijo:
todos deben importarlo desde aquí.
"""

from pathlib import Path

# Carpeta raíz del proyecto (donde está este archivo, subiendo dos niveles:
# de core/constants.py hasta la raíz youtube_automation/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Carpetas de datos y salidas
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

# Nos aseguramos de que estas carpetas existan siempre al arrancar la app
for directory in (DATA_DIR, LOGS_DIR, OUTPUT_DIR, TEMP_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# Nombre del archivo de configuración no sensible
CONFIG_FILE = BASE_DIR / "config.yaml"

# Valores por defecto (se pueden sobrescribir desde config.yaml)
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_AI_PROVIDER = "gemini"
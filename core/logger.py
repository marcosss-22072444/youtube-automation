"""
logger.py

Sistema de logging centralizado. Cualquier módulo del proyecto debe
obtener su logger llamando a get_logger(__name__), en vez de configurar
su propio logging por separado.
"""

import logging
from datetime import datetime

from core.constants import LOGS_DIR, DEFAULT_LOG_LEVEL

# Nombre del archivo de log: uno nuevo por día (ej: 2026-07-24.log)
_LOG_FILE = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"

# Formato de cada línea del log: fecha/hora, nombre del módulo, nivel, mensaje
_LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"


def get_logger(name: str) -> logging.Logger:
    """
    Devuelve un logger configurado, identificado por 'name'
    (normalmente se le pasa __name__ del archivo que lo llama).

    Escribe los mensajes tanto en consola como en un archivo diario
    dentro de la carpeta logs/.
    """
    logger = logging.getLogger(name)

    # Evita añadir handlers duplicados si get_logger se llama varias veces
    # con el mismo nombre (por ejemplo, al recargar un módulo).
    if logger.handlers:
        return logger

    logger.setLevel(DEFAULT_LOG_LEVEL)

    formatter = logging.Formatter(_LOG_FORMAT)

    # Handler para consola (lo que ves en el terminal)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para archivo (lo que queda guardado en logs/)
    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
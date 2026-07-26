"""
schema.py

Define la estructura (esquema) de todas las tablas del proyecto y
proporciona initialize_database(), que las crea si no existen.

Cada módulo nuevo que necesite su propia tabla debe añadir aquí su
sentencia CREATE TABLE, y registrarla en initialize_database().
"""

from core.database import get_connection
from core.logger import get_logger

logger = get_logger(__name__)


_CREATE_CHANNELS_TABLE = """
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    topic TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    shorts_per_week INTEGER NOT NULL DEFAULT 0,
    long_videos_per_week INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
"""


def initialize_database():
    """
    Crea todas las tablas del proyecto si no existen todavía.
    Se debe llamar una vez al arrancar la aplicación (ej: desde main.py).
    """
    with get_connection() as conn:
        conn.execute(_CREATE_CHANNELS_TABLE)
        # Futuras tablas (ideas, videos, stats...) se añadirán aquí
        # conn.execute(_CREATE_IDEAS_TABLE)
        # conn.execute(_CREATE_VIDEOS_TABLE)

    logger.info("Base de datos inicializada correctamente.")
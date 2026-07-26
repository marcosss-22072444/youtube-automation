"""
database.py

Conexión reutilizable a la base de datos SQLite del proyecto.
Cualquier módulo que necesite guardar datos (channels, ideas, stats...)
debe usar get_connection() de aquí, en vez de abrir su propia conexión.
"""

import sqlite3
from contextlib import contextmanager

from core.constants import DATA_DIR

DB_PATH = DATA_DIR / "database.sqlite"


@contextmanager
def get_connection():
    """
    Proporciona una conexión SQLite lista para usar, con:
    - row_factory configurado para acceder a columnas por nombre.
    - claves foráneas activadas.
    - cierre automático de la conexión al salir del bloque 'with'.

    Uso:
        with get_connection() as conn:
            conn.execute("SELECT * FROM channels")
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
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
    voice_name TEXT NOT NULL DEFAULT 'ef_dora',
    created_at TEXT NOT NULL
);
"""

_CREATE_IDEAS_TABLE = """
CREATE TABLE IF NOT EXISTS ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    content_type TEXT NOT NULL DEFAULT 'short',
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (channel_id) REFERENCES channels (id) ON DELETE CASCADE
);
"""
_CREATE_SCRIPTS_TABLE = """
CREATE TABLE IF NOT EXISTS scripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idea_id INTEGER NOT NULL,
    content_type TEXT NOT NULL DEFAULT 'short',
    content TEXT NOT NULL,
    word_count INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    FOREIGN KEY (idea_id) REFERENCES ideas (id) ON DELETE CASCADE
);
"""
_CREATE_VOICE_TRACKS_TABLE = """
CREATE TABLE IF NOT EXISTS voice_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    voice_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (script_id) REFERENCES scripts (id) ON DELETE CASCADE
);
"""
_CREATE_VISUALS_TABLE = """
CREATE TABLE IF NOT EXISTS visuals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER NOT NULL,
    scene_number INTEGER NOT NULL,
    image_prompt TEXT NOT NULL,
    file_path TEXT NOT NULL,
    asset_type TEXT NOT NULL DEFAULT 'image',
    source TEXT NOT NULL DEFAULT 'sdxl',
    created_at TEXT NOT NULL,
    FOREIGN KEY (script_id) REFERENCES scripts (id) ON DELETE CASCADE
);
"""
_CREATE_VIDEOS_TABLE = """
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    srt_path TEXT,
    duration_seconds REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (script_id) REFERENCES scripts (id) ON DELETE CASCADE
);
"""
_CREATE_THUMBNAILS_TABLE = """
CREATE TABLE IF NOT EXISTS thumbnails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    title_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (script_id) REFERENCES scripts (id) ON DELETE CASCADE
);
"""
_CREATE_METADATA_TABLE = """
CREATE TABLE IF NOT EXISTS metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    tags TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (script_id) REFERENCES scripts (id) ON DELETE CASCADE
);
"""
_CREATE_UPLOADED_VIDEOS_TABLE = """
CREATE TABLE IF NOT EXISTS uploaded_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    youtube_video_id TEXT NOT NULL,
    privacy_status TEXT NOT NULL,
    thumbnail_uploaded INTEGER NOT NULL DEFAULT 0,
    uploaded_at TEXT NOT NULL,
    FOREIGN KEY (script_id) REFERENCES scripts (id) ON DELETE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES channels (id) ON DELETE CASCADE
);
"""

def initialize_database():
    """
    Crea todas las tablas del proyecto si no existen todavía.
    Se debe llamar una vez al arrancar la aplicación (ej: desde main.py).
    """
    with get_connection() as conn:
        conn.execute(_CREATE_CHANNELS_TABLE)
        conn.execute(_CREATE_IDEAS_TABLE)
        conn.execute(_CREATE_SCRIPTS_TABLE)
        conn.execute(_CREATE_VOICE_TRACKS_TABLE)
        conn.execute(_CREATE_VISUALS_TABLE)
        conn.execute(_CREATE_VIDEOS_TABLE)
        conn.execute(_CREATE_THUMBNAILS_TABLE)
        conn.execute(_CREATE_METADATA_TABLE)
        conn.execute(_CREATE_UPLOADED_VIDEOS_TABLE)
        # Futuras tablas (stats...) se añadirán aquí
    logger.info("Base de datos inicializada correctamente.")
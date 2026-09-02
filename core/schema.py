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
    timezone TEXT,
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
    word_timestamps_path TEXT,
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

_CREATE_CHANNEL_SCHEDULES_TABLE = """
CREATE TABLE IF NOT EXISTS channel_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    content_type TEXT NOT NULL,
    day_of_week INTEGER NOT NULL,
    time_of_day TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (channel_id) REFERENCES channels (id) ON DELETE CASCADE
);
"""

_CREATE_SCHEDULE_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS schedule_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_entry_id INTEGER NOT NULL,
    run_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    uploaded_video_id INTEGER,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    next_retry_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (schedule_entry_id) REFERENCES channel_schedules (id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_video_id) REFERENCES uploaded_videos (id) ON DELETE SET NULL,
    UNIQUE (schedule_entry_id, run_date)
);
"""

_CREATE_VIDEO_STATS_TABLE = """
CREATE TABLE IF NOT EXISTS video_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uploaded_video_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    view_count INTEGER NOT NULL,
    like_count INTEGER NOT NULL,
    comment_count INTEGER NOT NULL,
    subscriber_count INTEGER NOT NULL,
    collected_at TEXT NOT NULL,
    FOREIGN KEY (uploaded_video_id) REFERENCES uploaded_videos (id) ON DELETE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES channels (id) ON DELETE CASCADE
);
"""

_CREATE_RESEARCH_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS research_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idea_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'completed',
    created_at TEXT NOT NULL,
    FOREIGN KEY (idea_id) REFERENCES ideas (id) ON DELETE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES channels (id) ON DELETE CASCADE
);
"""

_CREATE_RESEARCH_SOURCES_TABLE = """
CREATE TABLE IF NOT EXISTS research_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    research_run_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    source_type TEXT NOT NULL,
    reliability_score REAL NOT NULL,
    raw_content TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (research_run_id) REFERENCES research_runs (id) ON DELETE CASCADE
);
"""

_CREATE_RESEARCH_FACTS_TABLE = """
CREATE TABLE IF NOT EXISTS research_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    research_run_id INTEGER NOT NULL,
    claim TEXT NOT NULL,
    status TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    source_ids TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (research_run_id) REFERENCES research_runs (id) ON DELETE CASCADE
);
"""

_CREATE_CHANNEL_RESEARCH_CONFIG_TABLE = """
CREATE TABLE IF NOT EXISTS channel_research_config (
    channel_id INTEGER PRIMARY KEY,
    instructions TEXT,
    min_sources_required INTEGER,
    confidence_threshold REAL,
    enabled INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (channel_id) REFERENCES channels (id) ON DELETE CASCADE
);
"""

_CREATE_CHANNEL_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS channel_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    setting_key TEXT NOT NULL,
    setting_value TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (channel_id) REFERENCES channels (id) ON DELETE CASCADE,
    UNIQUE (channel_id, setting_key)
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
        conn.execute(_CREATE_CHANNEL_SCHEDULES_TABLE)
        conn.execute(_CREATE_SCHEDULE_RUNS_TABLE)
        conn.execute(_CREATE_VIDEO_STATS_TABLE)
        conn.execute(_CREATE_RESEARCH_RUNS_TABLE)
        conn.execute(_CREATE_RESEARCH_SOURCES_TABLE)
        conn.execute(_CREATE_RESEARCH_FACTS_TABLE)
        conn.execute(_CREATE_CHANNEL_RESEARCH_CONFIG_TABLE)
        conn.execute(_CREATE_CHANNEL_SETTINGS_TABLE)
    logger.info("Base de datos inicializada correctamente.")
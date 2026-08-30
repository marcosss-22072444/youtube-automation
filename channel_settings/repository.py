"""repository.py — Acceso a la tabla 'channel_settings'."""
import json
import sqlite3
from datetime import datetime

from core.database import get_connection


def get_raw(channel_id: int, setting_key: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT setting_value FROM channel_settings WHERE channel_id = ? AND setting_key = ?",
            (channel_id, setting_key),
        ).fetchone()
    return row["setting_value"] if row else None


def set_raw(channel_id: int, setting_key: str, json_value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO channel_settings (channel_id, setting_key, setting_value, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(channel_id, setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                updated_at = excluded.updated_at
            """,
            (channel_id, setting_key, json_value, datetime.now().isoformat()),
        )


def delete_setting(channel_id: int, setting_key: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM channel_settings WHERE channel_id = ? AND setting_key = ?",
            (channel_id, setting_key),
        )


def list_settings_for_channel(channel_id: int) -> dict:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT setting_key, setting_value FROM channel_settings WHERE channel_id = ?",
            (channel_id,),
        ).fetchall()
    return {row["setting_key"]: json.loads(row["setting_value"]) for row in rows}
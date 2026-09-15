"""main.py — TEST Remote API: router pipeline (runs + errores)."""
from fastapi.testclient import TestClient
from core.logger import get_logger
from core.schema import initialize_database
from core.database import get_connection
from core.config import settings
from channels import manager as channel_manager
from scheduler import manager as schedule_manager
from remote_api.app import app

logger = get_logger(__name__)

def main():
    initialize_database()
    client = TestClient(app)
    headers = {"X-API-Key": settings.remote_api_key}
    canal = channel_manager.create_channel(name="Canal Pipeline API", topic="t", shorts_per_week=1, long_videos_per_week=0)
    entry = schedule_manager.add_schedule_entry(canal.id, "short", 1, "18:00")

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO schedule_runs (schedule_entry_id, run_date, status, error_message, retry_count, created_at, updated_at) VALUES (?,?,?,?,?,datetime('now'),datetime('now'))",
            (entry.id, "2026-09-14", "failed", "Connection timeout", 1),
        )

    r1 = client.get(f"/pipeline/channel/{canal.id}/runs", headers=headers)
    p1 = r1.status_code == 200 and len(r1.json()) == 1 and r1.json()[0]["status"] == "failed"
    logger.info(f"P1 runs del canal correctos: {p1} ({r1.json()})")

    r2 = client.get("/pipeline/errors", headers=headers)
    p2 = r2.status_code == 200 and any(e["channel_id"] == canal.id and "timeout" in e["error_message"] for e in r2.json())
    logger.info(f"P2 lista global de errores incluye el fallo: {p2}")

    logger.info("✅ TODO CORRECTO" if p1 and p2 else "❌ FALLOS")

if __name__ == "__main__":
    main()
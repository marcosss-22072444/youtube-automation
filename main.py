"""main.py — TEST Remote API: router stats."""
from fastapi.testclient import TestClient
from core.logger import get_logger
from core.schema import initialize_database
from core.database import get_connection
from core.config import settings
from channels import manager as channel_manager
from ideas import repository as idea_repository
from ideas.models import Idea
from scripts import repository as script_repository
from scripts.models import Script
from remote_api.app import app

logger = get_logger(__name__)

def main():
    initialize_database()
    client = TestClient(app)
    headers = {"X-API-Key": settings.remote_api_key}
    canal = channel_manager.create_channel(name="Canal Stats API", topic="t", shorts_per_week=1, long_videos_per_week=0)

    idea = idea_repository.create(Idea(channel_id=canal.id, content_type="short", title="T", summary="S"))
    script = script_repository.create(Script(idea_id=idea.id, content_type="short", content="x", word_count=1))

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO uploaded_videos (script_id, channel_id, youtube_video_id, privacy_status, thumbnail_uploaded, uploaded_at) VALUES (?,?,?,?,?,datetime('now'))",
            (script.id, canal.id, "abc123", "private", 0),
        )
        uploaded_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO video_stats (uploaded_video_id, channel_id, view_count, like_count, comment_count, subscriber_count, collected_at) VALUES (?,?,?,?,?,?,datetime('now'))",
            (uploaded_id, canal.id, 150, 10, 2, 500),
        )

    r1 = client.get(f"/stats/channel/{canal.id}", headers=headers)
    p1 = r1.status_code == 200 and len(r1.json()) == 1 and r1.json()[0]["view_count"] == 150
    logger.info(f"P1 channel stats con datos correctos: {p1} ({r1.json()})")

    p2 = "revenue" in r1.json()[0] and r1.json()[0]["revenue"] is None
    logger.info(f"P2 campos Analytics reservados presentes (None): {p2}")

    r2 = client.get(f"/stats/video/{uploaded_id}/history", headers=headers)
    p3 = r2.status_code == 200 and len(r2.json()) == 1 and r2.json()[0]["like_count"] == 10
    logger.info(f"P3 historial de video correcto: {p3}")

    logger.info("✅ TODO CORRECTO" if all([p1, p2, p3]) else "❌ FALLOS")

if __name__ == "__main__":
    main()
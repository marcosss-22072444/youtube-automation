"""main.py — TEST Remote API: PATCH /schedules/{id}."""
from fastapi.testclient import TestClient
from core.logger import get_logger
from core.schema import initialize_database
from core.config import settings
from channels import manager as channel_manager
from remote_api.app import app

logger = get_logger(__name__)

def main():
    initialize_database()
    client = TestClient(app)
    headers = {"X-API-Key": settings.remote_api_key}
    canal = channel_manager.create_channel(name="Canal Patch Sched", topic="t", shorts_per_week=1, long_videos_per_week=0)

    r0 = client.post("/schedules", json={"channel_id": canal.id, "content_type": "short", "day_of_week": 1, "time_of_day": "18:00"}, headers=headers)
    eid = r0.json()["id"]

    r1 = client.patch(f"/schedules/{eid}", json={"content_type": "long", "day_of_week": 3, "time_of_day": "22:00", "enabled": True}, headers=headers)
    p1 = r1.status_code == 200 and r1.json() == {"id": eid, "content_type": "long", "day_of_week": 3, "time_of_day": "22:00", "enabled": True}
    logger.info(f"P1 patch actualiza correctamente: {p1} ({r1.json()})")

    r2 = client.get(f"/schedules/{canal.id}", headers=headers)
    p2 = len(r2.json()) == 1 and r2.json()[0]["time_of_day"] == "22:00"
    logger.info(f"P2 el listado refleja el cambio: {p2}")

    r3 = client.patch(f"/schedules/{eid}", json={"content_type": "invalido", "day_of_week": 3, "time_of_day": "22:00"}, headers=headers)
    p3 = r3.status_code == 400
    logger.info(f"P3 rechaza content_type invalido: {p3}")

    logger.info("✅ TODO CORRECTO" if all([p1, p2, p3]) else "❌ FALLOS")

if __name__ == "__main__":
    main()
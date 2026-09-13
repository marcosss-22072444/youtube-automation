"""main.py — TEST Remote API: router schedules (create/list/delete)."""
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

    canal = channel_manager.create_channel(name="Canal Schedule API", topic="t", shorts_per_week=1, long_videos_per_week=0)

    r1 = client.post("/schedules", json={"channel_id": canal.id, "content_type": "short", "day_of_week": 1, "time_of_day": "18:00"}, headers=headers)
    p1 = r1.status_code == 200
    logger.info(f"P1 crea horario: {p1} ({r1.json() if p1 else r1.text})")

    r2 = client.get(f"/schedules/{canal.id}", headers=headers)
    p2 = r2.status_code == 200 and len(r2.json()) == 1 and r2.json()[0]["time_of_day"] == "18:00"
    logger.info(f"P2 lista muestra el horario creado: {p2}")

    entry_id = r1.json()["id"]
    r3 = client.delete(f"/schedules/{entry_id}", headers=headers)
    p3 = r3.status_code == 200
    logger.info(f"P3 elimina horario: {p3}")

    r4 = client.get(f"/schedules/{canal.id}", headers=headers)
    p4 = len(r4.json()) == 0
    logger.info(f"P4 lista vacia tras eliminar: {p4}")

    r5 = client.post("/schedules", json={"channel_id": canal.id, "content_type": "invalido", "day_of_week": 1, "time_of_day": "18:00"}, headers=headers)
    p5 = r5.status_code == 400
    logger.info(f"P5 rechaza content_type invalido: {p5}")

    logger.info("✅ TODO CORRECTO" if all([p1, p2, p3, p4, p5]) else "❌ FALLOS")

if __name__ == "__main__":
    main()
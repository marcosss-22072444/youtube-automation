"""main.py — TEST Remote API: channels pause/activate/delete."""
from fastapi.testclient import TestClient
from core.logger import get_logger
from core.schema import initialize_database
from core.config import settings
from remote_api.app import app

logger = get_logger(__name__)

def main():
    initialize_database()
    client = TestClient(app)
    headers = {"X-API-Key": settings.remote_api_key}

    r0 = client.post("/channels", json={"name": "Canal Pause Test", "topic": "t", "shorts_per_week": 1}, headers=headers)
    cid = r0.json()["id"]

    r1 = client.post(f"/channels/{cid}/pause", headers=headers)
    p1 = r1.status_code == 200 and r1.json()["status"] == "paused"
    logger.info(f"P1 pause: {p1} ({r1.json()})")

    r2 = client.post(f"/channels/{cid}/activate", headers=headers)
    p2 = r2.status_code == 200 and r2.json()["status"] == "active"
    logger.info(f"P2 activate: {p2} ({r2.json()})")

    r3 = client.delete(f"/channels/{cid}", headers=headers)
    p3 = r3.status_code == 200
    logger.info(f"P3 delete: {p3}")

    r4 = client.post(f"/channels/{cid}/pause", headers=headers)
    p4 = r4.status_code == 404
    logger.info(f"P4 canal eliminado devuelve 404: {p4}")

    logger.info("✅ TODO CORRECTO" if all([p1, p2, p3, p4]) else "❌ FALLOS")

if __name__ == "__main__":
    main()
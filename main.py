"""main.py — TEST Remote API: auth y CRUD basico de channels."""
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

    r1 = client.get("/channels", headers={"X-API-Key": "clave_incorrecta"})
    p1 = r1.status_code == 401
    logger.info(f"P1 rechaza API key incorrecta: {p1}")

    r2 = client.post("/channels", json={"name": "Canal API Test", "topic": "t", "shorts_per_week": 1}, headers=headers)
    p2 = r2.status_code == 200
    logger.info(f"P2 crea canal con API key correcta: {p2} ({r2.json() if p2 else r2.text})")

    r3 = client.get("/channels", headers=headers)
    p3 = r3.status_code == 200 and any(c["name"] == "Canal API Test" for c in r3.json())
    logger.info(f"P3 lista incluye el canal creado: {p3}")

    r4 = client.get("/channels/99999", headers=headers)
    p4 = r4.status_code == 404
    logger.info(f"P4 canal inexistente devuelve 404: {p4}")

    logger.info("✅ TODO CORRECTO" if all([p1, p2, p3, p4]) else "❌ FALLOS")

if __name__ == "__main__":
    main()
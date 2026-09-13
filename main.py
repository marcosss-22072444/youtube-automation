"""main.py — TEST Remote API: router credentials (nunca expone valores)."""
from fastapi.testclient import TestClient
from core.logger import get_logger
from core.schema import initialize_database
from core.config import settings
from channels import manager as channel_manager
from remote_api.app import app

logger = get_logger(__name__)
SECRET = "clave_super_secreta_12345"

def main():
    initialize_database()
    client = TestClient(app)
    headers = {"X-API-Key": settings.remote_api_key}
    canal = channel_manager.create_channel(name="Canal Cred API", topic="t", shorts_per_week=1, long_videos_per_week=0)

    r1 = client.get(f"/credentials/{canal.id}", headers=headers)
    p1 = r1.status_code == 200 and r1.json()["configured_providers"] == []
    logger.info(f"P1 sin credenciales, lista vacia: {p1}")

    r2 = client.post(f"/credentials/{canal.id}", json={"provider_name": "pexels", "value": SECRET}, headers=headers)
    p2 = r2.status_code == 200 and SECRET not in str(r2.json())
    logger.info(f"P2 set no expone el valor en respuesta: {p2} ({r2.json()})")

    r3 = client.get(f"/credentials/{canal.id}", headers=headers)
    p3 = r3.json()["configured_providers"] == ["pexels"] and SECRET not in str(r3.json())
    logger.info(f"P3 list muestra solo nombre, no valor: {p3} ({r3.json()})")

    r4 = client.post(f"/credentials/{canal.id}", json={"provider_name": "invalido", "value": "x"}, headers=headers)
    p4 = "error" in r4.json()
    logger.info(f"P4 rechaza proveedor no permitido: {p4}")

    r5 = client.delete(f"/credentials/{canal.id}/pexels", headers=headers)
    r6 = client.get(f"/credentials/{canal.id}", headers=headers)
    p5 = r5.status_code == 200 and r6.json()["configured_providers"] == []
    logger.info(f"P5 delete elimina correctamente: {p5}")

    logger.info("✅ TODO CORRECTO" if all([p1, p2, p3, p4, p5]) else "❌ FALLOS")

if __name__ == "__main__":
    main()
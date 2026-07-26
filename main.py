"""
main.py

Script de prueba del Módulo 1 (Core). Verifica que la configuración,
el logger y el proveedor de IA funcionan correctamente juntos.
Este archivo se irá ampliando en módulos futuros para lanzar la app real.
"""

from core.logger import get_logger
from core.config import settings
from core.ai_providers.gemini_provider import GeminiProvider
from core.exceptions import BaseAppError
from core.schema import initialize_database

logger = get_logger(__name__)


def main():
    initialize_database()
    logger.info(f"Total de canales guardados: {len(todos)}")
    for c in todos:
    logger.info(f"  - [{c.id}] {c.name} | activo={c.is_active} | shorts/sem={c.shorts_per_week} | largos/sem={c.long_videos_per_week}")

    if todos:
        channel_manager.pause_channel(todos[0].id)
        logger.info(f"Canal '{todos[0].name}' pausado correctamente.")
    logger.info("Iniciando prueba del Core...")
    logger.info(f"Proveedor de IA configurado: {settings.ai_provider}")

    try:
        provider = GeminiProvider()
        respuesta = provider.generate(
            prompt="Responde solo con la palabra: funciona"
        )
        logger.info(f"Respuesta de la IA: {respuesta.strip()}")
        logger.info("✅ El Core funciona correctamente.")

    except BaseAppError as error:
        logger.error(f"❌ Fallo en el Core: {error}")


if __name__ == "__main__":
    main()
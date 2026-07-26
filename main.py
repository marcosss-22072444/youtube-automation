"""
main.py

Script de arranque/prueba del Core. Se irá ampliando en módulos
futuros para lanzar la app real.
"""

from core.logger import get_logger
from core.config import settings
from core.ai_providers.gemini_provider import GeminiProvider
from core.exceptions import BaseAppError
from core.schema import initialize_database

logger = get_logger(__name__)


def main():
    initialize_database()

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